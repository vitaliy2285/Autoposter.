"""Utility helpers for logging, hashing and resilient async operations."""

from __future__ import annotations

import asyncio
import hashlib
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Awaitable, Callable, TypeVar

T = TypeVar("T")


def ensure_dirs(project_root: Path) -> None:
    """Create required directories if they do not exist."""
    (project_root / "logs").mkdir(parents=True, exist_ok=True)


def setup_logging(project_root: Path, level: str = "INFO") -> logging.Logger:
    """Configure rotating file logging for the bot.

    Args:
        project_root: Root directory of the project.
        level: Logging level name.

    Returns:
        Configured root logger.
    """
    ensure_dirs(project_root)
    log_path = project_root / "logs" / "bot.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    root_logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    return root_logger


def sha256_text(text: str) -> str:
    """Return SHA256 hash for a text string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


async def retry_async(
    func: Callable[[], Awaitable[T]],
    retries: int = 3,
    base_delay: float = 1.0,
    logger: logging.Logger | None = None,
) -> T:
    """Execute async function with exponential backoff retries."""
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return await func()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if logger:
                logger.error("Attempt %s/%s failed: %s", attempt, retries, exc)
            if attempt < retries:
                await asyncio.sleep(base_delay * (2 ** (attempt - 1)))

    assert last_error is not None
    raise last_error
