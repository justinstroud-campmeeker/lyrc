from __future__ import annotations

from textual import events
from textual.app import ComposeResult
from textual.geometry import Offset
from textual.message import Message
from textual.widget import Widget
from textual.widgets import ListItem, ListView, Label

STAGE_DIRECTIONS = [
    "Chorus",
    "Verse",
    "Verse 1",
    "Verse 2",
    "Verse 3",
    "Pre-Chorus",
    "Bridge",
    "Outro",
    "Intro",
    "Hook",
    "Interlude",
    "Break",
    "Tag",
    "Refrain",
    "Drop",
]


class StageDirectionDropdown(Widget):
    """Overlay autocomplete dropdown for stage directions."""

    DEFAULT_CSS = ""

    class DirectionSelected(Message):
        def __init__(self, direction: str) -> None:
            super().__init__()
            self.direction = direction

    class Dismissed(Message):
        pass

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._filtered: list[str] = list(STAGE_DIRECTIONS)

    def compose(self) -> ComposeResult:
        # No IDs on ListItems — avoids duplicate-ID errors on re-filter
        yield ListView(
            *[ListItem(Label(d)) for d in STAGE_DIRECTIONS],
            id="sd-list",
        )

    def show(self, filter_text: str, offset: Offset) -> None:
        self.styles.offset = offset
        self.display = True
        self._filter(filter_text)
        lv = self.query_one(ListView)
        lv.focus()
        if len(lv) > 0:
            lv.index = 0

    def hide(self) -> None:
        self.display = False

    def _filter(self, text: str) -> None:
        lv = self.query_one(ListView)
        needle = text.lower()
        self._filtered = [
            d for d in STAGE_DIRECTIONS
            if not needle or needle in d.lower()
        ]
        # Rebuild without IDs to avoid duplicate-ID errors across calls
        lv.clear()
        for d in self._filtered:
            lv.append(ListItem(Label(d)))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        event.stop()
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(self._filtered):
            self.post_message(self.DirectionSelected(self._filtered[idx]))
        self.hide()

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            event.stop()
            self.post_message(self.Dismissed())
            self.hide()
