# Lyrc

A cross-platform desktop application for writing song lyrics, designed to pair with AI music generation tools like [Suno](https://suno.com).

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![PySide6](https://img.shields.io/badge/PySide6-6.6%2B-green)
![Tests](https://img.shields.io/badge/tests-93%20passing-brightgreen)

---

## Features

- **Per-line syllable counts** shown in the gutter as you type
- **Rhyme scheme badges** — colour-coded letters (A/B/C…) mark which lines rhyme, based on a configurable scheme (default: AABB)
- **Stage direction autocomplete** — type `[` to open an intellisense-style popup (Chorus, Bridge, Verse, etc.)
- **Collapsible sections** — each stage direction is its own collapsible block
- **Section management** — reorder, duplicate, or copy sections with one click
- **Thesaurus & rhyme finder** — press `Ctrl+T` or `Ctrl+R` on any word for instant suggestions (powered by [Datamuse](https://www.datamuse.com/api/))
- **Clipboard copy** — copy the whole song or a single section formatted for pasting
- **Song browser** — sidebar listing all saved songs; click to open
- **Markdown storage** — songs are plain `.md` files you can edit anywhere
- **Dark theme** throughout

---

## Installation

### Prerequisites

- Python 3.11 or newer
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/your-username/lyrc.git
cd lyrc

# 2. Create and activate a virtual environment (recommended)
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -e ".[dev]"
```

> **Note:** PySide6 is a large package (~170 MB). The first install will take a minute.

### Running

```bash
python main.py
```

Or, if you used `pip install -e .`:

```bash
lyrc
```

---

## Usage

### Creating a song

Press **Ctrl+N** (or **File → New Song**), enter a title, and hit **Create**. A new song opens in the editor with a single "Verse 1" section ready to type in.

### Writing lyrics

Type normally in any line. Each line shows its syllable count on the left and a rhyme-group badge on the right.

Press **Enter** to split the current line and insert a new one below.  
Press **Backspace** on an empty line to delete it.  
Use **↑ / ↓** to move between lines (and between sections).

### Stage directions

Type `[` anywhere in a line to open the autocomplete popup. Keep typing to filter, then press **Enter**, **Tab**, or click to select. A new section is inserted with the chosen direction as its header.

### Thesaurus & rhymes

Place the cursor on (or next to) any word, then:

| Shortcut | Action |
|----------|--------|
| `Ctrl+T` | Synonyms for the word |
| `Ctrl+R` | Rhymes for the word |

A popup appears with up to 15 suggestions. Press **Enter** / **Tab** or click to replace the word.

### Importing existing lyrics

Drop a Markdown file into the `songs/` folder (created automatically next to `main.py`). The format is:

```markdown
# Song Title

[Verse 1]
First line of verse
Second line of verse

[Chorus]
Chorus line one
Chorus line two
```

The song will appear in the browser immediately on the next launch (or after saving any song in the current session).

### Keyboard shortcuts

Press **F1** (or **Help → Keyboard Shortcuts**) for the full reference. Quick summary:

| Shortcut | Action |
|----------|--------|
| `F1` | Keyboard shortcut help |
| `Ctrl+N` | New song |
| `Ctrl+S` | Save |
| `Ctrl+Y` | Copy entire song to clipboard |
| `Ctrl+B` | Toggle song browser |
| `Ctrl+Q` | Quit |
| `Enter` | Insert new line / split line |
| `Backspace` | Delete empty line |
| `[` | Open stage-direction popup |
| `Ctrl+T` | Thesaurus (synonyms) |
| `Ctrl+R` | Rhyme finder |

---

## Project structure

```
lyrc/
├── models/
│   ├── song.py              # Song, Section, LyricLine dataclasses + markdown I/O
│   └── rhyme_scheme.py      # Assigns A/B/C rhyme groups to lines
├── services/
│   ├── clipboard.py         # Copy song / section to system clipboard
│   ├── datamuse.py          # Datamuse API client (synonyms + rhymes, cached)
│   ├── song_storage.py      # Save / load / list songs from the songs/ directory
│   ├── syllable_counter.py  # pyphen-based syllable counting with cache
│   └── text_utils.py        # Framework-agnostic word-at-cursor helper
├── styles/
│   └── dark.qss             # Qt stylesheet (dark theme)
├── widgets/
│   ├── line_editor.py       # Single lyric line (syllable label + QLineEdit + badge)
│   ├── rhyme_badge.py       # Coloured rhyme-group label
│   ├── section_widget.py    # Collapsible section with header buttons
│   ├── song_browser.py      # Left-panel song list
│   ├── song_editor.py       # Main editing surface (scroll area of sections)
│   ├── stage_direction_popup.py  # Floating autocomplete popup
│   └── word_suggestion_popup.py  # Thesaurus / rhyme suggestions popup
├── workers/
│   └── datamuse_worker.py   # QRunnable worker for async Datamuse calls
└── app.py                   # QMainWindow, NewSongDialog, HelpDialog
main.py                      # Entry point
tests/                       # 93 pytest tests
songs/                       # Your saved songs (created on first run)
```

---

## Tech stack

| Component | Library |
|-----------|---------|
| UI framework | [PySide6](https://doc.qt.io/qtforpython/) (Qt 6) |
| Syllable counting | [pyphen](https://pyphen.org/) |
| Rhymes & synonyms | [Datamuse API](https://www.datamuse.com/api/) via [requests](https://requests.readthedocs.io/) |
| Clipboard | [pyperclip](https://pyperclip.readthedocs.io/) |
| Testing | [pytest](https://pytest.org/) |

---

## Rhyme schemes

The default scheme is **AABB** (pairs of rhyming lines). The scheme can be changed per-song in the model. Supported schemes:

| Scheme | Pattern | Example |
|--------|---------|---------|
| AABB | AA BB | fire / hire, moon / tune |
| ABAB | Alternating | fire / moon, hire / tune |
| ABBA | Enclosed | fire / moon, moon / fire |
| ABCB | Ballad | x / moon, x / tune |
| AAAA | Monorhyme | all lines rhyme |
| FREE | None | no grouping |

---

## Development

```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v
```

Songs are stored as UTF-8 Markdown files in `songs/` with atomic writes (write to temp file, then rename) to prevent corruption.
