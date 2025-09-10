import logging
import asyncio
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from ..database import db
from ..utils.notifications import notify_user_approved, notify_user_rejected
from ..security.audit_logger import audit_logger
from ..security.validator import validator
from ..security.rate_limiter import rate_limiter
from ..config import MESSAGES, ROLES, USER_STATUSES
logger = logging.getLogger(__name__)
router = Router()

async def delete_message_after_delay(message: Message, delay_seconds: int):
    """Удаляет сообщение через указанное количество секунд"""
    try:
        await asyncio.sleep(delay_seconds)
        await message.delete()
    except Exception as e:
        logger.warning(f"Failed to delete message after delay: {e}")

async def is_admin(telegram_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    user = await db.get_user_by_telegram_id(telegram_id)
    return user and user.role == ROLES['ADMIN'] and user.status == USER_STATUSES['APPROVED']
@router.callback_query(F.data.startswith("approve_user_"))

async def handle_approve_user_callback(callback: CallbackQuery):
    """Обработка одобрения заявки на регистрацию"""
    # Проверка rate limiting
    if not await rate_limiter.is_allowed(callback.from_user.id):
        await callback.answer("⏰ Слишком много запросов. Попробуйте позже.")
        return
    
    # Валидация Telegram ID
    is_valid, error = validator.validate_telegram_id(callback.from_user.id)
    if not is_valid:
        await callback.answer("❌ Ошибка валидации")
        return
    
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав")
        return
    try:
        user_id = int(callback.data.split('_')[2])
        # Проверка статуса пользователя
        user = await db.get_user_by_id(user_id)
        if not user or user.status != USER_STATUSES['PENDING']:
            await callback.answer("❌ Заявка уже обработана")
            return
        # Одобрение пользователя
        await db.update_user_status(user_id, USER_STATUSES['APPROVED'])
        # Логирование действия администратора
        audit_logger.log_admin_action(callback.from_user.id, "approve_user", user_id, {
            "user_name": user.full_name,
            "user_phone": user.phone_number,
            "user_apartment": user.apartment
        })
        # Уведомление пользователя
        from aiogram import Bot
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        from ..config import BOT_TOKEN
        try:
            notification_bot = Bot(
                token=BOT_TOKEN,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML)
            )
            await notify_user_approved(notification_bot, user)
            await notification_bot.session.close()
        except Exception as e:
            logger.warning(f"Could not send user notification: {e}")
        # Удаляем сообщение с заявкой
        await callback.message.delete()
        # Отправляем уведомление администратору
        notification_msg = await callback.message.answer("✅ Заявка одобрена")
        # Удаляем уведомление через 5 секунд
        asyncio.create_task(delete_message_after_delay(notification_msg, 5))
        await callback.answer()
        logger.info(f"User {user.full_name} (ID: {user_id}) approved by admin {callback.from_user.id}")
    except Exception as e:
        logger.error(f"Failed to approve user: {e}")
        await callback.answer("❌ Произошла ошибка")
@router.callback_query(F.data.startswith("reject_user_"))

async def handle_reject_user_callback(callback: CallbackQuery):
    """Обработка отклонения заявки на регистрацию"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав")
        return
    try:
        user_id = int(callback.data.split('_')[2])
        # Проверка статуса пользователя
        user = await db.get_user_by_id(user_id)
        if not user or user.status != USER_STATUSES['PENDING']:
            await callback.answer("❌ Заявка уже обработана")
            return
        # Отклонение пользователя
        await db.update_user_status(user_id, USER_STATUSES['REJECTED'])
        # Логирование действия администратора
        audit_logger.log_admin_action(callback.from_user.id, "reject_user", user_id, {
            "user_name": user.full_name,
            "user_phone": user.phone_number,
            "user_apartment": user.apartment
        })
        # Уведомление пользователя
        from aiogram import Bot
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        from ..config import BOT_TOKEN
        try:
            notification_bot = Bot(
                token=BOT_TOKEN,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML)
            )
            await notify_user_rejected(notification_bot, user)
            await notification_bot.session.close()
        except Exception as e:
            logger.warning(f"Could not send user notification: {e}")
        # Удаляем сообщение с заявкой
        await callback.message.delete()
        # Отправляем уведомление администратору
        notification_msg = await callback.message.answer("❌ Заявка отклонена")
        # Удаляем уведомление через 5 секунд
        asyncio.create_task(delete_message_after_delay(notification_msg, 5))
        await callback.answer()
        logger.info(f"User {user.full_name} (ID: {user_id}) rejected by admin {callback.from_user.id}")
    except Exception as e:
        logger.error(f"Failed to reject user: {e}")
        await callback.answer("❌ Произошла ошибка")

def register_admin_handlers(dp):
    """Регистрация обработчиков администраторов"""
    dp.include_router(router)
