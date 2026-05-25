"""One collapsible song section."""
from __future__ import annotations

import copy

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget,
)

from lyrc.models.song import Section
from lyrc.widgets.line_editor import LineEditorWidget


class SectionWidget(QWidget):
    """Header (collapsible toggle) + stacked line editors."""

    # ── signals ────────────────────────────────────────────────────────────────
    line_text_changed = Signal(object, int, str)        # section, idx, text
    new_line_inserted = Signal(object, int, str, str)   # section, after_idx, before, after
    line_removed = Signal(object, int)                  # section, idx
    focus_crossed_top = Signal(object)                  # section
    focus_crossed_bottom = Signal(object)               # section
    open_bracket_in_line = Signal(object, object)       # section, line_widget
    thesaurus_requested = Signal(object, object, str, int, int)
    rhyme_requested = Signal(object, object, str, int, int)
    request_move_up = Signal(object)
    request_move_down = Signal(object)
    request_duplicate = Signal(object)
    request_copy = Signal(object)

    def __init__(self, section: Section, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._section = section
        self._building = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 4)
        outer.setSpacing(0)

        # ── header row ─────────────────────────────────────────────────────────
        header_row = QWidget()
        header_row.setObjectName("sectionHeaderRow")
        header_layout = QHBoxLayout(header_row)
        header_layout.setContentsMargins(4, 2, 4, 2)
        header_layout.setSpacing(4)

        self._collapse_btn = QPushButton("▼")
        self._collapse_btn.setObjectName("collapseBtn")
        self._collapse_btn.setFixedSize(20, 20)
        self._collapse_btn.setCheckable(True)
        self._collapse_btn.setChecked(not section.collapsed)
        self._collapse_btn.clicked.connect(self._toggle_collapse)
        header_layout.addWidget(self._collapse_btn)

        title_text = f"[{section.direction}]" if section.direction else "(intro)"
        self._title_label = QLabel(title_text)
        self._title_label.setObjectName("sectionTitle")
        header_layout.addWidget(self._title_label, 1)

        # action buttons
        for label, slot in [("↑", self._on_move_up), ("↓", self._on_move_down),
                             ("⎘", self._on_duplicate), ("⧉", self._on_copy)]:
            btn = QPushButton(label)
            btn.setObjectName("sectionActionBtn")
            btn.setFixedSize(22, 20)
            btn.clicked.connect(slot)
            header_layout.addWidget(btn)

        outer.addWidget(header_row)

        # ── content area ───────────────────────────────────────────────────────
        self._content = QWidget()
        self._content.setObjectName("sectionContent")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(8, 0, 0, 0)
        self._content_layout.setSpacing(0)
        outer.addWidget(self._content)

        # separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("sectionSep")
        outer.addWidget(sep)

        # populate lines
        self._building = True
        for line in section.lines:
            self._append_line_widget(line.text, line.rhyme_group)
        self._building = False

        # apply initial collapsed state
        self._content.setVisible(not section.collapsed)

    # ── public API ─────────────────────────────────────────────────────────────

    @property
    def section_model(self) -> Section:
        return self._section

    def line_widgets(self) -> list[LineEditorWidget]:
        result = []
        for i in range(self._content_layout.count()):
            item = self._content_layout.itemAt(i)
            if item and isinstance(item.widget(), LineEditorWidget):
                result.append(item.widget())
        return result

    def line_index(self, widget: LineEditorWidget) -> int:
        return self.line_widgets().index(widget)

    def focus_first_line(self) -> None:
        widgets = self.line_widgets()
        if widgets:
            widgets[0].focus_input()

    def focus_last_line(self) -> None:
        widgets = self.line_widgets()
        if widgets:
            widgets[-1].focus_input(cursor_end=True)

    def focus_line(self, index: int) -> None:
        widgets = self.line_widgets()
        if widgets:
            idx = max(0, min(index, len(widgets) - 1))
            widgets[idx].focus_input()

    def add_line_widget(self, text: str, rhyme_group: str, after_index: int) -> LineEditorWidget:
        lw = self._make_line_widget(text, rhyme_group)
        self._content_layout.insertWidget(after_index + 1, lw)
        return lw

    def remove_line_widget(self, index: int) -> None:
        widgets = self.line_widgets()
        if 0 <= index < len(widgets):
            w = widgets[index]
            self._content_layout.removeWidget(w)
            w.deleteLater()

    def update_line_rhyme(self, index: int, group: str) -> None:
        widgets = self.line_widgets()
        if 0 <= index < len(widgets):
            widgets[index].set_rhyme_group(group)

    def update_line_syllables(self, index: int, count: int) -> None:
        widgets = self.line_widgets()
        if 0 <= index < len(widgets):
            widgets[index].set_syllable_count(count)

    def get_line_value(self, index: int) -> str:
        widgets = self.line_widgets()
        if 0 <= index < len(widgets):
            return widgets[index].get_value()
        return ""

    def set_line_value(self, index: int, value: str) -> None:
        widgets = self.line_widgets()
        if 0 <= index < len(widgets):
            widgets[index].set_value(value)

    # ── private ────────────────────────────────────────────────────────────────

    def _append_line_widget(self, text: str, rhyme_group: str) -> LineEditorWidget:
        lw = self._make_line_widget(text, rhyme_group)
        self._content_layout.addWidget(lw)
        return lw

    def _make_line_widget(self, text: str, rhyme_group: str) -> LineEditorWidget:
        lw = LineEditorWidget(text=text, rhyme_group=rhyme_group, parent=self._content)
        lw.text_changed.connect(lambda t, w=lw: self._on_text_changed(w, t))
        lw.open_bracket.connect(lambda w=lw: self._on_open_bracket(w))
        lw.focus_prev.connect(lambda w=lw: self._on_focus_prev(w))
        lw.focus_next.connect(lambda w=lw: self._on_focus_next(w))
        lw.enter_pressed.connect(lambda before, after, w=lw: self._on_enter(w, before, after))
        lw.delete_line.connect(lambda w=lw: self._on_delete_line(w))
        lw.thesaurus_requested.connect(lambda word, s, e, w=lw: self._on_thesaurus(w, word, s, e))
        lw.rhyme_requested.connect(lambda word, s, e, w=lw: self._on_rhyme(w, word, s, e))
        return lw

    def _toggle_collapse(self, checked: bool) -> None:
        self._collapse_btn.setText("▼" if checked else "▶")
        self._content.setVisible(checked)
        self._section.collapsed = not checked

    def _on_text_changed(self, w: LineEditorWidget, text: str) -> None:
        if self._building:
            return
        idx = self.line_index(w)
        self.line_text_changed.emit(self, idx, text)

    def _on_open_bracket(self, w: LineEditorWidget) -> None:
        self.open_bracket_in_line.emit(self, w)

    def _on_focus_prev(self, w: LineEditorWidget) -> None:
        widgets = self.line_widgets()
        idx = self.line_index(w)
        if idx > 0:
            widgets[idx - 1].focus_input(cursor_end=True)
        else:
            self.focus_crossed_top.emit(self)

    def _on_focus_next(self, w: LineEditorWidget) -> None:
        widgets = self.line_widgets()
        idx = self.line_index(w)
        if idx < len(widgets) - 1:
            widgets[idx + 1].focus_input()
        else:
            self.focus_crossed_bottom.emit(self)

    def _on_enter(self, w: LineEditorWidget, before: str, after: str) -> None:
        idx = self.line_index(w)
        self.new_line_inserted.emit(self, idx, before, after)

    def _on_delete_line(self, w: LineEditorWidget) -> None:
        idx = self.line_index(w)
        self.line_removed.emit(self, idx)

    def _on_thesaurus(self, w: LineEditorWidget, word: str, start: int, end: int) -> None:
        self.thesaurus_requested.emit(self, w, word, start, end)

    def _on_rhyme(self, w: LineEditorWidget, word: str, start: int, end: int) -> None:
        self.rhyme_requested.emit(self, w, word, start, end)

    def _on_move_up(self) -> None:
        self.request_move_up.emit(self)

    def _on_move_down(self) -> None:
        self.request_move_down.emit(self)

    def _on_duplicate(self) -> None:
        self.request_duplicate.emit(self)

    def _on_copy(self) -> None:
        self.request_copy.emit(self)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        mods = event.modifiers()
        key = event.key()
        if mods == Qt.KeyboardModifier.ControlModifier:
            if key == Qt.Key.Key_Up:
                self.request_move_up.emit(self)
                return
            if key == Qt.Key.Key_Down:
                self.request_move_down.emit(self)
                return
            if key == Qt.Key.Key_D:
                self.request_duplicate.emit(self)
                return
            if key == Qt.Key.Key_W:
                self.request_copy.emit(self)
                return
        super().keyPressEvent(event)
