import logging
import aiosqlite
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup
from ..database import db
from ..keyboards.admin_keyboards import get_admin_approval_keyboard
from ..keyboards.resident_keyboards import get_resident_main_menu, get_approved_user_keyboard
from ..config import MESSAGES
logger = logging.getLogger(__name__)

async def notify_admins_new_registration(bot: Bot, user):
    """Уведомление администраторов о новой заявке на регистрацию"""
    try:
        admins = await db.get_admin_users()
        text = f"""🔔 Новая заявка на регистрацию
👤 ФИО: {user.full_name}
📱 Телефон: {user.phone_number}
🏠 Квартира: {user.apartment}"""
        keyboard = get_admin_approval_keyboard(user.id)
        for admin in admins:
            try:
                await bot.send_message(
                    chat_id=admin.telegram_id,
                    text=text,
                    reply_markup=keyboard
                )
                logger.info(f"Notification sent to admin {admin.full_name} (TG: {admin.telegram_id})")
            except Exception as e:
                logger.error(f"Failed to notify admin {admin.telegram_id}: {e}")
    except Exception as e:
        logger.error(f"Failed to notify admins about new registration: {e}")

async def notify_user_approved(bot: Bot, user):
    """Уведомление пользователя об одобрении регистрации"""
    try:
        text = MESSAGES['REGISTRATION_APPROVED']
        keyboard = get_approved_user_keyboard()
        await bot.send_message(
            chat_id=user.telegram_id,
            text=text,
            reply_markup=keyboard
        )
        logger.info(f"Approval notification sent to user {user.full_name} (TG: {user.telegram_id})")
    except Exception as e:
        logger.error(f"Failed to notify user {user.telegram_id} about approval: {e}")

async def notify_user_rejected(bot: Bot, user):
    """Уведомление пользователя об отклонении регистрации"""
    try:
        text = MESSAGES['REGISTRATION_REJECTED']
        await bot.send_message(
            chat_id=user.telegram_id,
            text=text
        )
        logger.info(f"Rejection notification sent to user {user.full_name} (TG: {user.telegram_id})")
    except Exception as e:
        logger.error(f"Failed to notify user {user.telegram_id} about rejection: {e}")

async def get_security_users():
    """Получение всех сотрудников охраны"""
    try:
        async with aiosqlite.connect(db.db_path) as db_conn:
            async with db_conn.execute("""
                SELECT id, telegram_id, role, full_name, phone_number, apartment, status, created_at, updated_at
                FROM users WHERE role = 'security' AND status = 'approved'
            """) as cursor:
                rows = await cursor.fetchall()
                from database.models import User
                return [
                    User(
                        id=row[0], telegram_id=row[1], role=row[2], full_name=row[3],
                        phone_number=row[4], apartment=row[5], status=row[6],
                        created_at=row[7], updated_at=row[8]
                    ) for row in rows
                ]
    except Exception as e:
        logger.error(f"Failed to get security users: {e}")
        return []
