from __future__ import annotations

from textual.app import ComposeResult
from textual.geometry import Offset
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Collapsible

from lyrc.models.song import Section
from lyrc.widgets.line_editor import LyricLineWidget


class SectionWidget(Widget):
    """One song section with a collapsible header and editable lines."""

    BINDINGS = [
        ("ctrl+up",   "move_up",    "Move section up"),
        ("ctrl+down", "move_down",  "Move section down"),
        ("ctrl+d",    "duplicate",  "Duplicate section"),
        ("ctrl+w",    "copy_sec",   "Copy section"),
    ]

    # ── Messages ─────────────────────────────────────────────────────────────

    class LineTextChanged(Message):
        def __init__(self, section: "SectionWidget", line_index: int, text: str) -> None:
            super().__init__()
            self.section = section
            self.line_index = line_index
            self.text = text

    class NewLineInserted(Message):
        def __init__(
            self,
            section: "SectionWidget",
            after_line_index: int,
            text_before: str,
            text_after: str,
        ) -> None:
            super().__init__()
            self.section = section
            self.after_line_index = after_line_index
            self.text_before = text_before
            self.text_after = text_after

    class LineRemoved(Message):
        def __init__(self, section: "SectionWidget", line_index: int) -> None:
            super().__init__()
            self.section = section
            self.line_index = line_index

    class RequestMoveUp(Message):
        def __init__(self, section: "SectionWidget") -> None:
            super().__init__()
            self.section = section

    class RequestMoveDown(Message):
        def __init__(self, section: "SectionWidget") -> None:
            super().__init__()
            self.section = section

    class RequestDuplicate(Message):
        def __init__(self, section: "SectionWidget") -> None:
            super().__init__()
            self.section = section

    class RequestCopy(Message):
        def __init__(self, section: "SectionWidget") -> None:
            super().__init__()
            self.section = section

    class OpenBracketInLine(Message):
        def __init__(
            self,
            section: "SectionWidget",
            line_widget: LyricLineWidget,
            offset: Offset,
        ) -> None:
            super().__init__()
            self.section = section
            self.line_widget = line_widget
            self.offset = offset

    class FocusCrossedTop(Message):
        """Focus moved above the first line — caller should focus previous section."""
        def __init__(self, section: "SectionWidget") -> None:
            super().__init__()
            self.section = section

    class FocusCrossedBottom(Message):
        """Focus moved below the last line — caller should focus next section."""
        def __init__(self, section: "SectionWidget") -> None:
            super().__init__()
            self.section = section

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def __init__(self, section: Section, **kwargs) -> None:
        super().__init__(**kwargs)
        self._section = section

    @property
    def section_model(self) -> Section:
        return self._section

    def compose(self) -> ComposeResult:
        title = f"[{self._section.direction}]" if self._section.direction else "(intro)"
        with Collapsible(title=title, collapsed=self._section.collapsed, id="collapsible"):
            for i, line in enumerate(self._section.lines):
                yield LyricLineWidget(
                    text=line.text,
                    rhyme_group=line.rhyme_group,
                    id=f"lyric-{self._section.section_index}-{i}",
                    classes="lyric-line",
                )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _line_widgets(self) -> list[LyricLineWidget]:
        return list(self.query(LyricLineWidget))

    def _line_index(self, widget: LyricLineWidget) -> int:
        return self._line_widgets().index(widget)

    # ── LyricLineWidget event handlers ────────────────────────────────────────

    def on_lyric_line_widget_text_changed(self, event: LyricLineWidget.TextChanged) -> None:
        event.stop()
        idx = self._line_index(event.widget)
        self.post_message(self.LineTextChanged(self, idx, event.new_text))

    def on_lyric_line_widget_open_bracket_typed(self, event: LyricLineWidget.OpenBracketTyped) -> None:
        event.stop()
        self.post_message(self.OpenBracketInLine(self, event.widget, event.cursor_offset))

    def on_lyric_line_widget_new_line_requested(self, event: LyricLineWidget.NewLineRequested) -> None:
        event.stop()
        idx = self._line_index(event.widget)
        self.post_message(self.NewLineInserted(self, idx, event.text_before, event.text_after))

    def on_lyric_line_widget_line_deleted(self, event: LyricLineWidget.LineDeleted) -> None:
        event.stop()
        idx = self._line_index(event.widget)
        self.post_message(self.LineRemoved(self, idx))

    def on_lyric_line_widget_focus_next(self, event: LyricLineWidget.FocusNext) -> None:
        event.stop()
        widgets = self._line_widgets()
        idx = self._line_index(event.widget)
        if idx < len(widgets) - 1:
            widgets[idx + 1].focus_input()
        else:
            self.post_message(self.FocusCrossedBottom(self))

    def on_lyric_line_widget_focus_prev(self, event: LyricLineWidget.FocusPrev) -> None:
        event.stop()
        widgets = self._line_widgets()
        idx = self._line_index(event.widget)
        if idx > 0:
            widgets[idx - 1].focus_input(cursor_end=True)
        else:
            self.post_message(self.FocusCrossedTop(self))

    # ── Actions ───────────────────────────────────────────────────────────────

    def action_move_up(self) -> None:
        self.post_message(self.RequestMoveUp(self))

    def action_move_down(self) -> None:
        self.post_message(self.RequestMoveDown(self))

    def action_duplicate(self) -> None:
        self.post_message(self.RequestDuplicate(self))

    def action_copy_sec(self) -> None:
        self.post_message(self.RequestCopy(self))

    # ── Public API ────────────────────────────────────────────────────────────

    def focus_first_line(self) -> None:
        widgets = self._line_widgets()
        if widgets:
            widgets[0].focus_input()

    def focus_last_line(self) -> None:
        widgets = self._line_widgets()
        if widgets:
            widgets[-1].focus_input(cursor_end=True)

    def focus_line(self, index: int) -> None:
        widgets = self._line_widgets()
        if widgets:
            idx = max(0, min(index, len(widgets) - 1))
            widgets[idx].focus_input()

    def add_line_widget(self, text: str, rhyme_group: str, after_index: int, line_model_index: int) -> LyricLineWidget:
        """Mount a new LyricLineWidget after the given index and return it."""
        widgets = self._line_widgets()
        collapsible = self.query_one(Collapsible)
        new_widget = LyricLineWidget(
            text=text,
            rhyme_group=rhyme_group,
            id=f"lyric-{self._section.section_index}-new-{id(text)}",
            classes="lyric-line",
        )
        if widgets and after_index < len(widgets):
            collapsible.mount(new_widget, after=widgets[after_index])
        else:
            collapsible.mount(new_widget)
        return new_widget

    def remove_line_widget(self, index: int) -> None:
        widgets = self._line_widgets()
        if 0 <= index < len(widgets):
            widgets[index].remove()

    def update_line_rhyme(self, index: int, group: str) -> None:
        widgets = self._line_widgets()
        if 0 <= index < len(widgets):
            widgets[index].rhyme_group = group

    def update_line_syllables(self, index: int, count: int) -> None:
        widgets = self._line_widgets()
        if 0 <= index < len(widgets):
            widgets[index].syllable_count = count
