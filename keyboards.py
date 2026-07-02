from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📈 Профиль")],
        [KeyboardButton(text="📋 Список заказов")],
        [KeyboardButton(text="💳 Вывод средств")]
    ], resize_keyboard=True)

def cancel_order_kb(order_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚫 Отказаться от заказа", callback_data=f"cancel_{order_id}")]
    ])

def withdrawal_approve_kb(request_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить вывод", callback_data=f"approve_withdraw_{request_id}")]
    ])

back = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
])