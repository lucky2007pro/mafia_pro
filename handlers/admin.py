"""Admin buyruqlari."""
from __future__ import annotations
import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, ChatMemberAdministrator, ChatMemberOwner
from logic.registry import get_game, delete_game
from logic.manager import GamePhase
from config import settings

log = logging.getLogger(__name__)
router = Router()


async def is_admin(m: Message) -> bool:
    try:
        mb = await m.bot.get_chat_member(m.chat.id, m.from_user.id)
        return isinstance(mb, (ChatMemberAdministrator, ChatMemberOwner))
    except Exception:
        return False


@router.message(Command("skipnight"))
async def cmd_skipnight(m: Message):
    if not await is_admin(m): return await m.answer("⛔ Faqat adminlar!")
    game = get_game(m.chat.id)
    if not game or game.phase != GamePhase.NIGHT:
        return await m.answer("⚠️ Tun bosqichi emas.")
    await m.answer("⏭️ Tun o'tkazildi.")
    from handlers.actions import process_dawn
    await process_dawn(m.chat.id, m.bot, m.chat.id)


@router.message(Command("skipday"))
async def cmd_skipday(m: Message):
    if not await is_admin(m): return await m.answer("⛔ Faqat adminlar!")
    game = get_game(m.chat.id)
    if not game or game.phase != GamePhase.DAY:
        return await m.answer("⚠️ Kun bosqichi emas.")
    await m.answer("⏭️ Muhokama o'tkazildi.")
    from handlers.actions import begin_voting
    await begin_voting(m.chat.id, m.bot, m.chat.id)


@router.message(Command("skipvote"))
async def cmd_skipvote(m: Message):
    if not await is_admin(m): return await m.answer("⛔ Faqat adminlar!")
    game = get_game(m.chat.id)
    if not game or game.phase != GamePhase.VOTING:
        return await m.answer("⚠️ Ovoz berish emas.")
    await m.answer("⏭️ Ovoz berish yakunlandi.")
    from handlers.actions import process_vote
    await process_vote(m.chat.id, m.bot, m.chat.id)


@router.message(Command("gamestatus"))
async def cmd_gamestatus(m: Message):
    if not await is_admin(m): return await m.answer("⛔ Faqat adminlar!")
    game = get_game(m.chat.id)
    if not game: return await m.answer("O'yin yo'q.")

    alive = game.alive()
    dead  = game.dead()
    na    = game.na

    lines = [
        f"🔧 <b>O'YIN HOLATI</b>",
        f"📍 Bosqich: <code>{game.phase.value}</code>",
        f"📅 Kun: {game.day_num}",
        f"👥 Tirik: {len(alive)} | O'lik: {len(dead)}",
        "",
        "<b>Tirik o'yinchilar:</b>",
    ]
    for p in alive:
        done = "✅" if p.night_action_done else ("⏳" if p.cfg and p.cfg.night_action else "—")
        lines.append(f"  {p.emoji} {p.full_name} [{p.cfg.name_uz if p.cfg else '?'}] {done}")

    if game.phase == GamePhase.NIGHT:
        lines += [
            "", "<b>Tun harakatlari:</b>",
            f"  Mafia: {na.mafia_target}",
            f"  Shifokor: {na.doctor_target}",
            f"  Detektiv: {na.detective_target}",
            f"  Qo'riqchi: {na.bodyguard_target}",
            f"  Manyak: {na.maniac_target}",
            f"  Escort: {na.escort_target}",
            f"  Zahar: {na.witch_poison} | Tiklash: {na.witch_heal}",
        ]

    await m.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("kick"))
async def cmd_kick(m: Message):
    if not await is_admin(m): return await m.answer("⛔ Faqat adminlar!")
    game = get_game(m.chat.id)
    if not game: return await m.answer("O'yin yo'q.")
    if not m.reply_to_message:
        return await m.answer("⚠️ O'yinchining xabariga javob bering!")
    tid = m.reply_to_message.from_user.id
    p = game.get(tid)
    if not p: return await m.answer("Bu kishi o'yinda emas.")
    p.is_alive = False
    await m.answer(f"🚫 {p.mention} o'yindan chiqarildi.", parse_mode="HTML")
    win = game.check_win()
    if win:
        from handlers.actions import finish_game
        await finish_game(m.chat.id, m.bot, m.chat.id, win[0], win[1])


@router.message(Command("settime"))
async def cmd_settime(m: Message):
    if not await is_admin(m): return await m.answer("⛔ Faqat adminlar!")
    parts = m.text.split()
    if len(parts) != 3:
        return await m.answer("Foydalanish: /settime <night|day|vote|lobby> <soniya>")
    phase, secs_s = parts[1], parts[2]
    try:
        secs = int(secs_s)
        if not 10 <= secs <= 600: raise ValueError
    except ValueError:
        return await m.answer("10 dan 600 gacha son kiriting!")
    mapping = {"night": "NIGHT_TIMEOUT", "day": "DAY_DISCUSSION_TIME",
               "vote": "VOTE_TIMEOUT", "lobby": "LOBBY_TIMEOUT"}
    attr = mapping.get(phase.lower())
    if not attr: return await m.answer("Noma'lum bosqich!")
    setattr(settings, attr, secs)
    await m.answer(f"✅ {phase} = {secs}s", parse_mode="HTML")


@router.message(Command("serverstats"))
async def cmd_serverstats(m: Message):
    if m.from_user.id not in settings.ADMIN_IDS:
        return
    from logic.registry import active_count, server_stats
    s = server_stats()
    await m.answer(
        f"🖥️ <b>SERVER HOLATI</b>\n\n"
        f"🎮 Faol o'yinlar: {s['active_games']}\n"
        f"👥 Jami o'yinchilar: {s['total_players']}",
        parse_mode="HTML"
    )
