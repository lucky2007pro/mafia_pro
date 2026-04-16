"""/help uchun inline menyular."""
from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from logic.roles import RoleType


POPULAR_ROLE_BUTTONS: list[tuple[str, str]] = [
    ("civilian", "👱 Tinch axoli"),
    ("don", "🕴 Don"),
    ("mafia", "🧑 Mafia"),
    ("komissar", "🕵️ Komissar Katani"),
    ("serjant", "👮 Serjant"),
    ("doctor", "👨 Shifokor"),
    ("qotil", "🔪 Qotil"),
    ("mashuqa", "💃 Ma'shuqa"),
    ("lawyer", "⚖️ Advokat"),
    ("suicide", "💣 Suitsid"),
    ("daydi", "🧥 Daydi"),
    ("omadli", "🤞 Omadli"),
    ("kamikaze", "💣 Kamikaze"),
]

ALL_ROLE_ORDER: list[RoleType] = [
    RoleType.CIVILIAN,
    RoleType.DOCTOR,
    RoleType.DETECTIVE,
    RoleType.BODYGUARD,
    RoleType.SNIPER,
    RoleType.MAYOR,
    RoleType.VIGILANTE,
    RoleType.JOURNALIST,
    RoleType.SPY,
    RoleType.DAYDI,
    RoleType.OMADLI,
    RoleType.MAFIA,
    RoleType.DON,
    RoleType.GODFATHER,
    RoleType.LAWYER,
    RoleType.MANIAC,
    RoleType.SUICIDE,
    RoleType.ESCORT,
    RoleType.WITCH,
    RoleType.KAMIKAZE,
]


def help_roles_main_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for key, label in POPULAR_ROLE_BUTTONS:
        b.button(text=label, callback_data=f"help_role:{key}")

    b.button(text="📚 Barcha mavjud rollar", callback_data="help_roles:all")
    b.button(text="📋 Buyruqlar", callback_data="help:commands")
    b.adjust(2, 2, 2, 2, 2, 2, 1, 2)
    return b.as_markup()


def help_roles_all_kb() -> InlineKeyboardMarkup:
    from logic.roles import get_role

    b = InlineKeyboardBuilder()
    for role in ALL_ROLE_ORDER:
        cfg = get_role(role)
        b.button(text=f"{cfg.emoji} {cfg.name_uz}", callback_data=f"help_role:{role.value}")

    b.button(text="⬅️ Orqaga", callback_data="help:main")
    b.adjust(2, 2, 2, 2, 2, 2, 2, 2, 1)
    return b.as_markup()


def help_back_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="⬅️ Rollar menyusi", callback_data="help:main")
    b.adjust(1)
    return b.as_markup()

