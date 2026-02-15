from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import NewsItem


class Source(ABC):
    @abstractmethod
    async def fetch(self) -> NewsItem | None:
        raise NotImplementedError
