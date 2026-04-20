from __future__ import annotations
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ── BOT ──────────────────────────────────
    BOT_TOKEN: str = Field(..., description="BotFather token")
    BOT_USERNAME: str = Field(default="", description="Bot username for deep links")
    BOT_WEBHOOK_URL: str = Field(default="", description="Webhook URL (bo'sh = polling)")
    BOT_WEBHOOK_PORT: int = Field(default=8443)
    ADMIN_IDS: list[int] = Field(default=[], description="Super admin Telegram ID'lari")
    GEMINI_API_KEYS: list[str] = Field(default=[], description="Gemini AI kalitlari ro'yxati")

    # ── REDIS (100+ concurrent o'yin uchun) ──
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    REDIS_GAME_TTL: int = 7200          # O'yin ma'lumotlari 2 soat saqlanadi

    # ── DATABASE ──────────────────────────────
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///mafia.db")

    # ── O'YIN SOZLAMALARI ─────────────────────
    MIN_PLAYERS: int = 4
    MAX_PLAYERS: int = 100
    LOBBY_TIMEOUT: int = 120
    NIGHT_TIMEOUT: int = 45
    DAY_DISCUSSION_TIME: int = 90
    VOTE_TIMEOUT: int = 50
    LAST_WORDS_TIMEOUT: int = 15        # Vasiyat yozish vaqti
    VOTE_COOLDOWN: float = 0.8          # Anti-spam: tugmalar orasidagi min vaqt

    # ── SCALING ───────────────────────────────
    MAX_GAMES_PER_SERVER: int = 100     # Bir serverda parallel o'yinlar
    WORKER_TASKS_LIMIT: int = 500       # asyncio task limiti

    # ── ECONOMY ───────────────────────────────
    WIN_COINS_REWARD: int = 20          # G'alaba uchun beriladigan tanga
    FAKE_PASSPORT_PRICE: int = 120      # Do'kondagi soxta passport narxi
    BUY_COINS_RATE: int = 10            # /buycoins: 1 birlik uchun beriladigan tanga

    # ── ROL TAQSIMLASH ────────────────────────
    # Eslatma: asosiy taqsimlash endi dynamic (logic/manager.py).
    # ROLE_DIST legacy/fallback sifatida saqlanmoqda.
    # format: {player_count: {role: count, ...}}
    ROLE_DIST: dict = {
        4:  dict(mafia=1, don=0, doctor=1, detective=0, bodyguard=0,
                 sniper=0, maniac=0, suicide=0, godfather=0, lawyer=0,
                 escort=0, journalist=0, vigilante=0, mayor=0, witch=0, spy=0),
        5:  dict(mafia=1, don=0, doctor=1, detective=1, bodyguard=0,
                 sniper=0, maniac=0, suicide=0, godfather=0, lawyer=0,
                 escort=0, journalist=0, vigilante=0, mayor=0, witch=0, spy=0),
        6:  dict(mafia=1, don=1, doctor=1, detective=1, bodyguard=0,
                 sniper=0, maniac=0, suicide=0, godfather=0, lawyer=0,
                 escort=0, journalist=0, vigilante=0, mayor=0, witch=0, spy=0),
        7:  dict(mafia=1, don=1, doctor=1, detective=1, bodyguard=0,
                 sniper=0, maniac=1, suicide=0, godfather=0, lawyer=0,
                 escort=0, journalist=0, vigilante=0, mayor=0, witch=0, spy=0),
        8:  dict(mafia=2, don=1, doctor=1, detective=1, bodyguard=0,
                 sniper=0, maniac=1, suicide=0, godfather=0, lawyer=0,
                 escort=0, journalist=0, vigilante=0, mayor=0, witch=0, spy=0),
        9:  dict(mafia=2, don=1, doctor=1, detective=1, bodyguard=1,
                 sniper=0, maniac=1, suicide=0, godfather=0, lawyer=0,
                 escort=0, journalist=0, vigilante=0, mayor=0, witch=0, spy=0),
        10: dict(mafia=2, don=1, doctor=1, detective=1, bodyguard=1,
                 sniper=1, maniac=1, suicide=0, godfather=0, lawyer=0,
                 escort=0, journalist=0, vigilante=0, mayor=1, witch=0, spy=0),
        11: dict(mafia=2, don=1, doctor=1, detective=1, bodyguard=1,
                 sniper=1, maniac=1, suicide=0, godfather=1, lawyer=0,
                 escort=0, journalist=0, vigilante=0, mayor=1, witch=0, spy=0),
        12: dict(mafia=2, don=1, doctor=1, detective=1, bodyguard=1,
                 sniper=1, maniac=1, suicide=1, godfather=1, lawyer=0,
                 escort=1, journalist=0, vigilante=0, mayor=1, witch=0, spy=0,
                 daydi=1, omadli=1, kamikaze=0),
        13: dict(mafia=3, don=1, doctor=1, detective=1, bodyguard=1,
                 sniper=1, maniac=1, suicide=1, godfather=1, lawyer=1,
                 escort=1, journalist=0, vigilante=0, mayor=1, witch=0, spy=0,
                 daydi=1, omadli=1, kamikaze=0),
        14: dict(mafia=3, don=1, doctor=1, detective=1, bodyguard=1,
                 sniper=1, maniac=1, suicide=1, godfather=1, lawyer=1,
                 escort=1, journalist=1, vigilante=0, mayor=1, witch=0, spy=0,
                 daydi=1, omadli=1, kamikaze=1),
        15: dict(mafia=3, don=1, doctor=1, detective=1, bodyguard=1,
                 sniper=1, maniac=1, suicide=1, godfather=1, lawyer=1,
                 escort=1, journalist=1, vigilante=1, mayor=1, witch=0, spy=1,
                 daydi=1, omadli=1, kamikaze=1),
    }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
