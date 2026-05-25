"""Single editable lyric line with syllable gutter and rhyme badge."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QWidget

from lyrc.services.syllable_counter import count_line_syllables
from lyrc.services.text_utils import word_at_cursor
from lyrc.widgets.rhyme_badge import RhymeBadge


class _LineEdit(QLineEdit):
    """QLineEdit that emits extra signals for navigation keys."""

    open_bracket = Signal()
    focus_prev = Signal()
    focus_next = Signal()
    enter_pressed = Signal(str, str)   # text_before, text_after
    delete_line = Signal()
    thesaurus_requested = Signal(str, int, int)
    rhyme_requested = Signal(str, int, int)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        mods = event.modifiers()

        if mods == Qt.KeyboardModifier.ControlModifier:
            if key == Qt.Key.Key_T:
                result = word_at_cursor(self.text(), self.cursorPosition())
                if result:
                    word, start, end = result
                    self.thesaurus_requested.emit(word, start, end)
                return
            if key == Qt.Key.Key_R:
                result = word_at_cursor(self.text(), self.cursorPosition())
                if result:
                    word, start, end = result
                    self.rhyme_requested.emit(word, start, end)
                return

        if key == Qt.Key.Key_Up and self.cursorPosition() == 0:
            self.focus_prev.emit()
            return
        if key == Qt.Key.Key_Down and self.cursorPosition() == len(self.text()):
            self.focus_next.emit()
            return
        if key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            pos = self.cursorPosition()
            val = self.text()
            self.enter_pressed.emit(val[:pos], val[pos:])
            return
        if key == Qt.Key.Key_Backspace and self.text() == "":
            self.delete_line.emit()
            return

        super().keyPressEvent(event)

        # detect '[' after the default handler so self.text() is updated
        if key == Qt.Key.Key_BracketLeft:
            self.open_bracket.emit()


class LineEditorWidget(QWidget):
    """One lyric line: [syllable count | input field | rhyme badge]."""

    text_changed = Signal(str)
    open_bracket = Signal()
    focus_prev = Signal()
    focus_next = Signal()
    enter_pressed = Signal(str, str)
    delete_line = Signal()
    thesaurus_requested = Signal(str, int, int)
    rhyme_requested = Signal(str, int, int)

    def __init__(self, text: str = "", rhyme_group: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._suppress_change = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._syl_label = QLabel("·")
        self._syl_label.setFixedWidth(28)
        self._syl_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._syl_label.setObjectName("syllableCount")

        self._edit = _LineEdit()
        self._edit.setText(text)
        self._edit.setObjectName("lineEdit")

        self._badge = RhymeBadge()

        layout.addWidget(self._syl_label)
        layout.addWidget(self._edit, 1)
        layout.addWidget(self._badge)

        # wire internal signals
        self._edit.textChanged.connect(self._on_text_changed)
        self._edit.open_bracket.connect(self.open_bracket)
        self._edit.focus_prev.connect(self.focus_prev)
        self._edit.focus_next.connect(self.focus_next)
        self._edit.enter_pressed.connect(self.enter_pressed)
        self._edit.delete_line.connect(self.delete_line)
        self._edit.thesaurus_requested.connect(self.thesaurus_requested)
        self._edit.rhyme_requested.connect(self.rhyme_requested)

        # initialise counts
        self._update_syllable_label(text)
        self.set_rhyme_group(rhyme_group)

    # ── slots ──────────────────────────────────────────────────────────────────

    def _on_text_changed(self, value: str) -> None:
        if self._suppress_change:
            return
        self._update_syllable_label(value)
        self.text_changed.emit(value)

    def _update_syllable_label(self, text: str) -> None:
        count = count_line_syllables(text)
        self._syl_label.setText(str(count) if count else "·")

    # ── public API ─────────────────────────────────────────────────────────────

    def get_value(self) -> str:
        return self._edit.text()

    def set_value(self, value: str) -> None:
        self._suppress_change = True
        self._edit.setText(value)
        self._update_syllable_label(value)
        self._suppress_change = False

    def set_rhyme_group(self, group: str) -> None:
        self._badge.set_group(group)

    def set_syllable_count(self, count: int) -> None:
        self._syl_label.setText(str(count) if count else "·")

    def focus_input(self, cursor_end: bool = False) -> None:
        self._edit.setFocus()
        if cursor_end:
            self._edit.setCursorPosition(len(self._edit.text()))

    def cursor_position(self) -> int:
        return self._edit.cursorPosition()

    def replace_word(self, start: int, end: int, replacement: str) -> None:
        text = self._edit.text()
        new_text = text[:start] + replacement + text[end:]
        self._suppress_change = True
        self._edit.setText(new_text)
        self._edit.setCursorPosition(start + len(replacement))
        self._suppress_change = False
        self._update_syllable_label(new_text)
        self.text_changed.emit(new_text)
