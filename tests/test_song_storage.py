"""Tests for song storage: save/load, slugify, atomic write."""
import pytest
from pathlib import Path

from lyrc.models.song import LyricLine, Section, Song
from lyrc.services.song_storage import load_song, save_song, slugify


def make_song(title: str = "Test Song") -> Song:
    return Song(
        title=title,
        sections=[
            Section(
                direction="Verse 1",
                lines=[
                    LyricLine(text="First line", line_index=0),
                    LyricLine(text="Second line", line_index=1),
                ],
                section_index=0,
            ),
            Section(
                direction="Chorus",
                lines=[
                    LyricLine(text="Chorus line", line_index=0),
                ],
                section_index=1,
            ),
        ],
    )


# ── slugify ────────────────────────────────────────────────────────────────────

def test_slugify_basic():
    assert slugify("My Song") == "my-song"


def test_slugify_strips_punctuation():
    assert slugify("Hello, World!") == "hello-world"


def test_slugify_multiple_spaces():
    assert slugify("Too  Many   Spaces") == "too-many-spaces"


def test_slugify_already_clean():
    assert slugify("simple") == "simple"


def test_slugify_empty_falls_back():
    assert slugify("!!!") == "untitled"


def test_slugify_numbers_preserved():
    assert slugify("Song 2") == "song-2"


# ── save / load round-trip ─────────────────────────────────────────────────────

def test_save_creates_file(tmp_path, monkeypatch):
    monkeypatch.setattr("lyrc.services.song_storage.SONGS_DIR", tmp_path)
    song = make_song()
    path = save_song(song)
    assert path.exists()


def test_save_assigns_file_path(tmp_path, monkeypatch):
    monkeypatch.setattr("lyrc.services.song_storage.SONGS_DIR", tmp_path)
    song = make_song()
    assert song.file_path is None
    save_song(song)
    assert song.file_path is not None


def test_save_uses_slug_filename(tmp_path, monkeypatch):
    monkeypatch.setattr("lyrc.services.song_storage.SONGS_DIR", tmp_path)
    song = make_song("My Cool Song")
    path = save_song(song)
    assert path.name == "my-cool-song.md"


def test_load_round_trip_title(tmp_path, monkeypatch):
    monkeypatch.setattr("lyrc.services.song_storage.SONGS_DIR", tmp_path)
    song = make_song("Round Trip")
    path = save_song(song)
    loaded = load_song(path)
    assert loaded.title == "Round Trip"


def test_load_round_trip_sections(tmp_path, monkeypatch):
    monkeypatch.setattr("lyrc.services.song_storage.SONGS_DIR", tmp_path)
    song = make_song()
    path = save_song(song)
    loaded = load_song(path)
    assert len(loaded.sections) == 2
    assert loaded.sections[0].direction == "Verse 1"
    assert loaded.sections[1].direction == "Chorus"


def test_load_round_trip_lines(tmp_path, monkeypatch):
    monkeypatch.setattr("lyrc.services.song_storage.SONGS_DIR", tmp_path)
    song = make_song()
    path = save_song(song)
    loaded = load_song(path)
    assert loaded.sections[0].lines[0].text == "First line"
    assert loaded.sections[0].lines[1].text == "Second line"


def test_save_overwrites_existing(tmp_path, monkeypatch):
    monkeypatch.setattr("lyrc.services.song_storage.SONGS_DIR", tmp_path)
    song = make_song()
    path = save_song(song)
    song.sections[0].lines[0].text = "Updated line"
    save_song(song)
    loaded = load_song(path)
    assert loaded.sections[0].lines[0].text == "Updated line"


def test_file_is_utf8(tmp_path, monkeypatch):
    monkeypatch.setattr("lyrc.services.song_storage.SONGS_DIR", tmp_path)
    song = make_song("Ünïcödé Sông")
    path = save_song(song)
    text = path.read_text(encoding="utf-8")
    assert "Ünïcödé" in text
