"""Application settings loading and persistence."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import aiofiles
from dotenv import load_dotenv


@dataclass
class Stats:
    """Posting statistics container."""

    total_posts: int = 0
    last_post_time: str | None = None


@dataclass
class Settings:
    """Runtime settings for autoposter bot."""

    admin_ids: list[int] = field(default_factory=list)
    topic: str = "дизайн интерьера"
    posting_times: list[str] = field(default_factory=lambda: ["09:00", "15:00", "21:00"])
    tone: str = "экспертный"
    mood: str = "утренний"
    kandinsky_style: str = "DEFAULT"
    kandinsky_width: int = 1024
    kandinsky_height: int = 1024
    kandinsky_auth_type: str = "api"
    kandinsky_api_key: str = ""
    kandinsky_secret_key: str = ""
    kandinsky_email: str = ""
    kandinsky_password: str = ""
    enable_prompt_beautification: bool = False
    openai_url: str = "https://api.openai.com/v1"
    openai_key: str = ""
    text_model: str = "gpt-5.2"
    prompt_model: str = "gpt-5.2"
    telegram_channel: str = ""
    is_active: bool = False
    last_posts_hashes: list[str] = field(default_factory=list)
    stats: Stats = field(default_factory=Stats)

    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[1], repr=False)

    @property
    def config_path(self) -> Path:
        """Return path to config.json file."""
        return self.project_root / "config.json"

    @classmethod
    async def load(cls, project_root: Path | None = None) -> "Settings":
        """Load settings from .env and config.json with JSON priority."""
        base_root = project_root or Path(__file__).resolve().parents[1]
        load_dotenv(base_root / ".env")

        settings = cls(project_root=base_root)
        settings._load_from_env()
        await settings._load_from_json()
        return settings

    def _load_from_env(self) -> None:
        """Load defaults from environment variables."""
        self.admin_ids = self._parse_int_list(os.getenv("ADMIN_IDS", ""))
        self.topic = os.getenv("TOPIC", self.topic)
        self.posting_times = self._parse_time_list(os.getenv("POSTING_TIMES", ",".join(self.posting_times)))
        self.tone = os.getenv("TONE", self.tone)
        self.mood = os.getenv("MOOD", self.mood)
        self.kandinsky_style = os.getenv("KANDINSKY_STYLE", self.kandinsky_style)
        self.kandinsky_width = int(os.getenv("KANDINSKY_WIDTH", str(self.kandinsky_width)))
        self.kandinsky_height = int(os.getenv("KANDINSKY_HEIGHT", str(self.kandinsky_height)))
        self.kandinsky_auth_type = os.getenv("KANDINSKY_AUTH_TYPE", self.kandinsky_auth_type)
        self.kandinsky_api_key = os.getenv("KANDINSKY_API_KEY", self.kandinsky_api_key)
        self.kandinsky_secret_key = os.getenv("KANDINSKY_SECRET_KEY", self.kandinsky_secret_key)
        self.kandinsky_email = os.getenv("KANDINSKY_EMAIL", self.kandinsky_email)
        self.kandinsky_password = os.getenv("KANDINSKY_PASSWORD", self.kandinsky_password)
        self.enable_prompt_beautification = os.getenv("ENABLE_PROMPT_BEAUTIFICATION", "false").lower() == "true"
        self.openai_url = os.getenv("OPENAI_URL", self.openai_url)
        self.openai_key = os.getenv("OPENAI_KEY", self.openai_key)
        self.text_model = os.getenv("TEXT_MODEL", self.text_model)
        self.prompt_model = os.getenv("PROMPT_MODEL", self.prompt_model)
        self.telegram_channel = os.getenv("TELEGRAM_CHANNEL", self.telegram_channel)
        self.is_active = os.getenv("IS_ACTIVE", "false").lower() == "true"

    async def _load_from_json(self) -> None:
        """Load and apply overrides from config.json if file exists."""
        if not self.config_path.exists():
            return

        async with aiofiles.open(self.config_path, "r", encoding="utf-8") as file:
            raw = await file.read()
        data = json.loads(raw)
        self.apply_updates(data)

    def apply_updates(self, updates: dict[str, Any]) -> None:
        """Apply updates to settings object from dict payload."""
        for key, value in updates.items():
            if key == "stats" and isinstance(value, dict):
                self.stats = Stats(**{**asdict(self.stats), **value})
                continue
            if hasattr(self, key):
                setattr(self, key, value)

    async def save(self) -> None:
        """Persist settings into config.json."""
        payload = asdict(self)
        payload.pop("project_root", None)
        async with aiofiles.open(self.config_path, "w", encoding="utf-8") as file:
            await file.write(json.dumps(payload, ensure_ascii=False, indent=2))

    async def reset_to_env(self) -> None:
        """Reset mutable values from environment while preserving admin_ids."""
        admin_ids = list(self.admin_ids)
        self._load_from_env()
        self.admin_ids = admin_ids or self.admin_ids
        self.last_posts_hashes = []
        self.stats = Stats()
        await self.save()

    def register_post_stat(self) -> None:
        """Increase counters after successful publication."""
        self.stats.total_posts += 1
        self.stats.last_post_time = datetime.utcnow().isoformat()

    @staticmethod
    def _parse_time_list(raw: str) -> list[str]:
        return [item.strip() for item in raw.split(",") if item.strip()]

    @staticmethod
    def _parse_int_list(raw: str) -> list[int]:
        return [int(item.strip()) for item in raw.split(",") if item.strip().isdigit()]
