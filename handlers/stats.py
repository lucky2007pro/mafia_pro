from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from database.db import get_user_stats, get_top_players, get_chat_stats

router = Router()

@router.message(Command("mystats"))
async def cmd_mystats(m: Message):
    if m.chat.type != "private":
        return await m.answer("ℹ️ Bu buyruq faqat shaxsiy chatda ishlaydi.")
    u = await get_user_stats(m.from_user.id)
    if not u or u.games_played == 0:
        return await m.answer("📊 Hali biror o'yin o'ynamagansiz!")
    await m.answer(
        f"👤 <b>{m.from_user.full_name}</b>\n\n"
        f"🎮 O'yinlar: <b>{u.games_played}</b>\n"
        f"🏆 G'alabalar: <b>{u.games_won}</b>\n"
        f"📈 Win rate: <b>{u.win_rate}%</b>\n"
        f"💀 Jami o'ldirdi: <b>{u.total_kills}</b>\n\n"
        f"<b>Rol tarixi:</b>\n"
        f"  🔫 Mafia/Don: {u.times_mafia}x\n"
        f"  💊 Shifokor: {u.times_doctor}x\n"
        f"  🔍 Detektiv: {u.times_detective}x\n"
        f"  🎯 Snayper: {u.times_sheriff}x",
        parse_mode="HTML"
    )

@router.message(Command("top"))
async def cmd_top(m: Message):
    if m.chat.type != "private":
        return await m.answer("ℹ️ Bu buyruq faqat shaxsiy chatda ishlaydi.")
    players = await get_top_players(10)
    if not players:
        return await m.answer("Hali statistika yo'q.")
    medals = ["🥇","🥈","🥉"] + ["🎖️"]*7
    lines = ["🏆 <b>TOP 10 O'YINCHILAR</b>\n"]
    for i, p in enumerate(players):
        lines.append(
            f"{medals[i]} <b>{p.full_name}</b> — "
            f"🎮{p.games_played} 🏆{p.games_won} 📈{p.win_rate}%"
        )
    await m.answer("\n".join(lines), parse_mode="HTML")

@router.message(Command("stats"))
async def cmd_stats(m: Message):
    if m.chat.type not in ("group", "supergroup"):
        return await m.answer("Faqat guruhlarda!")
    s = await get_chat_stats(m.chat.id)
    if not s["total_games"]:
        return await m.answer("Bu guruhda hali o'yin bo'lmagan.")
    t = s["total_games"]
    def bar(n): return "█"*(n*10//t) + "░"*(10 - n*10//t) if t else "░"*10
    await m.answer(
        f"📊 <b>GURUH STATISTIKASI</b>\n\n"
        f"🎮 Jami: <b>{t}</b> o'yin\n\n"
        f"🏙️ Shahar: <b>{s['city_wins']}</b> ({s['city_wins']*100//t}%)\n"
        f"   {bar(s['city_wins'])}\n\n"
        f"🔫 Mafia: <b>{s['mafia_wins']}</b> ({s['mafia_wins']*100//t}%)\n"
        f"   {bar(s['mafia_wins'])}\n\n"
        f"⚡ Neytral: <b>{s['neutral_wins']}</b> ({s['neutral_wins']*100//t}%)\n"
        f"   {bar(s['neutral_wins'])}",
        parse_mode="HTML"
    )
