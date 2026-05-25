"""Word suggestion popup (thesaurus / rhyme) — Qt replacement."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QFrame, QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget,
)


class WordSuggestionPopup(QFrame):
    """Floating popup listing synonym or rhyme suggestions."""

    word_selected = Signal(str)
    dismissed = Signal()

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent, Qt.WindowType.Popup)
        self.setObjectName("wordSuggestionPopup")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFixedWidth(240)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        self._title_label = QLabel()
        self._title_label.setObjectName("wspTitle")
        layout.addWidget(self._title_label)

        self._list = QListWidget()
        self._list.setObjectName("wspList")
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.itemActivated.connect(self._on_item_activated)
        layout.addWidget(self._list)

        self._loading_label = QLabel("Loading…")
        self._loading_label.setObjectName("wspLoading")
        self._loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._loading_label)

    # ── public API ─────────────────────────────────────────────────────────────

    def show_loading(self, title: str, global_pos: QPoint) -> None:
        self._title_label.setText(title)
        self._list.clear()
        self._list.hide()
        self._loading_label.show()
        self.adjustSize()
        self.move(global_pos)
        self.show()

    def set_results(self, words: list[str]) -> None:
        self._loading_label.hide()
        self._list.clear()
        for w in words:
            self._list.addItem(QListWidgetItem(w))
        count = min(self._list.count(), 12)
        row_h = self._list.sizeHintForRow(0) if self._list.count() > 0 else 22
        self._list.setFixedHeight(count * row_h + 4)
        self._list.show()
        if self._list.count() > 0:
            self._list.setCurrentRow(0)
            self._list.setFocus()
        self.adjustSize()

    # ── private ────────────────────────────────────────────────────────────────

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        self.close()
        self.word_selected.emit(item.text())

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab):
            item = self._list.currentItem()
            if item:
                self.close()
                self.word_selected.emit(item.text())
        elif key == Qt.Key.Key_Escape:
            self.close()
            self.dismissed.emit()
        else:
            super().keyPressEvent(event)
