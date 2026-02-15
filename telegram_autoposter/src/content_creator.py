from __future__ import annotations

import logging

from .config import SettingsManager
from .formatter import format_post
from .generators import DeepSeekTextGenerator, KandinskyImageGenerator
from .models import PostPackage
from .sources import GitHubHunter
from .utils import make_hash

LOGGER = logging.getLogger(__name__)


class ContentCreator:
    def __init__(self, settings_manager: SettingsManager, image_generator: KandinskyImageGenerator) -> None:
        self.settings_manager = settings_manager
        self.source = GitHubHunter(settings_manager)
        self.text_generator = DeepSeekTextGenerator(settings_manager)
        self.image_generator = image_generator

    async def build_post(self, force: bool = False) -> PostPackage | None:
        settings = self.settings_manager.settings
        news = await self.source.fetch()
        if not news:
            LOGGER.info("No unique news found")
            return None

        raw_text = await self.text_generator.generate_post(news)
        if not raw_text:
            LOGGER.warning("Text generator returned empty text")
            return None

        content_hash = make_hash(f"{news.url}:{raw_text}")
        if not force and content_hash in settings.recent_hashes:
            LOGGER.info("Duplicate hash detected; skip")
            return None

        formatted = format_post(raw_text, settings.tone, settings.topic, settings.mood)
        prompt = await self.text_generator.generate_image_prompt(news, formatted)
        image_path = await self.image_generator.generate(prompt)

        return PostPackage(text=formatted, image_path=image_path, news=news, content_hash=content_hash)
