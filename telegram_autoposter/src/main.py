"""Entry point for Telegram autoposter bot."""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from src.bot import create_bot, create_dispatcher
    from src.config import Settings
    from src.content_creator import ContentCreator
    from src.scheduler import PostingScheduler
    from src.utils import setup_logging
else:
    from .bot import create_bot, create_dispatcher
    from .config import Settings
    from .content_creator import ContentCreator
    from .scheduler import PostingScheduler
    from .utils import setup_logging


async def run() -> None:
    """Bootstrap settings, services and start polling."""
    project_root = Path(__file__).resolve().parents[1]
    settings = await Settings.load(project_root=project_root)
    setup_logging(project_root, level="INFO")
    logger = logging.getLogger(__name__)

    bot = create_bot(settings)
    content_creator = ContentCreator(settings, project_root=project_root)
    scheduler = PostingScheduler(bot=bot, settings=settings, content_creator=content_creator)
    dp = create_dispatcher(settings, scheduler)

    scheduler.start()
    logger.info("Bot started")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(run())
