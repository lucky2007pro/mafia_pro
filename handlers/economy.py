from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from config import settings
from database.db import (
    add_coins,
    buy_fake_passport,
    get_top_players,
    get_user_stats,
    get_wallet,
)
from utils.texts import RULES

router = Router()


def _profile_text(full_name: str, stats, wallet) -> str:
    games_played = stats.games_played if stats else 0
    games_won = stats.games_won if stats else 0
    win_rate = stats.win_rate if stats else 0.0
    kills = stats.total_kills if stats else 0
    return (
        f"👤 <b>{full_name}</b>\n\n"
        f"💰 Tangalar: <b>{wallet.coins}</b>\n"
        f"🪪 Soxta passport: <b>{wallet.fake_passports}</b>\n"
        f"📥 Jami topilgan: <b>{wallet.total_earned}</b>\n\n"
        f"🎮 O'yinlar: <b>{games_played}</b>\n"
        f"🏆 G'alabalar: <b>{games_won}</b>\n"
        f"📈 Win rate: <b>{win_rate}%</b>\n"
        f"💀 Kill: <b>{kills}</b>"
    )


@router.message(Command("profile"))
async def cmd_profile(m: Message):
    if m.chat.type != "private":
        return await m.answer("ℹ️ Bu buyruq faqat shaxsiy chatda ishlaydi.")
    stats = await get_user_stats(m.from_user.id)
    wallet = await get_wallet(m.from_user.id)
    await m.answer(_profile_text(m.from_user.full_name, stats, wallet), parse_mode="HTML")


@router.message(Command("coins"))
async def cmd_coins(m: Message):
    if m.chat.type != "private":
        return await m.answer("ℹ️ Bu buyruq faqat shaxsiy chatda ishlaydi.")
    wallet = await get_wallet(m.from_user.id)
    await m.answer(
        f"💰 <b>Sizning balansingiz</b>\n\n"
        f"Tangalar: <b>{wallet.coins}</b>\n"
        f"Soxta passport: <b>{wallet.fake_passports}</b>\n"
        f"\nYutganingizda +{settings.WIN_COINS_REWARD} tanga olasiz.",
        parse_mode="HTML",
    )


@router.message(Command("shop"))
async def cmd_shop(m: Message):
    if m.chat.type != "private":
        return await m.answer("ℹ️ Bu buyruq faqat shaxsiy chatda ishlaydi.")
    wallet = await get_wallet(m.from_user.id)
    await m.answer(
        f"🛒 <b>DO'KON</b>\n\n"
        f"1) 🪪 Soxta passport — <b>{settings.FAKE_PASSPORT_PRICE}</b> tanga\n"
        f"   Xarid: <code>/buy passport</code>\n\n"
        f"Balansingiz: <b>{wallet.coins}</b> tanga",
        parse_mode="HTML",
    )


@router.message(Command("buy"))
async def cmd_buy(m: Message):
    if m.chat.type != "private":
        return await m.answer("ℹ️ Bu buyruq faqat shaxsiy chatda ishlaydi.")
    parts = (m.text or "").split(maxsplit=1)
    if len(parts) < 2:
        return await m.answer("Foydalanish: /buy passport")

    item = parts[1].strip().lower()
    if item not in ("passport", "fake_passport", "soxta", "soxta_passport"):
        return await m.answer("Noma'lum mahsulot. Hozircha: passport")

    ok, msg, wallet = await buy_fake_passport(m.from_user.id)
    if ok:
        await m.answer(
            f"{msg}\n"
            f"🪪 Passportlar: <b>{wallet.fake_passports}</b>\n"
            f"💰 Qolgan tanga: <b>{wallet.coins}</b>",
            parse_mode="HTML",
        )
    else:
        await m.answer(
            f"⛔ {msg}\n"
            f"💰 Balans: <b>{wallet.coins}</b>",
            parse_mode="HTML",
        )


@router.message(Command("buycoins"))
async def cmd_buycoins(m: Message):
    if m.chat.type != "private":
        return await m.answer("ℹ️ Bu buyruq faqat shaxsiy chatda ishlaydi.")
    parts = (m.text or "").split(maxsplit=1)
    units = 1
    if len(parts) == 2:
        try:
            units = int(parts[1])
            if units <= 0:
                raise ValueError
        except ValueError:
            return await m.answer("Foydalanish: /buycoins <musbat son>")

    coins = units * settings.BUY_COINS_RATE
    wallet = await add_coins(m.from_user.id, coins)
    await m.answer(
        f"💳 Demo xarid qabul qilindi: +<b>{coins}</b> tanga\n"
        f"💰 Yangi balans: <b>{wallet.coins}</b>",
        parse_mode="HTML",
    )


@router.message(F.text == "👤 Profil")
async def menu_profile(m: Message):
    await cmd_profile(m)


@router.message(F.text == "💰 Tangalar")
async def menu_coins(m: Message):
    await cmd_coins(m)


@router.message(F.text == "🛒 Do'kon")
async def menu_shop(m: Message):
    await cmd_shop(m)


@router.message(F.text == "🏆 Reyting")
async def menu_top(m: Message):
    players = await get_top_players(10)
    if not players:
        return await m.answer("Hali statistika yo'q.")
    medals = ["🥇", "🥈", "🥉"] + ["🎖️"] * 7
    lines = ["🏆 <b>TOP 10 O'YINCHILAR</b>\n"]
    for i, p in enumerate(players):
        lines.append(
            f"{medals[i]} <b>{p.full_name}</b> — "
            f"🎮{p.games_played} 🏆{p.games_won} 📈{p.win_rate}%"
        )
    await m.answer("\n".join(lines), parse_mode="HTML")


@router.message(F.text == "🎭 Rollar")
async def menu_roles(m: Message):
    await m.answer("Rollar menyusi uchun /help ni bosing.")


@router.message(F.text == "📘 Qoidalar")
async def menu_rules(m: Message):
    await m.answer(RULES, parse_mode="HTML")


@router.message(F.text == "❓ Yordam")
async def menu_help(m: Message):
    await m.answer("Yordam uchun /help ni bosing.")

