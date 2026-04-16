"""
O'yin harakatlari — Tun, Tong, Kun, Ovoz berish.
Barcha 16 rol qo'llab-quvvatlanadi.
"""
from __future__ import annotations
import asyncio
import logging
import time
from typing import cast
from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery

from logic.registry import get_game, delete_game
from logic.manager import GamePhase
from logic.roles import RoleType, Team, get_role
from keyboards.game_kb import (
    target_kb, vote_kb, don_action_kb,
    witch_kb, lawyer_kb, reveal_mayor_kb,
    detective_action_kb, vote_entry_kb
)
from utils.texts import (
    night_start_text, dawn_text, day_text,
    vote_start_text, vote_progress_text,
    execution_text, game_over_text, last_words_text
)
from config import settings
from database.db import save_game_result, add_coins

log = logging.getLogger(__name__)
router = Router()


# ══════════════════════════════════════════════
#  TUN BOSHLASH
# ══════════════════════════════════════════════
async def begin_night(chat_id: int, bot: Bot, group_id: int):
    game = get_game(chat_id)
    if not game:
        return

    game.phase = GamePhase.NIGHT
    night_num  = game.day_num + 1
    alive      = game.alive()

    await bot.send_message(
        group_id, night_start_text(night_num), parse_mode="HTML"
    )

    async def _stage_notice(text: str):
        try:
            await bot.send_message(group_id, text, parse_mode="HTML")
        except Exception:
            pass

    role_stage_notices = [
        (RoleType.DETECTIVE, "🔍 <b>Komissar tekshiruvga chiqdi.</b>"),
        (RoleType.DOCTOR, "💊 <b>Shifokor davolashga ketdi.</b>"),
        (RoleType.BODYGUARD, "🛡️ <b>Qo'riqchi himoya joyiga chiqdi.</b>"),
        (RoleType.LAWYER, "⚖️ <b>Mafia himoya bosqichi boshlandi.</b>"),
        (RoleType.MAFIA, "🔫 <b>Mafia yakuniy hujumga tayyorlanmoqda.</b>"),
        (RoleType.DON, "👑 <b>Don mafiya rejasini boshqarmoqda.</b>"),
        (RoleType.GODFATHER, "🤵 <b>Godfather soyada ishlayapti.</b>"),
        (RoleType.MANIAC, "🔪 <b>Manyak tun bo'yi kezmoqda.</b>"),
        (RoleType.VIGILANTE, "🗡️ <b>Qonunchi adolat izlamoqda.</b>"),
        (RoleType.WITCH, "🧙 <b>Jodugar maxfiy harakatga o'tdi.</b>"),
        (RoleType.DAYDI, "🧥 <b>Daydi kuzatuvga chiqdi.</b>"),
        (RoleType.JOURNALIST, "📰 <b>Jurnalist maxfiy yozmoqda.</b>"),
        (RoleType.SPY, "🕵️ <b>Agent kuzatishga tayyor.</b>"),
    ]
    alive_roles = {p.role for p in alive if p.role}
    for role, text in role_stage_notices:
        if role in alive_roles:
            await _stage_notice(text)

    # Har bir aktiv rolga DM yuborish
    for p in alive:
        cfg = get_role(p.role)
        if not cfg.night_action:
            # Agent (Spy) — passiv, ma'lumot keyingi tongda beriladi
            continue

        others = [x for x in alive if x.user_id != p.user_id]

        try:
            if p.role == RoleType.DON:
                await bot.send_message(
                    p.user_id,
                    f"👑 <b>DON — Tun {night_num}</b>\n\n"
                    f"O'ldirish nishoni yoki Detektiv tekshiruvi?",
                    parse_mode="HTML",
                    reply_markup=don_action_kb(chat_id)
                )

            elif p.role == RoleType.LAWYER:
                mafia_others = [
                    x for x in game.alive_mafia() if x.user_id != p.user_id
                ]
                if mafia_others:
                    await bot.send_message(
                        p.user_id,
                        f"⚖️ <b>ADVOKAT — Tun {night_num}</b>\n\n"
                        f"Qaysi mafia a'zosini himoya qilasiz?",
                        parse_mode="HTML",
                        reply_markup=lawyer_kb(mafia_others, chat_id)
                    )

            elif p.role == RoleType.WITCH:
                await bot.send_message(
                    p.user_id,
                    f"🧙 <b>JODUGAR — Tun {night_num}</b>\n\n"
                    f"Qaysi sehrni ishlatmoqchisiz?",
                    parse_mode="HTML",
                    reply_markup=witch_kb(chat_id, p.witch_poison_used, p.witch_heal_used)
                )

            elif p.role == RoleType.VIGILANTE and p.vigilante_used:
                # Qonunchi qobiliyatini ishlatib bo'lgan
                pass

            elif p.role == RoleType.DETECTIVE:
                await bot.send_message(
                    p.user_id,
                    f"🔍 <b>KOMISSAR — Tun {night_num}</b>\n\n"
                    f"Tekshirish yoki o'q otishdan birini tanlang.",
                    parse_mode="HTML",
                    reply_markup=detective_action_kb(chat_id),
                )

            else:
                exclude = [p.user_id] if p.role not in (
                    RoleType.DOCTOR, RoleType.BODYGUARD
                ) else []
                kb = target_kb(others, "night_target", chat_id, exclude)
                await bot.send_message(
                    p.user_id,
                    f"{cfg.emoji} <b>{cfg.name_uz.upper()} — Tun {night_num}</b>\n\n"
                    f"{cfg.action_prompt}",
                    parse_mode="HTML",
                    reply_markup=kb
                )

        except Exception as e:
            log.warning(f"[{chat_id}] {p.user_id} ga DM yuborilmadi: {e}")

    asyncio.create_task(_night_timer(chat_id, bot, group_id))


