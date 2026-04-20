"""
O'yin xabarlari shablonlari — barcha matnlar shu yerda.
"""
from __future__ import annotations
from typing import cast
from logic.manager import NightResult
from logic.player import Player
from logic.roles import get_role, RoleType
from config import settings


# ══════════════════════════════════════════════
#  LOBBY
# ══════════════════════════════════════════════
def lobby_text(players: dict, chat_id: int) -> str:
    plist = "\n".join(
        f"{i}. {p.mention} ✅"
        for i, p in enumerate(players.values(), 1)
    )
    n = len(players)
    status = (
        f"✅ Yetarli! Admin boshlashi mumkin."
        if n >= settings.MIN_PLAYERS
        else f"⏳ Yana <b>{settings.MIN_PLAYERS - n}</b> kishi kerak...\n(<i>Pastdagi tugma orqali o'yinga AI bot qo'shishingiz mumkin</i>)"
    )
    return (
        f"🎭 <b>MAFIA O'YINI — LOBBY</b>\n\n"
        f"👥 O'yinchilar: <b>{n}/{settings.MAX_PLAYERS}</b>\n\n"
        f"{plist}\n\n"
        f"{status}\n\n"
        f"⏱ Lobby <b>{settings.LOBBY_TIMEOUT}</b> soniyada yopiladi."
    )


# ══════════════════════════════════════════════
#  TUN
# ══════════════════════════════════════════════
def night_start_text(night_num: int) -> str:
    return (
        f"🌙 <b>TUN {night_num} BOSHLANDI</b>\n\n"
        f"😴 Shahar uxlamoqda...\n\n"
        f"🔫 Mafia — qurbonni tanlang\n"
        f"💊 Shifokor — kimni daving?\n"
        f"🔍 Detektiv — kimni tekshirasiz?\n"
        f"🛡️ Qo'riqchi — kimni himoya qilasiz?\n"
        f"🔪 Manyak — bu tun kim?\n"
        f"💃 Faoliyatchi — kimni bandlaysiz?\n"
        f"🧙 Jodugar — qaysi sehringiz?\n"
        f"🧥 Daydi — kimni kuzatasiz?\n\n"
        f"⏳ <b>{settings.NIGHT_TIMEOUT}</b> soniya vaqt bor.\n"
        f"📨 <i>Shaxsiy xabarlaringizni tekshiring!</i>"
    )


# ══════════════════════════════════════════════
#  TONG
# ══════════════════════════════════════════════
def dawn_text(day_num: int, res: NightResult, players: dict) -> str:
    lines = [f"☀️ <b>TUN {day_num} TUGADI</b>\n"]

    if not res.killed and not res.bodyguard_died and not res.witch_poison:
        lines.append("🌟 Bu tun hech kim halok bo'lmadi!")
    else:
        for kid in res.killed:
            p = players.get(kid)
            if p:
                cfg = get_role(p.role)
                lines.append(
                    f"🩸 <b>{p.mention}</b> tunda hayotdan ko'z yumdi.\n"
                    f"   Roli edi: {cfg.emoji} {cfg.name_uz}"
                )
        if res.bodyguard_died:
            bg = players.get(res.bodyguard_died)
            if bg:
                lines.append(f"🛡️ {bg.mention} boshqasini himoya qilib qurbon bo'ldi!")

    # Shifokor qutqardi
    if res.saved_by_doctor:
        p = players.get(res.saved_by_doctor)
        nm = p.mention if p else "kimdir"
        lines.append(f"💊 Shifokor {nm}ni o'limdan saqlab qoldi!")

    # Qo'riqchi qutqardi
    if res.saved_by_bodyguard and not res.bodyguard_died:
        p = players.get(res.saved_by_bodyguard)
        nm = p.mention if p else "kimdir"
        lines.append(f"🛡️ Qo'riqchi {nm}ni himoya qildi!")

    # Jurnalist oshkor qildi
    if res.journalist_reveal:
        jr = res.journalist_reveal
        p  = players.get(jr["target_id"])
        cfg = get_role(cast(RoleType, cast(object, jr["role"])))
        nm  = p.mention if p else jr["name"]
        lines.append(
            f"📰 <b>JURNALIST XABARI:</b> {nm} — {cfg.emoji} <b>{cfg.name_uz}</b>!"
        )

    # Jodugar
    if res.witch_heal:
        p = players.get(res.witch_heal)
        if p:
            lines.append(f"🧙 Jodugar kimnidir tikladi!")

    # Qo'shimcha hodisalar
    for ev in res.events:
        lines.append(ev)

    return "\n\n".join(lines)


# ══════════════════════════════════════════════
#  KUN
# ══════════════════════════════════════════════
def day_text(day_num: int, alive: list[Player]) -> str:
    pl = "\n".join(
        f"{i}. {p.mention}" + (" 🎩" if p.mayor_revealed else "")
        for i, p in enumerate(alive, 1)
    )
    return (
        f"☀️ <b>KUN {day_num} — MUHOKAMA</b>\n\n"
        f"👥 Tirik o'yinchilar ({len(alive)}):\n{pl}\n\n"
        f"💬 <b>{settings.DAY_DISCUSSION_TIME}</b> soniya muhokama!\n"
        f"🎯 Snayper: /snipe | 📢 Mer: /reveal"
    )


