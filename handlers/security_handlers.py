import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from database import db
from keyboards.security_keyboards import get_security_main_menu, get_pass_usage_keyboard, get_pass_search_keyboard, get_passes_list_keyboard
from utils.validators import validate_car_number
from config import MESSAGES, ROLES, USER_STATUSES, PASS_STATUSES

logger = logging.getLogger(__name__)
router = Router()

async def is_security(telegram_id: int) -> bool:
    """Проверка, является ли пользователь сотрудником охраны"""
    user = await db.get_user_by_telegram_id(telegram_id)
    return user and user.role == ROLES['SECURITY'] and user.status == USER_STATUSES['APPROVED']


@router.message(Command("search"))
async def search_command(message: Message):
    """Быстрый поиск через команду /search"""
    if not await is_security(message.from_user.id):
        await message.answer("❌ Нет прав", reply_markup=get_security_main_menu())
        return
    
    await message.answer("🔍 Введите номер автомобиля для поиска:", reply_markup=get_pass_search_keyboard())

@router.message(F.text == "🔍 Найти пропуск")
async def handle_search_pass_message(message: Message):
    """Обработка нажатия кнопки 'Найти пропуск'"""
    logger.info(f"SECURITY SEARCH BUTTON PRESSED by user {message.from_user.id}, text: '{message.text}'")
    
    if not await is_security(message.from_user.id):
        logger.warning(f"User {message.from_user.id} is not security")
        await message.answer("❌ Нет прав", reply_markup=get_security_main_menu())
        return
    
    logger.info(f"Security user {message.from_user.id} starting search")
    await message.answer("🔍 Введите номер автомобиля для поиска:", reply_markup=get_pass_search_keyboard())

@router.message(F.text & ~F.text.startswith('/') & ~F.text.in_(["🔍 Найти пропуск", "✅ Отметить использованным", "🔙 Назад", "📝 Подать заявку", "📋 Мои заявки", "❌ Отмена"]))
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
        await message.answer("❌ Нет прав", reply_markup=get_security_main_menu())
        return
    
    await message.answer("Нажмите на кнопку \"🔍 Найти пропуск\" для поиска заявки. После открытия шлагбаума отметьте пропуск как использованный, нажав \"✅\" под пропуском.", reply_markup=get_security_main_menu())

@router.message(F.text.regexp(r'^\d{1,3}$'))
async def handle_security_text(message: Message):
    """Обработка текстовых сообщений от охранника (только для охранников)"""
    logger.info(f"SECURITY TEXT MESSAGE from user {message.from_user.id}, text: '{message.text}'")
    
    # Сначала проверяем, является ли пользователь охранником
    if not await is_security(message.from_user.id):
        logger.info(f"User {message.from_user.id} is not security, skipping")
        return  # Не обрабатываем сообщения от не-охранников
    
    # Игнорируем кнопки клавиатуры
    if message.text in ["🔍 Найти пропуск", "✅ Отметить использованным", "🔙 Назад"]:
        return
    
    # Обрабатываем как поиск по номеру машины
    await handle_pass_search_internal(message)

@router.message(F.text.regexp(r'^[А-Яа-я]\d{3}[А-Яа-я]{2}\d{3}$'))
async def handle_pass_search(message: Message):
    """Обработка поиска пропуска по номеру автомобиля (полный формат)"""
    logger.info(f"SECURITY PASS SEARCH by user {message.from_user.id}, text: '{message.text}'")
    
    if not await is_security(message.from_user.id):
        logger.warning(f"User {message.from_user.id} is not security")
        return
    
    await handle_pass_search_internal(message)

async def handle_pass_search_internal(message: Message):
    """Внутренняя функция поиска пропуска"""
    
    car_number = message.text.strip()
    
    # Если введен полный номер, валидируем его
    if len(car_number) > 3 and not validate_car_number(car_number):
        await message.answer(MESSAGES['ENTER_CAR_NUMBER'], reply_markup=get_pass_search_keyboard())
        return
    
    # Ищем все пропуски по номеру (полному или частичному)
    passes = await db.find_all_passes_by_car_number(car_number)
    
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


