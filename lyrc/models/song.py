from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LyricLine:
    text: str
    line_index: int
    rhyme_group: str = ""
    syllable_count: int = 0


@dataclass
class Section:
    direction: str
    lines: list[LyricLine] = field(default_factory=list)
    collapsed: bool = False
    section_index: int = 0


@dataclass
class Song:
    title: str
    sections: list[Section] = field(default_factory=list)
    rhyme_scheme: str = "AABB"
    file_path: Path | None = None

    def all_lines(self) -> list[LyricLine]:
        result = []
        for section in self.sections:
            result.extend(section.lines)
        return result

    def to_markdown(self) -> str:
        parts = [f"# {self.title}", ""]
        for section in self.sections:
            if section.direction:
                parts.append(f"[{section.direction}]")
            for line in section.lines:
                parts.append(line.text)
            parts.append("")
        return "\n".join(parts).rstrip() + "\n"

    @classmethod
    def from_markdown(cls, text: str, path: Path) -> "Song":
        lines = text.splitlines()
        title = "Untitled"
        sections: list[Section] = []
        current_section: Section | None = None

        stage_re = re.compile(r"^\[([^\]]+)\]$")

        for raw_line in lines:
            if raw_line.startswith("# ") and title == "Untitled":
                title = raw_line[2:].strip()
                continue

            m = stage_re.match(raw_line.strip())
            if m:
                current_section = Section(direction=m.group(1))
                sections.append(current_section)
            else:
                # Skip blank lines before any section has started
                if current_section is None:
                    if raw_line.strip():
                        # Non-blank content before any stage direction → implicit section
                        current_section = Section(direction="")
                        sections.append(current_section)
                    else:
                        continue
                lyric = LyricLine(
                    text=raw_line,
                    line_index=len(current_section.lines),
                    rhyme_group="",
                )
                current_section.lines.append(lyric)

        # Strip trailing empty lines from each section (they are section separators)
        for s in sections:
            while s.lines and s.lines[-1].text.strip() == "":
                s.lines.pop()

        # Remove sections that have no lines and no direction
        sections = [s for s in sections if s.direction or s.lines]

        # Ensure every section has at least one (possibly empty) line
        for s in sections:
            if not s.lines:
                s.lines.append(LyricLine(text="", line_index=0, rhyme_group=""))

        song = cls(title=title, sections=sections, file_path=path)
        for i, s in enumerate(song.sections):
            s.section_index = i
        return song
