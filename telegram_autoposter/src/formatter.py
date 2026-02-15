from __future__ import annotations

import random
import re

TONE_EMOJIS = {
    "мотивирующий": ["🚀", "🔥", "💪"],
    "экспертный": ["🧠", "📌", "🔍"],
    "дружеский": ["🤝", "🙂", "✨"],
    "киберпанк": ["⚡️", "🕶", "💾"],
}
MOOD_EMOJIS = {"утренний": ["🌅"], "вечерний": ["🌆"], "ночной": ["🌙", "🌌"]}
LIST_BULLETS = ["✦", "•", "─"]


def _typography(text: str) -> str:
    text = text.replace('"', "«", 1)
    text = re.sub(r'"([^\"]+)"', r'«\1»', text)
    text = text.replace(" - ", " — ").replace(" -- ", " — ")
    return text


def _hashtags(topic: str, text: str) -> str:
    if "#" in text:
        return text
    words = [w for w in re.findall(r"[а-яА-Яa-zA-Z0-9]+", topic.lower()) if len(w) > 2]
    base = [f"#{w}" for w in words[:3]] or ["#новости", "#кибербезопасность"]
    extra = ["#infosec", "#cve", "#autopost"]
    return f"{text}\n\n{' '.join((base + extra)[:5])}"


def format_post(raw_text: str, tone: str, topic: str, mood: str) -> str:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if not lines:
        lines = [topic]

    title = lines[0]
    emojis = random.sample(TONE_EMOJIS.get(tone, ["✨", "📌"]) + MOOD_EMOJIS.get(mood, []), k=2)
    formatted_lines = [f"<b>{' '.join(emojis)} {title}</b>"]

    bullet_idx = 0
    for line in lines[1:]:
        if line.startswith("-") or line.startswith("*"):
            marker = LIST_BULLETS[bullet_idx % len(LIST_BULLETS)]
            formatted_lines.append(f"{marker} {line[1:].strip()}")
            bullet_idx += 1
        else:
            formatted_lines.append(line)

    post = "\n\n".join(formatted_lines)
    post = _typography(post)
    post = _hashtags(topic, post)
    if len(post) > 1024:
        post = post[:1021].rstrip() + "…"
    return post
