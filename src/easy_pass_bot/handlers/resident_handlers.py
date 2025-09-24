import logging
import asyncio
import time
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import Command
from ..database import db
from ..database.models import User, Pass
from ..keyboards.resident_keyboards import get_resident_main_menu, get_resident_passes_keyboard, get_pass_creation_keyboard, get_approved_user_keyboard
from ..utils.validators import validate_registration_form, validate_car_number
from ..utils.notifications import notify_admins_new_registration
from ..security.rate_limiter import rate_limiter
from ..security.validator import validator
from ..security.audit_logger import audit_logger
from ..monitoring.metrics import metrics_collector
from ..services.error_handler import error_handler
from ..core.exceptions import ValidationError, DatabaseError
from ..services.cache_service import cache_service
from ..features.analytics import analytics_service
from ..features.navigation import navigation_service
from ..config import MESSAGES, ROLES, USER_STATUSES, PASS_STATUSES, BOT_TOKEN
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
            await message.answer(MESSAGES['WELCOME'])
        elif user.status == USER_STATUSES['PENDING']:
            analytics_service.track_page_view(user_id, "pending_status")
            await message.answer("⏳ Ваша заявка на регистрацию находится на модерации.", reply_markup=get_approved_user_keyboard())
        elif user.status == USER_STATUSES['REJECTED']:
            analytics_service.track_page_view(user_id, "rejected_status")
            await message.answer(MESSAGES['REGISTRATION_REJECTED'], reply_markup=get_approved_user_keyboard())
        elif user.role == ROLES['RESIDENT'] and user.status == USER_STATUSES['APPROVED']:
            analytics_service.track_page_view(user_id, "resident_main_menu")
            navigation_service.add_to_history(user_id, "resident_main_menu")
            await message.answer("🏠 Добро пожаловать в PM Desk!", reply_markup=get_approved_user_keyboard())
        elif user.role == ROLES['ADMIN'] and user.status == USER_STATUSES['APPROVED']:
            await message.answer(
                "👑 Добро пожаловать в панель администратора PM Desk. Здесь вы сможете управлять входящими заявками на регистрацию в системе.",
                reply_markup=ReplyKeyboardRemove()
            )
        elif user.role == ROLES['SECURITY'] and user.status == USER_STATUSES['APPROVED']:
            analytics_service.track_page_view(user_id, "security_main_menu")
            navigation_service.add_to_history(user_id, "security_main_menu")
            from ..keyboards.security_keyboards import get_security_main_menu
            await message.answer("Нажмите на кнопку \"🔍 Найти пропуск\" для поиска заявки. После открытия шлагбаума отметьте пропуск как использованный, нажав \"✅\" под пропуском.", reply_markup=get_security_main_menu())
    except Exception as e:
        # Обрабатываем ошибку через централизованный обработчик
        error_response = await error_handler.handle_error(e, {'user_id': user_id, 'action': 'start_command'})
        await message.answer(error_response)
        analytics_service.track_action(user_id, "start_command", success=False)
@router.message(F.text.contains(","))

