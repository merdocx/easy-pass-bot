import time
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from ..database import db
from ..database.models import User
from ..keyboards.security_keyboards import get_security_main_menu, get_pass_search_keyboard, get_passes_list_keyboard, get_approved_user_keyboard
from ..utils.validators import validate_car_number
from ..utils.notifications import notify_admins_new_registration
from ..security.rate_limiter import rate_limiter
from ..security.validator import validator
from ..security.audit_logger import audit_logger
from ..monitoring.metrics import metrics_collector
from ..features.analytics import analytics_service
from ..core.exceptions import ValidationError, DatabaseError
from ..core.logging import get_logger, log_user_action, log_performance, log_error
from ..config import MESSAGES, ROLES, USER_STATUSES, PASS_STATUSES, BOT_TOKEN
logger = get_logger(__name__)
router = Router()

async def is_security(telegram_id: int) -> bool:
    """Проверка, является ли пользователь сотрудником охраны"""
    user = await db.get_user_by_telegram_id(telegram_id)
    return user and user.role == ROLES['SECURITY'] and user.status == USER_STATUSES['APPROVED']

async def is_admin(telegram_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    user = await db.get_user_by_telegram_id(telegram_id)
    return user and user.role == ROLES['ADMIN'] and user.status == USER_STATUSES['APPROVED']

async def is_staff(telegram_id: int) -> bool:
    """Проверка, является ли пользователь персоналом (админ или охранник)"""
    return await is_security(telegram_id) or await is_admin(telegram_id)

@router.message(Command("start"))
async def start_command(message: Message):
    """Обработка команды /start для персонала"""
    user_id = message.from_user.id
    try:
        # Отслеживаем начало сессии
        analytics_service.start_session(user_id)
        analytics_service.track_action(user_id, "start_command")
        log_user_action(logger, user_id, "start_command")
        
        user = await db.get_user_by_telegram_id(user_id)
        if not user:
            # Новый пользователь - показываем форму регистрации для персонала
            analytics_service.track_page_view(user_id, "staff_welcome_page")
            await message.answer(MESSAGES['WELCOME_STAFF'])
        elif user.status == USER_STATUSES['PENDING']:
            analytics_service.track_page_view(user_id, "pending_status")
            await message.answer("⏳ Ваша заявка на регистрацию находится на модерации.", reply_markup=get_approved_user_keyboard())
        elif user.status == USER_STATUSES['REJECTED']:
            analytics_service.track_page_view(user_id, "rejected_status")
            await message.answer(MESSAGES['REGISTRATION_REJECTED'], reply_markup=get_approved_user_keyboard())
        elif user.role == ROLES['SECURITY'] and user.status == USER_STATUSES['APPROVED']:
            analytics_service.track_page_view(user_id, "security_main_menu")
            await message.answer(
                "Нажмите на кнопку \"🔍 Найти пропуск\" для поиска заявки. После открытия шлагбаума отметьте пропуск как использованный, нажав \"✅\" под пропуском.",
                reply_markup=get_security_main_menu()
            )
        elif user.role == ROLES['ADMIN'] and user.status == USER_STATUSES['APPROVED']:
            analytics_service.track_page_view(user_id, "admin_main_menu")
            await message.answer(
                "👑 Добро пожаловать в панель администратора PM Desk. Здесь вы сможете управлять входящими заявками на регистрацию в системе.",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            # Если пользователь не персонал, отправляем обычное приветствие
            await message.answer(MESSAGES['WELCOME_STAFF'])
    except Exception as e:
        log_error(logger, e, {"user_id": user_id, "action": "start_command"})
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")

@router.message(F.text.contains(","))
async def handle_staff_registration(message: Message):
    """Обработка регистрации персонала (админы и охранники) - формат "ФИО, Телефон" """
    user_id = message.from_user.id
    start_time = time.time()
    
    # Проверка rate limiting
    if not await rate_limiter.is_allowed(user_id):
        remaining_time = rate_limiter.get_block_time_remaining(user_id)
        if remaining_time:
            await message.answer(f"⏳ Слишком много запросов. Попробуйте через {int(remaining_time)} секунд.")
            audit_logger.log_rate_limit_exceeded(user_id, 15)
            metrics_collector.record_user_action("staff_registration", user_id, False)
        return
    
    # Проверяем, что пользователь еще не зарегистрирован
    user = await db.get_user_by_telegram_id(user_id)
    if user:
        if user.role in [ROLES['SECURITY'], ROLES['ADMIN']]:
            await message.answer("Вы уже зарегистрированы в системе.", reply_markup=get_approved_user_keyboard())
        else:
            await message.answer("Вы уже зарегистрированы как житель.", reply_markup=get_approved_user_keyboard())
        return
    
    # Валидация формы регистрации персонала
    is_valid, error_msg, form_data = validator.validate_staff_registration_data(message.text)
    if not is_valid:
        await message.answer(error_msg or MESSAGES['INVALID_FORMAT_STAFF'], reply_markup=get_approved_user_keyboard())
        audit_logger.log_failed_attempt(user_id, "staff_registration", error_msg or "Invalid format")
        return
    
    # Определяем роль пользователя (по умолчанию SECURITY, админы создаются вручную)
    role = ROLES['SECURITY']
    
    # Создание пользователя персонала
    new_user = User(
        telegram_id=message.from_user.id,
        role=role,
        full_name=form_data['full_name'],
        phone_number=form_data['phone_number'],
        apartment="N/A",  # Для персонала квартира не требуется
        status=USER_STATUSES['PENDING']
    )
    
    try:
        user_id = await db.create_user(new_user)
        new_user.id = user_id
        
        # Логирование успешной регистрации
        audit_logger.log_user_registration(user_id, form_data)
        
        # Уведомление администраторов
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
            "staff_registration", duration, "success", user_id
        )
        metrics_collector.record_user_action("staff_registration", user_id, True)
        logger.info(f"New staff user registered: {new_user.full_name} (ID: {user_id}, Role: {role})")
        
    except Exception as e:
        duration = time.time() - start_time
        metrics_collector.record_response_time(
            "staff_registration", duration, "error", user_id
        )
        metrics_collector.record_user_action("staff_registration", user_id, False)
        metrics_collector.record_error("staff_registration_error", "staff_registration", user_id, str(e))
        logger.error(f"Failed to register staff user: {e}")
        await message.answer(
            "❌ Произошла ошибка при регистрации. Попробуйте позже.",
            reply_markup=get_approved_user_keyboard()
        )

@router.message(Command("search"))

async def search_command(message: Message):
    """Быстрый поиск через команду /search"""
    if not await is_security(message.from_user.id):
        await message.answer("❌ Нет прав", reply_markup=ReplyKeyboardRemove())
        return
    await message.answer("🔍 Введите номер автомобиля для поиска:", reply_markup=get_pass_search_keyboard())
@router.message(F.text == "🔍 Найти пропуск")

async def handle_search_pass_message(message: Message):
    """Обработка нажатия кнопки 'Найти пропуск'"""
    logger.info(f"SECURITY SEARCH BUTTON PRESSED by user {message.from_user.id}, text: '{message.text}'")
    if not await is_security(message.from_user.id):
        logger.warning(f"User {message.from_user.id} is not security")
        await message.answer("❌ Нет прав", reply_markup=ReplyKeyboardRemove())
        return
    logger.info(f"Security user {message.from_user.id} starting search")
    await message.answer(
        "🔍 Введите номер автомобиля для поиска:",
        reply_markup=get_pass_search_keyboard()
    )
@router.message(
    F.text & ~F.text.startswith('/') &
    ~F.text.in_([
        "🔍 Найти пропуск", "✅ Отметить использованным", "🔙 Назад",
        "📝 Подать заявку", "📋 Мои заявки", "❌ Отмена"
    ])
)

async def handle_security_text_messages(message: Message):
    """Обработка текстовых сообщений от охранников (кроме команд и кнопок)"""
    # Сначала проверяем, является ли пользователь охранником
    if not await is_security(message.from_user.id):
        # Если не охранник, пропускаем без return (чтобы сообщение передалось дальше)
        return
    logger.info(f"SECURITY TEXT MESSAGE from user {message.from_user.id}, text: '{message.text}'")
    # Обрабатываем как поиск по номеру машины
    await handle_pass_search_internal(message)
@router.message(F.text == "🔙 Назад")

async def handle_back_pass_search_message(message: Message):
    """Возврат в главное меню охранника"""
    if not await is_security(message.from_user.id):
        await message.answer("❌ Нет прав", reply_markup=ReplyKeyboardRemove())
        return
    await message.answer("Нажмите на кнопку \"🔍 Найти пропуск\" для поиска заявки. После открытия шлагбаума отметьте пропуск как использованный, нажав \"✅\" под пропуском.", reply_markup=get_security_main_menu())
@router.message(F.text.regexp(r'^\d{1,3}$'))

async def handle_security_text(message: Message):
    """Обработка текстовых сообщений от охранника (только для охранников)"""
    user_id = message.from_user.id
    logger.info(f"SECURITY TEXT MESSAGE from user {user_id}, text: '{message.text}'")
    # Проверка rate limiting
    if not await rate_limiter.is_allowed(user_id):
        remaining_time = rate_limiter.get_block_time_remaining(user_id)
        if remaining_time:
            await message.answer(f"⏳ Слишком много запросов. Попробуйте через {int(remaining_time)} секунд.")
            audit_logger.log_rate_limit_exceeded(user_id, 15)
        return
    # Сначала проверяем, является ли пользователь охранником
    if not await is_security(user_id):
        logger.info(f"User {user_id} is not security, skipping")
        return  # Не обрабатываем сообщения от не-охранников
    # Игнорируем кнопки клавиатуры
    if message.text in ["🔍 Найти пропуск", "✅ Отметить использованным", "🔙 Назад"]:
        return
    # Обрабатываем как поиск по номеру машины
    await handle_pass_search_internal(message)
@router.message(F.text.regexp(r'^[А-Яа-я]\d{3}[А-Яа-я]{2}\d{3}$'))

async def handle_pass_search(message: Message):
    """Обработка поиска пропуска по номеру автомобиля (полный формат)"""
    user_id = message.from_user.id
    logger.info(f"SECURITY PASS SEARCH by user {user_id}, text: '{message.text}'")
    # Проверка rate limiting
    if not await rate_limiter.is_allowed(user_id):
        remaining_time = rate_limiter.get_block_time_remaining(user_id)
        if remaining_time:
            await message.answer(f"⏳ Слишком много запросов. Попробуйте через {int(remaining_time)} секунд.")
            audit_logger.log_rate_limit_exceeded(user_id, 15)
        return
    if not await is_security(user_id):
        logger.warning(f"User {user_id} is not security")
        return
    await handle_pass_search_internal(message)

async def handle_pass_search_internal(message: Message):
    """Внутренняя функция поиска пропуска"""
    user_id = message.from_user.id
    car_number = message.text.strip().upper()  # Приводим к верхнему регистру
    # Валидация поискового запроса
    is_valid, error_msg = validator.validate_search_query(car_number)
    if not is_valid:
        await message.answer(error_msg or MESSAGES['ENTER_CAR_NUMBER'], reply_markup=get_pass_search_keyboard())
        audit_logger.log_failed_attempt(user_id, "pass_search", error_msg or "Invalid search query")
        return
    # Если введен полный номер, валидируем его
    if len(car_number) > 3 and not validate_car_number(car_number):
        await message.answer(MESSAGES['ENTER_CAR_NUMBER'], reply_markup=get_pass_search_keyboard())
        audit_logger.log_failed_attempt(user_id, "pass_search", "Invalid car number format")
        return
    # Ищем все пропуски по номеру (полному или частичному)
    passes = await db.find_all_passes_by_car_number(car_number)
    # Логирование поиска
    audit_logger.log_successful_action(user_id, "pass_search", {
        "search_query": car_number,
        "results_count": len(passes)
    })
    if not passes:
        await message.answer(f"❌ Пропусков с номером, содержащим '{car_number}', не найдено", reply_markup=get_security_main_menu())
        return
    # Показываем все найденные пропуски с inline-кнопками
    text = f"🔍 Найдено пропусков: {len(passes)}\n\n"
    for i, pass_obj in enumerate(passes, 1):
        user = await db.get_user_by_id(pass_obj.user_id)
        created_at_str = pass_obj.created_at.strftime('%d.%m.%Y %H:%M') if hasattr(pass_obj.created_at, 'strftime') else str(pass_obj.created_at)
        text += f"{i}. {pass_obj.car_number}\n"
        text += f"   👤 {user.full_name} (кв. {user.apartment})\n"
        text += f"   📅 {created_at_str}\n\n"
    # Создаем клавиатуру с кнопками для каждого пропуска
    keyboard = get_passes_list_keyboard(passes)
    await message.answer(text, reply_markup=keyboard)
@router.callback_query(F.data.startswith("use_pass_"))

async def handle_use_pass_callback(callback: CallbackQuery):
    """Обработка отметки использования пропуска через callback"""
    if not await is_security(callback.from_user.id):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    # Извлекаем ID пропуска из callback_data
    pass_id = int(callback.data.split("_")[2])
    # Получаем пропуск из базы данных
    pass_obj = await db.get_pass_by_id(pass_id)
    if not pass_obj:
        await callback.answer("❌ Пропуск не найден", show_alert=True)
        return
    # Проверяем, что пропуск активен
    if pass_obj.status != PASS_STATUSES['ACTIVE']:
        await callback.answer("❌ Пропуск уже использован или неактивен", show_alert=True)
        return
    # Отмечаем пропуск как использованный
    await db.update_pass_status(pass_id, PASS_STATUSES['USED'], callback.from_user.id)
    # Логирование использования пропуска
    audit_logger.log_pass_usage(pass_obj.user_id, pass_id, pass_obj.car_number, callback.from_user.id)
    # Получаем информацию о пользователе для уведомления
    user = await db.get_user_by_id(pass_obj.user_id)
    await callback.answer("✅ Пропуск отмечен как использованный", show_alert=True)
    await callback.message.edit_text(
        f"✅ Пропуск {pass_obj.car_number} отмечен как использованный\n\n"
        f"👤 {user.full_name}\n"
        f"🏠 Квартира {user.apartment}"
    )
    await callback.message.answer(
        "Нажмите на кнопку \"🔍 Найти пропуск\" для поиска заявки. После открытия шлагбаума отметьте пропуск как использованный, нажав \"✅\" под пропуском.",
        reply_markup=get_security_main_menu()
    )
@router.callback_query(F.data == "search_another")

async def handle_search_another_callback(callback: CallbackQuery):
    """Обработка поиска другого пропуска"""
    if not await is_security(callback.from_user.id):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    await callback.message.edit_text("🔍 Введите номер автомобиля для поиска:")
    await callback.message.answer("🔍 Введите номер автомобиля для поиска:", reply_markup=get_pass_search_keyboard())

def register_security_handlers(dp):
    """Регистрация обработчиков охраны"""
    logger.info("Registering security handlers")
    dp.include_router(router)
    logger.info("Security handlers registered successfully")
