"""Tests for stage-direction filtering logic (no Qt runtime needed)."""
import pytest

from lyrc.widgets.stage_direction_popup import STAGE_DIRECTIONS


# Test the filter logic in isolation (pure Python, no widget instantiation)

def _filter(text: str) -> list[str]:
    needle = text.lower()
    return [d for d in STAGE_DIRECTIONS if not needle or needle in d.lower()]


def test_empty_filter_returns_all():
    assert _filter("") == STAGE_DIRECTIONS


def test_filter_chorus():
    result = _filter("cho")
    assert "Chorus" in result
    assert all("cho" in d.lower() for d in result)


def test_filter_verse():
    result = _filter("verse")
    assert all("verse" in d.lower() for d in result)
    assert "Verse 1" in result
    assert "Verse 2" in result


def test_filter_case_insensitive():
    lower = _filter("chorus")
    upper = _filter("CHORUS")
    assert lower == upper


def test_filter_no_match_returns_empty():
    result = _filter("zzzzz")
    assert result == []


def test_filter_single_char_broad():
    result = _filter("b")
    assert len(result) > 0
    assert all("b" in d.lower() for d in result)


def test_all_directions_are_strings():
    assert all(isinstance(d, str) for d in STAGE_DIRECTIONS)


def test_no_duplicate_directions():
    assert len(STAGE_DIRECTIONS) == len(set(STAGE_DIRECTIONS))


def test_common_directions_present():
    for expected in ("Chorus", "Verse 1", "Bridge", "Outro", "Intro"):
        assert expected in STAGE_DIRECTIONS


def test_filter_first_result_is_selectable():
    # Simulates Tab selecting index 0 after filtering — result must exist
    result = _filter("cho")
    assert len(result) > 0
    assert result[0] == "Chorus"
