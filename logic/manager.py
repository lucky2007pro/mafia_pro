"""
GameManager — O'yinning to'liq mantiqi va holat boshqaruvi.
100+ parallel o'yin uchun mo'ljallangan.
"""
from __future__ import annotations
import asyncio
import random
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from logic.player import Player
from logic.roles import (
    RoleType, Team,
    MAFIA_ROLES, CITY_ROLES, NEUTRAL_ROLES
)
from config import settings

log = logging.getLogger(__name__)


class GamePhase(str, Enum):
    WAITING    = "waiting"
    STARTING   = "starting"
    NIGHT      = "night"
    DAWN       = "dawn"
    DAY        = "day"
    VOTING     = "voting"
    LAST_WORDS = "last_words"
    EXECUTION  = "execution"
    FINISHED   = "finished"


@dataclass
class NightResult:
    """Bir tun natijasi."""
    killed:            list[int]  = field(default_factory=list)
    saved_by_doctor:   Optional[int] = None
    saved_by_bodyguard:Optional[int] = None
    bodyguard_died:    Optional[int] = None
    detective_result:  Optional[dict] = None  # {target_id, is_mafia, role, protected}
    spy_info:          Optional[int] = None   # Mafia nishoni (spy uchun)
    journalist_reveal: Optional[dict] = None  # {target_id, role}
    witch_poison:      Optional[int] = None
    witch_heal:        Optional[int] = None
    events:            list[str]  = field(default_factory=list)
    blocked:           list[int]  = field(default_factory=list)  # Escort blokladi
    daydi_reports:     list[tuple[int, str]] = field(default_factory=list)  # (daydi_id, matn)


@dataclass
class NightActions:
    """Bir tundagi harakatlar."""
    mafia_target:      Optional[int] = None
    doctor_target:     Optional[int] = None
    detective_target:  Optional[int] = None
    detective_shot_target: Optional[int] = None
    bodyguard_target:  Optional[int] = None
    maniac_target:     Optional[int] = None
    vigilante_target:  Optional[int] = None
    journalist_target: Optional[int] = None
    escort_target:     Optional[int] = None
    witch_poison:      Optional[int] = None
    witch_heal:        Optional[int] = None
    lawyer_target:     Optional[int] = None
    daydi_watch:       dict[int, int] = field(default_factory=dict)  # daydi_id -> target_id
    acted:             set[int] = field(default_factory=set)

    def reset(self):
        self.__init__()


@dataclass
class VoteSession:
    votes:      dict[int, tuple[int, int]] = field(default_factory=dict)  # voter→(target, weight)
    skips:      set[int]       = field(default_factory=set)

    def cast(self, voter: int, target: int, weight: int = 1) -> bool:
        if voter in self.votes or voter in self.skips:
            return False
        self.votes[voter] = (target, weight)
        return True

    def skip(self, voter: int) -> bool:
        if voter in self.votes or voter in self.skips:
            return False
        self.skips.add(voter)
        return True

    def tally(self) -> dict[int, int]:
        """target_id → ağırlıklı oy sayısı"""
        result: dict[int, int] = {}
        for target, weight in self.votes.values():
            result[target] = result.get(target, 0) + weight
        return result

    def leader(self) -> Optional[int]:
        t = self.tally()
        if not t:
            return None
        mx = max(t.values())
        leaders = [k for k, v in t.items() if v == mx]
        return leaders[0] if len(leaders) == 1 else None

    def total(self) -> int:
        return len(self.votes) + len(self.skips)