async def _night_timer(chat_id: int, bot: Bot, group_id: int):
    await asyncio.sleep(settings.NIGHT_TIMEOUT)
    game = get_game(chat_id)
    if game and game.phase == GamePhase.NIGHT:
        await process_dawn(chat_id, bot, group_id)


async def _offer_last_words(chat_id: int, bot: Bot, dead_ids: list[int]):
    game = get_game(chat_id)
    if not game:
        return

    for uid in dead_ids:
        p = game.get(uid)
        if not p or p.is_alive:
            continue
        deadline = game.last_words_deadlines.get(uid)
        if deadline is None:
            continue
        if deadline != float("inf") and time.monotonic() > deadline:
            continue
        try:
            await bot.send_message(uid, last_words_text(settings.LAST_WORDS_TIMEOUT), parse_mode="HTML")
        except Exception:
            pass


# ══════════════════════════════════════════════
#  TUN HARAKATLARI — CALLBACK'LAR
# ══════════════════════════════════════════════
@router.callback_query(F.data.startswith("night_target:"))
async def cb_night_target(cb: CallbackQuery, bot: Bot):
    _, tid, cid = cb.data.split(":")
    target_id, chat_id = int(tid), int(cid)
    game = get_game(chat_id)
    if not game or game.phase != GamePhase.NIGHT:
        return await cb.answer("Tun bosqichi emas!", show_alert=True)

    ok, msg = game.set_night_target(cb.from_user.id, target_id)
    await cb.answer(msg, show_alert=not ok)
    if ok:
        try:
            await cb.message.edit_text(
                cb.message.text + f"\n\n✅ Tanlandi: {game.get(target_id).full_name}",
                parse_mode="HTML"
            )
        except Exception:
            pass
        if game.all_night_done():
            await process_dawn(chat_id, bot, chat_id)


