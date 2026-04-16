"""
Lobby, Join/Leave, StartGame handlerlari.
"""
from __future__ import annotations
import asyncio
import logging
from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from logic.registry import create_game, get_game, delete_game, exists
from logic.manager import GamePhase
from logic.roles import RoleType, Team, get_role, MAFIA_ROLES
from keyboards.game_kb import lobby_kb
from utils.texts import lobby_text
from config import settings

log = logging.getLogger(__name__)
router = Router()


# ──────────────────────────────────────────────
#  /newgame
# ──────────────────────────────────────────────
@router.message(Command("newgame"))
async def cmd_newgame(message: Message, bot: Bot):
    if message.chat.type not in ("group", "supergroup"):
        return await message.answer("⚠️ Bu buyruq faqat guruhlarda ishlaydi!")

    cid = message.chat.id
    if exists(cid):
        return await message.answer("⚠️ O'yin allaqachon bor! /endgame bilan to'xtating.")

    game = create_game(cid)
    u = message.from_user
    game.add(u.id, u.username or "", u.full_name)

    msg = await message.answer(
        lobby_text(game.players, cid),
        parse_mode="HTML",
        reply_markup=lobby_kb(cid)
    )
    game.msg_ids["lobby"] = msg.message_id

    asyncio.create_task(_lobby_timer(cid, bot, cid))


async def _lobby_timer(chat_id: int, bot: Bot, group_id: int):
    await asyncio.sleep(settings.LOBBY_TIMEOUT)
    game = get_game(chat_id)
    if not game or game.phase != GamePhase.WAITING:
        return
    n = len(game.players)
    if n < settings.MIN_PLAYERS:
        delete_game(chat_id)
        return await bot.send_message(
            group_id,
            f"⏰ Vaqt tugadi. O'yinchilar yetarli emas ({n}/{settings.MIN_PLAYERS}). Bekor qilindi."
        )
    await _do_start(chat_id, bot, group_id)


# ──────────────────────────────────────────────
#  JOIN / LEAVE callbacks
# ──────────────────────────────────────────────
@router.callback_query(F.data.startswith("join:"))
async def cb_join(cb: CallbackQuery):
    cid = int(cb.data.split(":")[1])
    game = get_game(cid)
    if not game or game.phase != GamePhase.WAITING:
        return await cb.answer("Lobby mavjud emas!", show_alert=True)
    u = cb.from_user
    if not game.add(u.id, u.username or "", u.full_name):
        msg = "Allaqachon bor!" if u.id in game.players else "Lobby to'lgan!"
        return await cb.answer(msg, show_alert=True)
    await cb.answer("✅ Qo'shildingiz!")
    await _refresh_lobby(cb, cid, game)


@router.callback_query(F.data.startswith("leave:"))
async def cb_leave(cb: CallbackQuery):
    cid = int(cb.data.split(":")[1])
    game = get_game(cid)
    if not game or game.phase != GamePhase.WAITING:
        return await cb.answer("Lobbydan chiqib bo'lmaydi!", show_alert=True)
    if not game.remove(cb.from_user.id):
        return await cb.answer("Siz lobbyda emassiz!", show_alert=True)
    await cb.answer("🚪 Chiqdingiz.")
    if not game.players:
        delete_game(cid)
        return await cb.message.edit_text("❌ Lobby yopildi.")
    await _refresh_lobby(cb, cid, game)


async def _refresh_lobby(cb: CallbackQuery, cid: int, game):
    try:
        await cb.message.edit_text(
            lobby_text(game.players, cid),
            parse_mode="HTML",
            reply_markup=lobby_kb(cid)
        )
    except Exception:
        pass


# ──────────────────────────────────────────────
#  START / CANCEL callbacks
# ──────────────────────────────────────────────
@router.callback_query(F.data.startswith("startgame:"))
async def cb_startgame(cb: CallbackQuery, bot: Bot):
    cid = int(cb.data.split(":")[1])
    game = get_game(cid)
    if not game or game.phase != GamePhase.WAITING:
        return await cb.answer("O'yin holati o'zgardi!", show_alert=True)
    if len(game.players) < settings.MIN_PLAYERS:
        return await cb.answer(
            f"Yetarli o'yinchi yo'q ({len(game.players)}/{settings.MIN_PLAYERS})",
            show_alert=True
        )
    await cb.answer()
    await _do_start(cid, bot, cb.message.chat.id)