# ══════════════════════════════════════════════
#  OVOZ BERISH
# ══════════════════════════════════════════════
def vote_start_text() -> str:
    return (
        f"🗳️ <b>OVOZ BERISH!</b>\n\n"
        f"Ovoz berish endi bot orqali bajariladi.\n"
        f"Tugmani bosib botga o'ting va ovozingizni bering.\n\n"
        f"⏳ <b>{settings.VOTE_TIMEOUT}</b> soniya\n\n"
        f"🎩 <i>Mer 2 ovozga, oshkor qilgan Mer 3 ovozga ega.</i>"
    )


def last_words_text(deadline: int) -> str:
    return (
        f"💬 <b>OXIRGI SO'ZLAR</b>\n\n"
        f"Siz o'ldingiz. Endi botga bitta xabar yuborishingiz mumkin.\n"
        f"Bu xabar guruhga chiqariladi.\n\n"
        f"⏳ Vaqt: <b>{deadline}</b> soniya"
    )


def vote_progress_text(alive: list[Player], tally: dict[int, int], voted: int, total: int) -> str:
    lines = [f"🗳️ <b>OVOZ BERISH</b> ({voted}/{total})\n"]
    for p in alive:
        cnt = tally.get(p.user_id, 0)
        bar = "🔴" * cnt + "⚪" * max(0, 5 - cnt)
        lines.append(f"{bar} {p.full_name}: {cnt}")
    return "\n".join(lines)


# ══════════════════════════════════════════════
#  IJRO
# ══════════════════════════════════════════════
def execution_text(executed_id: int | None, players: dict, extra: str | None) -> str:
    lines = ["⚖️ <b>OVOZ BERISH YAKUNLANDI</b>\n"]
    if executed_id:
        p = players.get(executed_id)
        if p:
            cfg = get_role(p.role)
            lines.append(
                f"🪓 <b>{p.mention}</b> ko'pchilik ovozi bilan o'yindan chiqarildi!\n"
                f"   Roli edi: {cfg.emoji} <b>{cfg.name_uz}</b>"
            )
    else:
        lines.append("🤝 Ovozlar teng taqsimlandi — hech kim chiqarilmadi.")
    if extra:
        lines.append(extra)
    return "\n\n".join(lines)


# ══════════════════════════════════════════════
#  O'YIN TUGADI
# ══════════════════════════════════════════════
def game_over_text(winner_msg: str, players_text: str, day_count: int) -> str:
    return (
        f"🏆 <b>O'YIN TUGADI!</b>\n\n"
        f"{winner_msg}\n\n"
        f"<b>Barcha o'yinchilar va rollari:</b>\n"
        f"{players_text}\n\n"
        f"📊 Jami <b>{day_count}</b> kun davom etdi.\n\n"
        f"Yangi o'yin: /newgame"
    )


# ══════════════════════════════════════════════
#  QOIDALAR
# ══════════════════════════════════════════════
RULES = """
🎭 <b>MAFIA O'YINI — TO'LIQ QOIDALAR</b>

<b>👥 ROLLAR:</b>

<b>🔴 MAFIA GURUHI:</b>
🔫 <b>Mafia</b> — Tunda bittani o'ldiradi
👑 <b>Don</b> — O'ldiradi + detektivni aniqlaydi. Detektivga begunoh ko'rinadi!
🤵 <b>Godfather (Ota)</b> — Detektivga fuqaro ko'rinadi
⚖️ <b>Advokat</b> — Mafia a'zosini detektivdan himoya qiladi

<b>🔵 SHAHAR GURUHI:</b>
👤 <b>Fuqaro</b> — Kunduz ovoz beradi
💊 <b>Shifokor</b> — Tunda saqlay oladi (o'zini 1x)
🔍 <b>Detektiv</b> — Tunda rol tekshiradi
🛡️ <b>Qo'riqchi</b> — Himoya qiladi, o'zi o'ladi
🎯 <b>Snayper</b> — Kunduz 1 o'q (xato = o'zi o'ladi)
🎩 <b>Mer</b> — 2 ovoz (oshkor qilsa 3)
🗡️ <b>Qonunchi</b> — Tunda 1x o'ldiradi (begunoh o'lsa o'zi ham o'ladi)
📰 <b>Jurnalist</b> — Rolni hammaga oshkor qiladi (1x)
🕵️ <b>Agent</b> — Mafia nishonini biladi (passiv)
🧥 <b>Daydi</b> — Tunda kuzatadi, hujum bo'lsa xabar oladi
🍀 <b>Omadli</b> — Birinchi o'limdan omon qoladi

<b>⚪ NEYTRAL:</b>
🔪 <b>Manyak</b> — Tunda o'ldiradi, yolg'iz g'alaba
💣 <b>Suitsid</b> — Ovoz bilan o'lsa kimnidir olib ketadi
💃 <b>Faoliyatchi</b> — Tun harakatini bloklaydi
🧙 <b>Jodugar</b> — Zahar (1x) + Tiklash (1x)
💣 <b>Kamikaze</b> — Ovoz bilan chiqsa, bitta o'yinchini olib ketadi

<b>🏆 G'ALABA:</b>
• Shahar → Barcha mafia+manyak yo'q qilinsa
• Mafia → Tirik mafia ≥ tirik shahar bo'lsa
• Manyak → Oxirgi 1 kishi bo'lib qolsa
• Jodugar → Oxirgi 3 ichida bo'lsa
"""