# ══════════════════════════════════════════════
#  GAME MANAGER
# ══════════════════════════════════════════════
class GameManager:
    def __init__(self, chat_id: int):
        self.chat_id     = chat_id
        self.players:    dict[int, Player] = {}
        self.phase       = GamePhase.WAITING
        self.day_num     = 0
        self.na          = NightActions()
        self.vote:       Optional[VoteSession] = None
        self.msg_ids:    dict[str, int] = {}
        self.log:        list[str] = []
        self._task:      Optional[asyncio.Task] = None
        self.last_words_queue: list[int] = []  # O'lgan o'yinchilar navbati
        self.last_words_deadlines: dict[int, float] = {}
        self.kamikaze_winner_id: Optional[int] = None
        self.private_voting: bool = settings.PRIVATE_VOTING

    # ── O'YINCHILAR ──────────────────────────
    def add(self, uid: int, uname: str, name: str) -> bool:
        if uid in self.players or len(self.players) >= settings.MAX_PLAYERS:
            return False
        self.players[uid] = Player(uid, uname, name)
        return True

    def remove(self, uid: int) -> bool:
        return bool(self.players.pop(uid, None))

    def get(self, uid: int) -> Optional[Player]:
        return self.players.get(uid)

    def alive(self) -> list[Player]:
        return [p for p in self.players.values() if p.is_alive]

    def dead(self) -> list[Player]:
        return [p for p in self.players.values() if not p.is_alive]

    def alive_mafia(self) -> list[Player]:
        return [p for p in self.alive() if p.role in MAFIA_ROLES]

    def alive_city(self) -> list[Player]:
        return [p for p in self.alive() if p.role in CITY_ROLES]

    def alive_neutral(self) -> list[Player]:
        return [p for p in self.alive() if p.role in NEUTRAL_ROLES]

    def _build_balanced_role_list(self, n: int) -> list[RoleType]:
        """O'yinchilar soniga qarab muqobil va balansli rol tarkibi."""
        if n <= 6:
            # Kichik guruhlar uchun majburiy himoya rollari
            killer = random.choice([RoleType.MAFIA, RoleType.DON])
            # 4-6 kishi uchun har doim Shifokor yoki Omadli rolini beramiz
            protector = random.choice([RoleType.DOCTOR, RoleType.OMADLI])
            roles = [killer, protector]
            if n >= 5:
                roles.append(RoleType.DETECTIVE)
            roles.extend([RoleType.CIVILIAN] * max(0, n - len(roles)))
            return roles

        if n <= 8:
            # Talab bo'yicha: 1 mafia tomoni, 1 shifokor, 1 komissar, qolgani fuqaro
            killer = random.choice([RoleType.MAFIA, RoleType.DON])
            roles = [killer, RoleType.DOCTOR, RoleType.DETECTIVE]
            roles.extend([RoleType.CIVILIAN] * max(0, n - len(roles)))
            return roles

        # 9+ da asosiy yadro
        roles: list[RoleType] = [
            RoleType.DON,
            RoleType.MAFIA,
            RoleType.DOCTOR,
            RoleType.DETECTIVE,
        ]

        # Bosqichma-bosqich kengayish (9-15 uchun ham, undan yuqoriga ham asos bo'ladi)
        progressive: list[tuple[int, RoleType]] = [
            (10, RoleType.BODYGUARD),
            (11, RoleType.MAYOR),
            (12, RoleType.LAWYER),
            (13, RoleType.SNIPER),
            (14, RoleType.SPY),
            (15, RoleType.JOURNALIST),
            (15, RoleType.MANIAC),
        ]
        for min_players, role in progressive:
            if n >= min_players:
                roles.append(role)

        if n <= 15:
            roles.extend([RoleType.CIVILIAN] * max(0, n - len(roles)))
            return roles[:n]

        max_mafia = max(2, n // 4)          # taxm. 25% atrofida
        max_neutral = 1 + max(0, (n - 12) // 6)

        extra_cycle: list[RoleType] = [
            RoleType.CIVILIAN,
            RoleType.DAYDI,
            RoleType.OMADLI,
            RoleType.VIGILANTE,
            RoleType.ESCORT,
            RoleType.WITCH,
            RoleType.GODFATHER,
            RoleType.SUICIDE,
            RoleType.KAMIKAZE,
            RoleType.BODYGUARD,
            RoleType.SNIPER,
            RoleType.SPY,
            RoleType.JOURNALIST,
            RoleType.DOCTOR,
            RoleType.DETECTIVE,
            RoleType.CIVILIAN,
        ]

        idx = 0
        safety = 0
        while len(roles) < n:
            cand = extra_cycle[idx % len(extra_cycle)]
            idx += 1
            safety += 1

            mafia_cnt = sum(1 for r in roles if r in MAFIA_ROLES)
            neutral_cnt = sum(1 for r in roles if r in NEUTRAL_ROLES)

            if cand in MAFIA_ROLES and mafia_cnt >= max_mafia:
                if safety > len(extra_cycle) * 3:
                    roles.append(RoleType.CIVILIAN)
                continue
            if cand in NEUTRAL_ROLES and neutral_cnt >= max_neutral:
                if safety > len(extra_cycle) * 3:
                    roles.append(RoleType.CIVILIAN)
                continue

            roles.append(cand)

        return roles[:n]

    # ── ROL TAQSIMLASH ────────────────────────
    def assign_roles(self) -> dict[int, RoleType]:
        n = len(self.players)
        if n < settings.MIN_PLAYERS:
            raise ValueError(f"Kamida {settings.MIN_PLAYERS} kishi kerak!")

        role_list = self._build_balanced_role_list(n)
        random.shuffle(role_list)

        players = list(self.players.values())
        random.shuffle(players)

        result = {}
        for p, r in zip(players, role_list):
            p.role = r
            result[p.user_id] = r

        log.info(f"[{self.chat_id}] Rollar: {result}")
        return result

    # ── TUN: HARAKAT QABUL QILISH ─────────────
    def set_night_target(self, uid: int, target_id: int) -> tuple[bool, str]:
        p = self.get(uid)
        t = self.get(target_id)
        if not p or not p.is_alive: return False, "Siz o'yinda emassiz!"
        if not t or not t.is_alive: return False, "Nishon topilmadi!"
        if p.blocked_by_escort:     return False, "⛔ Siz bu tun bloklandingiz!"

        role = p.role
        na = self.na

        if role in (RoleType.MAFIA, RoleType.DON, RoleType.GODFATHER):
            if self.day_num == 0:
                return False, "Birinchi tun — tinchlik tuni! Mafiya bu tun hech kimni o'ldirolmaydi."
            na.mafia_target = target_id
        elif role == RoleType.DOCTOR:
            if uid == target_id:
                if p.doctor_self_heals <= 0:
                    return False, "O'zingizni yana davolay olmaysiz!"
                p.doctor_self_heals -= 1
            elif target_id == p.last_healed:
                return False, "Ketma-ket bir xil kishini davolab bo'lmaydi!"
            p.last_healed = target_id
            na.doctor_target = target_id
        elif role == RoleType.DETECTIVE:
            na.detective_target = target_id
        elif role == RoleType.BODYGUARD:
            if uid == target_id: return False, "O'zingizni himoya qila olmaysiz!"
            na.bodyguard_target = target_id
        elif role == RoleType.MANIAC:
            na.maniac_target = target_id
        elif role == RoleType.VIGILANTE:
            if p.vigilante_used: return False, "Bu qobiliyat allaqachon ishlatilgan!"
            p.vigilante_used = True
            na.vigilante_target = target_id
        elif role == RoleType.JOURNALIST:
            if p.journalist_used: return False, "Jurnalist faqat 1 marta foydalanishi mumkin!"
            p.journalist_used = True
            na.journalist_target = target_id
        elif role == RoleType.ESCORT:
            if uid == target_id: return False, "O'zingizni bloklay olmaysiz!"
            na.escort_target = target_id
        elif role == RoleType.DAYDI:
            na.daydi_watch[uid] = target_id
        else:
            return False, "Sizning rolingizda tunda harakat yo'q!"

        na.acted.add(uid)
        p.night_target = target_id
        p.night_action_done = True
        return True, f"✅ {t.full_name} tanlandi."

    def set_detective_check(self, uid: int, target_id: int) -> tuple[bool, str]:
        p = self.get(uid)
        t = self.get(target_id)
        if not p or p.role != RoleType.DETECTIVE:
            return False, "Faqat Komissar!"
        if not t or not t.is_alive:
            return False, "Nishon topilmadi!"
        self.na.detective_target = target_id
        self.na.acted.add(uid)
        p.night_target = target_id
        p.night_action_done = True
        return True, f"✅ {t.full_name} tekshiruvga olindi."

    def set_detective_shot(self, uid: int, target_id: int) -> tuple[bool, str]:
        p = self.get(uid)
        t = self.get(target_id)
        if not p or p.role != RoleType.DETECTIVE:
            return False, "Faqat Komissar!"
        if p.detective_shot_used:
            return False, "O'q otish huquqi allaqachon ishlatilgan!"
        if not t or not t.is_alive:
            return False, "Nishon topilmadi!"
        p.detective_shot_used = True
        self.na.detective_shot_target = target_id
        self.na.acted.add(uid)
        p.night_target = target_id
        p.night_action_done = True
        return True, f"✅ {t.full_name} ga o'q tayyorlandi."

    def set_lawyer_target(self, uid: int, target_id: int) -> tuple[bool, str]:
        p = self.get(uid)
        t = self.get(target_id)
        if not p or p.role != RoleType.LAWYER: return False, "Faqat Advokat!"
        if not t: return False, "Topilmadi!"
        if t.role not in MAFIA_ROLES: return False, "Faqat mafia a'zosini himoya qilish mumkin!"
        if uid == target_id: return False, "O'zingizni himoya qila olmaysiz!"
        self.na.lawyer_target = target_id
        self.na.acted.add(uid)
        p.night_action_done = True
        return True, f"✅ {t.full_name} himoya qilindi."

    def set_don_check(self, uid: int, target_id: int) -> tuple[bool, str]:
        p = self.get(uid)
        t = self.get(target_id)
        if not p or p.role != RoleType.DON: return False, "Faqat Don!"
        if not t: return False, "Topilmadi!"
        is_det = (t.role == RoleType.DETECTIVE)
        result = "✅ HA — bu DETEKTIV!" if is_det else "❌ YO'Q — detektiv emas."
        self.na.acted.add(uid)
        p.night_action_done = True
        return True, result

    def set_witch_action(self, uid: int, action: str, target_id: int) -> tuple[bool, str]:
        p = self.get(uid)
        t = self.get(target_id)
        if not p or p.role != RoleType.WITCH: return False, "Faqat Jodugar!"
        if action == "poison":
            if p.witch_poison_used: return False, "Zahar ichimliği tugagan!"
            if not t or not t.is_alive: return False, "Nishon topilmadi!"
            p.witch_poison_used = True
            self.na.witch_poison = target_id
        elif action == "heal":
            if p.witch_heal_used: return False, "Davo ichimliği tugagan!"
            dead = [pl for pl in self.players.values() if not pl.is_alive]
            if not dead: return False, "Tiklash uchun o'lik o'yinchi yo'q!"
            p.witch_heal_used = True
            self.na.witch_heal = target_id
        self.na.acted.add(uid)
        p.night_action_done = True
        return True, "✅ Bajarildi."

    def all_night_done(self) -> bool:
        """Barcha aktiv rollar harakatini bajardimi?"""
        na = self.na
        for p in self.alive():
            if not p.cfg or not p.cfg.night_action:
                continue
            if p.role in (RoleType.MAFIA, RoleType.DON,
                          RoleType.GODFATHER, RoleType.LAWYER):
                # Mafia guruh sifatida — biri yetarli
                if na.mafia_target is not None:
                    continue
            if p.user_id not in na.acted:
                return False
        return True

    # ── TUN: HISOBLASH ───────────────────────
    def _try_kill(self, target: Optional[Player], res: NightResult, reason: str) -> bool:
        """O'yinchini o'ldirishga urinish; Omadli bir marta omon qoladi."""
        if not target or not target.is_alive:
            return False
        if target.role == RoleType.OMADLI and not target.omadli_luck_used:
            target.omadli_luck_used = True
            res.events.append(f"🍀 {target.mention} omad bilan o'limdan qutuldi! ({reason})")
            return False
        if not target.shield_used:
            from database.db import get_wallet
            import asyncio
            async def check_shield():
                w = await get_wallet(target.user_id)
                return w.shields > 0
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                has_shield = loop.run_until_complete(check_shield())
            finally:
                loop.close()
            if has_shield:
                target.shield_used = True
                async def use_shield():
                    from database.db import buy_shield
                    await buy_shield(target.user_id)
                asyncio.create_task(use_shield())
                res.events.append(f"🛡️ {target.mention} bir martalik himoyasi bilan omon qoldi! ({reason})")
                return False
        target.is_alive = False
        return True

    def resolve_night(self) -> NightResult:
        na = self.na
        res = NightResult()

        # 1. ESCORT bloklash
        if na.escort_target:
            target = self.get(na.escort_target)
            if target:
                target.blocked_by_escort = True
                res.blocked.append(na.escort_target)
                # Agar escort mafia a'zosini bloklaganda — mafia o'ldira olmaydi
                if target.role in MAFIA_ROLES:
                    na.mafia_target = None

        # 2. ADVOKAT himoyasi
        if na.lawyer_target:
            lt = self.get(na.lawyer_target)
            if lt:
                lt.lawyer_protected = True

        # 3. QONUNCHI vijdon azobi
        for p in self.alive():
            if p.vigilante_guilt and p.role == RoleType.VIGILANTE:
                if self._try_kill(p, res, "vijdon azobi"):
                    res.events.append(
                        f"🗡️ {p.mention} vijdon azobi bilan halok bo'ldi..."
                    )

        # 4. QONUNCHI nishoni
        if na.vigilante_target:
            vt = self.get(na.vigilante_target)
            shooter = next(
                (p for p in self.alive() if p.role == RoleType.VIGILANTE), None
            )
            if vt and vt.is_alive and shooter:
                if vt.role in MAFIA_ROLES or vt.role == RoleType.MANIAC:
                    if self._try_kill(vt, res, "qonunchi hujumi"):
                        shooter.kills += 1
                        res.events.append(f"🗡️ Qonunchi adolatni o'z qo'lga oldi!")
                else:
                    # Begunoh — keyingi tun qonunchi o'ladi
                    if self._try_kill(vt, res, "qonunchi xatosi"):
                        shooter.vigilante_guilt = True
                        res.events.append(
                            f"🗡️ Qonunchi noto'g'ri nishon oldi! "
                            f"{vt.mention} halok bo'ldi... qonunchi esa aybdorlik his qilmoqda."
                        )

        # 4.5. KOMISSAR O'QI
        if na.detective_shot_target:
            dt = self.get(na.detective_shot_target)
            shooter = next((p for p in self.alive() if p.role == RoleType.DETECTIVE), None)
            if dt and dt.is_alive and shooter:
                if dt.role in MAFIA_ROLES or dt.role == RoleType.MANIAC:
                    if self._try_kill(dt, res, "komissar o'qi"):
                        shooter.kills += 1
                        res.killed.append(na.detective_shot_target)
                        res.events.append(f"🔍 {shooter.mention} o'q uzdi va {dt.mention} yiqildi!")
                else:
                    if self._try_kill(shooter, res, "komissar xatosi"):
                        res.killed.append(shooter.user_id)
                        res.events.append(
                            f"🔍 {shooter.mention} begunoh odamga o'q uzdi va o'zi halok bo'ldi..."
                        )

        # 5. MAFIA O'LDIRISHI
        mafia_target = na.mafia_target
        if mafia_target:
            mt = self.get(mafia_target)
            if mt and mt.is_alive:
                res.spy_info = mafia_target  # Spy uchun
                if na.doctor_target == mafia_target:
                    res.saved_by_doctor = mafia_target
                elif mt.protected_by_bodyguard is not None:
                    bg_id = mt.protected_by_bodyguard
                    bg = self.get(bg_id)
                    if bg and bg.is_alive:
                        if self._try_kill(bg, res, "qo'riqchi qurboni"):
                            res.bodyguard_died = bg_id
                            res.saved_by_bodyguard = mafia_target
                            res.events.append(
                                f"🛡️ {bg.mention} {mt.mention}ni himoya qilib, o'zi qurbon bo'ldi!"
                            )
                else:
                    if self._try_kill(mt, res, "mafia hujumi"):
                        res.killed.append(mafia_target)

        # 6. MANYAK O'LDIRISHI
        if na.maniac_target and na.maniac_target != mafia_target:
            mn_t = self.get(na.maniac_target)
            if mn_t and mn_t.is_alive:
                if na.doctor_target == na.maniac_target:
                    res.events.append("💊 Shifokor manyak qurbonini ham saqlab qoldi!")
                elif mn_t.protected_by_bodyguard:
                    bg_id = mn_t.protected_by_bodyguard
                    bg = self.get(bg_id)
                    if bg and bg.is_alive:
                        if self._try_kill(bg, res, "manyakdan himoya"):
                            res.events.append(f"🛡️ {bg.mention} manyakdan himoya qilib halok bo'ldi!")
                else:
                    if self._try_kill(mn_t, res, "manyak hujumi"):
                        res.killed.append(na.maniac_target)
                        res.events.append(f"🔪 Manyak yana bir qurbon oldi...")

        # 7. JODUGAR ZAHRI
        if na.witch_poison:
            wt = self.get(na.witch_poison)
            if wt and wt.is_alive:
                if self._try_kill(wt, res, "jodugar zahri"):
                    res.witch_poison = na.witch_poison
                    res.killed.append(na.witch_poison)

        # 8.5 DAYDI hisobotlari
        attacked: list[tuple[int, str]] = []
        if na.mafia_target:
            attacked.append((na.mafia_target, "Mafia hujumi"))
        if na.maniac_target and na.maniac_target != na.mafia_target:
            attacked.append((na.maniac_target, "Manyak hujumi"))
        if na.witch_poison:
            attacked.append((na.witch_poison, "Jodugar zahri"))

        for daydi_id, watched_id in na.daydi_watch.items():
            watched = self.get(watched_id)
            for target_id, source in attacked:
                if watched_id == target_id and watched:
                    state = "halok bo'ldi" if not watched.is_alive else "tirik qoldi"
                    res.daydi_reports.append(
                        (
                            daydi_id,
                            f"🧥 <b>DAYDI HISOBOTI</b>\n\n"
                            f"Siz kuzatgan o'yinchi: {watched.mention}\n"
                            f"Hodisa: {source}\n"
                            f"Natija: <b>{state}</b>",
                        )
                    )
                    break

        # 8. JODUGAR DAVOSI
        if na.witch_heal:
            wh = self.get(na.witch_heal)
            if wh and not wh.is_alive:
                wh.is_alive = True
                res.witch_heal = na.witch_heal
                res.events.append(f"🧙 Jodugar kimnidir o'limdan tikladi!")

        # 9. DETEKTIV NATIJASI
        if na.detective_target:
            dt = self.get(na.detective_target)
            if dt:
                is_maf = dt.is_mafia_member and not dt.appears_innocent_to_detective
                res.detective_result = {
                    "target_id":  na.detective_target,
                    "name":       dt.full_name,
                    "is_mafia":   is_maf,
                    "role":       dt.role,
                }

        # 10. JURNALIST OSHKOR QILISHI
        if na.journalist_target:
            jt = self.get(na.journalist_target)
            if jt:
                jt.role_revealed = True
                res.journalist_reveal = {
                    "target_id": na.journalist_target,
                    "name":      jt.full_name,
                    "role":      jt.role,
                }

        # Reset
        self.na.reset()
        for p in self.alive():
            p.reset_night()

        self.day_num += 1
        return res

    # ── OVOZ BERISH ───────────────────────────
    def start_vote(self) -> VoteSession:
        self.vote = VoteSession()
        return self.vote

    def cast_vote(self, voter_id: int, target_id: int) -> tuple[bool, str]:
        if not self.vote:
            return False, "Sessiya yo'q!"
        voter = self.get(voter_id)
        if not voter or not voter.is_alive:
            return False, "Ovoz bera olmaysiz!"
        ok = self.vote.cast(voter_id, target_id, weight=voter.vote_weight)
        return ok, "✅ Ovoz qabul qilindi!" if ok else "Allaqachon ovoz bergansiz!"

    def cast_skip(self, voter_id: int) -> tuple[bool, str]:
        if not self.vote: return False, "Sessiya yo'q!"
        ok = self.vote.skip(voter_id)
        return ok, "✅ O'tkazib yuborish!" if ok else "Allaqachon ovoz bergansiz!"

    def resolve_vote(self) -> tuple[Optional[int], Optional[str]]:
        if not self.vote: return None, None
        leader_id = self.vote.leader()
        extra_event = None
        temp_res = NightResult()

        if leader_id:
            target = self.get(leader_id)
            if target and target.is_alive:
                if not self._try_kill(target, temp_res, "ovoz berish"):
                    extra_event = f"🍀 {target.mention} omad bilan ovozdan omon qoldi!"
                    leader_id = None
                else:
                    target.was_voted_out = True
                    self.queue_last_words(target.user_id, settings.LAST_WORDS_TIMEOUT)

                    # SUITSID va KAMIKAZE: birini olib ketadi
                    if target.role in (RoleType.SUICIDE, RoleType.KAMIKAZE):
                        victims = [p for p in self.alive() if p.user_id != target.user_id]
                        if victims:
                            v = random.choice(victims)
                            if self._try_kill(v, temp_res, "portlash"):
                                self.queue_last_words(v.user_id, settings.LAST_WORDS_TIMEOUT)
                                extra_event = (
                                    f"💣 {target.mention} portladi va "
                                    f"{v.mention}ni ham olib ketdi!"
                                )
                                if target.role == RoleType.KAMIKAZE:
                                    target.kamikaze_triggered = True
                                    if v.role in MAFIA_ROLES:
                                        self.kamikaze_winner_id = target.user_id
                            else:
                                extra_event = (
                                    f"💣 {target.mention} portladi, ammo {v.mention} omad bilan tirik qoldi!"
                                )

        self.vote = None
        return leader_id, extra_event

    def queue_last_words(self, uid: int, timeout: int | None = None) -> bool:
        p = self.get(uid)
        if not p or uid in self.last_words_deadlines:
            return False
        timeout = timeout or 0
        deadline = time.monotonic() + timeout if timeout > 0 else float("inf")
        self.last_words_queue.append(uid)
        self.last_words_deadlines[uid] = deadline
        return True

    def take_last_words(self, uid: int) -> bool:
        p = self.get(uid)
        deadline = self.last_words_deadlines.get(uid)
        if deadline is None:
            return False
        if deadline != float("inf") and time.monotonic() > deadline:
            self.last_words_deadlines.pop(uid, None)
            if uid in self.last_words_queue:
                self.last_words_queue.remove(uid)
            return False
        self.last_words_deadlines.pop(uid, None)
        if uid in self.last_words_queue:
            self.last_words_queue.remove(uid)
        if p:
            p.last_words_used = True
        return True

    # ── SNAYPER ───────────────────────────────
    def sniper_shoot(self, uid: int, target_id: int) -> tuple[bool, str]:
        s = self.get(uid)
        t = self.get(target_id)
        if not s or s.role != RoleType.SNIPER or not s.is_alive:
            return False, "Faqat tirik snayper otishi mumkin!"
        if s.sniper_shots <= 0:
            return False, "O'qingiz tugagan!"
        if not t or not t.is_alive:
            return False, "Nishon topilmadi!"
        s.sniper_shots -= 1
        if t.role in MAFIA_ROLES or t.role == RoleType.MANIAC:
            temp_res = NightResult()
            if self._try_kill(t, temp_res, "snayper o'qi"):
                s.kills += 1
                return True, f"🎯 {t.mention} — to'g'ri nishon!"
            return True, f"🎯 {t.mention} omad bilan o'qdan omon qoldi!"
        else:
            s.is_alive = False
            return True, (
                f"🎯 {t.mention} begunoh edi... "
                f"{s.mention} uyat ichida halok bo'ldi."
            )

    # ── MER OSHKOR QILISH ────────────────────
    def mayor_reveal(self, uid: int) -> tuple[bool, str]:
        p = self.get(uid)
        if not p or p.role != RoleType.MAYOR:
            return False, "Faqat Mer!"
        if p.mayor_revealed:
            return False, "Siz allaqachon o'z rolingizni oshkor qilgansiz!"
        p.mayor_revealed = True
        return True, f"🎩 {p.mention} o'zini MER ekanini oshkor qildi! Uning ovozi 3 ga ko'tarildi!"

    # ── G'ALABA TEKSHIRUVI ─────────────────────
    def check_win(self) -> Optional[tuple[Team, str]]:
        alive = self.alive()
        if not alive:
            return (Team.NEUTRAL,
                    "🤝 Hech kim g'olib bo'lmadi. Barcha halok bo'ldi!")

        # Kamikaze maxsus g'alabasi
        if self.kamikaze_winner_id:
            kz = self.get(self.kamikaze_winner_id)
            if kz:
                return (Team.NEUTRAL,
                        f"💣 {kz.mention} — KAMIKAZE g'olib! Portlash mafia a'zosini olib ketdi.")

        mafia_alive    = [p for p in alive if p.role in MAFIA_ROLES]
        city_alive     = [p for p in alive if p.role in CITY_ROLES]
        maniac_alive   = [p for p in alive if p.role == RoleType.MANIAC]
        neutral_alive  = [p for p in alive if p.role in NEUTRAL_ROLES]

        # Witch g'alabasi — oxirgi 3 da
        witch = next((p for p in alive if p.role == RoleType.WITCH), None)
        if witch and len(alive) <= 3:
            return (Team.NEUTRAL,
                    f"🧙 {witch.mention} — JODUGAR g'olib! U oxirigacha yashadi.")

        # Manyak yolg'iz qoldi
        if len(maniac_alive) == 1 and len(alive) == 1:
            return (Team.NEUTRAL,
                    f"🔪 {maniac_alive[0].mention} — MANYAK g'olib! U hammani yo'q qildi.")

        # Mafia shaharni egalladi
        non_mafia_threat = len(city_alive) + len(maniac_alive)
        
        # Kichik guruhlar (<=6) uchun oxirgi shaharlik o'lguncha davom etadi
        if len(self.players) <= 6:
            if not city_alive and not maniac_alive:
                return (Team.MAFIA, "🔫 MAFIA g'olib! Barcha qarshiliklar yo'q qilindi.")
        else:
            if mafia_alive and len(mafia_alive) >= non_mafia_threat:
                return (Team.MAFIA, "🔫 MAFIA g'olib! Ular shaharni nazorat ostiga oldi.")

        # Barcha mafia va tahdid yo'q
        if not mafia_alive and not maniac_alive:
            return (Team.CITY, "🏙️ SHAHAR g'olib! Barcha tahdid bartaraf etildi!")

        return None

    # ── YORDAM ───────────────────────────────
    def players_text(self, show_roles: bool = False) -> str:
        lines = []
        for i, p in enumerate(self.players.values(), 1):
            st = "🟢" if p.is_alive else "💀"
            r  = f" — {p.emoji} <b>{p.cfg.name_uz}</b>" if (show_roles and p.role) else ""
            lines.append(f"{i}. {st} {p.mention}{r}")
        return "\n".join(lines) or "—"

    def mafia_list_text(self) -> str:
        """Mafia a'zolari ro'yxati (faqat mafia uchun)."""
        return "\n".join(
            f"  {p.emoji} {p.mention} — {p.cfg.name_uz}"
            for p in self.players.values()
            if p.role in MAFIA_ROLES
        )

    def event(self, text: str):
        self.log.append(f"[Kun {self.day_num}] {text}")