@router.callback_query(F.data.startswith("cancelgame:"))
async def cb_cancelgame(cb: CallbackQuery):
    cid = int(cb.data.split(":")[1])
    delete_game(cid)
    await cb.message.edit_text("❌ O'yin bekor qilindi.")
    await cb.answer("Bekor qilindi.")


@router.message(Command("startgame"))
async def cmd_startgame(message: Message, bot: Bot):
    if message.chat.type not in ("group", "supergroup"):
        return
    cid = message.chat.id
    game = get_game(cid)
    if not game or game.phase != GamePhase.WAITING:
        return await message.answer("Aktiv lobby yo'q. /newgame bilan boshlang.")
    if len(game.players) < settings.MIN_PLAYERS:
        return await message.answer(f"Kamida {settings.MIN_PLAYERS} kishi kerak!")
    await _do_start(cid, bot, cid)


@router.message(Command("endgame"))
async def cmd_endgame(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        return
    cid = message.chat.id
    if not exists(cid):
        return await message.answer("Hozir o'yin yo'q.")
    delete_game(cid)
    await message.answer("🛑 O'yin admin tomonidan to'xtatildi.")


@router.message(Command("players"))
async def cmd_players(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        return
    game = get_game(message.chat.id)
    if not game:
        return await message.answer("Hozir o'yin yo'q.")
    alive = game.alive()
    dead  = game.dead()
    text  = f"👥 <b>TIRIK ({len(alive)})</b>\n{game.players_text()}"
    if dead:
        dead_text = "\n".join(
            f"💀 {p.mention} — {p.emoji} {p.cfg.name_uz}" for p in dead
        )
        text += f"\n\n<b>💀 O'LGANLAR ({len(dead)})</b>\n{dead_text}"
    await message.answer(text, parse_mode="HTML")


# ──────────────────────────────────────────────
#  O'YINNI ISHGA TUSHIRISH
# ──────────────────────────────────────────────
async def _do_start(chat_id: int, bot: Bot, group_id: int):
    game = get_game(chat_id)
    if not game:
        return

    game.phase = GamePhase.STARTING
    n = len(game.players)

    await bot.send_message(
        group_id,
        f"🎭 <b>O'YIN BOSHLANMOQDA!</b>\n\n"
        f"👥 O'yinchilar: <b>{n}</b>\n"
        f"📨 Har bir o'yinchiga shaxsiy xabarda rol yuborilmoqda...\n\n"
        f"⚠️ <i>Agar DM kelmasa — botga /start yuboring!</i>",
        parse_mode="HTML"
    )

    # Rollarni taqsimlash
    try:
        assignment = game.assign_roles()
    except ValueError as e:
        await bot.send_message(group_id, f"⚠️ Xatolik: {e}")
        delete_game(chat_id)
        return

    # Mafia a'zolari bir-birini tanisin
    mafia_list = game.mafia_list_text()

    failed = []
    for p in game.players.values():
        cfg = get_role(p.role)
        dm  = (
            f"🎭 <b>Sizning rolingiz:</b>\n\n"
            f"{cfg.emoji} <b>{cfg.name_uz}</b>\n\n"
            f"{cfg.full_desc}"
        )
        if p.role in MAFIA_ROLES and len(game.alive_mafia()) > 1:
            dm += f"\n\n👥 <b>Mafia jamoasi:</b>\n{mafia_list}"

        try:
            await bot.send_message(p.user_id, dm, parse_mode="HTML")
        except Exception:
            failed.append(p.full_name)

    if failed:
        await bot.send_message(
            group_id,
            f"⚠️ Quyidagi o'yinchilarga DM yuborilmadi:\n"
            + "\n".join(f"• {n}" for n in failed)
            + "\n\nUlarga /start yuborishni so'rang!"
        )
        await asyncio.sleep(4)

    from handlers.actions import begin_night
    await begin_night(chat_id, bot, group_id)
