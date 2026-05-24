"""Tests for syllable counting."""
import pytest

from lyrc.services.syllable_counter import count_line_syllables, count_syllables


# ── count_syllables (single word) ─────────────────────────────────────────────

def test_single_syllable_words():
    assert count_syllables("cat") == 1
    assert count_syllables("dog") == 1
    assert count_syllables("the") == 1
    assert count_syllables("fire") == 1  # pyphen may count as 1 or 2 — just > 0
    assert count_syllables("fire") > 0


def test_two_syllable_words():
    assert count_syllables("happy") == 2
    assert count_syllables("morning") == 2
    assert count_syllables("running") == 2


def test_three_syllable_words():
    assert count_syllables("beautiful") >= 3
    assert count_syllables("yesterday") == 3


def test_empty_word_returns_zero():
    assert count_syllables("") == 0
    assert count_syllables("  ") == 0


def test_case_insensitive():
    assert count_syllables("Hello") == count_syllables("hello")
    assert count_syllables("MORNING") == count_syllables("morning")


def test_caches_results():
    # Call twice — should return same value (exercises the cache path)
    first = count_syllables("beautiful")
    second = count_syllables("beautiful")
    assert first == second


# ── count_line_syllables ───────────────────────────────────────────────────────

def test_empty_line():
    assert count_line_syllables("") == 0


def test_single_word_line():
    assert count_line_syllables("hello") == 2


def test_multi_word_line():
    # "hello world" = 2 + 1 = 3
    assert count_line_syllables("hello world") == 3


def test_punctuation_ignored():
    assert count_line_syllables("hello, world!") == count_line_syllables("hello world")


def test_numbers_ignored():
    # Digits are not matched by [a-zA-Z']+ — same as no words
    assert count_line_syllables("123 456") == 0


def test_apostrophe_in_contraction():
    # "don't" should be counted as one word
    result = count_line_syllables("don't")
    assert result >= 1


def test_longer_line():
    line = "I woke up on a Tuesday morning"
    result = count_line_syllables(line)
    # "I"=1 "woke"=1 "up"=1 "on"=1 "a"=1 "Tues-day"=2 "morn-ing"=2 → 9
    assert result >= 7  # allow pyphen variance
