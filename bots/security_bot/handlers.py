"""
Обработчики для бота охраны и администраторов
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import Command
import sys
import os

# Добавляем пути для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from easy_pass_bot.database import db
from easy_pass_bot.keyboards.security_keyboards import get_security_main_menu, get_pass_search_keyboard, get_passes_list_keyboard
from easy_pass_bot.security.rate_limiter import rate_limiter
from easy_pass_bot.security.validator import validator
from easy_pass_bot.security.audit_logger import audit_logger
from config import SECURITY_MESSAGES, ROLES, USER_STATUSES, PASS_STATUSES

logger = logging.getLogger(__name__)
router = Router()

async def is_security(telegram_id: int) -> bool:
    """Проверка, является ли пользователь сотрудником охраны"""
    user = await db.get_user_by_telegram_id(telegram_id)
    return user and user.role == ROLES['SECURITY'] and user.status == USER_STATUSES['APPROVED']

async def is_admin(telegram_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    user = await db.get_user_by_telegram_id(telegram_id)
    return user and user.role == ROLES['ADMIN'] and user.status == USER_STATUSES['APPROVED']

@router.message(Command("start"))
async def start_command(message: Message):
    """Обработка команды /start для персонала"""
    user_id = message.from_user.id
    user = await db.get_user_by_telegram_id(user_id)
    
    if not user:
        # Новый пользователь - показываем форму регистрации для персонала
        await message.answer("👮 Добро пожаловать в PM Desk для персонала!\nЗаполните форму регистрации:\nОтправьте сообщение в формате:\nФИО, Телефон\nНапример: Иванов Иван Иванович, 89997776655")
    elif user.status == USER_STATUSES['PENDING']:
        await message.answer("⏳ Ваша заявка на регистрацию находится на модерации.")
    elif user.status == USER_STATUSES['REJECTED']:
        await message.answer("❌ Заявка отклонена. Обратитесь к администратору.")
    elif user.role == ROLES['SECURITY'] and user.status == USER_STATUSES['APPROVED']:
        await message.answer(SECURITY_MESSAGES['WELCOME'], reply_markup=get_security_main_menu())
    elif user.role == ROLES['ADMIN'] and user.status == USER_STATUSES['APPROVED']:
        # Администратор получает только информационное сообщение, без клавиатуры
        await message.answer(SECURITY_MESSAGES['ADMIN_WELCOME'], reply_markup=ReplyKeyboardRemove())
    else:
        # Если пользователь не персонал, отправляем обычное приветствие
        await message.answer("👮 Добро пожаловать в PM Desk для персонала!\nЗаполните форму регистрации:\nОтправьте сообщение в формате:\nФИО, Телефон\nНапример: Иванов Иван Иванович, 89997776655")

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

@router.message(F.text == "📋 Список пропусков")
async def handle_passes_list_message(message: Message):
    """Обработка нажатия кнопки 'Список пропусков'"""
    if not await is_security(message.from_user.id):
        await message.answer("❌ Нет прав", reply_markup=ReplyKeyboardRemove())
        return
    
    # Получаем все активные пропуски
    passes = await db.get_all_passes()
    active_passes = [p for p in passes if p.status == PASS_STATUSES['ACTIVE'] and not p.is_archived]
    
    if not active_passes:
        await message.answer("📋 Нет активных пропусков")
        return
    
    await message.answer("📋 Активные пропуски:", reply_markup=get_passes_list_keyboard(active_passes))

@router.message(F.text.contains(","))
async def handle_staff_registration(message: Message):
    """Обработка регистрации персонала (админы и охранники) - формат "ФИО, Телефон" """
    user_id = message.from_user.id
    
    # Проверяем, что пользователь еще не зарегистрирован
    user = await db.get_user_by_telegram_id(user_id)
    if user:
        if user.role in [ROLES['SECURITY'], ROLES['ADMIN']]:
            await message.answer("Вы уже зарегистрированы в системе.")
        else:
            await message.answer("Вы уже зарегистрированы как житель.")
        return
    
    # Валидация формы регистрации персонала
    is_valid, error_msg, form_data = validator.validate_staff_registration_data(message.text)
    if not is_valid:
        await message.answer(error_msg or "❌ Неверный формат.\nОтправьте: ФИО, Телефон\nНапример: Иванов Иван Иванович, +7 900 123 45 67")
        return
    
    # Определяем роль пользователя (по умолчанию SECURITY, админы создаются вручную)
    role = ROLES['SECURITY']
    
    # Создание пользователя персонала
    from easy_pass_bot.database.models import User
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
        
        # Уведомление администраторов
        try:
            from aiogram import Bot
            from aiogram.client.default import DefaultBotProperties
            from aiogram.enums import ParseMode
            from easy_pass_bot.utils.notifications import notify_admins_new_registration
            from config import SECURITY_BOT_TOKEN
            
            notification_bot = Bot(
                token=SECURITY_BOT_TOKEN,
                default=DefaultBotProperties(parse_mode=ParseMode.HTML)
            )
            await notify_admins_new_registration(notification_bot, new_user)
            await notification_bot.session.close()
        except Exception as e:
            logger.warning(f"Could not send notifications: {e}")
        
        # Отправляем уведомление
        await message.answer("✅ Заявка отправлена на модерацию!")
        
        logger.info(f"New staff user registered: {new_user.full_name} (ID: {user_id}, Role: {role})")
        
    except Exception as e:
        logger.error(f"Failed to register staff user: {e}")
        await message.answer("❌ Произошла ошибка при регистрации. Попробуйте позже.")

@router.message(
    F.text & ~F.text.startswith('/') &
    ~F.text.in_([
        "🔍 Найти пропуск", "✅ Отметить использованным", "🔙 Назад",
        "📝 Подать заявку", "📋 Мои заявки", "❌ Отмена", "📋 Список пропусков"
    ])
)
async def handle_security_text_messages(message: Message):
    """Обработка текстовых сообщений от охранников (кроме команд и кнопок)"""
    if not await is_security(message.from_user.id):
        await message.answer("❌ Нет прав", reply_markup=ReplyKeyboardRemove())
        return
    
    car_number = message.text.strip().upper()  # Приводим к верхнему регистру
    
    try:
        # Валидация номера автомобиля для поиска (поддерживает частичный поиск)
        is_valid, error = validator.validate_car_number_search(car_number)
        if not is_valid:
            await message.answer(f"❌ {error or 'Неверный формат номера автомобиля'}")
            return
        
        # Поиск всех пропусков по номеру (полному или частичному)
        passes = await db.find_all_passes_by_car_number(car_number)
        
        if not passes:
            await message.answer(
                f"❌ Пропусков с номером, содержащим '{car_number}', не найдено",
                reply_markup=get_security_main_menu()
            )
            return
        
        # Если найден только один пропуск, показываем подробную информацию
        if len(passes) == 1:
            pass_obj = passes[0]
            user = await db.get_user_by_id(pass_obj.user_id)
            
            # Формируем сообщение с информацией о пропуске
            pass_info = f"""✅ Пропуск найден!

