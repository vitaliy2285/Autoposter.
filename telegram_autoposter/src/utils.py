from __future__ import annotations

import asyncio
import hashlib
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")


def setup_logging(project_root: Path) -> None:
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / "bot.log"

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    root.addHandler(file_handler)
    root.addHandler(stream_handler)


def make_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


async def retry_async(
    fn: Callable[[], Awaitable[T]],
    *,
    retries: int = 3,
    base_delay: float = 1.0,
    logger: logging.Logger | None = None,
) -> T:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return await fn()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if logger:
                logger.warning("Attempt %s/%s failed: %s", attempt, retries, exc)
            if attempt < retries:
                await asyncio.sleep(base_delay * (2 ** (attempt - 1)))
    assert last_error is not None
    raise last_error


def parse_times(raw: str) -> list[str]:
    items = [item.strip() for item in raw.split(",") if item.strip()]
    for item in items:
        hours, minutes = item.split(":")
        if not (0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59):
            raise ValueError(f"Invalid time: {item}")
    return items
