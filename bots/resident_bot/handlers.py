"""
Обработчики для бота жителей
"""
import logging
import asyncio
import time
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import sys
import os

# Добавляем пути для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from easy_pass_bot.database import db
from easy_pass_bot.database.models import User, Pass
from easy_pass_bot.keyboards.resident_keyboards import get_resident_main_menu, get_resident_passes_keyboard, get_pass_creation_keyboard, get_approved_user_keyboard
from easy_pass_bot.utils.validators import validate_registration_form, validate_car_number
from easy_pass_bot.utils.notifications import notify_admins_new_registration
from easy_pass_bot.security.rate_limiter import rate_limiter
from easy_pass_bot.security.validator import validator
from easy_pass_bot.security.audit_logger import audit_logger
from easy_pass_bot.monitoring.metrics import metrics_collector
from easy_pass_bot.services.error_handler import error_handler
from easy_pass_bot.core.exceptions import ValidationError, DatabaseError
from easy_pass_bot.services.cache_service import cache_service
from easy_pass_bot.features.analytics import analytics_service
from easy_pass_bot.features.navigation import navigation_service
from config import RESIDENT_MESSAGES, ROLES, USER_STATUSES, PASS_STATUSES

logger = logging.getLogger(__name__)
router = Router()

async def is_resident(telegram_id: int) -> bool:
    """Проверка, является ли пользователь жителем"""
    user = await db.get_user_by_telegram_id(telegram_id)
    return user and user.role == ROLES['RESIDENT'] and user.status == USER_STATUSES['APPROVED']

@router.message(Command("start"))
async def start_command(message: Message):
    """Обработка команды /start с аналитикой"""
    user_id = message.from_user.id
    try:
        # Отслеживаем начало сессии
        analytics_service.start_session(user_id)
        analytics_service.track_action(user_id, "start_command")
        user = await db.get_user_by_telegram_id(user_id)
        if not user:
            # Новый пользователь - показываем форму регистрации
            analytics_service.track_page_view(user_id, "welcome_page")
            await message.answer(RESIDENT_MESSAGES['WELCOME'])
        elif user.status == USER_STATUSES['PENDING']:
            analytics_service.track_page_view(user_id, "pending_status")
            await message.answer("⏳ Ваша заявка на регистрацию находится на модерации.", reply_markup=get_approved_user_keyboard())
        elif user.status == USER_STATUSES['REJECTED']:
            analytics_service.track_page_view(user_id, "rejected_status")
            await message.answer(RESIDENT_MESSAGES['REGISTRATION_REJECTED'], reply_markup=get_approved_user_keyboard())
        elif user.role == ROLES['RESIDENT'] and user.status == USER_STATUSES['APPROVED']:
            analytics_service.track_page_view(user_id, "resident_main_menu")
            await message.answer("🏠 Главное меню", reply_markup=get_resident_main_menu())
        else:
            await message.answer("❌ У вас нет доступа к этому боту")
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await error_handler.handle_error(message, e)

@router.message(F.text == "📝 Подать заявку")
async def handle_create_pass_button(message: Message):
    """Обработка нажатия кнопки 'Подать заявку'"""
    if not await is_resident(message.from_user.id):
        await message.answer(RESIDENT_MESSAGES['NO_RIGHTS'])
        return
    
    # Проверка лимита активных пропусков
    user = await db.get_user_by_telegram_id(message.from_user.id)
    active_passes_count = await db.count_active_passes(user.id)
    
    if active_passes_count >= 3:  # MAX_ACTIVE_PASSES
        await message.answer(RESIDENT_MESSAGES['MAX_PASSES_REACHED'])
        return
    
    await message.answer(RESIDENT_MESSAGES['PASS_CREATION_REQUEST'], reply_markup=get_pass_creation_keyboard())

@router.message(F.text == "📋 Мои заявки")
async def handle_my_passes_button(message: Message):
    """Обработка нажатия кнопки 'Мои заявки'"""
    if not await is_resident(message.from_user.id):
        await message.answer(RESIDENT_MESSAGES['NO_RIGHTS'])
        return
    
    user = await db.get_user_by_telegram_id(message.from_user.id)
    passes = await db.get_user_passes(user.id)
    
    if not passes:
        await message.answer("📋 У вас нет активных заявок на пропуски", reply_markup=get_resident_passes_keyboard())
        return
    
    # Формируем сообщение с заявками
    text = "📋 Ваши заявки на пропуски:\n\n"
    for i, pass_obj in enumerate(passes, 1):
        status_emoji = {
            'active': '✅',
            'used': '🔴',
            'cancelled': '❌'
        }.get(pass_obj.status, '❓')
        
        text += f"{i}. {status_emoji} {pass_obj.car_number} - {pass_obj.status}\n"
        if pass_obj.created_at:
            text += f"   📅 Создана: {pass_obj.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        if pass_obj.used_at:
            text += f"   🚗 Использована: {pass_obj.used_at.strftime('%d.%m.%Y %H:%M')}\n"
        text += "\n"
    
    await message.answer(text, reply_markup=get_resident_passes_keyboard())

@router.message(F.text == "❌ Отмена")
async def handle_cancel_button(message: Message):
    """Обработка нажатия кнопки 'Отмена'"""
    if not await is_resident(message.from_user.id):
        await message.answer(RESIDENT_MESSAGES['NO_RIGHTS'])
        return
    
    await message.answer("❌ Действие отменено", reply_markup=get_resident_main_menu())

