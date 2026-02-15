"""APScheduler integration for planned Telegram posting."""

from __future__ import annotations

import logging
from datetime import datetime

from aiogram import Bot
from aiogram.types import FSInputFile
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import Settings
from .content_creator import ContentCreator

LOGGER = logging.getLogger(__name__)


class PostingScheduler:
    """Manage periodic posting jobs and runtime publish flow."""

    def __init__(self, bot: Bot, settings: Settings, content_creator: ContentCreator) -> None:
        self.bot = bot
        self.settings = settings
        self.content_creator = content_creator
        self.scheduler = AsyncIOScheduler(timezone="UTC")

    def start(self) -> None:
        """Start scheduler with current posting times."""
        self.reload_jobs()
        if not self.scheduler.running:
            self.scheduler.start()
        LOGGER.info("Scheduler started")

    def shutdown(self) -> None:
        """Shutdown scheduler safely."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
        LOGGER.info("Scheduler stopped")

    def reload_jobs(self) -> None:
        """Rebuild cron jobs from current settings."""
        self.scheduler.remove_all_jobs()
        if not self.settings.is_active:
            LOGGER.info("Autoposting disabled, jobs not scheduled")
            return
        if not self.settings.telegram_channel:
            LOGGER.warning("Telegram channel is not configured; scheduler skipped")
            return

        for time_item in self.settings.posting_times:
            hours, minutes = time_item.split(":")
            trigger = CronTrigger(hour=int(hours), minute=int(minutes))
            self.scheduler.add_job(self.publish_post, trigger=trigger, name=f"publish_{time_item}")
            LOGGER.info("Scheduled posting at %s", time_item)

    def get_next_run(self) -> str | None:
        """Get nearest next run time among scheduled jobs."""
        jobs = self.scheduler.get_jobs()
        times = [job.next_run_time for job in jobs if job.next_run_time]
        if not times:
            return None
        return min(times).isoformat()

    async def publish_post(self) -> None:
        """Generate and publish post. Deactivate on Telegram permission errors."""
        if not self.settings.is_active:
            return
        if not self.settings.telegram_channel:
            LOGGER.warning("Cannot publish: channel is not set")
            return

        try:
            text, image_path, text_hash = await self.content_creator.create_post()
        except Exception as exc:  # noqa: BLE001
            LOGGER.error("Content generation failed: %s", exc)
            return

        try:
            await self.bot.send_photo(
                chat_id=self.settings.telegram_channel,
                photo=FSInputFile(str(image_path)),
                caption=text,
            )
            self.settings.last_posts_hashes = [text_hash, *self.settings.last_posts_hashes[:9]]
            self.settings.register_post_stat()
            await self.settings.save()
            LOGGER.info("Post published successfully at %s", datetime.utcnow().isoformat())
        except Exception as exc:  # noqa: BLE001
            LOGGER.error("Telegram publish failed: %s", exc)
            self.settings.is_active = False
            await self.settings.save()
            self.reload_jobs()
