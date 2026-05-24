from __future__ import annotations

from textual import events
from textual.app import ComposeResult
from textual.geometry import Offset
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Input, Static

from lyrc.services.syllable_counter import count_line_syllables


class LyricLineWidget(Widget):
    """A single editable lyric line with a syllable-count gutter and rhyme badge."""

    DEFAULT_CSS = ""

    text: reactive[str] = reactive("", layout=False)
    syllable_count: reactive[int] = reactive(0, layout=False)
    rhyme_group: reactive[str] = reactive("", layout=False)

    # ── Messages ────────────────────────────────────────────────────────────

    class TextChanged(Message):
        def __init__(self, widget: "LyricLineWidget", new_text: str) -> None:
            super().__init__()
            self.widget = widget
            self.new_text = new_text

    class OpenBracketTyped(Message):
        def __init__(self, widget: "LyricLineWidget", cursor_offset: Offset) -> None:
            super().__init__()
            self.widget = widget
            self.cursor_offset = cursor_offset

    class LineDeleted(Message):
        def __init__(self, widget: "LyricLineWidget") -> None:
            super().__init__()
            self.widget = widget

    class FocusNext(Message):
        def __init__(self, widget: "LyricLineWidget") -> None:
            super().__init__()
            self.widget = widget

    class FocusPrev(Message):
        def __init__(self, widget: "LyricLineWidget") -> None:
            super().__init__()
            self.widget = widget

    class NewLineRequested(Message):
        def __init__(
            self,
            widget: "LyricLineWidget",
            text_before: str,
            text_after: str,
        ) -> None:
            super().__init__()
            self.widget = widget
            self.text_before = text_before
            self.text_after = text_after

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def __init__(self, text: str = "", rhyme_group: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self._init_text = text
        self._init_rhyme = rhyme_group

    def compose(self) -> ComposeResult:
        yield Static("0", id="syllable-count", classes="syllable-gutter")
        yield Input(value=self._init_text, id="line-input")
        yield Static("", id="rhyme-badge", classes="rhyme-badge")

    def on_mount(self) -> None:
        self.text = self._init_text
        self.rhyme_group = self._init_rhyme
        count = count_line_syllables(self._init_text)
        self.syllable_count = count
        self.query_one("#syllable-count", Static).update(str(count) if count else "·")

    # ── Input events ─────────────────────────────────────────────────────────

    def on_input_changed(self, event: Input.Changed) -> None:
        event.stop()
        new_val = event.value
        self.text = new_val

        count = count_line_syllables(new_val)
        self.syllable_count = count
        self.query_one("#syllable-count", Static).update(str(count) if count else "·")

        self.post_message(self.TextChanged(self, new_val))

        # Detect '[' as the last typed character
        if new_val.endswith("["):
            region = self.content_region
            offset = Offset(region.x + 5, region.y + 1)
            self.post_message(self.OpenBracketTyped(self, offset))

    def on_key(self, event: events.Key) -> None:
        inp = self.query_one("#line-input", Input)
        cursor = inp.cursor_position

        if event.key == "up":
            if cursor == 0:
                event.stop()
                self.post_message(self.FocusPrev(self))
            return

        if event.key == "down":
            if cursor >= len(inp.value):
                event.stop()
                self.post_message(self.FocusNext(self))
            return

        if event.key == "enter":
            event.stop()
            val = inp.value
            before = val[:cursor]
            after = val[cursor:]
            self.post_message(self.NewLineRequested(self, before, after))
            return

        if event.key == "backspace":
            if inp.value == "":
                event.stop()
                self.post_message(self.LineDeleted(self))
            return

    # ── Reactives ────────────────────────────────────────────────────────────

    def watch_rhyme_group(self, group: str) -> None:
        try:
            badge = self.query_one("#rhyme-badge", Static)
        except Exception:
            return
        if group:
            badge.update(group)
            badge.set_classes(f"rhyme-badge rhyme-badge--visible rhyme-{group}")
        else:
            badge.update("")
            badge.set_classes("rhyme-badge")

    def watch_syllable_count(self, count: int) -> None:
        try:
            gutter = self.query_one("#syllable-count", Static)
            gutter.update(str(count) if count else "·")
        except Exception:
            pass

    # ── Public API ───────────────────────────────────────────────────────────

    def focus_input(self, cursor_end: bool = False) -> None:
        inp = self.query_one("#line-input", Input)
        inp.focus()
        if cursor_end:
            inp.cursor_position = len(inp.value)

    def get_input_value(self) -> str:
        return self.query_one("#line-input", Input).value

    def set_input_value(self, value: str) -> None:
        inp = self.query_one("#line-input", Input)
        with inp.prevent(Input.Changed):
            inp.value = value
        self.text = value
        count = count_line_syllables(value)
        self.syllable_count = count
