"""
19 ta to'liq rol ta'rifi — mashhur Mafia botlardagi barcha rollar.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class RoleType(str, Enum):
    # ── MAFIA GURUHI ─────────────────────────
    MAFIA      = "mafia"       # 🔫 Oddiy mafia
    DON        = "don"         # 👑 Don — rahbar, detektivga begunoh ko'rinadi
    GODFATHER  = "godfather"   # 🤵 Ota — detektivga fuqaro ko'rinadi
    LAWYER     = "lawyer"      # ⚖️  Advokat — kimnidir detektivdan himoya qiladi

    # ── SHAHAR GURUHI ─────────────────────────
    CIVILIAN   = "civilian"    # 👤 Fuqaro
    DOCTOR     = "doctor"      # 💊 Shifokor
    DETECTIVE  = "detective"   # 🔍 Detektiv
    BODYGUARD  = "bodyguard"   # 🛡️  Qo'riqchi
    SNIPER     = "sniper"      # 🎯 Snayper
    MAYOR      = "mayor"       # 🎩 Mer — 2 ovoz
    VIGILANTE  = "vigilante"   # 🗡️  Qonunchi — tunda o'ldira oladi (bir marta)
    JOURNALIST = "journalist"  # 📰 Jurnalist — kimningdir rolini oshkor qiladi
    SPY        = "spy"         # 🕵️  Agent — tunda mafia nishonini biladi
    DAYDI      = "daydi"       # 🧥 Daydi — tunda kuzatadi, hujumdan xabar oladi
    OMADLI     = "omadli"      # 🍀 Omadli — birinchi o'limdan qutuladi

    # ── NEYTRAL ───────────────────────────────
    MANIAC     = "maniac"      # 🔪 Manyak — yolg'iz g'alaba
    SUICIDE    = "suicide"     # 💣 Suitsid — ovoz bilan o'lsa kimnidir olib ketadi
    ESCORT     = "escort"      # 💃 Faoliyatchi — kimningdir tun harakatini bloklaydi
    WITCH      = "witch"       # 🧙 Jodugar — zahar va davo ichimliği (har biri 1x)
    KAMIKAZE   = "kamikaze"    # 💣 Kamikaze — ovoz bilan chiqarilsa birini olib ketadi


class Team(str, Enum):
    MAFIA   = "mafia"
    CITY    = "city"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class RoleConfig:
    role_type:    RoleType
    team:         Team
    emoji:        str
    name_uz:      str
    short_desc:   str           # Qisqa tavsif (lobby uchun)
    full_desc:    str           # To'liq tavsif (DM uchun)
    night_action: bool
    action_prompt: str = ""
    can_chat_night: bool = False
    win_with_mafia: bool = False
    reveals_as_innocent: bool = False  # Detektivga begunoh ko'rinadimi


ROLES: dict[RoleType, RoleConfig] = {

    # ════════════════════════════════════════
    #  MAFIA GURUHI
    # ════════════════════════════════════════

    RoleType.MAFIA: RoleConfig(
        role_type   = RoleType.MAFIA,
        team        = Team.MAFIA,
        emoji       = "🔫",
        name_uz     = "Mafia",
        short_desc  = "Har tunda bittani o'ldiradi",
        full_desc   = (
            "Siz <b>MAFIA</b>siz! 🔫\n\n"
            "Her tunda jamoangiz bilan birgalikda bir fuqaroni o'ldirish uchun nishon tanlang.\n\n"
            "Maqsad: Tirik mafiya soni tirik shahar + neytrallar soniga teng yoki ko'p bo'lsin.\n\n"
            "🤫 <i>Shaxsiy xabarda siz va Don faqat birgalikda nishon belgilaysiz.</i>"
        ),
        night_action  = True,
        action_prompt = "🔫 Bu tun kimni yo'q qilamiz?",
        can_chat_night= True,
    ),

    RoleType.DON: RoleConfig(
        role_type   = RoleType.DON,
        team        = Team.MAFIA,
        emoji       = "👑",
        name_uz     = "Don Mafia",
        short_desc  = "Mafia rahbari: o'ldiradi + detektivni aniqlaydi",
        full_desc   = (
            "Siz <b>DON MAFIA</b>siz! 👑\n\n"
            "Qobiliyatlar:\n"
            "• 🔫 Jamoangiz bilan bittani o'ldirish\n"
            "• 🕵️ Tunda bir kishini tekshirish: u Detektivmi?\n\n"
            "Detektiv tekshirsa — siz oddiy fuqaro bo'lib ko'rinasiz.\n\n"
            "Maqsad: Mafia bilan g'alaba qiling."
        ),
        night_action  = True,
        action_prompt = "👑 Tanlang: O'ldirish yoki Detektivni topish?",
        can_chat_night= True,
        reveals_as_innocent=True,
    ),

    RoleType.GODFATHER: RoleConfig(
        role_type   = RoleType.GODFATHER,
        team        = Team.MAFIA,
        emoji       = "🤵",
        name_uz     = "Ota (Godfather)",
        short_desc  = "Detektivga fuqaro ko'rinadi, lekin mafia",
        full_desc   = (
            "Siz <b>OTA (GODFATHER)</b>siz! 🤵\n\n"
            "Detektiv sizni tekshirsa — siz FUQARO bo'lib ko'rinasiz!\n\n"
            "Qobiliyat:\n"
            "• 🔫 Mafia bilan birgalikda o'ldirish\n"
            "• 🛡️ Detektivga «begunoh» ko'rinish\n\n"
            "Siz eng xavfli sirli kuchsiz. Don o'lsa — siz rahbar bo'lasiz."
        ),
        night_action  = True,
        action_prompt = "🤵 Bu tun kimni nishonga olamiz?",
        can_chat_night= True,
        reveals_as_innocent=True,
    ),

    RoleType.LAWYER: RoleConfig(
        role_type   = RoleType.LAWYER,
        team        = Team.MAFIA,
        emoji       = "⚖️",
        name_uz     = "Advokat",
        short_desc  = "Mafia a'zosini detektiv tekshiruvidan himoya qiladi",
        full_desc   = (
            "Siz <b>ADVOKAT</b>siz! ⚖️\n\n"
            "Tunda bir mafia a'zosini tanlang — Detektiv uni tekshirsa, natija «BEGUNOH» bo'ladi.\n\n"
            "Qoidalar:\n"
            "• Faqat mafia a'zosini himoya qilish mumkin\n"
            "• O'zingizni himoya qila olmaysiz\n"
            "• Har tunda bir kishi"
        ),
        night_action  = True,
        action_prompt = "⚖️ Qaysi mafia a'zosini himoya qilasiz?",
        can_chat_night= True,
    ),

    # ════════════════════════════════════════
    #  SHAHAR GURUHI
    # ════════════════════════════════════════

    RoleType.CIVILIAN: RoleConfig(
        role_type   = RoleType.CIVILIAN,
        team        = Team.CITY,
        emoji       = "👤",
        name_uz     = "Fuqaro",
        short_desc  = "Oddiy shahar fuqarosi",
        full_desc   = (
            "Siz <b>FUQARO</b>siz! 👤\n\n"
            "Maxsus qobiliyatingiz yo'q. Lekin sizning ovozingiz muhim!\n\n"
            "Kunduz muhokamada faol ishtirok eting, shubhalilarni aniqlang va ovoz bering.\n\n"
            "Maqsad: Barcha mafia va manyakni o'yindan chiqaring."
        ),
        night_action = False,
    ),

    RoleType.DOCTOR: RoleConfig(
        role_type   = RoleType.DOCTOR,
        team        = Team.CITY,
        emoji       = "💊",
        name_uz     = "Shifokor",
        short_desc  = "Tunda kimnidir o'limdan saqlaydi",
        full_desc   = (
            "Siz <b>SHIFOKOR</b>siz! 💊\n\n"
            "Har tunda bir kishini mafia hujumidan saqlaysiz.\n\n"
            "Qoidalar:\n"
            "• O'zingizni faqat <b>1 marta</b> saqlash mumkin\n"
            "• Ketma-ket ikki tunda bir xil odamni saqlash mumkin emas\n"
            "• Qo'riqchi bilan ayniy kishi himoyasi qo'shilmaydi"
        ),
        night_action  = True,
        action_prompt = "💊 Bu tun kimni davolaysiz?",
    ),

    RoleType.DETECTIVE: RoleConfig(
        role_type   = RoleType.DETECTIVE,
        team        = Team.CITY,
        emoji       = "🔍",
        name_uz     = "Detektiv",
        short_desc  = "Tunda kimningdir rolini tekshiradi",
        full_desc   = (
            "Siz <b>DETEKTIV</b>siz! 🔍\n\n"
            "Har tunda bir kishining Mafia guruhiga mansubligini tekshirasiz.\n\n"
            "Muhim eslatmalar:\n"
            "• Don va Godfather sizga «BEGUNOH» ko'rinadi!\n"
            "• Advokat himoya qilgan mafia ham «BEGUNOH» ko'rinadi\n"
            "• Natijani faqat siz bilasiz"
        ),
        night_action  = True,
        action_prompt = "🔍 Kimni tekshirasiz?",
    ),

    RoleType.BODYGUARD: RoleConfig(
        role_type   = RoleType.BODYGUARD,
        team        = Team.CITY,
        emoji       = "🛡️",
        name_uz     = "Qo'riqchi",
        short_desc  = "Birini himoya qiladi, hujumda o'zi o'ladi",
        full_desc   = (
            "Siz <b>QO'RIQCHI</b>siz! 🛡️\n\n"
            "Tunda bir kishini tanlang — agar u hujumga uchrasa, siz o'rniga halok bo'lasiz!\n\n"
            "Qoidalar:\n"
            "• O'zingizni himoya qila olmaysiz\n"
            "• Shifokor ham, qo'riqchi ham bir odamni himoya qilsa — faqat qo'riqchi ishlaydi\n"
            "• O'lgandan keyin qaytib kelmaysiz"
        ),
        night_action  = True,
        action_prompt = "🛡️ Kimni himoya qilasiz? (Ehtiyot bo'ling — siz o'lishingiz mumkin!)",
    ),

    RoleType.SNIPER: RoleConfig(
        role_type   = RoleType.SNIPER,
        team        = Team.CITY,
        emoji       = "🎯",
        name_uz     = "Snayper",
        short_desc  = "Kunduz 1 marta o'q otadi (xato = o'zi o'ladi)",
        full_desc   = (
            "Siz <b>SNAYPER</b>siz! 🎯\n\n"
            "Butun o'yin davomida faqat <b>1 marta</b> o'q otish imkoni bor.\n\n"
            "Kunduz kuni /snipe buyrug'i bilan nishon belgilang:\n"
            "• ✅ Nishon mafia yoki manyak → o'sha o'ladi\n"
            "• ❌ Nishon begunoh → SIZ o'lasiz!\n\n"
            "Foydalaning yoki foydalanmang — bu sizning qaroringiz."
        ),
        night_action = False,
    ),

    RoleType.MAYOR: RoleConfig(
        role_type   = RoleType.MAYOR,
        team        = Team.CITY,
        emoji       = "🎩",
        name_uz     = "Mer (Mayor)",
        short_desc  = "Ovozda 2 ta ovozga ega",
        full_desc   = (
            "Siz <b>MER (MAYOR)</b>siz! 🎩\n\n"
            "Siyosiy kuch! Sizning ovozingiz <b>2 ta ovozga</b> teng.\n\n"
            "Maxsus qobiliyat:\n"
            "• 📢 /reveal buyrug'i bilan istalgan vaqt rolingizni oshkor qilishingiz mumkin\n"
            "  → Oshkor qilsangiz: ovozingiz <b>3 ga</b> ko'tariladi!\n"
            "  → Lekin mafia endi sizni tahdid sifatida ko'radi!\n\n"
            "Tunda hech nima qilmaysiz."
        ),
        night_action = False,
    ),

    RoleType.VIGILANTE: RoleConfig(
        role_type   = RoleType.VIGILANTE,
        team        = Team.CITY,
        emoji       = "🗡️",
        name_uz     = "Qonunchi (Vigilante)",
        short_desc  = "Tunda 1 marta o'ldira oladi — lekin begunoh o'lsa, o'zi ham o'ladi",
        full_desc   = (
            "Siz <b>QONUNCHI (VIGILANTE)</b>siz! 🗡️\n\n"
            "O'z qo'lingizga adolat olishga qaror qildingiz.\n\n"
            "Qobiliyat: Tunda bir marta kimnidir o'ldira olasiz.\n"
            "• Nishon mafia/manyak → u o'ladi\n"
            "• Nishon begunoh fuqaro → u o'ladi, lekin siz ham <b>keyingi tunda</b> aybdorlik hissi bilan o'lasiz!\n\n"
            "Bu qobiliyatni ishlatish <b>ixtiyoriy</b>. Foydalanmasangiz ham bo'ladi."
        ),
        night_action  = True,
        action_prompt = "🗡️ Bu tun kimni yo'q qilmoqchisiz? (Ixtiyoriy — «O'tkazish» ham bosishingiz mumkin)",
    ),

    RoleType.JOURNALIST: RoleConfig(
        role_type   = RoleType.JOURNALIST,
        team        = Team.CITY,
        emoji       = "📰",
        name_uz     = "Jurnalist",
        short_desc  = "Kimningdir rolini hammaga oshkor qiladi",
        full_desc   = (
            "Siz <b>JURNALIST</b>siz! 📰\n\n"
            "Tunda bir kishini tanlang — ertasi kun uning roli HAMMAGA e'lon qilinadi!\n\n"
            "Qoidalar:\n"
            "• Bu ham juda kuchli, ham xavfli qurol\n"
            "• Mafia a'zosini fosh qilsangiz — shahar g'alaba sari yaqinlashadi\n"
            "• Shifokorni fosh qilsangiz — mafia shifokorni o'ldiradi!\n"
            "• Faqat 1 marta ishlatiladi"
        ),
        night_action  = True,
        action_prompt = "📰 Kimning rolini e'lon qilmoqchisiz?",
    ),

    RoleType.SPY: RoleConfig(
        role_type   = RoleType.SPY,
        team        = Team.CITY,
        emoji       = "🕵️",
        name_uz     = "Agent (Spy)",
        short_desc  = "Tunda mafia kimni nishonga olganini biladi",
        full_desc   = (
            "Siz <b>AGENT (SPY)</b>siz! 🕵️\n\n"
            "Maxfiy razvedka! Tunda siz mafia nishonlagan odamning <b>ismini</b> bilasiz.\n\n"
            "Lekin:\n"
            "• Kim nishon olganligini bilasiz, kim nishon olgani yo'q\n"
            "• Manyak nishonini bilmaysiz\n"
            "• Shifokor kimni saqlashini bilmaysiz\n\n"
            "Bu ma'lumot sizga kunduz kuni juda foydali bo'ladi!"
        ),
        night_action = False,  # Passiv: avtomatik ma'lumot oladi
    ),

    RoleType.DAYDI: RoleConfig(
        role_type   = RoleType.DAYDI,
        team        = Team.CITY,
        emoji       = "🧥",
        name_uz     = "Daydi",
        short_desc  = "Tunda kimnidir kuzatadi, hujum bo'lsa xabar oladi",
        full_desc   = (
            "Siz <b>DAYDI</b>siz! 🧥\n\n"
            "Har tunda bir o'yinchini kuzatasiz. Agar o'sha o'yinchi bu tun hujumga uchrasa, "
            "tongda sizga maxfiy xabar keladi.\n\n"
            "• Kimga hujum bo'lganini bilasiz\n"
            "• Hujum turi haqida ishora olasiz\n"
            "• Bu ma'lumotni kunduz muhokamada foydali ishlating"
        ),
        night_action  = True,
        action_prompt = "🧥 Bu tun kimni kuzatmoqchisiz?",
    ),

    RoleType.OMADLI: RoleConfig(
        role_type   = RoleType.OMADLI,
        team        = Team.CITY,
        emoji       = "🍀",
        name_uz     = "Omadli",
        short_desc  = "Birinchi marta o'ldirilishdan omon qoladi",
        full_desc   = (
            "Siz <b>OMADLI</b>siz! 🍀\n\n"
            "Sizda bir martalik omad qalqoni bor: birinchi marta o'ldirilayotganingizda "
            "tirik qolishingiz mumkin.\n\n"
            "• Qalqon faqat 1 marta ishlaydi\n"
            "• Keyingi hujumlarda oddiy o'yinchi kabi o'lasiz\n"
            "• Omon qolganingizni guruh ko'radi"
        ),
        night_action = False,
    ),

    # ════════════════════════════════════════
    #  NEYTRAL GURUH
    # ════════════════════════════════════════

    RoleType.MANIAC: RoleConfig(
        role_type   = RoleType.MANIAC,
        team        = Team.NEUTRAL,
        emoji       = "🔪",
        name_uz     = "Manyak",
        short_desc  = "Yolg'iz o'ldiradi, yolg'iz g'alaba qiladi",
        full_desc   = (
            "Siz <b>MANYAK</b>siz! 🔪\n\n"
            "Siz na mafia, na shahar tomonisiz. Yolg'iz ishlaysiz.\n\n"
            "Har tunda bir kishini o'ldirasiz.\n\n"
            "G'alaba: Siz YOLG'IZ tirik qolsangiz — hamma o'lgan bo'lsa — siz g'olib!\n\n"
            "⚠️ <i>Hammadan ehtiyot bo'ling. Hech kimga ishonmang.</i>"
        ),
        night_action  = True,
        action_prompt = "🔪 Bu tun kimni yo'q qilasiz?",
    ),

    RoleType.SUICIDE: RoleConfig(
        role_type   = RoleType.SUICIDE,
        team        = Team.NEUTRAL,
        emoji       = "💣",
        name_uz     = "Suitsid (Jallod)",
        short_desc  = "Ovoz bilan o'ldirilsa kimnidir olib ketadi",
        full_desc   = (
            "Siz <b>SUITSID (JALLOD)</b>siz! 💣\n\n"
            "Maxsus g'alaba sharti: Siz kunduz ovoz bilan o'yindan chiqarilsangiz — "
            "random bir o'yinchini o'zingiz bilan olib ketasiz!\n\n"
            "Maqsad: Ovoz bilan o'ldiriling!\n\n"
            "Strategiya:\n"
            "• Shubhali ko'rining\n"
            "• Muhokamada qarama-qarshi fikr bildiring\n"
            "• Odamlarni asablantiring — ular sizga ovoz bersin!\n\n"
            "Tunda hech nima qilmaysiz."
        ),
        night_action = False,
    ),

    RoleType.ESCORT: RoleConfig(
        role_type   = RoleType.ESCORT,
        team        = Team.NEUTRAL,
        emoji       = "💃",
        name_uz     = "Faoliyatchi (Escort)",
        short_desc  = "Kimningdir tun harakatini bloklaydi",
        full_desc   = (
            "Siz <b>FAOLIYATCHI (ESCORT)</b>siz! 💃\n\n"
            "Tunda bir kishini «band qilasiz» — u o'z qobiliyatini ishlatamaydi!\n\n"
            "Bloklanganlar:\n"
            "• Shifokor kimni saqlay olmaydi\n"
            "• Detektiv tekshira olmaydi\n"
            "• Qo'riqchi himoya qila olmaydi\n"
            "• Mafia a'zosi o'ldira olmaydi!\n\n"
            "G'alaba: Agar oxirgi ikki o'yinchi siz va mafia bo'lsangiz — mafia g'olib bo'ladi."
        ),
        night_action  = True,
        action_prompt = "💃 Kimni «band qilmoqchisiz»? (Uning tun harakati bloklanadi)",
    ),

    RoleType.WITCH: RoleConfig(
        role_type   = RoleType.WITCH,
        team        = Team.NEUTRAL,
        emoji       = "🧙",
        name_uz     = "Jodugar (Witch)",
        short_desc  = "Zahar (1x o'ldirish) + Davo (1x tiklash)",
        full_desc   = (
            "Siz <b>JODUGAR (WITCH)</b>siz! 🧙\n\n"
            "Ikki sehrli ichimligingiz bor, har biri <b>faqat 1 marta</b>:\n\n"
            "☠️ <b>Zahar ichimliği</b> — Tunda kimnidir o'ldirish\n"
            "💉 <b>Davo ichimliği</b> — O'lgan o'yinchini tiklash\n\n"
            "G'alaba: Oxirgi 3 o'yinchi ichida bo'lsangiz — siz g'olib!\n\n"
            "Strategiya: Eng to'g'ri vaqtda eng to'g'ri odamni tanlang."
        ),
        night_action  = True,
        action_prompt = "🧙 Qaysi sehrni ishlatmoqchisiz?",
    ),

    RoleType.KAMIKAZE: RoleConfig(
        role_type   = RoleType.KAMIKAZE,
        team        = Team.NEUTRAL,
        emoji       = "💣",
        name_uz     = "Kamikaze",
        short_desc  = "Ovoz bilan chiqarilsa portlab bitta o'yinchini olib ketadi",
        full_desc   = (
            "Siz <b>KAMIKAZE</b>siz! 💣\n\n"
            "Agar kunduz ovoz berishda o'yindan chiqarilsangiz, portlab o'zingiz bilan "
            "yana bitta tirik o'yinchini olib ketasiz.\n\n"
            "Maxsus g'alaba: portlashda mafia a'zosi o'lsa, siz darhol g'olib bo'lasiz."
        ),
        night_action = False,
    ),
}


def get_role(rt: RoleType) -> RoleConfig:
    return ROLES[rt]

def is_mafia(rt: RoleType) -> bool:
    return ROLES[rt].team == Team.MAFIA

def is_city(rt: RoleType) -> bool:
    return ROLES[rt].team == Team.CITY

def is_neutral(rt: RoleType) -> bool:
    return ROLES[rt].team == Team.NEUTRAL

# Mafia rollari to'plami (tez tekshirish uchun)
MAFIA_ROLES = {RoleType.MAFIA, RoleType.DON, RoleType.GODFATHER, RoleType.LAWYER}
CITY_ROLES  = {RoleType.CIVILIAN, RoleType.DOCTOR, RoleType.DETECTIVE,
               RoleType.BODYGUARD, RoleType.SNIPER, RoleType.MAYOR,
               RoleType.VIGILANTE, RoleType.JOURNALIST, RoleType.SPY,
               RoleType.DAYDI, RoleType.OMADLI}
NEUTRAL_ROLES = {RoleType.MANIAC, RoleType.SUICIDE, RoleType.ESCORT,
                 RoleType.WITCH, RoleType.KAMIKAZE}
