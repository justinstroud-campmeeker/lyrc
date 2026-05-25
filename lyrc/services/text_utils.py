"""Framework-agnostic text helpers."""
from __future__ import annotations


def word_at_cursor(text: str, pos: int) -> tuple[str, int, int] | None:
    """Return (word, start, end) for the word touching *pos*, or None.

    Word characters are letters and apostrophes (contractions).
    """
    start = pos
    while start > 0 and (text[start - 1].isalpha() or text[start - 1] == "'"):
        start -= 1
    end = pos
    while end < len(text) and (text[end].isalpha() or text[end] == "'"):
        end += 1
    if start == end:
        return None
    return text[start:end], start, end
