from __future__ import annotations

import logging

from openai import AsyncOpenAI

from ..config import SettingsManager
from ..models import NewsItem
from ..utils import retry_async

LOGGER = logging.getLogger(__name__)


class DeepSeekTextGenerator:
    def __init__(self, settings_manager: SettingsManager) -> None:
        self.settings_manager = settings_manager

    async def generate_post(self, news: NewsItem) -> str:
        settings = self.settings_manager.settings
        client = AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)

        async def _generate() -> str:
            prompt = (
                f"Тема канала: {settings.topic}. Тон: {settings.tone}. Настроение: {settings.mood}.\n"
                f"Инфоповод: {news.title} — {news.description}.\n"
                "Сделай пост с блоками: СУТЬ, УГРОЗА, ЗАЩИТА."
            )
            response = await client.chat.completions.create(
                model=settings.openai_model,
                temperature=0.75,
                messages=[
                    {"role": "system", "content": settings.system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )
            return (response.choices[0].message.content or "").strip()

        return await retry_async(_generate, logger=LOGGER)

    async def generate_image_prompt(self, news: NewsItem, text: str) -> str:
        settings = self.settings_manager.settings
        client = AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)

        async def _generate() -> str:
            response = await client.chat.completions.create(
                model=settings.openai_model,
                temperature=0.6,
                messages=[
                    {"role": "system", "content": "Create visual prompt in English for cyber security poster, <=240 chars."},
                    {"role": "user", "content": f"{news.title}\n{text}"},
                ],
            )
            return (response.choices[0].message.content or news.title)[:240]

        return await retry_async(_generate, logger=LOGGER)