async def handle_registration(message: Message):
    """Обработка регистрации жителя (1 шаг)"""
    user_id = message.from_user.id
    start_time = time.time()
    # Проверка rate limiting
    if not await rate_limiter.is_allowed(user_id):
        remaining_time = rate_limiter.get_block_time_remaining(user_id)
        if remaining_time:
            await message.answer(f"⏳ Слишком много запросов. Попробуйте через {int(remaining_time)} секунд.")
            audit_logger.log_rate_limit_exceeded(user_id, 15)
            metrics_collector.record_user_action("registration", user_id, False)
        return
    user = await db.get_user_by_telegram_id(user_id)
    if user:
        await message.answer("Вы уже зарегистрированы в системе.", reply_markup=get_approved_user_keyboard())
        return
    # Валидация формы с улучшенной безопасностью
    is_valid, error_msg, form_data = validator.validate_registration_data(message.text)
    if not is_valid:
        await message.answer(error_msg or MESSAGES['INVALID_FORMAT'], reply_markup=get_approved_user_keyboard())
        audit_logger.log_failed_attempt(user_id, "registration", error_msg or "Invalid format")
        return
    # Создание пользователя
    new_user = User(
        telegram_id=message.from_user.id,
        role=ROLES['RESIDENT'],
        full_name=form_data['full_name'],
        phone_number=form_data['phone_number'],
        apartment=form_data['apartment'],
        status=USER_STATUSES['PENDING']
    )
    try:
        user_id = await db.create_user(new_user)
        new_user.id = user_id
        # Логирование успешной регистрации
        audit_logger.log_user_registration(user_id, form_data)
        # Уведомление администраторов
        # Создаем новый экземпляр бота для уведомлений
        from aiogram import Bot
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        try:
            notification_bot = Bot(
                token=BOT_TOKEN,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML)
            )
            await notify_admins_new_registration(notification_bot, new_user)
            await notification_bot.session.close()
        except Exception as e:
            logger.warning(f"Could not send notifications: {e}")
        # Отправляем уведомление
        await message.answer(MESSAGES['REGISTRATION_SENT'])
        # Записываем метрики
        duration = time.time() - start_time
        metrics_collector.record_response_time(
            "registration", duration, "success", user_id
        )
        metrics_collector.record_user_action("registration", user_id, True)
        logger.info(f"New user registered: {new_user.full_name} (ID: {user_id})")
    except Exception as e:
        duration = time.time() - start_time
        metrics_collector.record_response_time(
            "registration", duration, "error", user_id
        )
        metrics_collector.record_user_action("registration", user_id, False)
        metrics_collector.record_error("registration_error", "registration", user_id, str(e))
        logger.error(f"Failed to register user: {e}")
        await message.answer(
            "❌ Произошла ошибка при регистрации. Попробуйте позже.",
            reply_markup=get_approved_user_keyboard()
        )
@router.message(F.text == "📝 Подать заявку")

async def handle_create_pass_message(message: Message):
    """Обработка нажатия кнопки 'Подать заявку'"""
    logger.info(f"Create pass message from user {message.from_user.id}")
    try:
        if not await is_resident(message.from_user.id):
            logger.warning(f"User {message.from_user.id} is not a resident")
            await message.answer("❌ Нет прав", reply_markup=get_approved_user_keyboard())
            return
        logger.info(f"User {message.from_user.id} is a resident, showing pass creation form")
        keyboard = get_pass_creation_keyboard()
        await message.answer(MESSAGES['PASS_CREATION_REQUEST'], reply_markup=keyboard)
        logger.info(f"Pass creation form shown to user {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in handle_create_pass_message: {e}")
        await message.answer("❌ Произошла ошибка", reply_markup=get_approved_user_keyboard())
@router.message(F.text == "❌ Отмена")

async def handle_cancel_pass_creation_message(message: Message):
    """Обработка отмены создания заявки"""
    logger.info(f"Cancel button pressed by user {message.from_user.id}")
    if not await is_resident(message.from_user.id):
        await message.answer("❌ Нет прав", reply_markup=get_approved_user_keyboard())
        return
    # Заменяем клавиатуру на главное меню
    keyboard = get_approved_user_keyboard()
    await message.answer("✅ Создание заявки отменено\n\n🏠 Добро пожаловать в PM Desk!", reply_markup=keyboard)
    logger.info(f"User {message.from_user.id} returned to main menu")
@router.message(F.text == "📋 Мои заявки")

async def handle_my_passes_message(message: Message):
    """Обработка просмотра заявок жителя"""
    if not await is_resident(message.from_user.id):
        await message.answer("❌ Нет прав", reply_markup=get_approved_user_keyboard())
        return
    user = await db.get_user_by_telegram_id(message.from_user.id)
    passes = await db.get_user_passes(user.id)
    if not passes:
        text = "📋 У вас пока нет заявок на пропуска"
    else:
        text = "📋 Ваши заявки на пропуска:\n\n"
        for pass_obj in passes:
            status_emoji = "🟢" if pass_obj.status == PASS_STATUSES['ACTIVE'] else "🔴"
            status_text = "Активна" if pass_obj.status == PASS_STATUSES['ACTIVE'] else "Использована"
            text += f"{status_emoji} {pass_obj.car_number} - {status_text}\n"
            text += f"📅 {pass_obj.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
    await message.answer(text, reply_markup=get_resident_passes_keyboard())
