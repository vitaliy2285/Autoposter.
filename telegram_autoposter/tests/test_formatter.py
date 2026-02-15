from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.formatter import format_post


def test_format_post_adds_bold_title_and_hashtags() -> None:
    raw = "Заголовок\n\n- пункт 1\n- пункт 2"
    output = format_post(raw_text=raw, tone="экспертный", topic="дизайн интерьера", mood="утренний")
    assert "**" in output
    assert "#" in output
    assert len(output) <= 1024
