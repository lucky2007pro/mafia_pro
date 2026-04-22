from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from config import settings
from database.db import (
    add_coins,
    buy_fake_passport,
    buy_shield,
    get_top_players,
    get_top_elo,
    get_user_stats,
    get_wallet,
)
from utils.texts import RULES

router = Router()


@router.message(Command("profile"))
async def cmd_profile(m: Message):
    """WebApp orqali profil va do'konni ochish."""
    if m.chat.type != "private":
        return await m.answer("ℹ️ Bu buyruq faqat shaxsiy chatda ishlaydi.")
    
    # Placeholder URL — foydalanuvchi o'zining xosting linkini qo'yishi kerak.
    # Hozircha local index.html ga ishora qilib bo'lmaydi (TG bot URL talab qiladi).
    webapp_url = "https://your-webapp-url.com/index.html" # TODO: Update with real URL
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Profil va Do'kon", web_app=WebAppInfo(url=webapp_url))]
    ])
    
    await m.answer(
        "📊 <b>STATISTIKA VA DO'KON</b>\n\n"
        "Quyidagi tugma orqali WebApp interfeysini ochishingiz mumkin.",
        parse_mode="HTML",
        reply_markup=kb
    )


@router.message(Command("top"))
async def cmd_top(message: Message):
    top_elo = await get_top_elo(10)
    if not top_elo:
        return await message.answer("Reyting hali shakllanmagan.")
    
    text = "🏆 <b>GLOBAL REYTING (ELO)</b>\n\n"
    for i, u in enumerate(top_elo, 1):
        text += f"{i}. {u.full_name} — ⭐️ {u.elo_rating}\n"
    
    await message.answer(text, parse_mode="HTML")


@router.message(Command("buy_info"))
async def cmd_buy_info(message: Message):
    """O'yin ichida shubhali ma'lumot sotib olish."""
    from logic.registry import get_game
    game = None
    if message.chat.type in ("group", "supergroup"):
        game = get_game(message.chat.id)
    
    if not game or game.phase not in ("day", "voting"):
        return await message.answer("⚠️ Ma'lumotni faqat o'yin davomida (kunduzi) sotib olish mumkin!")

    w = await get_wallet(message.from_user.id)
    price = settings.INFO_PRICE
    if w.coins < price:
        return await message.answer(f"❌ Mablag' yetarli emas! Narxi: {price} tanga.")

    await add_coins(message.from_user.id, -price)
    
    import random
    mafia = game.alive_mafia()
    if mafia:
        m = random.choice(mafia)
        await message.answer(f"🤫 <b>MAXFIY MA'LUMOT:</b>\n\n{m.full_name} biroz shubhali ko'rinyapti... 😉", parse_mode="HTML")
    else:
        await message.answer("🤫 <b>MAXFIY MA'LUMOT:</b>\n\nHozircha hamma narsa tinchdek ko'rinmoqda.")


@router.message(Command("buyshield"))
async def cmd_buyshield(m: Message):
    """Bir martalik shaxsiy himoya sotib olish."""
    if m.chat.type != "private":
        return await m.answer("ℹ️ Bu buyruq faqat shaxsiy chatda ishlaydi.")
    
    ok, msg, wallet = await buy_shield(m.from_user.id)
    if ok:
        await m.answer(
            f"{msg}\n"
            f"🛡️ Himoyalar: <b>{wallet.shields}</b>\n"
            f"💰 Qolgan tanga: <b>{wallet.coins}</b>",
            parse_mode="HTML",
        )
    else:
        await m.answer(
            f"⛔ {msg}\n"
            f"💰 Balans: <b>{wallet.coins}</b>",
            parse_mode="HTML",
        )


@router.message(Command("wallet"))
async def cmd_wallet(m: Message):
    await cmd_profile(m)


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
        f"2) 🛡️ Bir martalik himoya — <b>{settings.SHIELD_PRICE}</b> tanga\n"
        f"   Xarid: <code>/buyshield</code>\n\n"
        f"3) 🤫 Maxfiy ma'lumot (guruhda) — <b>{settings.INFO_PRICE}</b> tanga\n"
        f"   Xarid: <code>/buy_info</code> (faqat o'yin davomida)\n\n"
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

