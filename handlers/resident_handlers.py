import logging
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from database import db, User, Pass
from keyboards.resident_keyboards import get_resident_main_menu, get_resident_passes_keyboard, get_pass_creation_keyboard, get_approved_user_keyboard
from utils.validators import validate_registration_form, validate_car_number
from utils.notifications import notify_admins_new_registration
from config import MESSAGES, ROLES, USER_STATUSES, PASS_STATUSES, BOT_TOKEN

logger = logging.getLogger(__name__)
router = Router()

async def is_resident(telegram_id: int) -> bool:
    """Проверка, является ли пользователь жителем"""
    user = await db.get_user_by_telegram_id(telegram_id)
    return user and user.role == ROLES['RESIDENT'] and user.status == USER_STATUSES['APPROVED']

@router.message(Command("start"))
async def start_command(message: Message):
    """Обработка команды /start"""
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        # Новый пользователь - показываем форму регистрации
        await message.answer(MESSAGES['WELCOME'])
    elif user.status == USER_STATUSES['PENDING']:
        await message.answer("⏳ Ваша заявка на регистрацию находится на модерации.", reply_markup=get_approved_user_keyboard())
    elif user.status == USER_STATUSES['REJECTED']:
        await message.answer(MESSAGES['REGISTRATION_REJECTED'], reply_markup=get_approved_user_keyboard())
    elif user.role == ROLES['RESIDENT'] and user.status == USER_STATUSES['APPROVED']:
        await message.answer("🏠 Добро пожаловать в Easy Pass!", reply_markup=get_approved_user_keyboard())
    elif user.role == ROLES['SECURITY'] and user.status == USER_STATUSES['APPROVED']:
        from keyboards.security_keyboards import get_security_main_menu
        await message.answer("Нажмите на кнопку \"🔍 Найти пропуск\" для поиска заявки. После открытия шлагбаума отметьте пропуск как использованный, нажав \"✅\" под пропуском.", reply_markup=get_security_main_menu())
    elif user.role == ROLES['ADMIN'] and user.status == USER_STATUSES['APPROVED']:
        await message.answer("👑 Панель администратора Easy Pass\n\nВы будете получать уведомления о новых заявках на регистрацию.\nДля модерации используйте кнопки в уведомлениях.")

@router.message(F.text.contains(","))
async def handle_registration(message: Message):
    """Обработка регистрации жителя (1 шаг)"""
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if user:
        await message.answer("Вы уже зарегистрированы в системе.", reply_markup=get_approved_user_keyboard())
        return
    
    # Валидация формы
    form_data = validate_registration_form(message.text)
    if not form_data:
        await message.answer(MESSAGES['INVALID_FORMAT'], reply_markup=get_approved_user_keyboard())
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
        
        # Уведомление администраторов
        # Создаем новый экземпляр бота для уведомлений
        from aiogram import Bot
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        from config import BOT_TOKEN
        
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
        sent_message = await message.answer(MESSAGES['REGISTRATION_SENT'])
        
        logger.info(f"New user registered: {new_user.full_name} (ID: {user_id})")
        
    except Exception as e:
        logger.error(f"Failed to register user: {e}")
        await message.answer("❌ Произошла ошибка при регистрации. Попробуйте позже.", reply_markup=get_approved_user_keyboard())

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
    await message.answer("✅ Создание заявки отменено\n\n🏠 Добро пожаловать в Easy Pass!", reply_markup=keyboard)
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

@router.message(F.text.regexp(r'^[А-Яа-я]\d{3}[А-Яа-я]{2}\d{3}$'))
async def handle_resident_text(message: Message):
    """Обработка текстовых сообщений от жителей"""
    logger.info(f"TEXT MESSAGE RECEIVED from user {message.from_user.id}, text: '{message.text}'")
    
    # Проверяем, является ли пользователь жителем
    if not await is_resident(message.from_user.id):
        logger.info(f"User {message.from_user.id} is not a resident, skipping")
        # Если не житель, не обрабатываем сообщение, но не блокируем передачу дальше
        return
    
    text = message.text.strip()
    logger.info(f"Text message from resident {message.from_user.id}: {text}")
    
    # Игнорируем кнопки клавиатуры
    if text in ["📝 Подать заявку", "📋 Мои заявки"]:
        return
    
    # Проверяем, соответствует ли текст формату номера автомобиля
    import re
    pattern = r'^[А-Яа-я]\d{3}[А-Яа-я]{2}\d{3}$'
    if re.match(pattern, text):
        logger.info(f"Text matches car number pattern: {text}")
        await handle_pass_creation_internal(message, text)
    else:
        logger.info(f"Text does not match car number pattern: {text}")
        # Если это не номер автомобиля, игнорируем

async def handle_pass_creation_internal(message: Message, car_number: str):
    """Внутренняя функция обработки создания заявки на пропуск"""
    logger.info(f"Processing car number: {car_number}")
    
    # Преобразуем маленькие буквы в заглавные
    car_number = car_number.upper()
    logger.info(f"Converted to uppercase: {car_number}")
    
    # Валидация номера
    if not validate_car_number(car_number):
        logger.warning(f"Invalid car number: {car_number}")
        await message.answer(MESSAGES['ENTER_CAR_NUMBER'], reply_markup=get_pass_creation_keyboard())
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