@router.callback_query(F.data.startswith("skip_action:"))
async def cb_skip_action(cb: CallbackQuery, bot: Bot):
    chat_id = int(cb.data.split(":")[1])
    game = get_game(chat_id)
    if not game or game.phase != GamePhase.NIGHT:
        return await cb.answer("Tun bosqichi emas!", show_alert=True)

    p = game.get(cb.from_user.id)
    if p:
        p.night_action_done = True
        game.na.acted.add(p.user_id)
    await cb.answer("⏭️ Bu tun harakatsiz qoldingiz.")
    try:
        await cb.message.edit_text("⏭️ Bu tun harakatsiz qoldingiz.")
    except Exception:
        pass
    if game.all_night_done():
        await process_dawn(chat_id, bot, chat_id)


# Don
@router.callback_query(F.data.startswith("don_kill:"))
async def cb_don_kill(cb: CallbackQuery):
    chat_id = int(cb.data.split(":")[1])
    game = get_game(chat_id)
    if not game or game.phase != GamePhase.NIGHT:
        return await cb.answer("Tun bosqichi emas!", show_alert=True)
    others = [p for p in game.alive() if p.user_id != cb.from_user.id]
    await cb.message.edit_text(
        "🔫 <b>Kimni o'ldirmoqchisiz?</b>",
        parse_mode="HTML",
        reply_markup=target_kb(others, "night_target", chat_id)
    )
    await cb.answer()


@router.callback_query(F.data.startswith("don_check:"))
async def cb_don_check_menu(cb: CallbackQuery):
    chat_id = int(cb.data.split(":")[1])
    game = get_game(chat_id)
    if not game: return
    others = [p for p in game.alive() if p.user_id != cb.from_user.id]
    await cb.message.edit_text(
        "🕵️ <b>Kimni tekshirasiz? (Detektivmi?)</b>",
        parse_mode="HTML",
        reply_markup=target_kb(others, "don_check_target", chat_id)
    )
    await cb.answer()


@router.callback_query(F.data.startswith("don_check_target:"))
async def cb_don_check_result(cb: CallbackQuery, bot: Bot):
    _, tid, cid = cb.data.split(":")
    target_id, chat_id = int(tid), int(cid)
    game = get_game(chat_id)
    if not game: return
    ok, result = game.set_don_check(cb.from_user.id, target_id)
    await cb.answer(result, show_alert=True)
    if ok:
        try:
            await cb.message.edit_text(f"🕵️ Tekshiruv natijasi: {result}", parse_mode="HTML")
        except Exception:
            pass
        if game.all_night_done():
            await process_dawn(chat_id, bot, chat_id)


# Komissar / Detektiv
@router.callback_query(F.data.startswith("detective_check:"))
async def cb_detective_check(cb: CallbackQuery):
    chat_id = int(cb.data.split(":")[1])
    game = get_game(chat_id)
    if not game:
        return
    others = [p for p in game.alive() if p.user_id != cb.from_user.id]
    await cb.message.edit_text(
        "🔍 <b>Kimni tekshirasiz?</b>",
        parse_mode="HTML",
        reply_markup=target_kb(others, "detective_check_target", chat_id),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("detective_check_target:"))
async def cb_detective_check_target(cb: CallbackQuery, bot: Bot):
    _, tid, cid = cb.data.split(":")
    target_id, chat_id = int(tid), int(cid)
    game = get_game(chat_id)
    if not game:
        return
    ok, result = game.set_detective_check(cb.from_user.id, target_id)
    await cb.answer(result, show_alert=True)
    if ok:
        try:
            await cb.message.edit_text(f"🔍 Tekshiruv tanlandi: {game.get(target_id).full_name}", parse_mode="HTML")
        except Exception:
            pass
        if game.all_night_done():
            await process_dawn(chat_id, bot, chat_id)


@router.callback_query(F.data.startswith("detective_shot:"))
async def cb_detective_shot(cb: CallbackQuery):
    chat_id = int(cb.data.split(":")[1])
    game = get_game(chat_id)
    if not game:
        return
    others = [p for p in game.alive() if p.user_id != cb.from_user.id]
    await cb.message.edit_text(
        "🔫 <b>Kimga o'q uzasiz?</b>",
        parse_mode="HTML",
        reply_markup=target_kb(others, "detective_shot_target", chat_id),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("detective_shot_target:"))
async def cb_detective_shot_target(cb: CallbackQuery, bot: Bot):
    _, tid, cid = cb.data.split(":")
    target_id, chat_id = int(tid), int(cid)
    game = get_game(chat_id)
    if not game:
        return
    ok, result = game.set_detective_shot(cb.from_user.id, target_id)
    await cb.answer(result, show_alert=True)
    if ok:
        try:
            await cb.message.edit_text(f"🔫 O'q tanlandi: {game.get(target_id).full_name}", parse_mode="HTML")
        except Exception:
            pass
        if game.all_night_done():
            await process_dawn(chat_id, bot, chat_id)


# Advokat
@router.callback_query(F.data.startswith("lawyer_protect:"))
async def cb_lawyer_protect(cb: CallbackQuery, bot: Bot):
    _, tid, cid = cb.data.split(":")
    target_id, chat_id = int(tid), int(cid)
    game = get_game(chat_id)
    if not game: return
    ok, msg = game.set_lawyer_target(cb.from_user.id, target_id)
    await cb.answer(msg, show_alert=not ok)
    if ok:
        try:
            await cb.message.edit_text(f"⚖️ {msg}", parse_mode="HTML")
        except Exception:
            pass
        if game.all_night_done():
            await process_dawn(chat_id, bot, chat_id)


# Jodugar
@router.callback_query(F.data.startswith("witch_poison:"))
async def cb_witch_poison(cb: CallbackQuery):
    chat_id = int(cb.data.split(":")[1])
    game = get_game(chat_id)
    if not game: return
    others = [p for p in game.alive() if p.user_id != cb.from_user.id]
    await cb.message.edit_text(
        "☠️ <b>Kimga zahar berasiz?</b>",
        parse_mode="HTML",
        reply_markup=target_kb(others, "witch_poison_target", chat_id)
    )
    await cb.answer()


@router.callback_query(F.data.startswith("witch_poison_target:"))
async def cb_witch_poison_target(cb: CallbackQuery, bot: Bot):
    _, tid, cid = cb.data.split(":")
    target_id, chat_id = int(tid), int(cid)
    game = get_game(chat_id)
    if not game: return
    ok, msg = game.set_witch_action(cb.from_user.id, "poison", target_id)
    await cb.answer(msg, show_alert=not ok)
    if ok:
        try:
            await cb.message.edit_text(f"☠️ {msg}")
        except Exception:
            pass
        if game.all_night_done():
            await process_dawn(chat_id, bot, chat_id)


@router.callback_query(F.data.startswith("witch_heal:"))
async def cb_witch_heal(cb: CallbackQuery):
    chat_id = int(cb.data.split(":")[1])
    game = get_game(chat_id)
    if not game: return
    dead_players = game.dead()
    if not dead_players:
        return await cb.answer("Tiklash uchun o'lik o'yinchi yo'q!", show_alert=True)
    await cb.message.edit_text(
        "💉 <b>Kimni tiklaysiz?</b>",
        parse_mode="HTML",
        reply_markup=target_kb(dead_players, "witch_heal_target", chat_id)
    )
    await cb.answer()


@router.callback_query(F.data.startswith("witch_heal_target:"))
async def cb_witch_heal_target(cb: CallbackQuery, bot: Bot):
    _, tid, cid = cb.data.split(":")
    target_id, chat_id = int(tid), int(cid)
    game = get_game(chat_id)
    if not game: return
    ok, msg = game.set_witch_action(cb.from_user.id, "heal", target_id)
    await cb.answer(msg, show_alert=not ok)
    if ok:
        try:
            await cb.message.edit_text(f"💉 {msg}")
        except Exception:
            pass
        if game.all_night_done():
            await process_dawn(chat_id, bot, chat_id)


# ══════════════════════════════════════════════
#  TONG
# ══════════════════════════════════════════════
async def process_dawn(chat_id: int, bot: Bot, group_id: int):
    game = get_game(chat_id)
    if not game or game.phase != GamePhase.NIGHT:
        return

    game.phase = GamePhase.DAWN

    res = game.resolve_night()

    # SPY — mafia nishonini biladi
    if res.spy_info:
        for p in game.alive():
            if p.role == RoleType.SPY:
                target = game.get(res.spy_info)
                target_text = target.mention if target else "noma'lum"
                try:
                    await bot.send_message(
                        p.user_id,
                        f"🕵️ <b>AGENT MA'LUMOTI:</b>\n\n"
                        f"Bu tun mafia nishoni: {target_text}",
                        parse_mode="HTML"
                    )
                except Exception:
                    pass

    # DAYDI — kuzatilgan nishon hujumi haqida maxfiy hisobot
    if res.daydi_reports:
        for uid, report_text in res.daydi_reports:
            try:
                await bot.send_message(uid, report_text, parse_mode="HTML")
            except Exception:
                pass

    # DETEKTIV natijasi (faqat detektivga)
    if res.detective_result:
        dr = res.detective_result
        for p in game.alive():
            if p.role == RoleType.DETECTIVE:
                verdict = "🔴 MAFIA!" if dr["is_mafia"] else "🟢 Begunoh (Shahar)"
                role_cfg = get_role(cast(RoleType, cast(object, dr["role"])))
                try:
                    await bot.send_message(
                        p.user_id,
                        f"🔍 <b>TEKSHIRUV NATIJASI:</b>\n\n"
                        f"👤 {dr['name']}\n"
                        f"Guruh: {verdict}\n"
                        f"<i>(Haqiqiy rol: {role_cfg.emoji} {role_cfg.name_uz})</i>",
                        parse_mode="HTML"
                    )
                except Exception:
                    pass

    # Guruhga tong xabari
    all_players = game.players
    await bot.send_message(
        group_id,
        dawn_text(game.day_num, res, all_players),
        parse_mode="HTML"
    )

    dead_ids = []
    for uid in res.killed:
        p = game.get(uid)
        if p and not p.is_alive:
            dead_ids.append(uid)
    if res.bodyguard_died:
        p = game.get(res.bodyguard_died)
        if p and not p.is_alive:
            dead_ids.append(res.bodyguard_died)

    if dead_ids:
        for uid in dead_ids:
            game.queue_last_words(uid, settings.LAST_WORDS_TIMEOUT)
        await _offer_last_words(chat_id, bot, dead_ids)

    # G'alaba tekshiruvi
    win = game.check_win()
    if win:
        await asyncio.sleep(2)
        return await finish_game(chat_id, bot, group_id, win[0], win[1])

    await asyncio.sleep(3)
    await begin_day(chat_id, bot, group_id)


# ══════════════════════════════════════════════
#  KUN
# ══════════════════════════════════════════════
async def begin_day(chat_id: int, bot: Bot, group_id: int):
    game = get_game(chat_id)
    if not game:
        return

    game.phase = GamePhase.DAY
    alive = game.alive()

    # Mer tugmasi (agar oshkor qilmagan bo'lsa)
    mayor = next((p for p in alive if p.role == RoleType.MAYOR and not p.mayor_revealed), None)
    if mayor:
        try:
            await bot.send_message(
                mayor.user_id,
                "🎩 <b>MER</b>\n\nRolingizni oshkor qilasizmi? (ovozingiz 3 ga oshadi)",
                parse_mode="HTML",
                reply_markup=reveal_mayor_kb(chat_id)
            )
        except Exception:
            pass

    await bot.send_message(
        group_id,
        day_text(game.day_num, alive),
        parse_mode="HTML"
    )

    asyncio.create_task(_day_timer(chat_id, bot, group_id))


async def _day_timer(chat_id: int, bot: Bot, group_id: int):
    await asyncio.sleep(settings.DAY_DISCUSSION_TIME)
    game = get_game(chat_id)
    if game and game.phase == GamePhase.DAY:
        await begin_voting(chat_id, bot, group_id)


# ══════════════════════════════════════════════
#  OVOZ BERISH
# ══════════════════════════════════════════════
async def begin_voting(chat_id: int, bot: Bot, group_id: int):
    game = get_game(chat_id)
    if not game:
        return

    game.phase = GamePhase.VOTING
    game.start_vote()
    alive = game.alive()

    msg = await bot.send_message(
        group_id,
        vote_start_text(),
        parse_mode="HTML",
        reply_markup=vote_entry_kb(settings.BOT_USERNAME, chat_id)
    )
    game.msg_ids["vote"] = msg.message_id

    for p in alive:
        try:
            await bot.send_message(
                p.user_id,
                vote_start_text() + "\n\n<b>Quyidan ovoz bering:</b>",
                parse_mode="HTML",
                reply_markup=vote_kb(alive, chat_id),
            )
        except Exception:
            pass

    asyncio.create_task(_vote_timer(chat_id, bot, group_id))


async def _vote_timer(chat_id: int, bot: Bot, group_id: int):
    await asyncio.sleep(settings.VOTE_TIMEOUT)
    game = get_game(chat_id)
    if game and game.phase == GamePhase.VOTING:
        await process_vote(chat_id, bot, group_id)


@router.callback_query(F.data.startswith("vote:"))
async def cb_vote(cb: CallbackQuery, bot: Bot):
    _, tid, cid = cb.data.split(":")
    target_id, chat_id = int(tid), int(cid)
    game = get_game(chat_id)
    if not game or game.phase != GamePhase.VOTING:
        return await cb.answer("Ovoz berish bosqichi emas!", show_alert=True)

    ok, msg = game.cast_vote(cb.from_user.id, target_id)
    if ok:
        target = game.get(target_id)
        await cb.answer(f"✅ {target.full_name if target else ''} ga ovoz!")
        await _refresh_vote(cb, chat_id, game)
        alive_cnt = len(game.alive())
        if game.vote and game.vote.total() >= alive_cnt:
            await process_vote(chat_id, bot, chat_id)
    else:
        await cb.answer(msg, show_alert=True)


@router.callback_query(F.data.startswith("vote_skip:"))
async def cb_vote_skip(cb: CallbackQuery, bot: Bot):
    chat_id = int(cb.data.split(":")[1])
    game = get_game(chat_id)
    if not game or game.phase != GamePhase.VOTING:
        return await cb.answer("Ovoz berish bosqichi emas!", show_alert=True)

    ok, msg = game.cast_skip(cb.from_user.id)
    await cb.answer(msg)
    if ok:
        await _refresh_vote(cb, chat_id, game)
        if game.vote and game.vote.total() >= len(game.alive()):
            await process_vote(chat_id, bot, chat_id)


async def _refresh_vote(cb: CallbackQuery, chat_id: int, game):
    if not game.vote:
        return
    alive  = game.alive()
    tally  = game.vote.tally()
    voted  = game.vote.total()
    total  = len(alive)
    try:
        await cb.message.edit_text(
            vote_progress_text(alive, tally, voted, total),
            parse_mode="HTML",
            reply_markup=vote_kb(alive, chat_id)
        )
    except Exception:
        pass


async def process_vote(chat_id: int, bot: Bot, group_id: int):
    game = get_game(chat_id)
    if not game or game.phase != GamePhase.VOTING:
        return

    game.phase = GamePhase.EXECUTION
    exec_id, extra = game.resolve_vote()

    await bot.send_message(
        group_id,
        execution_text(exec_id, game.players, extra),
        parse_mode="HTML"
    )

    dead_ids = []
    if exec_id:
        p = game.get(exec_id)
        if p and not p.is_alive:
            dead_ids.append(exec_id)

    for uid in list(game.last_words_queue):
        p = game.get(uid)
        if p and not p.is_alive and uid not in dead_ids:
            dead_ids.append(uid)

    if dead_ids:
        await _offer_last_words(chat_id, bot, dead_ids)

    # G'alaba tekshiruvi
    win = game.check_win()
    if win:
        await asyncio.sleep(2)
        return await finish_game(chat_id, bot, group_id, win[0], win[1])

    await asyncio.sleep(3)
    await begin_night(chat_id, bot, group_id)


# ══════════════════════════════════════════════
#  MER OSHKOR QILISH
# ══════════════════════════════════════════════
@router.callback_query(F.data.startswith("mayor_reveal:"))
async def cb_mayor_reveal(cb: CallbackQuery, bot: Bot):
    chat_id = int(cb.data.split(":")[1])
    game = get_game(chat_id)
    if not game:
        return await cb.answer("O'yin topilmadi!", show_alert=True)

    ok, msg = game.mayor_reveal(cb.from_user.id)
    await cb.answer(msg[:200], show_alert=True)
    if ok:
        await bot.send_message(chat_id, f"📢 {msg}", parse_mode="HTML")
        try:
            await cb.message.delete()
        except Exception:
            pass


# ══════════════════════════════════════════════
#  SNAYPER (kunduz otish)
# ══════════════════════════════════════════════
@router.callback_query(F.data.startswith("snipe:"))
async def cb_snipe(cb: CallbackQuery, bot: Bot):
    _, tid, cid = cb.data.split(":")
    target_id, chat_id = int(tid), int(cid)
    game = get_game(chat_id)
    if not game or game.phase not in (GamePhase.DAY, GamePhase.VOTING):
        return await cb.answer("Snayper faqat kunduz otishi mumkin!", show_alert=True)

    ok, msg = game.sniper_shoot(cb.from_user.id, target_id)
    await cb.answer(msg[:200], show_alert=True)
    if ok:
        await bot.send_message(chat_id, f"🎯 {msg}", parse_mode="HTML")
        dead_ids = []
        target = game.get(target_id)
        shooter = game.get(cb.from_user.id)
        if target and not target.is_alive:
            dead_ids.append(target_id)
        elif shooter and not shooter.is_alive:
            dead_ids.append(cb.from_user.id)
        for uid in dead_ids:
            game.queue_last_words(uid, settings.LAST_WORDS_TIMEOUT)
        if dead_ids:
            await _offer_last_words(chat_id, bot, dead_ids)
        win = game.check_win()
        if win:
            await finish_game(chat_id, bot, chat_id, win[0], win[1])
        try:
            await cb.message.delete()
        except Exception:
            pass


@router.callback_query(F.data.startswith("snipe_cancel:"))
async def cb_snipe_cancel(cb: CallbackQuery):
    await cb.answer("Bekor qilindi.")
    try:
        await cb.message.delete()
    except Exception:
        pass


# ══════════════════════════════════════════════
#  O'YINNI YAKUNLASH
# ══════════════════════════════════════════════
async def finish_game(chat_id: int, bot: Bot, group_id: int, winner: Team, reason: str):
    game = get_game(chat_id)
    if not game:
        return

    game.phase = GamePhase.FINISHED

    from logic.roles import MAFIA_ROLES, CITY_ROLES, NEUTRAL_ROLES
    win_roles = {
        Team.MAFIA:   MAFIA_ROLES,
        Team.CITY:    CITY_ROLES,
        Team.NEUTRAL: NEUTRAL_ROLES,
    }.get(winner, set())

    await bot.send_message(
        group_id,
        game_over_text(reason, game.players_text(show_roles=True), game.day_num),
        parse_mode="HTML"
    )

    # DB ga saqlash
    try:
        results = []
        for p in game.players.values():
            won = (p.role in win_roles) if p.role else False
            if won:
                await add_coins(p.user_id, settings.WIN_COINS_REWARD)
            results.append({
                "user_id":      p.user_id,
                "role":         p.role.value if p.role else "unknown",
                "survived":     p.is_alive,
                "won":          won,
                "kills":        p.kills,
                "was_voted_out": p.was_voted_out,
            })
        await save_game_result(
            chat_id      = chat_id,
            day_count    = game.day_num,
            player_count = len(game.players),
            winner_team  = winner.value,
            player_results = results,
        )
    except Exception as e:
        log.error(f"DB saqlashda xato: {e}")

    delete_game(chat_id)

