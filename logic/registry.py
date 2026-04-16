"""
O'yinlar registri — 100+ parallel o'yin uchun xotira boshqaruvi.
Redis mavjud bo'lsa — Redis, bo'lmasa — lokal dict ishlatadi.
"""
from __future__ import annotations
import logging
from logic.manager import GameManager

log = logging.getLogger(__name__)

# ── IN-MEMORY REGISTRY (asosiy) ──────────────
_games: dict[int, GameManager] = {}


def get_game(chat_id: int) -> GameManager | None:
    return _games.get(chat_id)


def create_game(chat_id: int) -> GameManager:
    game = GameManager(chat_id)
    _games[chat_id] = game
    log.info(f"[Registry] Yangi o'yin: {chat_id} | Jami: {len(_games)}")
    return game


def delete_game(chat_id: int):
    g = _games.pop(chat_id, None)
    if g:
        log.info(f"[Registry] O'yin tugadi: {chat_id} | Qolgan: {len(_games)}")


def exists(chat_id: int) -> bool:
    return chat_id in _games


def all_games() -> dict[int, GameManager]:
    return _games


def active_count() -> int:
    return len(_games)


def server_stats() -> dict:
    """Server holati — monitoring uchun."""
    return {
        "active_games":   len(_games),
        "phases":         {g.phase.value: 0 for g in _games.values()},
        "total_players":  sum(len(g.players) for g in _games.values()),
    }
