from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from .bot import create_bot, create_dispatcher
from .config import SettingsManager
from .content_creator import ContentCreator
from .generators import KandinskyImageGenerator
from .scheduler import PostingScheduler
from .utils import setup_logging


async def run() -> None:
    project_root = Path(__file__).resolve().parents[1]
    setup_logging(project_root)

    settings_manager = await SettingsManager.load(project_root)
    bot = create_bot(settings_manager)
    image_generator = KandinskyImageGenerator(settings_manager, project_root)
    creator = ContentCreator(settings_manager, image_generator)
    scheduler = PostingScheduler(bot, settings_manager, creator)
    dispatcher = create_dispatcher(settings_manager, scheduler)

    scheduler.start()
    logging.getLogger(__name__).info("Bot started")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dispatcher.start_polling(bot)
    finally:
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(run())
