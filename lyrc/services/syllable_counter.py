from __future__ import annotations

import re

import pyphen

_cache: dict[str, int] = {}
_dic = pyphen.Pyphen(lang="en_US")


def count_syllables(word: str) -> int:
    w = word.strip().lower()
    if not w:
        return 0
    if w in _cache:
        return _cache[w]
    hyphenated = _dic.inserted(w)
    count = hyphenated.count("-") + 1
    _cache[w] = count
    return count


def count_line_syllables(line: str) -> int:
    words = re.findall(r"[a-zA-Z']+", line)
    return sum(count_syllables(w) for w in words)
