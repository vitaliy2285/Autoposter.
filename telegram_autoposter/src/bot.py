from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from .admin_handlers import admin_router
from .config import SettingsManager
from .scheduler import PostingScheduler


def create_bot(settings_manager: SettingsManager) -> Bot:
    return Bot(token=settings_manager.settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


def create_dispatcher(settings_manager: SettingsManager, scheduler: PostingScheduler) -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(admin_router(settings_manager, scheduler))
    return dp
