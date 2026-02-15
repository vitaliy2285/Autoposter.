from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.formatter import format_post


def test_format_post_adds_title_and_hashtags() -> None:
    raw = 'Заголовок\n\n- пункт 1\n- пункт 2'
    output = format_post(raw_text=raw, tone='экспертный', topic='кибер безопасность', mood='утренний')
    assert '<b>' in output
    assert '#кибер' in output or '#безопасность' in output
    assert len(output) <= 1024


def test_format_post_replaces_list_markers() -> None:
    raw = 'Title\n- one\n* two'
    output = format_post(raw, tone='дружеский', topic='topic', mood='ночной')
    assert '✦' in output or '•' in output or '─' in output
