"""Left-panel song browser widget."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget,
)

from lyrc.services.song_storage import list_songs


class SongBrowserPanel(QWidget):
    """Sidebar listing all songs with a New Song button."""

    song_selected = Signal(Path)
    new_song_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("songBrowser")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        title = QLabel("Songs")
        title.setObjectName("browserTitle")
        layout.addWidget(title)

        self._list = QListWidget()
        self._list.setObjectName("songList")
        self._list.itemActivated.connect(self._on_item_activated)
        layout.addWidget(self._list, 1)

        new_btn = QPushButton("+ New Song")
        new_btn.setObjectName("newSongBtn")
        new_btn.clicked.connect(self.new_song_requested)
        layout.addWidget(new_btn)

        self.refresh_list()

    # ── public API ─────────────────────────────────────────────────────────────

    def refresh_list(self) -> None:
        self._list.clear()
        for path in list_songs():
            item = QListWidgetItem(path.stem)
            item.setData(Qt.ItemDataRole.UserRole, path)
            self._list.addItem(item)

    # ── private ────────────────────────────────────────────────────────────────

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        path: Path | None = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.song_selected.emit(path)


