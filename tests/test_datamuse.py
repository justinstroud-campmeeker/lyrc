"""Tests for the Datamuse service — exercises caching and result shape.
Network calls are mocked so tests run offline.
"""
import pytest
from unittest.mock import patch, MagicMock

import lyrc.services.datamuse as dm


def _mock_response(words: list[str]):
    resp = MagicMock()
    resp.json.return_value = [{"word": w, "score": 100} for w in words]
    resp.raise_for_status.return_value = None
    return resp


@pytest.fixture(autouse=True)
def clear_cache():
    dm._cache.clear()
    yield
    dm._cache.clear()


# ── fetch_synonyms ─────────────────────────────────────────────────────────────

def test_synonyms_returns_words():
    with patch("lyrc.services.datamuse.requests.get") as mock_get:
        mock_get.return_value = _mock_response(["happy", "glad", "joyful"])
        result = dm.fetch_synonyms("cheerful")
    assert result == ["happy", "glad", "joyful"]


def test_synonyms_capped_at_15():
    words = [f"word{i}" for i in range(30)]
    with patch("lyrc.services.datamuse.requests.get") as mock_get:
        mock_get.return_value = _mock_response(words)
        result = dm.fetch_synonyms("test")
    assert len(result) == 15


def test_synonyms_cached_on_second_call():
    with patch("lyrc.services.datamuse.requests.get") as mock_get:
        mock_get.return_value = _mock_response(["bright"])
        dm.fetch_synonyms("light")
        dm.fetch_synonyms("light")
    assert mock_get.call_count == 1


def test_synonyms_empty_on_error():
    with patch("lyrc.services.datamuse.requests.get", side_effect=Exception("timeout")):
        result = dm.fetch_synonyms("oops")
    assert result == []


def test_synonyms_lowercase_word_used():
    with patch("lyrc.services.datamuse.requests.get") as mock_get:
        mock_get.return_value = _mock_response(["hello"])
        dm.fetch_synonyms("Hello")
    call_params = mock_get.call_args[1]["params"]
    assert call_params["rel_syn"] == "hello"


# ── fetch_rhymes ───────────────────────────────────────────────────────────────

def test_rhymes_returns_words():
    with patch("lyrc.services.datamuse.requests.get") as mock_get:
        mock_get.return_value = _mock_response(["fire", "hire", "wire"])
        result = dm.fetch_rhymes("desire")
    assert result == ["fire", "hire", "wire"]


def test_rhymes_falls_back_to_near_rhymes_when_empty():
    responses = [_mock_response([]), _mock_response(["blaze", "haze"])]
    with patch("lyrc.services.datamuse.requests.get", side_effect=responses):
        result = dm.fetch_rhymes("orange")
    assert result == ["blaze", "haze"]


def test_rhymes_cached():
    with patch("lyrc.services.datamuse.requests.get") as mock_get:
        mock_get.return_value = _mock_response(["moon"])
        dm.fetch_rhymes("june")
        dm.fetch_rhymes("june")
    assert mock_get.call_count == 1


def test_rhymes_empty_on_error():
    with patch("lyrc.services.datamuse.requests.get", side_effect=Exception("err")):
        result = dm.fetch_rhymes("xyz")
    assert result == []


def test_rhymes_capped_at_15():
    words = [f"w{i}" for i in range(25)]
    with patch("lyrc.services.datamuse.requests.get") as mock_get:
        mock_get.return_value = _mock_response(words)
        result = dm.fetch_rhymes("test")
    assert len(result) == 15
