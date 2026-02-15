"""Bot and dispatcher factory."""

from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from .admin_handlers import register_handlers
from .config import Settings
from .scheduler import PostingScheduler


def create_bot(settings: Settings) -> Bot:
    """Create aiogram Bot instance."""
    import os

    token = os.getenv("BOT_TOKEN", "")
    if not token:
        raise RuntimeError("BOT_TOKEN is missing in environment")
    return Bot(token=token)


def create_dispatcher(settings: Settings, scheduler: PostingScheduler) -> Dispatcher:
    """Create dispatcher and register handlers."""
    dp = Dispatcher(storage=MemoryStorage())
    register_handlers(dp, settings, scheduler)
    return dp
