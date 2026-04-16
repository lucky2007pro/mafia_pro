"""Maxsus kunduz buyruqlari — /snipe, /reveal"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from logic.registry import all_games
from logic.manager import GamePhase
from logic.roles import RoleType
from keyboards.game_kb import sniper_kb

router = Router()


@router.message(Command("snipe"))
async def cmd_snipe(message: Message):
    uid = message.from_user.id
    player_game = next(
        ((cid, g) for cid, g in all_games().items() if uid in g.players), None
    )
    if not player_game:
        return await message.answer("Siz hozir hech qaysi o'yinda emassiz!")
    chat_id, game = player_game
    p = game.get(uid)
    if not p or not p.is_alive:
        return await message.answer("Siz o'yinda emassiz.")
    if p.role != RoleType.SNIPER:
        return await message.answer("Siz snayper emassiz!")
    if game.phase != GamePhase.DAY:
        return await message.answer("Snayper faqat kunduz otishi mumkin!")
    if p.sniper_shots <= 0:
        return await message.answer("O'qingiz tugagan!")
    others = [x for x in game.alive() if x.user_id != uid]
    await message.answer(
        f"🎯 <b>SNAYPER — NISHON TANLASH</b>\n\n"
        f"⚠️ Begunoh otilsa — siz o'lasiz!\n"
        f"O'qlar: <b>{p.sniper_shots}/1</b>",
        parse_mode="HTML",
        reply_markup=sniper_kb(others, chat_id)
    )


@router.message(Command("reveal"))
async def cmd_reveal(message: Message):
    uid = message.from_user.id
    player_game = next(
        ((cid, g) for cid, g in all_games().items() if uid in g.players), None
    )
    if not player_game:
        return await message.answer("O'yinda emassiz!")
    chat_id, game = player_game
    p = game.get(uid)
    if not p or p.role != RoleType.MAYOR:
        return await message.answer("Faqat Mer oshkor qila oladi!")
    if p.mayor_revealed:
        return await message.answer("Allaqachon oshkor qilgansiz!")
    ok, msg = game.mayor_reveal(uid)
    if ok:
        await message.bot.send_message(chat_id, f"📢 {msg}", parse_mode="HTML")
