from __future__ import annotations

import requests

_cache: dict[tuple[str, str], list[str]] = {}
_BASE = "https://api.datamuse.com/words"
_MAX = 15


def fetch_synonyms(word: str) -> list[str]:
    key = (word.lower(), "rel_syn")
    if key in _cache:
        return _cache[key]
    try:
        resp = requests.get(_BASE, params={"rel_syn": word.lower()}, timeout=5)
        resp.raise_for_status()
        result = [item["word"] for item in resp.json()][:_MAX]
    except Exception:
        result = []
    _cache[key] = result
    return result


def fetch_rhymes(word: str) -> list[str]:
    key = (word.lower(), "rel_rhy")
    if key in _cache:
        return _cache[key]
    try:
        resp = requests.get(_BASE, params={"rel_rhy": word.lower()}, timeout=5)
        resp.raise_for_status()
        result = [item["word"] for item in resp.json()][:_MAX]
        if not result:
            resp2 = requests.get(_BASE, params={"rel_nry": word.lower()}, timeout=5)
            resp2.raise_for_status()
            result = [item["word"] for item in resp2.json()][:_MAX]
    except Exception:
        result = []
    _cache[key] = result
    return result
