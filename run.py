"""Локальный запуск через polling. В прод не идёт — только для разработки."""

import asyncio
import sys
import os

from loguru import logger
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.bot import bot
from bot.handlers import start, registration, confirmation, admin
from database.session import init_db, close_engine

# ── логгинг ───────────────────────────────────────────────────────────────────

os.makedirs('logs', exist_ok=True)

logger.remove()  # убираем дефолтный stderr-хендлер

logger.add(
    sys.stdout,
    format=(
        '<green>{time:HH:mm:ss}</green> | '
        '<level>{level:<8}</level> | '
        '<cyan>{name}</cyan> — <white>{message}</white>'
    ),
    level='INFO',
    colorize=True,
)

logger.add(
    'logs/bot.log',
    format='{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name} — {message}',
    level='DEBUG',
    rotation='10 MB',
    retention='7 days',
    encoding='utf-8',
)


# ── main ──────────────────────────────────────────────────────────────────────


async def main() -> None:
    await init_db()
    logger.info('База данных инициализирована')

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start.router)
    dp.include_router(registration.router)
    dp.include_router(confirmation.router)
    dp.include_router(admin.router)

    me = await bot.get_me()
    logger.info('Бот запущен: @{} (id={})', me.username, me.id)

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await close_engine()
        await bot.session.close()
        logger.info('Бот остановлен')


if __name__ == '__main__':
    asyncio.run(main())
