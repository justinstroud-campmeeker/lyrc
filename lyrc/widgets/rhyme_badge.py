"""Small coloured label showing a rhyme-group letter."""
from __future__ import annotations

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt

_COLORS: dict[str, str] = {
    "A": "#e06c75",
    "B": "#61afef",
    "C": "#98c379",
    "D": "#c678dd",
    "E": "#e5c07b",
    "F": "#56b6c2",
}


class RhymeBadge(QLabel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedWidth(22)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._set_style("")

    def set_group(self, group: str) -> None:
        self.setText(group)
        self._set_style(group)

    def _set_style(self, group: str) -> None:
        if group and group in _COLORS:
            color = _COLORS[group]
            self.setStyleSheet(
                f"background: {color}; color: #1e2127; border-radius: 3px; "
                f"font-weight: bold; font-size: 11px;"
            )
        else:
            self.setStyleSheet("background: transparent;")
            self.setText("")
