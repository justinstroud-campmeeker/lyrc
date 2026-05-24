from __future__ import annotations

import pyperclip

from lyrc.models.song import Section, Song


def song_to_plain_text(song: Song) -> str:
    """Produce Suno-compatible text (no title, sections separated by blank lines)."""
    parts: list[str] = []
    for section in song.sections:
        if section.direction:
            parts.append(f"[{section.direction}]")
        for line in section.lines:
            parts.append(line.text)
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def copy_song(song: Song) -> None:
    pyperclip.copy(song_to_plain_text(song))


def copy_section(section: Section) -> None:
    lines = "\n".join(line.text for line in section.lines)
    text = f"[{section.direction}]\n{lines}" if section.direction else lines
    pyperclip.copy(text)