@router.message(F.text.regexp(r'^[А-Яа-яA-Za-z]\d{3}[А-Яа-яA-Za-z]{2}\d{3}$'))

async def handle_resident_text(message: Message):
    """Обработка текстовых сообщений от жителей"""
    user_id = message.from_user.id
    logger.info(f"TEXT MESSAGE RECEIVED from user {user_id}, text: '{message.text}'")
    # Проверка rate limiting
    if not await rate_limiter.is_allowed(user_id):
        remaining_time = rate_limiter.get_block_time_remaining(user_id)
        if remaining_time:
            await message.answer(f"⏳ Слишком много запросов. Попробуйте через {int(remaining_time)} секунд.")
            audit_logger.log_rate_limit_exceeded(user_id, 15)
        return
    # Проверяем, является ли пользователь жителем
    if not await is_resident(user_id):
        logger.info(f"User {user_id} is not a resident, skipping")
        # Если не житель, не обрабатываем сообщение, но не блокируем передачу дальше
        return
    text = message.text.strip()
    logger.info(f"Text message from resident {message.from_user.id}: {text}")
    # Игнорируем кнопки клавиатуры
    if text in ["📝 Подать заявку", "📋 Мои заявки"]:
        return
    # Проверяем, соответствует ли текст формату номера автомобиля
    import re
    pattern = r'^[А-Яа-яA-Za-z]\d{3}[А-Яа-яA-Za-z]{2}\d{3}$'
    if re.match(pattern, text):
        logger.info(f"Text matches car number pattern: {text}")
        await handle_pass_creation_internal(message, text)
    else:
        logger.info(f"Text does not match car number pattern: {text}")
        # Если это не номер автомобиля, игнорируем

async def handle_pass_creation_internal(message: Message, car_number: str):
    """Внутренняя функция обработки создания заявки на пропуск"""
    user_id = message.from_user.id
    logger.info(f"Processing car number: {car_number}")
    # Преобразуем маленькие буквы в заглавные
    car_number = car_number.upper()
    logger.info(f"Converted to uppercase: {car_number}")
    # Улучшенная валидация номера
    is_valid, error_msg = validator.validate_car_number(car_number)
    if not is_valid:
        logger.warning(f"Invalid car number: {car_number} - {error_msg}")
        await message.answer(error_msg or MESSAGES['ENTER_CAR_NUMBER'], reply_markup=get_pass_creation_keyboard())
        audit_logger.log_failed_attempt(user_id, "pass_creation", error_msg or "Invalid car number")
        return
    user = await db.get_user_by_telegram_id(message.from_user.id)
    # Проверка лимитов убрана - пользователи могут создавать неограниченное количество заявок
    # Проверка дублирования
    if await db.check_duplicate_pass(user.id, car_number):
        await message.answer(MESSAGES['DUPLICATE_PASS'], reply_markup=get_approved_user_keyboard())
        return
    # Создание заявки
    pass_obj = Pass(
        user_id=user.id,
        car_number=car_number,
        status=PASS_STATUSES['ACTIVE']
    )
    try:
        pass_id = await db.create_pass(pass_obj)
        pass_obj.id = pass_id
        # Уведомления охранникам отключены - они работают только через поиск
        # Логирование успешного создания пропуска
        audit_logger.log_pass_creation(user_id, car_number)
        await message.answer(MESSAGES['PASS_CREATED'].format(car_number=car_number), reply_markup=get_approved_user_keyboard())
        logger.info(f"New pass created: {car_number} by user {user.full_name}")
    except Exception as e:
        logger.error(f"Failed to create pass: {e}")
        await message.answer("❌ Произошла ошибка при создании заявки. Попробуйте позже.", reply_markup=get_approved_user_keyboard())

def register_resident_handlers(dp):
    """Регистрация обработчиков жителей"""
    logger.info("Registering resident handlers")
    dp.include_router(router)
    logger.info("Resident handlers registered successfully")
