"""
Redis orqali o'yinlarni boshqarish (Scaling uchun).
Bu fayl registry.py ning o'rnini bosishi mumkin.
O'rnatish: pip install redis aioredis pickle5
"""
import pickle
import aioredis
from typing import Optional
from logic.manager import GameManager

REDIS_URL = "redis://localhost"

class RedisRegistry:
    def __init__(self):
        self.redis = aioredis.from_url(REDIS_URL)

    async def get_game(self, chat_id: int) -> Optional[GameManager]:
        data = await self.redis.get(f"game:{chat_id}")
        if data:
            return pickle.loads(data)
        return None

    async def save_game(self, game: GameManager):
        data = pickle.dumps(game)
        await self.redis.set(f"game:{game.chat_id}", data)

    async def delete_game(self, chat_id: int):
        await self.redis.delete(f"game:{chat_id}")

    async def find_game_by_player(self, user_id: int) -> Optional[GameManager]:
        # Bu Redis'da sekinroq ishlaydi (barcha o'yinlarni scan qilish kerak).
        # Shuning uchun player -> chat_id mappingini ham saqlash tavsiya etiladi.
        chat_id = await self.redis.get(f"player:{user_id}")
        if chat_id:
            return await self.get_game(int(chat_id))
        return None

    async def register_player(self, user_id: int, chat_id: int):
        await self.redis.set(f"player:{user_id}", chat_id)

    async def unregister_player(self, user_id: int):
        await self.redis.delete(f"player:{user_id}")
