"""Kandinsky 3.1 image generation service."""

from __future__ import annotations

import logging
from pathlib import Path
from uuid import uuid4

import aiofiles
import httpx

from .config import Settings
from .utils import retry_async

LOGGER = logging.getLogger(__name__)


class ImageGenerator:
    """Generate images via AsyncKandinsky with retries and timeouts."""

    def __init__(self, settings: Settings, project_root: Path) -> None:
        self.settings = settings
        self.temp_dir = project_root / "tmp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def _request_image_url(self, prompt: str) -> str:
        try:
            from async_kandinsky import AsyncKandinsky  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Package async-kandinsky is not installed") from exc

        client = AsyncKandinsky()
        if self.settings.kandinsky_auth_type == "web":
            await client.login(
                email=self.settings.kandinsky_email,
                password=self.settings.kandinsky_password,
            )
        else:
            await client.auth(
                api_key=self.settings.kandinsky_api_key,
                secret_key=self.settings.kandinsky_secret_key,
            )

        image_url = await client.generate_image(
            prompt=prompt,
            style=self.settings.kandinsky_style,
            width=self.settings.kandinsky_width,
            height=self.settings.kandinsky_height,
            use_llm=self.settings.enable_prompt_beautification,
        )
        return image_url

    async def generate(self, prompt: str) -> Path:
        """Generate image and save it into temporary directory."""

        async def _do_generate() -> Path:
            image_url = await self._request_image_url(prompt)
            filename = self.temp_dir / f"post_{uuid4().hex}.jpg"
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.get(image_url)
                response.raise_for_status()
            async with aiofiles.open(filename, "wb") as file:
                await file.write(response.content)
            return filename

        return await retry_async(_do_generate, retries=3, base_delay=2.0, logger=LOGGER)
