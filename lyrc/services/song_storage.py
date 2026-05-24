from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

from lyrc.models.song import Song

SONGS_DIR = Path(__file__).parent.parent.parent / "songs"


def ensure_songs_dir() -> None:
    SONGS_DIR.mkdir(parents=True, exist_ok=True)


def list_songs() -> list[Path]:
    ensure_songs_dir()
    return sorted(SONGS_DIR.glob("*.md"))


def load_song(path: Path) -> Song:
    text = path.read_text(encoding="utf-8")
    return Song.from_markdown(text, path)


def save_song(song: Song) -> Path:
    ensure_songs_dir()
    if song.file_path is None:
        slug = slugify(song.title)
        song.file_path = SONGS_DIR / f"{slug}.md"
    content = song.to_markdown()
    # Atomic write
    fd, tmp = tempfile.mkstemp(dir=song.file_path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, song.file_path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return song.file_path


def slugify(title: str) -> str:
    s = title.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "untitled"
