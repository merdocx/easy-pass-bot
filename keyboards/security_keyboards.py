from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_security_main_menu() -> ReplyKeyboardMarkup:
    """Главное меню охраны"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Найти пропуск")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

def get_pass_usage_keyboard(pass_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для отметки использования пропуска"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Отметить использованным", callback_data=f"use_pass_{pass_id}")],
            [InlineKeyboardButton(text="🔍 Найти другой пропуск", callback_data="search_another")]
        ]
    )
    return keyboard

def get_passes_list_keyboard(passes) -> InlineKeyboardMarkup:
    """Клавиатура со списком пропусков"""
    keyboard_buttons = []
    
    for i, pass_obj in enumerate(passes, 1):
        # Создаем кнопку для каждого пропуска
        button_text = f"✅ {pass_obj.car_number}"
        callback_data = f"use_pass_{pass_obj.id}"
        keyboard_buttons.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])
    
    # Добавляем кнопку "Найти другой пропуск"
    keyboard_buttons.append([InlineKeyboardButton(text="🔍 Найти другой пропуск", callback_data="search_another")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    return keyboard

def get_pass_search_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для поиска пропуска"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard


