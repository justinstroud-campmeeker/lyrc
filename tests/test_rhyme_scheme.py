"""Tests for rhyme group assignment."""
import pytest

from lyrc.models.rhyme_scheme import SCHEMES, assign_rhyme_groups
from lyrc.models.song import LyricLine


def make_lines(n: int) -> list[LyricLine]:
    return [LyricLine(text=f"line {i}", line_index=i) for i in range(n)]


def groups(lines: list[LyricLine]) -> list[str]:
    return [l.rhyme_group for l in lines]


# ── AABB ───────────────────────────────────────────────────────────────────────

def test_aabb_four_lines():
    lines = make_lines(4)
    assign_rhyme_groups(lines, "AABB")
    assert groups(lines) == ["A", "A", "B", "B"]


def test_aabb_repeats_on_six_lines():
    lines = make_lines(6)
    assign_rhyme_groups(lines, "AABB")
    assert groups(lines) == ["A", "A", "B", "B", "A", "A"]


def test_aabb_single_line():
    lines = make_lines(1)
    assign_rhyme_groups(lines, "AABB")
    assert groups(lines) == ["A"]


# ── ABAB ───────────────────────────────────────────────────────────────────────

def test_abab_four_lines():
    lines = make_lines(4)
    assign_rhyme_groups(lines, "ABAB")
    assert groups(lines) == ["A", "B", "A", "B"]


def test_abab_six_lines():
    lines = make_lines(6)
    assign_rhyme_groups(lines, "ABAB")
    assert groups(lines) == ["A", "B", "A", "B", "A", "B"]


# ── ABBA ───────────────────────────────────────────────────────────────────────

def test_abba():
    lines = make_lines(4)
    assign_rhyme_groups(lines, "ABBA")
    assert groups(lines) == ["A", "B", "B", "A"]


# ── ABCB ───────────────────────────────────────────────────────────────────────

def test_abcb():
    lines = make_lines(4)
    assign_rhyme_groups(lines, "ABCB")
    assert groups(lines) == ["A", "B", "C", "B"]


# ── AAAA ───────────────────────────────────────────────────────────────────────

def test_aaaa():
    lines = make_lines(4)
    assign_rhyme_groups(lines, "AAAA")
    assert groups(lines) == ["A", "A", "A", "A"]


# ── FREE ───────────────────────────────────────────────────────────────────────

def test_free_clears_groups():
    lines = make_lines(4)
    assign_rhyme_groups(lines, "AABB")
    assign_rhyme_groups(lines, "FREE")
    assert all(g == "" for g in groups(lines))


def test_free_empty_input():
    lines = make_lines(0)
    assign_rhyme_groups(lines, "FREE")  # should not raise
    assert groups(lines) == []


# ── Unknown scheme ─────────────────────────────────────────────────────────────

def test_unknown_scheme_treated_as_free():
    lines = make_lines(4)
    assign_rhyme_groups(lines, "XYZW")
    assert all(g == "" for g in groups(lines))


# ── Empty line list ────────────────────────────────────────────────────────────

def test_empty_lines_no_crash():
    assign_rhyme_groups([], "AABB")


# ── Mutates in place ───────────────────────────────────────────────────────────

def test_mutates_in_place():
    lines = make_lines(2)
    orig_ids = [id(l) for l in lines]
    assign_rhyme_groups(lines, "AABB")
    assert [id(l) for l in lines] == orig_ids
