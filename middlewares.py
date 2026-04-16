import time, logging
from collections import defaultdict
from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, CallbackQuery, Message

log = logging.getLogger(__name__)


class AntiSpamMiddleware(BaseMiddleware):
    def __init__(self, cooldown: float = 0.8):
        self.cd = cooldown
        self._last: dict[int, float] = defaultdict(float)

    async def __call__(self, handler, event, data):
        if isinstance(event, CallbackQuery):
            uid = event.from_user.id
            now = time.monotonic()
            if now - self._last[uid] < self.cd:
                await event.answer("⏳ Biroz kuting!", show_alert=False)
                return
            self._last[uid] = now
        return await handler(event, data)


class ErrorMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        try:
            return await handler(event, data)
        except Exception as e:
            log.exception(f"Handler xatosi: {e!r}")
            if isinstance(event, CallbackQuery):
                try: await event.answer("⚠️ Xato yuz berdi.", show_alert=True)
                except Exception: pass
            elif isinstance(event, Message):
                try: await event.answer("⚠️ Xatolik.")
                except Exception: pass


class UserTracker(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        if user:
            try:
                from database.db import get_or_create_user
                await get_or_create_user(user.id, user.username or "", user.full_name)
            except Exception: pass
        return await handler(event, data)
