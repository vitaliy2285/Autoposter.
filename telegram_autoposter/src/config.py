from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .models import RuntimeSettings


class SettingsManager:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.config_path = project_root / "config.json"
        self.settings = RuntimeSettings()

    @classmethod
    async def load(cls, project_root: Path) -> "SettingsManager":
        manager = cls(project_root)
        load_dotenv(project_root / ".env")
        manager.settings = manager._from_env()
        if manager.config_path.exists():
            manager._merge_json_overrides()
        else:
            await manager.save()
        return manager

    def _from_env(self) -> RuntimeSettings:
        admin_ids = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
        posting_times = [x.strip() for x in os.getenv("POSTING_TIMES", "09:00,15:00,21:00").split(",") if x.strip()]
        keywords = [x.strip().lower() for x in os.getenv("SOURCE_KEYWORDS", "cve,exploit").split(",") if x.strip()]
        return RuntimeSettings(
            admin_ids=admin_ids,
            bot_token=os.getenv("BOT_TOKEN", ""),
            github_token=os.getenv("GITHUB_TOKEN", ""),
            channel_id=os.getenv("CHANNEL_ID", ""),
            topic=os.getenv("TOPIC", "Кибербезопасность"),
            posting_times=posting_times,
            tone=os.getenv("TONE", "экспертный"),
            mood=os.getenv("MOOD", "утренний"),
            source_keywords=keywords,
            autopost_enabled=os.getenv("AUTOPOST_ENABLED", "false").lower() == "true",
            openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1"),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", "deepseek-chat"),
            system_prompt=os.getenv(
                "SYSTEM_PROMPT",
                "Ты — редактор телеграм-канала по кибербезопасности. Пиши строго на русском языке, структурно и лаконично.",
            ),
            kandinsky_auth_mode=os.getenv("KANDINSKY_AUTH_MODE", "api"),
            kandinsky_api_key=os.getenv("KANDINSKY_API_KEY", ""),
            kandinsky_secret_key=os.getenv("KANDINSKY_SECRET_KEY", ""),
            kandinsky_email=os.getenv("KANDINSKY_EMAIL", ""),
            kandinsky_password=os.getenv("KANDINSKY_PASSWORD", ""),
            kandinsky_style=os.getenv("KANDINSKY_STYLE", "DEFAULT"),
            kandinsky_width=int(os.getenv("KANDINSKY_WIDTH", "1280")),
            kandinsky_height=int(os.getenv("KANDINSKY_HEIGHT", "720")),
            prompt_beautification=os.getenv("PROMPT_BEAUTIFICATION", "true").lower() == "true",
        )

    def _merge_json_overrides(self) -> None:
        payload = json.loads(self.config_path.read_text(encoding="utf-8"))
        merged = self.settings.model_dump()
        merged.update(payload)
        self.settings = RuntimeSettings(**merged)

    async def save(self) -> None:
        data = self.settings.model_dump()
        self.config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    async def reset_to_env(self) -> None:
        self.settings = self._from_env()
        await self.save()

    async def update(self, **kwargs: Any) -> None:
        merged = self.settings.model_dump()
        merged.update(kwargs)
        self.settings = RuntimeSettings(**merged)
        await self.save()
