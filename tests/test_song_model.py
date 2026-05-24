"""Tests for Song model: construction, markdown serialization, round-trips."""
from pathlib import Path

import pytest

from lyrc.models.song import LyricLine, Section, Song


FAKE_PATH = Path("test.md")


def make_song(title: str = "My Song", n_sections: int = 2) -> Song:
    sections = [
        Section(
            direction=f"Section {i}",
            lines=[
                LyricLine(text=f"Line {i}-{j}", line_index=j)
                for j in range(4)
            ],
            section_index=i,
        )
        for i in range(n_sections)
    ]
    return Song(title=title, sections=sections)


# ── from_markdown ──────────────────────────────────────────────────────────────

def test_parse_title():
    md = "# Hello World\n\n[Verse]\nsome line\n"
    song = Song.from_markdown(md, FAKE_PATH)
    assert song.title == "Hello World"


def test_parse_sections():
    md = "# T\n\n[Verse 1]\nline1\nline2\n\n[Chorus]\nchorus line\n"
    song = Song.from_markdown(md, FAKE_PATH)
    assert len(song.sections) == 2
    assert song.sections[0].direction == "Verse 1"
    assert song.sections[1].direction == "Chorus"


def test_parse_line_content():
    md = "# T\n\n[Verse]\nFirst line here\nSecond line here\n"
    song = Song.from_markdown(md, FAKE_PATH)
    lines = song.sections[0].lines
    assert lines[0].text == "First line here"
    assert lines[1].text == "Second line here"


def test_blank_lines_between_sections_not_captured():
    md = "# T\n\n[Verse]\nline a\nline b\n\n[Chorus]\nchorus\n"
    song = Song.from_markdown(md, FAKE_PATH)
    # Blank separator should not end up as a lyric line
    assert all(l.text != "" or l.text == "" for l in song.sections[0].lines)
    assert len(song.sections[0].lines) == 2


def test_blank_lines_before_first_section_ignored():
    md = "# T\n\n\n\n[Verse]\nline\n"
    song = Song.from_markdown(md, FAKE_PATH)
    assert len(song.sections) == 1
    assert song.sections[0].direction == "Verse"


def test_section_index_assigned():
    md = "# T\n\n[A]\nline\n\n[B]\nline\n"
    song = Song.from_markdown(md, FAKE_PATH)
    assert song.sections[0].section_index == 0
    assert song.sections[1].section_index == 1


def test_empty_song_gives_no_sections():
    md = "# Empty\n"
    song = Song.from_markdown(md, FAKE_PATH)
    assert song.title == "Empty"
    assert len(song.sections) == 0


def test_default_title_when_missing():
    md = "[Verse]\nsome line\n"
    song = Song.from_markdown(md, FAKE_PATH)
    assert song.title == "Untitled"


# ── to_markdown ────────────────────────────────────────────────────────────────

def test_markdown_starts_with_title():
    song = make_song("Cool Song")
    md = song.to_markdown()
    assert md.startswith("# Cool Song\n")


def test_markdown_contains_stage_directions():
    song = make_song()
    md = song.to_markdown()
    assert "[Section 0]" in md
    assert "[Section 1]" in md


def test_markdown_contains_lines():
    song = make_song()
    md = song.to_markdown()
    assert "Line 0-0" in md
    assert "Line 1-3" in md


def test_markdown_ends_with_newline():
    song = make_song()
    assert song.to_markdown().endswith("\n")


# ── round-trip ─────────────────────────────────────────────────────────────────

def test_round_trip_title():
    song = make_song("Round Trip")
    song2 = Song.from_markdown(song.to_markdown(), FAKE_PATH)
    assert song2.title == "Round Trip"


def test_round_trip_section_count():
    song = make_song(n_sections=3)
    song2 = Song.from_markdown(song.to_markdown(), FAKE_PATH)
    assert len(song2.sections) == 3


def test_round_trip_directions():
    song = make_song()
    song2 = Song.from_markdown(song.to_markdown(), FAKE_PATH)
    for orig, parsed in zip(song.sections, song2.sections):
        assert orig.direction == parsed.direction


def test_round_trip_line_text():
    song = make_song()
    song2 = Song.from_markdown(song.to_markdown(), FAKE_PATH)
    for orig_sec, parsed_sec in zip(song.sections, song2.sections):
        for orig_line, parsed_line in zip(orig_sec.lines, parsed_sec.lines):
            assert orig_line.text == parsed_line.text


# ── all_lines ──────────────────────────────────────────────────────────────────

def test_all_lines_flattens():
    song = make_song(n_sections=2)
    # 2 sections × 4 lines = 8 total
    assert len(song.all_lines()) == 8


def test_all_lines_order():
    song = make_song(n_sections=2)
    lines = song.all_lines()
    assert lines[0].text == "Line 0-0"
    assert lines[4].text == "Line 1-0"
