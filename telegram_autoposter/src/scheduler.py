from __future__ import annotations

import logging
from datetime import datetime

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import FSInputFile
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import SettingsManager
from .content_creator import ContentCreator

LOGGER = logging.getLogger(__name__)


class PostingScheduler:
    def __init__(self, bot: Bot, settings_manager: SettingsManager, creator: ContentCreator) -> None:
        self.bot = bot
        self.settings_manager = settings_manager
        self.creator = creator
        self.scheduler = AsyncIOScheduler(timezone="UTC")

    def start(self) -> None:
        self.reload_jobs()
        if not self.scheduler.running:
            self.scheduler.start()

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def reload_jobs(self) -> None:
        settings = self.settings_manager.settings
        self.scheduler.remove_all_jobs()
        if not settings.autopost_enabled:
            return
        if not settings.channel_id:
            LOGGER.warning("Channel is not configured")
            return
        for t in settings.posting_times:
            h, m = t.split(":")
            self.scheduler.add_job(self.publish_post, trigger=CronTrigger(hour=int(h), minute=int(m)), kwargs={"force": False})

    def next_run(self) -> str | None:
        jobs = self.scheduler.get_jobs()
        times = [j.next_run_time for j in jobs if j.next_run_time]
        return min(times).isoformat() if times else None

    async def publish_post(self, force: bool = False) -> None:
        settings = self.settings_manager.settings
        package = await self.creator.build_post(force=force)
        if not package:
            return

        caption = f"{package.text}\n\n🔗 <a href='{package.news.url}'>Источник</a>"
        try:
            if package.image_path and package.image_path.startswith("http"):
                await self.bot.send_photo(settings.channel_id, package.image_path, caption=caption)
            elif package.image_path:
                await self.bot.send_photo(settings.channel_id, FSInputFile(package.image_path), caption=caption)
            else:
                await self.bot.send_message(settings.channel_id, caption)
        except (TelegramBadRequest, TelegramForbiddenError) as exc:
            LOGGER.error("Channel publish failed, disabling autoposting: %s", exc)
            settings.autopost_enabled = False
            await self.settings_manager.save()
            self.reload_jobs()
            return
        except Exception as exc:  # noqa: BLE001
            LOGGER.error("Unexpected telegram error: %s", exc)
            return

        settings.recent_hashes = [package.content_hash, *settings.recent_hashes[:9]]
        settings.stats.total_posts += 1
        settings.stats.last_post_at = datetime.utcnow().isoformat()
        await self.settings_manager.save()
        LOGGER.info("Published post from %s", package.news.source)
