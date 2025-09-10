import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from ..security.rate_limiter import rate_limiter
from ..security.validator import validator
logger = logging.getLogger(__name__)
router = Router()
@router.message(Command("help"))

async def help_command(message: Message):
    """Обработка команды /help"""
    # Проверка rate limiting
    if not await rate_limiter.is_allowed(message.from_user.id):
        await message.answer("⏰ Слишком много запросов. Попробуйте позже.")
        return
    
    # Валидация Telegram ID
    is_valid, error = validator.validate_telegram_id(message.from_user.id)
    if not is_valid:
        await message.answer("❌ Ошибка валидации")
        return
    help_text = """🤖 Easy Pass - Система управления пропусками
📋 Доступные команды:
/start - Главное меню
/help - Справка
/search - Поиск пропуска (для охраны)
/new - Новая заявка (для жителей)
🏠 Для жителей:
• Регистрация в 1 шаг
• Подача заявок на пропуска
• Просмотр своих заявок
🛡️ Для охраны:
• Поиск пропусков по номеру
• Отметка использования
👑 Для администраторов:
• Модерация заявок через уведомления
💡 Принцип работы: "Один клик - одно действие"
    """
    await message.answer(help_text)
@router.message(Command("new"))

async def new_pass_command(message: Message):
    """Быстрая команда для создания новой заявки"""
    from ..database import db
    from ..config import ROLES, USER_STATUSES, MESSAGES
    from ..keyboards.resident_keyboards import get_resident_main_menu
    user = await db.get_user_by_telegram_id(message.from_user.id)
    if not user or user.role != ROLES['RESIDENT'] or user.status != USER_STATUSES['APPROVED']:
        await message.answer("❌ Нет прав")
        return
    await message.answer(MESSAGES['PASS_CREATION_REQUEST'])

def register_common_handlers(dp):
    """Регистрация общих обработчиков"""
    dp.include_router(router)
