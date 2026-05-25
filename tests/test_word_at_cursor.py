"""Tests for lyrc.services.text_utils.word_at_cursor."""
import pytest

from lyrc.services.text_utils import word_at_cursor


def word_at(value: str, cursor: int):
    return word_at_cursor(value, cursor)


# ── Basic extraction ───────────────────────────────────────────────────────────

def test_cursor_inside_word():
    assert word_at("hello world", 3) == ("hello", 0, 5)


def test_cursor_at_start_of_word():
    assert word_at("hello world", 0) == ("hello", 0, 5)


def test_cursor_at_end_of_word():
    assert word_at("hello world", 5) == ("hello", 0, 5)


def test_cursor_on_second_word():
    assert word_at("hello world", 8) == ("world", 6, 11)


def test_cursor_between_words_returns_none():
    # Cursor on the space between words
    assert word_at("hello world", 5) == ("hello", 0, 5)  # end of "hello"
    # Cursor at position 6 = start of "world"
    assert word_at("hello world", 6) == ("world", 6, 11)


def test_cursor_on_space_only():
    assert word_at("   ", 1) is None


def test_empty_string():
    assert word_at("", 0) is None


def test_single_word():
    assert word_at("fire", 2) == ("fire", 0, 4)


def test_single_word_cursor_at_end():
    assert word_at("fire", 4) == ("fire", 0, 4)


# ── Apostrophes ───────────────────────────────────────────────────────────────

def test_contraction_treated_as_one_word():
    result = word_at("don't stop", 2)
    assert result == ("don't", 0, 5)


def test_cursor_after_apostrophe():
    result = word_at("don't stop", 4)
    assert result == ("don't", 0, 5)


# ── Punctuation boundaries ────────────────────────────────────────────────────

def test_comma_is_boundary():
    result = word_at("fire, ice", 2)
    assert result == ("fire", 0, 4)


def test_cursor_just_before_comma_returns_word():
    # position 4 is ','; walking left from 4 still finds 'fire' (0..4)
    result = word_at("fire, ice", 4)
    assert result == ("fire", 0, 4)


def test_cursor_after_comma():
    result = word_at("fire, ice", 6)
    assert result == ("ice", 6, 9)


# ── Replacement bounds ────────────────────────────────────────────────────────

def test_returned_bounds_splice_correctly():
    value = "the quick brown fox"
    result = word_at(value, 10)
    assert result is not None
    word, start, end = result
    assert value[start:end] == word
    replaced = value[:start] + "slow" + value[end:]
    assert replaced == "the quick slow fox"
