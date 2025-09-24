"""
Обработчики для администраторов
"""
import logging
import asyncio
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
import sys
import os

# Добавляем пути для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from easy_pass_bot.database import db
from easy_pass_bot.utils.notifications import notify_user_approved, notify_user_rejected
from easy_pass_bot.security.audit_logger import audit_logger
from easy_pass_bot.security.validator import validator
from easy_pass_bot.security.rate_limiter import rate_limiter
from config import SECURITY_MESSAGES, ROLES, USER_STATUSES

logger = logging.getLogger(__name__)
router = Router()

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
        
        # Уведомление пользователя
        try:
            from aiogram import Bot
            from aiogram.client.default import DefaultBotProperties
            from aiogram.enums import ParseMode
            from config import SECURITY_BOT_TOKEN
            
            notification_bot = Bot(
                token=SECURITY_BOT_TOKEN,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML)
            )
            await notify_user_approved(notification_bot, user)
            await notification_bot.session.close()
        except Exception as e:
            logger.warning(f"Could not send approval notification: {e}")
        
        # Аудит
        audit_logger.log_admin_action(
            callback.from_user.id,
            "approve_user",
            user_id,
            {"user_name": user.full_name, "user_phone": user.phone_number}
        )
        
        await callback.answer(SECURITY_MESSAGES['USER_APPROVED'])
        await callback.message.edit_text(f"✅ Пользователь {user.full_name} одобрен")
        
    except Exception as e:
        logger.error(f"Error approving user: {e}")
        await callback.answer("❌ Ошибка при одобрении пользователя")

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
        
        # Уведомление пользователя
        try:
            from aiogram import Bot
            from aiogram.client.default import DefaultBotProperties
            from aiogram.enums import ParseMode
            from config import SECURITY_BOT_TOKEN
            
            notification_bot = Bot(
                token=SECURITY_BOT_TOKEN,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML)
            )
            await notify_user_rejected(notification_bot, user)
            await notification_bot.session.close()
        except Exception as e:
            logger.warning(f"Could not send rejection notification: {e}")
        
        # Аудит
        audit_logger.log_admin_action(
            callback.from_user.id,
            "reject_user",
            user_id,
            {"user_name": user.full_name, "user_phone": user.phone_number}
        )
        
        await callback.answer(SECURITY_MESSAGES['USER_REJECTED'])
        await callback.message.edit_text(f"❌ Пользователь {user.full_name} отклонен")
        
    except Exception as e:
        logger.error(f"Error rejecting user: {e}")
        await callback.answer("❌ Ошибка при отклонении пользователя")

@router.callback_query(F.data.startswith("block_user_"))
async def handle_block_user_callback(callback: CallbackQuery):
    """Обработка блокировки пользователя"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав")
        return
    
    try:
        user_id = int(callback.data.split('_')[2])
        
        # Получаем пользователя
        user = await db.get_user_by_id(user_id)
        if not user:
            await callback.answer("❌ Пользователь не найден")
            return
        
        # Блокируем пользователя
        await db.block_user(user_id, "2025-12-31 23:59:59", "Заблокирован администратором")
        
        # Аудит
        await audit_logger.log_action(
            callback.from_user.id,
            "block_user",
            f"Blocked user {user_id} ({user.full_name})"
        )
        
        await callback.answer(SECURITY_MESSAGES['USER_BLOCKED'])
        await callback.message.edit_text(f"🚫 Пользователь {user.full_name} заблокирован")
        
    except Exception as e:
        logger.error(f"Error blocking user: {e}")
        await callback.answer("❌ Ошибка при блокировке пользователя")

@router.callback_query(F.data.startswith("unblock_user_"))
async def handle_unblock_user_callback(callback: CallbackQuery):
    """Обработка разблокировки пользователя"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав")
        return
    
    try:
        user_id = int(callback.data.split('_')[2])
        
        # Получаем пользователя
        user = await db.get_user_by_id(user_id)
        if not user:
            await callback.answer("❌ Пользователь не найден")
            return
        
        # Разблокируем пользователя
        await db.unblock_user(user_id)
        
        # Аудит
        await audit_logger.log_action(
            callback.from_user.id,
            "unblock_user",
            f"Unblocked user {user_id} ({user.full_name})"
        )
        
        await callback.answer(SECURITY_MESSAGES['USER_UNBLOCKED'])
        await callback.message.edit_text(f"✅ Пользователь {user.full_name} разблокирован")
        
    except Exception as e:
        logger.error(f"Error unblocking user: {e}")
        await callback.answer("❌ Ошибка при разблокировке пользователя")

def register_admin_handlers(dp):
    """Регистрация обработчиков для администраторов"""
    dp.include_router(router)
    logger.info("Admin handlers registered successfully")
