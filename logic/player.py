from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from logic.roles import RoleType, get_role, MAFIA_ROLES


@dataclass
class Player:
    user_id:   int
    username:  str
    full_name: str
    role:      Optional[RoleType] = None

    # ── HOLAT ─────────────────────────────────
    is_alive:        bool = True
    is_muted:        bool = False
    role_revealed:   bool = False    # Jurnalist oshkor qildimi

    # ── HIMOYA ────────────────────────────────
    protected_by_doctor:    bool = False
    protected_by_bodyguard: Optional[int] = None   # bodyguard user_id
    blocked_by_escort:      bool = False            # Tun harakati bloklandimi
    lawyer_protected:       bool = False            # Advokat himoyasidami

    # ── TUN HARAKATLARI ───────────────────────
    night_target:       Optional[int] = None
    night_action_done:  bool = False
    vigilante_guilt:    bool = False  # Qonunchi begunoh o'ldirsa — keyingi tun o'ladi
    vigilante_used:     bool = False  # Qonunchi qobiliyatini ishlatdimi
    detective_shot_used: bool = False  # Komissar o'q otish huquqidan foydalandimi

    # ── MAXSUS HOLATLAR ───────────────────────
    sniper_shots:      int = 1
    doctor_self_heals: int = 1     # Shifokor o'zini necha marta saqlashi mumkin
    last_healed:       Optional[int] = None   # Shifokor oldingi tun kimi saqladi
    journalist_used:   bool = False
    witch_poison_used: bool = False
    witch_heal_used:   bool = False
    mayor_revealed:    bool = False   # Mer o'z rolini oshkor qildimi
    omadli_luck_used:  bool = False   # Omadli bir martalik omadni ishlatdimi
    kamikaze_triggered: bool = False  # Kamikaze portlashni ishga tushirdimi
    last_words_used:   bool = False   # O'yinchi oxirgi so'zini ishlatdimi

    # ── STATISTIKA ────────────────────────────
    kills:             int = 0
    was_voted_out:     bool = False
    days_survived:     int = 0

    @property
    def cfg(self):
        return get_role(self.role) if self.role else None

    @property
    def emoji(self) -> str:
        return self.cfg.emoji if self.cfg else "❓"

    @property
    def display(self) -> str:
        return f"@{self.username}" if self.username else self.full_name

    @property
    def mention(self) -> str:
        return f'<a href="tg://user?id={self.user_id}">{self.full_name}</a>'

    @property
    def vote_weight(self) -> int:
        """Ovoz og'irligi."""
        from logic.roles import RoleType
        if self.role == RoleType.MAYOR:
            return 3 if self.mayor_revealed else 2
        return 1

    @property
    def is_mafia_member(self) -> bool:
        return self.role in MAFIA_ROLES if self.role else False

    @property
    def appears_innocent_to_detective(self) -> bool:
        """Detektivga begunoh ko'rinadimi?"""
        from logic.roles import RoleType
        return (
            self.role in (RoleType.DON, RoleType.GODFATHER)
            or self.lawyer_protected
        )

    def reset_night(self):
        """Har tun boshlanishida reset."""
        self.night_target              = None
        self.night_action_done         = False
        self.protected_by_doctor       = False
        self.protected_by_bodyguard    = None
        self.blocked_by_escort         = False
        self.lawyer_protected          = False

    def __repr__(self) -> str:
        st = "🟢" if self.is_alive else "💀"
        return f"{st} {self.full_name}[{self.role}]"
