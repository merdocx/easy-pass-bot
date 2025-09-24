from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_resident_main_menu() -> ReplyKeyboardMarkup:
    """Главное меню жителя"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📝 Подать заявку"),
                KeyboardButton(text="📋 Мои заявки")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

def get_resident_passes_keyboard(passes=None) -> ReplyKeyboardMarkup:
    """Клавиатура для просмотра заявок жителя"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📝 Подать заявку"),
                KeyboardButton(text="📋 Мои заявки")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

def get_approved_user_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для одобренного пользователя"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📝 Подать заявку"),
                KeyboardButton(text="📋 Мои заявки")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

def get_pass_creation_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура при создании заявки на пропуск"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard
