"""
common.py — /start, /help, /rules
"""
import time
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from keyboards.help_kb import help_roles_main_kb, help_roles_all_kb, help_back_kb
from keyboards.main_menu import private_menu_kb
from keyboards.game_kb import vote_kb
from logic.registry import get_game, all_games
from logic.manager import GamePhase
from logic.roles import RoleType, get_role
from utils.texts import RULES, vote_start_text, last_words_text
from config import settings

router = Router()


def _start_payload(message: Message) -> str:
    parts = (message.text or "").split(maxsplit=1)
    return parts[1] if len(parts) > 1 else ""

HELP_ALIAS_TO_ROLE: dict[str, RoleType] = {
    # Legacy callback keylari uchun moslik
    "komissar": RoleType.DETECTIVE,
    "serjant": RoleType.BODYGUARD,
    "qotil": RoleType.MANIAC,
    "mashuqa": RoleType.ESCORT,
    "suitsid": RoleType.SUICIDE,
    "suicide": RoleType.SUICIDE,
    "civilian": RoleType.CIVILIAN,
    "doctor": RoleType.DOCTOR,
    "don": RoleType.DON,
    "mafia": RoleType.MAFIA,
}

EXTRA_HELP_ROLES: dict[str, tuple[str, str]] = {}


def _role_details_text(role_key: str) -> str:
    role = HELP_ALIAS_TO_ROLE.get(role_key)
    if role:
        cfg = get_role(role)
        return f"{cfg.emoji} <b>{cfg.name_uz}</b>\n\n{cfg.full_desc}"

    # help_role callbackida role.value yuborilganda to'g'ridan-to'g'ri ochish
    try:
        cfg = get_role(RoleType(role_key))
        return f"{cfg.emoji} <b>{cfg.name_uz}</b>\n\n{cfg.full_desc}"
    except ValueError:
        pass

    extra = EXTRA_HELP_ROLES.get(role_key)
    if extra:
        return f"{extra[0]}\n\n{extra[1]}"

    return "⚠️ Rol topilmadi."


HELP_COMMANDS_TEXT = (
    "<b>📋 BUYRUQLAR</b>\n\n"
    "<b>Guruhda:</b>\n"
    "/newgame — Lobby ochish\n"
    "/startgame — O'yinni boshlash\n"
    "/endgame — To'xtatish\n"
    "/players — O'yinchilar\n"
    "/rules — Qoidalar\n"
    "/stats — Guruh statistikasi\n"
    "/top — Top 10\n\n"
    "<b>Shaxsiy:</b>\n"
    "/profile — Profil va inventar\n"
    "/coins — Tangalar\n"
    "/shop — Do'kon\n"
    "/buy passport — Soxta passport xarid\n"
    "/buycoins &lt;son&gt; — Tanga sotib olish (demo)\n"
    "/mystats — Profilim\n"
    "/snipe — Snayper otishi\n"
    "/reveal — Mer oshkor qilish\n\n"
    "<b>Admin:</b>\n"
    "/skipnight /skipday /skipvote\n"
    "/gamestatus /kick /settime"
)

@router.message(Command("start"))
async def cmd_start(message: Message):
    payload = _start_payload(message)

    if message.chat.type == "private" and payload.startswith("vote_"):
        try:
            chat_id = int(payload.split("_", maxsplit=1)[1])
        except ValueError:
            return await message.answer("⚠️ Noto'g'ri ovoz paneli.")

        game = get_game(chat_id)
        if not game or game.phase != GamePhase.VOTING:
            return await message.answer("⚠️ Hozir ovoz berish bosqichi emas.")

        p = game.get(message.from_user.id)
        if not p or not p.is_alive:
            return await message.answer("⚠️ Siz bu o'yinda faol emassiz.")

        await message.answer(
            vote_start_text() + "\n\n<b>Quyidan nishon tanlang:</b>",
            parse_mode="HTML",
            reply_markup=vote_kb(game.alive(), chat_id),
        )
        return

    if message.chat.type == "private" and payload.startswith("lastwords_"):
        await message.answer(
            last_words_text(settings.LAST_WORDS_TIMEOUT),
            parse_mode="HTML",
        )
        return

    if message.chat.type == "private":
        await message.answer(
            "👋 Salom! Men <b>Mafia Bot</b>man 🎭\n\n"
            "Guruhingizga qo'shing va o'yin boshlang!\n"
            "Pastki menyuda do'kon, profil va tanga bo'limlari bor.\n\n"
            "<b>Buyruqlar:</b>\n"
            "/newgame — Yangi o'yin\n"
            "/rules — Qoidalar\n"
            "/mystats — Mening statistikam\n"
            "/top — Top o'yinchilar",
            parse_mode="HTML",
            reply_markup=private_menu_kb(),
        )
    else:
        await message.answer(
            "🎭 <b>Mafia Bot</b> tayyor!\n/newgame bilan boshlang.",
            parse_mode="HTML",
        )


class _PendingLastWordsFilter:
    async def __call__(self, message: Message) -> bool:
        if message.chat.type != "private" or not message.text or message.text.startswith("/"):
            return False
        for game in all_games().values():
            player = game.get(message.from_user.id)
            if not player:
                continue
            deadline = game.last_words_deadlines.get(message.from_user.id)
            if deadline is None:
                continue
            if deadline != float("inf") and time.monotonic() > deadline:
                continue
            return True
        return False


@router.message(_PendingLastWordsFilter())
async def msg_last_words(message: Message):
    for chat_id, game in all_games().items():
        player = game.get(message.from_user.id)
        if not player:
            continue
        if not game.take_last_words(message.from_user.id):
            continue
        text = (
            f"💬 <b>OXIRGI SO'ZLAR</b>\n\n"
            f"👤 {player.mention}\n"
            f"📝 {message.html_text or message.text}"
        )
        await message.bot.send_message(chat_id, text, parse_mode="HTML")
        await message.answer("✅ Xabaringiz guruhga yuborildi.")
        return

@router.message(Command("help"))
async def cmd_help(message: Message):
    if message.chat.type != "private":
        return await message.answer("ℹ️ Bu buyruq faqat shaxsiy chatda ishlaydi.")
    await message.answer(
        "📚 <b>Mavjud rollar ro'yxati</b>\n\n"
        "Uning tavsifini ko'rish uchun rol nomini bosing:",
        parse_mode="HTML",
        reply_markup=help_roles_main_kb(),
    )


@router.callback_query(F.data == "help:main")
async def cb_help_main(cb: CallbackQuery):
    await cb.message.edit_text(
        "📚 <b>Mavjud rollar ro'yxati</b>\n\n"
        "Uning tavsifini ko'rish uchun rol nomini bosing:",
        parse_mode="HTML",
        reply_markup=help_roles_main_kb(),
    )
    await cb.answer()


@router.callback_query(F.data == "help_roles:all")
async def cb_help_all_roles(cb: CallbackQuery):
    await cb.message.edit_text(
        "🎭 <b>Barcha mavjud rollar</b>\n"
        "Kerakli rolni tanlab tavsifini oching.",
        parse_mode="HTML",
        reply_markup=help_roles_main_kb(),
    )
    await cb.answer()


@router.callback_query(F.data == "help:commands")
async def cb_help_commands(cb: CallbackQuery):
    await cb.message.edit_text(
        HELP_COMMANDS_TEXT,
        parse_mode="HTML",
        reply_markup=help_back_kb(),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("help_role:"))
async def cb_help_role(cb: CallbackQuery):
    role_key = cb.data.split(":", maxsplit=1)[1]
    await cb.message.edit_text(
        _role_details_text(role_key),
        parse_mode="HTML",
        reply_markup=help_back_kb(),
    )
    await cb.answer()

@router.message(Command("rules"))
async def cmd_rules(message: Message):
    if message.chat.type != "private":
        return await message.answer("ℹ️ Bu buyruq faqat shaxsiy chatda ishlaydi.")
    await message.answer(RULES, parse_mode="HTML")
