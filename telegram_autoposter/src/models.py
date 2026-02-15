from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class NewsItem(BaseModel):
    title: str
    description: str
    url: str
    source: str = "github"
    published_at: datetime | None = None


class PostPackage(BaseModel):
    text: str
    image_path: str | None = None
    news: NewsItem
    content_hash: str


class StatsModel(BaseModel):
    total_posts: int = 0
    last_post_at: str | None = None


class RuntimeSettings(BaseModel):
    admin_ids: list[int] = Field(default_factory=list)
    bot_token: str = ""
    github_token: str = ""
    channel_id: str = ""
    topic: str = "Кибербезопасность"
    posting_times: list[str] = Field(default_factory=lambda: ["09:00", "15:00", "21:00"])
    tone: Literal["мотивирующий", "экспертный", "дружеский", "киберпанк"] = "экспертный"
    mood: Literal["утренний", "вечерний", "ночной"] = "утренний"
    source_keywords: list[str] = Field(default_factory=lambda: ["cve", "exploit"])
    autopost_enabled: bool = False

    openai_base_url: str = "https://api.deepseek.com/v1"
    openai_api_key: str = ""
    openai_model: str = "deepseek-chat"
    system_prompt: str = (
        "Ты — редактор телеграм-канала по кибербезопасности. Пиши строго на русском языке, "
        "структурно, профессионально и без воды."
    )

    kandinsky_auth_mode: Literal["api", "web"] = "api"
    kandinsky_api_key: str = ""
    kandinsky_secret_key: str = ""
    kandinsky_email: str = ""
    kandinsky_password: str = ""
    kandinsky_style: Literal["DEFAULT", "KANDINSKY", "UHD", "ANIME"] = "DEFAULT"
    kandinsky_width: int = 1280
    kandinsky_height: int = 720
    prompt_beautification: bool = True

    recent_hashes: list[str] = Field(default_factory=list)
    stats: StatsModel = Field(default_factory=StatsModel)
