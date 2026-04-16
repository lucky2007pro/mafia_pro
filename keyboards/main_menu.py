"""Reply keyboard menyulari (pastki tugmalar)."""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def private_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Profil"), KeyboardButton(text="💰 Tangalar")],
            [KeyboardButton(text="🛒 Do'kon"), KeyboardButton(text="🏆 Reyting")],
            [KeyboardButton(text="🎭 Rollar"), KeyboardButton(text="📘 Qoidalar")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Menyudan tanlang...",
    )


def group_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Do'kon"), KeyboardButton(text="💰 Tangalar")],
            [KeyboardButton(text="🏆 Reyting"), KeyboardButton(text="🎭 Rollar")],
            [KeyboardButton(text="📘 Qoidalar"), KeyboardButton(text="❓ Yordam")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Menyudan tanlang...",
    )

