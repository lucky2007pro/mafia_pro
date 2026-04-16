"""
🎭 MAFIA BOT v3.0 — Production-ready
16 rol | 100+ parallel o'yin | SQLite/PostgreSQL | Redis
"""
import asyncio, logging, sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllChatAdministrators,
)
from config import settings
from middlewares import AntiSpamMiddleware, ErrorMiddleware, UserTracker
from handlers import common, game, actions, admin, stats, special, economy
from database.db import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("mafia.log", encoding="utf-8"),
    ]
)
log = logging.getLogger(__name__)


async def setup_commands(bot: Bot) -> None:
    # Private chat command menu
    await bot.set_my_commands(
        commands=[
            BotCommand(command="start", description="botni ishga tushirish"),
            BotCommand(command="help", description="buyruqlar"),
            BotCommand(command="profile", description="profil va inventar"),
            BotCommand(command="coins", description="tanga balansi"),
            BotCommand(command="shop", description="do'kon"),
            BotCommand(command="buy", description="buyum xarid qilish"),
            BotCommand(command="buycoins", description="tanga sotib olish"),
            BotCommand(command="mystats", description="profil statistikasi"),
            BotCommand(command="top", description="top oyinchilar"),
            BotCommand(command="rules", description="oyin qoidalari"),
            BotCommand(command="snipe", description="snayper otishi"),
            BotCommand(command="reveal", description="merni oshkor qilish"),
        ],
        scope=BotCommandScopeAllPrivateChats(),
    )

    # Group chat command menu
    await bot.set_my_commands(
        commands=[
            BotCommand(command="newgame", description="yangi oyin ochish"),
            BotCommand(command="startgame", description="oyinni boshlash"),
            BotCommand(command="players", description="oyinchilar royxati"),
            BotCommand(command="stats", description="guruh statistikasi"),
            BotCommand(command="top", description="top oyinchilar"),
            BotCommand(command="rules", description="oyin qoidalari"),
            BotCommand(command="endgame", description="oyinni toxtatish"),
        ],
        scope=BotCommandScopeAllGroupChats(),
    )

    # Admin menu (chat adminlari uchun)
    await bot.set_my_commands(
        commands=[
            BotCommand(command="skipnight", description="tunni otkazish"),
            BotCommand(command="skipday", description="kuni otkazish"),
            BotCommand(command="skipvote", description="ovoz berishni yakunlash"),
            BotCommand(command="gamestatus", description="oyin holati"),
            BotCommand(command="kick", description="oyinchini chiqarish"),
            BotCommand(command="settime", description="timer sozlash"),
        ],
        scope=BotCommandScopeAllChatAdministrators(),
    )


async def main():
    log.info("🎭 Mafia Bot v3.0 ishga tushmoqda...")
    await init_db()
    log.info("✅ Ma'lumotlar bazasi tayyor.")

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Middleware'lar
    dp.update.outer_middleware(ErrorMiddleware())
    dp.message.middleware(UserTracker())
    dp.callback_query.middleware(AntiSpamMiddleware(settings.VOTE_COOLDOWN))

    # Router'lar
    dp.include_router(common.router)
    dp.include_router(game.router)
    dp.include_router(actions.router)
    dp.include_router(admin.router)
    dp.include_router(stats.router)
    dp.include_router(special.router)
    dp.include_router(economy.router)

    await setup_commands(bot)

    me = await bot.get_me()
    log.info(f"✅ Bot: @{me.username} (ID:{me.id})")
    log.info(
        f"⚙️  Min:{settings.MIN_PLAYERS} | Max:{settings.MAX_PLAYERS} | "
        f"Lobby:{settings.LOBBY_TIMEOUT}s | Tun:{settings.NIGHT_TIMEOUT}s | "
        f"Kun:{settings.DAY_DISCUSSION_TIME}s | Ovoz:{settings.VOTE_TIMEOUT}s"
    )
    log.info("═" * 60)

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        log.info("🛑 Bot to'xtatildi.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Foydalanuvchi to'xtatdi.")
