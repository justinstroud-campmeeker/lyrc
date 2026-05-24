from __future__ import annotations

from lyrc.models.song import LyricLine

SCHEMES: dict[str, str] = {
    "AABB": "AABB",
    "ABAB": "ABAB",
    "ABBA": "ABBA",
    "AAAA": "AAAA",
    "ABCB": "ABCB",
    "FREE": "",
}


def assign_rhyme_groups(lines: list[LyricLine], scheme: str) -> None:
    """Mutate each LyricLine.rhyme_group in-place based on the repeating pattern."""
    pattern = SCHEMES.get(scheme, "")
    if not pattern:
        for line in lines:
            line.rhyme_group = ""
        return
    for i, line in enumerate(lines):
        line.rhyme_group = pattern[i % len(pattern)]
