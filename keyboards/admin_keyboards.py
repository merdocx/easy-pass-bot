from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_approval_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для модерации заявки администратором"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_user_{user_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_user_{user_id}")
        ]
    ])
    return keyboard
