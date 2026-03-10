"""
Cloud entrypoint — Yandex Cloud Functions / SourceCraft webhook.
Каждый вызов = один апдейт от Telegram.
"""

import json
import logging

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update

from bot.bot import bot
from bot.handlers import start, registration, confirmation, admin
from database.session import init_db

log = logging.getLogger(__name__)

_dp: Dispatcher | None = None


def _get_dp() -> Dispatcher:
    global _dp
    if _dp is None:
        _dp = Dispatcher(storage=MemoryStorage())
        _dp.include_router(start.router)
        _dp.include_router(registration.router)
        _dp.include_router(confirmation.router)
        _dp.include_router(admin.router)
    return _dp


async def handler(event: dict, context) -> dict:
    await init_db()
    dp = _get_dp()

    body = json.loads(event['body'])
    update = Update.model_validate(body)
    await dp.feed_update(bot, update)

    return {'statusCode': 200, 'body': ''}