🚗 Номер: {pass_obj.car_number}
👤 Владелец: {user.full_name if user else 'Неизвестно'}
📞 Телефон: {user.phone_number if user else 'Неизвестно'}
🏠 Квартира: {user.apartment if user else 'Неизвестно'}
📅 Создан: {pass_obj.created_at.strftime('%d.%m.%Y %H:%M') if pass_obj.created_at else 'Неизвестно'}
📊 Статус: {pass_obj.status}"""
            
            # Создаем инлайн клавиатуру для одного пропуска
            keyboard = get_passes_list_keyboard(passes)
            await message.answer(pass_info, reply_markup=keyboard)
        else:
            # Если найдено несколько пропусков, показываем список
            text = f"🔍 Найдено пропусков: {len(passes)}\n\n"
            for i, pass_obj in enumerate(passes, 1):
                user = await db.get_user_by_id(pass_obj.user_id)
                created_at_str = pass_obj.created_at.strftime('%d.%m.%Y %H:%M') if pass_obj.created_at else 'Неизвестно'
                text += f"{i}. {pass_obj.car_number}\n"
                text += f"   👤 {user.full_name if user else 'Неизвестно'} (кв. {user.apartment if user else 'N/A'})\n"
                text += f"   📅 {created_at_str}\n\n"
            
            # Создаем клавиатуру с кнопками для каждого пропуска
            keyboard = get_passes_list_keyboard(passes)
            await message.answer(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error searching pass: {e}")
        await message.answer("❌ Ошибка при поиске пропуска")

@router.callback_query(F.data.startswith("use_pass_"))
async def handle_use_pass_callback(callback: CallbackQuery):
    """Обработка отметки пропуска как использованного"""
    if not await is_security(callback.from_user.id):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    try:
        pass_id = int(callback.data.split('_')[2])
        
        # Получаем пропуск
        pass_obj = await db.get_pass_by_id(pass_id)
        if not pass_obj:
            await callback.answer("❌ Пропуск не найден", show_alert=True)
            return
        
        if pass_obj.status == PASS_STATUSES['USED']:
            await callback.answer(SECURITY_MESSAGES['PASS_ALREADY_USED'], show_alert=True)
            return
        
        # Отмечаем как использованный
        await db.mark_pass_as_used(pass_id, callback.from_user.id)
        
        # Получаем информацию о пользователе для отображения
        user = await db.get_user_by_id(pass_obj.user_id)
        user_name = user.full_name if user else 'Неизвестно'
        user_apt = user.apartment if user else 'N/A'
        
        await callback.answer("✅ Пропуск отмечен как использованный", show_alert=True)
        await callback.message.edit_text(
            f"✅ Пропуск {pass_obj.car_number} отмечен как использованный\n\n"
            f"👤 {user_name}\n"
            f"🏠 Квартира {user_apt}"
        )
        
        # Отправляем главное меню для дальнейших действий
        await callback.message.answer(
            "Нажмите на кнопку \"🔍 Найти пропуск\" для поиска заявки. После открытия шлагбаума отметьте пропуск как использованный, нажав \"✅\" под пропуском.",
            reply_markup=get_security_main_menu()
        )
        
    except Exception as e:
        logger.error(f"Error using pass: {e}")
        await callback.answer("❌ Ошибка при отметке пропуска", show_alert=True)

@router.callback_query(F.data == "search_another")
async def handle_search_another_callback(callback: CallbackQuery):
    """Обработка поиска другого пропуска"""
    if not await is_security(callback.from_user.id):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    await callback.message.edit_text("🔍 Введите номер автомобиля для поиска:")
    await callback.message.answer("🔍 Введите номер автомобиля для поиска:", reply_markup=get_pass_search_keyboard())

@router.callback_query(F.data == "back_to_main")
async def handle_back_to_main_callback(callback: CallbackQuery):
    """Обработка кнопки 'Главное меню'"""
    if not await is_security(callback.from_user.id):
        await callback.answer("❌ Нет прав", show_alert=True)
        return
    
    await callback.message.edit_text("🏠 Главное меню")
    await callback.message.answer(
        "Нажмите на кнопку \"🔍 Найти пропуск\" для поиска заявки. После открытия шлагбаума отметьте пропуск как использованный, нажав \"✅\" под пропуском.",
        reply_markup=get_security_main_menu()
    )

@router.message(F.text == "🔙 Назад")
async def handle_back_button(message: Message):
    """Обработка кнопки 'Назад'"""
    if not await is_security(message.from_user.id):
        await message.answer("❌ Нет прав")
        return
    
    # Возвращаемся в главное меню
    await message.answer(
        "Нажмите на кнопку \"🔍 Найти пропуск\" для поиска заявки. После открытия шлагбаума отметьте пропуск как использованный, нажав \"✅\" под пропуском.",
        reply_markup=get_security_main_menu()
    )

def register_security_handlers(dp):
    """Регистрация обработчиков для охраны"""
    dp.include_router(router)
    logger.info("Security handlers registered successfully")
