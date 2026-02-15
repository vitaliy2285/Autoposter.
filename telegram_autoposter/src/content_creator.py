"""Orchestrator that creates full post content: text + image."""

from __future__ import annotations

import logging
from pathlib import Path

from .ai_client import AIClient
from .config import Settings
from .formatter import format_post
from .image_generator import ImageGenerator
from .utils import sha256_text

LOGGER = logging.getLogger(__name__)


class ContentCreator:
    """Content pipeline with anti-duplication checks."""

    def __init__(self, settings: Settings, project_root: Path) -> None:
        self.settings = settings
        self.ai_client = AIClient(settings)
        self.image_generator = ImageGenerator(settings, project_root=project_root)

    async def create_post(self) -> tuple[str, Path, str]:
        """Generate unique text, format it and create corresponding image.

        Returns:
            Tuple of (formatted_text, image_path, text_hash).
        """
        generated_text = ""
        text_hash = ""
        for attempt in range(1, 4):
            uniqueness_hint = ""
            if attempt > 1:
                uniqueness_hint = "Сделай пост существенно отличающимся по структуре и примерам от предыдущих."

            generated_text = await self.ai_client.generate_post_text(
                topic=self.settings.topic,
                tone_description=self.settings.tone,
                mood=self.settings.mood,
                extra_instruction=uniqueness_hint,
            )
            text_hash = sha256_text(generated_text)
            if text_hash not in self.settings.last_posts_hashes:
                break
            LOGGER.info("Detected duplicated post hash on attempt %s", attempt)
        else:
            raise RuntimeError("Failed to generate unique post text after 3 attempts")

        formatted = format_post(
            raw_text=generated_text,
            tone=self.settings.tone,
            topic=self.settings.topic,
            mood=self.settings.mood,
        )
        image_prompt = await self.ai_client.generate_image_prompt(formatted)
        image_path = await self.image_generator.generate(image_prompt)

        return formatted, image_path, text_hash
