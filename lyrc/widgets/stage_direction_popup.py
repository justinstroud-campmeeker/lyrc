"""Stage-direction autocomplete popup (Qt replacement for Textual dropdown)."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QFrame, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

STAGE_DIRECTIONS = [
    "Verse 1", "Verse 2", "Verse 3", "Verse 4",
    "Chorus", "Pre-Chorus", "Post-Chorus",
    "Bridge", "Outro", "Intro", "Hook", "Refrain",
    "Interlude", "Break", "Drop", "Build",
]


class StageDirectionPopup(QFrame):
    """Floating popup for stage-direction completion."""

    direction_selected = Signal(str)
    dismissed = Signal()

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent, Qt.WindowType.Popup)
        self.setObjectName("stageDirectionPopup")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFixedWidth(200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        self._list = QListWidget()
        self._list.setObjectName("sdList")
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.itemActivated.connect(self._on_item_activated)
        layout.addWidget(self._list)

        self._all_items = list(STAGE_DIRECTIONS)

    # ── public API ─────────────────────────────────────────────────────────────

    def show_at(self, global_pos: QPoint, filter_text: str = "") -> None:
        self._filter(filter_text)
        if self._list.count() == 0:
            return
        self._list.setCurrentRow(0)
        self.adjustSize()
        self.move(global_pos)
        self.show()
        self._list.setFocus()

    def update_filter(self, text: str) -> None:
        self._filter(text)
        if self._list.count() > 0:
            self._list.setCurrentRow(0)
        else:
            self.close()
            self.dismissed.emit()

    # ── private ────────────────────────────────────────────────────────────────

    def _filter(self, text: str) -> None:
        self._list.clear()
        lower = text.lower()
        for direction in self._all_items:
            if lower in direction.lower():
                self._list.addItem(QListWidgetItem(direction))
        count = min(self._list.count(), 10)
        row_h = self._list.sizeHintForRow(0) if self._list.count() > 0 else 22
        self._list.setFixedHeight(count * row_h + 4)

    def _select_current(self) -> None:
        item = self._list.currentItem()
        if item:
            self.close()
            self.direction_selected.emit(item.text())

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab):
            self._select_current()
        elif key == Qt.Key.Key_Escape:
            self.close()
            self.dismissed.emit()
        else:
            super().keyPressEvent(event)

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        self.close()
        self.direction_selected.emit(item.text())

    def closeEvent(self, event) -> None:
        super().closeEvent(event)