@router.message(F.text == "🔙 Назад")
async def handle_back_button(message: Message):
    """Обработка нажатия кнопки 'Назад'"""
    if not await is_resident(message.from_user.id):
        await message.answer(RESIDENT_MESSAGES['NO_RIGHTS'])
        return
    
    await message.answer("🔙 Возврат в главное меню", reply_markup=get_resident_main_menu())

@router.message(
    F.text & ~F.text.startswith('/') &
    ~F.text.in_([
        "📝 Подать заявку", "📋 Мои заявки", "❌ Отмена", "🔙 Назад"
    ])
)
async def handle_text_messages(message: Message):
    """Обработка текстовых сообщений от жителей"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    try:
        # Проверка rate limiting
        if not await rate_limiter.is_allowed(user_id):
            await message.answer("⏰ Слишком много запросов. Попробуйте позже.")
            return
        
        # Валидация Telegram ID
        is_valid, error = validator.validate_telegram_id(user_id)
        if not is_valid:
            await message.answer("❌ Ошибка валидации")
            return
        
        user = await db.get_user_by_telegram_id(user_id)
        
        if not user:
            # Регистрация нового пользователя
            await handle_registration(message, text)
        elif user.status == USER_STATUSES['PENDING']:
            await message.answer("⏳ Ваша заявка на регистрацию находится на модерации.")
        elif user.status == USER_STATUSES['REJECTED']:
            await message.answer(RESIDENT_MESSAGES['REGISTRATION_REJECTED'])
        elif user.role == ROLES['RESIDENT'] and user.status == USER_STATUSES['APPROVED']:
            # Создание пропуска
            await handle_pass_creation(message, text, user)
        else:
            await message.answer("❌ У вас нет доступа к этому боту")
            
    except Exception as e:
        logger.error(f"Error handling text message: {e}")
        await error_handler.handle_error(message, e)

async def handle_registration(message: Message, text: str):
    """Обработка регистрации нового пользователя"""
    try:
        # Валидация формы регистрации
        validation_result = validate_registration_form(text)
        if not validation_result:
            await message.answer(RESIDENT_MESSAGES['INVALID_FORMAT'])
            return
        
        # Используем данные из валидации
        full_name = validation_result['full_name']
        phone = validation_result['phone_number']
        apartment = validation_result['apartment']
        
        # Создание пользователя
        user = User(
            telegram_id=message.from_user.id,
            role=ROLES['RESIDENT'],
            full_name=full_name,
            phone_number=phone,
            apartment=apartment,
            status=USER_STATUSES['PENDING']
        )
        
        user_id = await db.create_user(user)
        user.id = user_id
        
        # Уведомление администраторов
        try:
            from aiogram import Bot
            from aiogram.client.default import DefaultBotProperties
            from aiogram.enums import ParseMode
            from config import RESIDENT_BOT_TOKEN
            
            notification_bot = Bot(
                token=RESIDENT_BOT_TOKEN,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML)
            )
            await notify_admins_new_registration(notification_bot, user)
            await notification_bot.session.close()
        except Exception as e:
            logger.warning(f"Could not send notifications: {e}")
        
        # Аналитика
        analytics_service.track_action(message.from_user.id, "user_registration")
        
        await message.answer(RESIDENT_MESSAGES['REGISTRATION_SENT'])
        
    except Exception as e:
        logger.error(f"Error in registration: {e}")
        await message.answer("❌ Ошибка при регистрации. Попробуйте позже.")

async def handle_pass_creation(message: Message, text: str, user: User):
    """Обработка создания пропуска"""
    try:
        # Валидация номера автомобиля
        is_valid = validate_car_number(text)
        if not is_valid:
            await message.answer(RESIDENT_MESSAGES['ENTER_CAR_NUMBER'])
            return
        
        # Проверка дублирования
        if await db.check_duplicate_pass(user.id, text):
            await message.answer(RESIDENT_MESSAGES['DUPLICATE_PASS'])
            return
        
        # Создание пропуска
        pass_obj = Pass(
            user_id=user.id,
            car_number=text,
            status=PASS_STATUSES['ACTIVE']
        )
        
        pass_id = await db.create_pass(pass_obj)
        
        # Аналитика
        analytics_service.track_action(message.from_user.id, "pass_created")
        
        await message.answer(
            RESIDENT_MESSAGES['PASS_CREATED'].format(car_number=text),
            reply_markup=get_resident_main_menu()
        )
        
    except Exception as e:
        logger.error(f"Error creating pass: {e}")
        await message.answer("❌ Ошибка при создании заявки. Попробуйте позже.")

@router.callback_query(F.data.startswith("cancel_pass_"))
async def handle_cancel_pass_callback(callback: CallbackQuery):
    """Обработка отмены пропуска"""
    if not await is_resident(callback.from_user.id):
        await callback.answer(RESIDENT_MESSAGES['NO_RIGHTS'])
        return
    
    try:
        pass_id = int(callback.data.split('_')[2])
        
        # Обновление статуса пропуска
        await db.update_pass_status(pass_id, PASS_STATUSES['CANCELLED'])
        
        await callback.answer("✅ Заявка отменена")
        await callback.message.edit_text("✅ Заявка отменена", reply_markup=get_resident_main_menu())
        
    except Exception as e:
        logger.error(f"Error cancelling pass: {e}")
        await callback.answer("❌ Ошибка при отмене заявки")

def register_resident_handlers(dp):
    """Регистрация обработчиков для жителей"""
    dp.include_router(router)
    logger.info("Resident handlers registered successfully")
