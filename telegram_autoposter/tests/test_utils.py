from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.utils import make_hash, parse_times


def test_make_hash_stable() -> None:
    assert make_hash('abc') == make_hash('abc')


def test_parse_times() -> None:
    assert parse_times('09:00,15:30') == ['09:00', '15:30']
