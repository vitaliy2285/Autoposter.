from __future__ import annotations

import logging

import httpx

from ..config import SettingsManager
from ..models import NewsItem
from ..utils import make_hash, retry_async
from .base import Source

LOGGER = logging.getLogger(__name__)


class GitHubHunter(Source):
    def __init__(self, settings_manager: SettingsManager) -> None:
        self.settings_manager = settings_manager

    async def fetch(self) -> NewsItem | None:
        settings = self.settings_manager.settings

        async def _request() -> dict:
            query = "(CVE-2025 OR CVE-2024) exploit"
            url = f"https://api.github.com/search/repositories?q={query}&sort=updated&order=desc&per_page=10"
            headers = {"Accept": "application/vnd.github+json"}
            if settings.github_token:
                headers["Authorization"] = f"Bearer {settings.github_token}"
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()

        data = await retry_async(_request, logger=LOGGER)
        keywords = [kw.lower() for kw in settings.source_keywords]
        for item in data.get("items", []):
            title = item.get("name", "unknown")
            desc = item.get("description") or "Security research repository"
            url = item.get("html_url", "")
            combined = f"{title} {desc}".lower()
            if keywords and not any(kw in combined for kw in keywords):
                continue
            fingerprint = make_hash(f"{title}:{url}")
            if fingerprint in settings.recent_hashes:
                continue
            return NewsItem(title=title, description=desc, url=url, source="github")
        return None
