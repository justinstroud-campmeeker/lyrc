"""Main window and application entry-point."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QPushButton, QSplitter, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from lyrc.models.song import LyricLine, Section, Song
from lyrc.services.song_storage import SONGS_DIR, ensure_songs_dir, load_song, save_song
from lyrc.widgets.song_browser import SongBrowserPanel
from lyrc.widgets.song_editor import SongEditorWidget


class NewSongDialog(QDialog):
    """Simple modal for entering a new song title."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("newSongDialog")
        self.setWindowTitle("New Song")
        self.setModal(True)
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        layout.addWidget(QLabel("Song title:"))

        self._input = QLineEdit()
        self._input.setPlaceholderText("My Song")
        self._input.returnPressed.connect(self._accept_if_valid)
        layout.addWidget(self._input)

        buttons = QHBoxLayout()
        buttons.addStretch()

        self._ok_btn = QPushButton("Create")
        self._ok_btn.setObjectName("okBtn")
        self._ok_btn.clicked.connect(self._accept_if_valid)
        buttons.addWidget(self._ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        layout.addLayout(buttons)

    def title(self) -> str:
        return self._input.text().strip()

    def _accept_if_valid(self) -> None:
        if self.title():
            self.accept()


_SHORTCUTS = [
    ("General",        "F1",           "Show this help screen"),
    ("General",        "Ctrl+N",       "New song"),
    ("General",        "Ctrl+S",       "Save current song"),
    ("General",        "Ctrl+Y",       "Copy entire song to clipboard"),
    ("General",        "Ctrl+B",       "Toggle song browser"),
    ("General",        "Ctrl+Q",       "Quit"),
    ("Editing",        "Enter",        "Split line / insert new line below"),
    ("Editing",        "Backspace",    "Delete line when it is empty"),
    ("Editing",        "↑ / ↓",        "Move cursor between lines"),
    ("Editing",        "[",            "Open stage-direction popup"),
    ("Editing",        "Tab / Enter",  "Confirm selection in popup"),
    ("Editing",        "Escape",       "Dismiss popup"),
    ("Word tools",     "Ctrl+T",       "Thesaurus — synonyms for word at cursor"),
    ("Word tools",     "Ctrl+R",       "Rhyme finder for word at cursor"),
    ("Sections",       "↑ button",     "Move section up"),
    ("Sections",       "↓ button",     "Move section down"),
    ("Sections",       "⎘ button",     "Duplicate section"),
    ("Sections",       "⧉ button",     "Copy section to clipboard"),
    ("Sections",       "▼ / ▶ button", "Collapse / expand section"),
]


class HelpDialog(QDialog):
    """Keyboard shortcut reference — opened with F1."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("helpDialog")
        self.setWindowTitle("Keyboard Shortcuts")
        self.setModal(True)
        self.setMinimumWidth(520)
        self.setMinimumHeight(460)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        heading = QLabel("Lyrc — Keyboard Shortcuts")
        heading.setObjectName("helpHeading")
        layout.addWidget(heading)

        table = QTableWidget(len(_SHORTCUTS), 3)
        table.setObjectName("helpTable")
        table.setHorizontalHeaderLabels(["Group", "Shortcut", "Description"])
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setShowGrid(False)
        table.setAlternatingRowColors(True)

        for row, (group, shortcut, description) in enumerate(_SHORTCUTS):
            for col, text in enumerate((group, shortcut, description)):
                item = QTableWidgetItem(text)
                if col == 1:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
                    )
                table.setItem(row, col, item)

        table.resizeColumnToContents(0)
        table.resizeColumnToContents(1)
        layout.addWidget(table)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("okBtn")
        close_btn.clicked.connect(self.accept)
        row_layout = QHBoxLayout()
        row_layout.addStretch()
        row_layout.addWidget(close_btn)
        layout.addLayout(row_layout)

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_F1):
            self.accept()
        else:
            super().keyPressEvent(event)


class LyrcMainWindow(QMainWindow):
    """Top-level application window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Lyrc")
        self.resize(1000, 700)

        ensure_songs_dir()

        # ── central splitter ───────────────────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("mainSplitter")

        self._browser = SongBrowserPanel()
        self._browser.song_selected.connect(self._open_song)
        self._browser.new_song_requested.connect(self._new_song)
        splitter.addWidget(self._browser)

        self._editor = SongEditorWidget()
        splitter.addWidget(self._editor)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([200, 800])

        self.setCentralWidget(splitter)
        self.statusBar().showMessage("Ready")

        # ── menu / shortcuts ───────────────────────────────────────────────────
        self._setup_actions()

    def _setup_actions(self) -> None:
        file_menu = self.menuBar().addMenu("&File")

        new_action = QAction("&New Song", self)
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        new_action.triggered.connect(self._new_song)
        file_menu.addAction(new_action)

        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self._editor.action_save)
        file_menu.addAction(save_action)

        copy_action = QAction("&Copy All", self)
        copy_action.setShortcut(QKeySequence("Ctrl+Y"))
        copy_action.triggered.connect(self._editor.action_copy_all)
        file_menu.addAction(copy_action)

        file_menu.addSeparator()

        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        view_menu = self.menuBar().addMenu("&View")
        toggle_browser = QAction("Toggle &Browser", self)
        toggle_browser.setShortcut(QKeySequence("Ctrl+B"))
        toggle_browser.triggered.connect(self._toggle_browser)
        view_menu.addAction(toggle_browser)

        help_menu = self.menuBar().addMenu("&Help")
        help_action = QAction("&Keyboard Shortcuts", self)
        help_action.setShortcut(QKeySequence("F1"))
        help_action.triggered.connect(self._show_help)
        help_menu.addAction(help_action)

    def _open_song(self, path: Path) -> None:
        try:
            song = load_song(path)
            self._editor.load_song(song)
            self.statusBar().showMessage(f"Opened: {path.stem}")
        except Exception as exc:
            self.statusBar().showMessage(f"Error opening song: {exc}")

    def _new_song(self) -> None:
        dlg = NewSongDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            title = dlg.title()
            if title:
                self._create_song(title)

    def _create_song(self, title: str) -> None:
        song = Song(
            title=title,
            sections=[
                Section(
                    direction="Verse 1",
                    lines=[LyricLine(text="", line_index=0, rhyme_group="")],
                    section_index=0,
                )
            ],
        )
        save_song(song)
        self._editor.load_song(song)
        self._browser.refresh_list()
        self.statusBar().showMessage(f"Created: {title}")

    def _toggle_browser(self) -> None:
        self._browser.setVisible(not self._browser.isVisible())

    def _show_help(self) -> None:
        HelpDialog(self).exec()
