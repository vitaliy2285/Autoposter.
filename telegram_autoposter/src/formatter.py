"""Post formatting utilities to produce premium Telegram content style."""

from __future__ import annotations

import random
import re
from typing import Iterable

emoji_pools: dict[str, list[str]] = {
    "мотивирующий": ["🔥", "⚡️", "🚀", "💪", "✨"],
    "экспертный": ["📌", "💎", "🧠", "📊", "🔍"],
    "дружеский": ["👋", "😊", "🤗", "💬", "🌟"],
    "вдохновляющий": ["🌈", "✨", "🕊️", "🌱", "🌟"],
    "практичный": ["🛠️", "✅", "📎", "🧩", "📍"],
}

mood_emoji: dict[str, list[str]] = {
    "утренний": ["🌅", "☀️"],
    "вечерний": ["🌆", "🌙"],
    "праздничный": ["🎉", "🎊"],
}

LIST_MARKERS = ["✦", "•", "─", "✦"]


def _french_quotes(text: str) -> str:
    return text.replace('"', "«").replace("'", "’")


def _replace_dashes(text: str) -> str:
    return re.sub(r"\s-\s", " — ", text)


def _normalize_list_lines(lines: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(("- ", "* ")):
            marker = random.choice(LIST_MARKERS)
            normalized.append(f"{marker} {stripped[2:].strip()}")
        else:
            normalized.append(line.strip())
    return normalized


def _ensure_hashtags(text: str, topic: str) -> str:
    if re.search(r"#\w+", text, flags=re.UNICODE):
        return text
    topic_tag = re.sub(r"\s+", "", topic)
    variants = [f"#{topic_tag}", "#полезное", "#советы", "#вдохновение", "#telegram"]
    return f"{text}\n\n{' '.join(variants[: random.randint(3, 5)])}"


def format_post(raw_text: str, tone: str, topic: str, mood: str = "утренний") -> str:
    """Format model output into polished Telegram post caption.

    Args:
        raw_text: Original generated text.
        tone: Selected tone used for emoji pool.
        topic: Channel topic for fallback hashtags.
        mood: Mood key for optional extra emojis.

    Returns:
        Telegram-ready text no longer than 1024 chars.
    """
    cleaned = raw_text.strip()
    if not cleaned:
        cleaned = "Новый день — новые идеи для вашего канала!"

    paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [cleaned]

    title = paragraphs[0]
    if not title.startswith("**"):
        title = f"**{title.strip('* ')}**"

    pool = emoji_pools.get(tone.lower(), ["✨", "📌", "🔥"])
    mood_pool = mood_emoji.get(mood.lower(), [])
    prefix = " ".join(random.sample(pool, k=min(2, len(pool))))
    if mood_pool:
        prefix = f"{prefix} {random.choice(mood_pool)}".strip()
    paragraphs[0] = f"{prefix} {title}".strip()

    processed = []
    for paragraph in paragraphs:
        lines = paragraph.splitlines()
        lines = _normalize_list_lines(lines)
        processed.append("\n".join(lines).strip())

    text = "\n\n".join(processed)
    text = _french_quotes(text)
    text = _replace_dashes(text)
    text = _ensure_hashtags(text, topic=topic)

    if len(text) > 1024:
        text = text[:1000].rstrip() + "…"

    return text
