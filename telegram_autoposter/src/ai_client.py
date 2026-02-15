"""OpenAI-compatible client for text and prompt generation."""

from __future__ import annotations

import logging
from textwrap import dedent

from openai import AsyncOpenAI

from .config import Settings
from .utils import retry_async

LOGGER = logging.getLogger(__name__)


class AIClient:
    """Wrapper around OpenAI-compatible chat completion API."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = AsyncOpenAI(
            api_key=settings.openai_key,
            base_url=settings.openai_url,
        )

    def _build_system_prompt(self, topic: str, tone_description: str, mood: str) -> str:
        return dedent(
            f"""
            Ты — профессиональный копирайтер для Telegram-канала на тему {topic}.
            Твой стиль: {tone_description}. Дополнительное настроение поста: {mood}.
            Пиши пост в разговорном, но грамотном стиле.
            Используй эмодзи для акцентов, но не перебарщивай.
            Структура: цепляющий заголовок, введение, основная часть короткими абзацами,
            финальный вывод или вопрос для вовлечения, хештеги.
            Избегай клише и шаблонных фраз. Текст должен быть уникальным, живым и практичным.
            """
        ).strip()

    async def generate_post_text(
        self,
        topic: str,
        tone_description: str,
        mood: str,
        extra_instruction: str = "",
    ) -> str:
        """Generate post text with retry logic."""

        async def _do_generate() -> str:
            response = await self.client.chat.completions.create(
                model=self.settings.text_model,
                temperature=0.9,
                messages=[
                    {"role": "system", "content": self._build_system_prompt(topic, tone_description, mood)},
                    {
                        "role": "user",
                        "content": (
                            f"Создай уникальный пост для темы: {topic}."
                            f" {extra_instruction}".strip()
                        ),
                    },
                ],
            )
            return response.choices[0].message.content.strip()

        return await retry_async(_do_generate, retries=3, base_delay=1.0, logger=LOGGER)

    async def generate_image_prompt(self, post_text: str) -> str:
        """Generate compact English prompt for Kandinsky image generation."""

        async def _do_generate() -> str:
            response = await self.client.chat.completions.create(
                model=self.settings.prompt_model,
                temperature=0.7,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Based on the post text, craft a detailed photorealistic prompt in English "
                            "for Kandinsky 3.1, up to 300 chars. Mention composition, lighting and style."
                        ),
                    },
                    {"role": "user", "content": post_text},
                ],
            )
            return response.choices[0].message.content.strip()[:300]

        return await retry_async(_do_generate, retries=3, base_delay=1.0, logger=LOGGER)
