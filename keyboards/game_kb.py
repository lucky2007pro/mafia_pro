"""Barcha Inline tugmalar."""
from __future__ import annotations
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from logic.player import Player
from logic.roles import RoleType


def lobby_kb(chat_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✋ Qo'shilish",      callback_data=f"join:{chat_id}")
    b.button(text="🚪 Chiqish",         callback_data=f"leave:{chat_id}")
    b.button(text="🤖 AI Bot qo'shish", callback_data=f"addbot_btn:{chat_id}")
    b.button(text="🎮 O'yinni boshlash", callback_data=f"startgame:{chat_id}")
    b.button(text="❌ Bekor qilish",    callback_data=f"cancelgame:{chat_id}")
    b.adjust(2, 1, 2)
    return b.as_markup()


def start_only_kb(chat_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🎮 Boshlash", callback_data=f"startgame:{chat_id}")
    b.button(text="❌ Bekor",   callback_data=f"cancelgame:{chat_id}")
    b.adjust(2)
    return b.as_markup()


def target_kb(
    players: list[Player],
    prefix:  str,
    chat_id: int,
    exclude: list[int] | None = None,
    show_roles: bool = False,
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    exc = set(exclude or [])
    for p in players:
        if p.user_id in exc:
            continue
        label = f"{p.emoji if show_roles else '👤'} {p.full_name}"
        b.button(text=label, callback_data=f"{prefix}:{p.user_id}:{chat_id}")
    b.button(text="⏭️ O'tkazish", callback_data=f"skip_action:{chat_id}")
    b.adjust(2)
    return b.as_markup()


def vote_kb(players: list[Player], chat_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for p in players:
        weight_badge = " 🎩x2" if (hasattr(p, 'vote_weight') and p.vote_weight > 1) else ""
        b.button(
            text=f"☠️ {p.full_name}{weight_badge}",
            callback_data=f"vote:{p.user_id}:{chat_id}"
        )
    b.button(text="⏭️ Skip (hech kim emas)", callback_data=f"vote_skip:{chat_id}")
    b.adjust(2)
    return b.as_markup()


def deep_link_kb(bot_username: str, payload: str, button_text: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if bot_username:
        b.button(text=button_text, url=f"https://t.me/{bot_username}?start={payload}")
    return b.as_markup()


def vote_entry_kb(bot_username: str, chat_id: int) -> InlineKeyboardMarkup:
    return deep_link_kb(bot_username, f"vote_{chat_id}", "🗳 Ovoz berish")


def don_action_kb(chat_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔫 O'ldirish nishoni", callback_data=f"don_kill:{chat_id}")
    b.button(text="🕵️ Detektivni aniqlash", callback_data=f"don_check:{chat_id}")
    b.adjust(1)
    return b.as_markup()


def detective_action_kb(chat_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔍 Tekshirish", callback_data=f"detective_check:{chat_id}")
    b.button(text="🔫 O'q otish", callback_data=f"detective_shot:{chat_id}")
    b.button(text="⏭️ Bu tun harakatsiz", callback_data=f"skip_action:{chat_id}")
    b.adjust(1)
    return b.as_markup()


def witch_kb(chat_id: int, poison_used: bool, heal_used: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if not poison_used:
        b.button(text="☠️ Zahar berish", callback_data=f"witch_poison:{chat_id}")
    if not heal_used:
        b.button(text="💉 Tiklash",      callback_data=f"witch_heal:{chat_id}")
    b.button(text="⏭️ Bu tun harakatsiz", callback_data=f"skip_action:{chat_id}")
    b.adjust(1)
    return b.as_markup()


def sniper_kb(players: list[Player], chat_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for p in players:
        b.button(text=f"🎯 {p.full_name}", callback_data=f"snipe:{p.user_id}:{chat_id}")
    b.button(text="❌ Bekor", callback_data=f"snipe_cancel:{chat_id}")
    b.adjust(2)
    return b.as_markup()


def lawyer_kb(mafia_players: list[Player], chat_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for p in mafia_players:
        b.button(
            text=f"{p.emoji} {p.full_name}",
            callback_data=f"lawyer_protect:{p.user_id}:{chat_id}"
        )
    b.button(text="⏭️ O'tkazish", callback_data=f"skip_action:{chat_id}")
    b.adjust(2)
    return b.as_markup()


def reveal_mayor_kb(chat_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📢 O'z rolingizni oshkor qiling (+1 ovoz)", callback_data=f"mayor_reveal:{chat_id}")
    b.adjust(1)
    return b.as_markup()


def night_actions_kb(bot_username: str, chat_id: int) -> InlineKeyboardMarkup:
    """
    Tun boshlanganida har bir o'yinchi uchun botga o'tish tugmasi.
    """
    return deep_link_kb(bot_username, f"night_{chat_id}", "🤖 Botga o'tish")
