from __future__ import annotations

import base64
import logging
from pathlib import Path
from uuid import uuid4

from ..config import SettingsManager
from ..utils import retry_async

LOGGER = logging.getLogger(__name__)


class KandinskyImageGenerator:
    def __init__(self, settings_manager: SettingsManager, project_root: Path) -> None:
        self.settings_manager = settings_manager
        self.output_dir = project_root / "tmp"
        self.output_dir.mkdir(exist_ok=True)

    async def _init_client(self):
        from async_kandinsky import AsyncKandinsky  # type: ignore

        settings = self.settings_manager.settings
        client = AsyncKandinsky()
        if settings.kandinsky_auth_mode == "web":
            await client.login(email=settings.kandinsky_email, password=settings.kandinsky_password)
        else:
            await client.auth(api_key=settings.kandinsky_api_key, secret_key=settings.kandinsky_secret_key)
        return client

    async def generate(self, prompt: str) -> str | None:
        settings = self.settings_manager.settings

        async def _run() -> str | None:
            client = await self._init_client()
            result = await client.generate(
                prompt=prompt,
                width=settings.kandinsky_width,
                height=settings.kandinsky_height,
                style=settings.kandinsky_style,
                use_llm=settings.prompt_beautification,
            )
            if not result:
                return None
            file_path = self.output_dir / f"{uuid4().hex}.png"
            if result.startswith("http"):
                return result
            file_path.write_bytes(base64.b64decode(result))
            return str(file_path)

        try:
            return await retry_async(_run, logger=LOGGER)
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Image generation failed: %s", exc)
            return None
