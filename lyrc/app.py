from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Footer, Header, Input, Label
from textual.containers import Horizontal, Vertical

from lyrc.services.song_storage import SONGS_DIR, ensure_songs_dir, load_song
from lyrc.widgets.song_browser import SongBrowser
from lyrc.widgets.song_editor import SongEditor


class NewSongModal(ModalScreen[str | None]):
    """Modal for entering a new song title."""

    CSS = """
    NewSongModal {
        align: center middle;
    }
    #modal-container {
        width: 50;
        height: auto;
        background: $surface;
        border: round $accent;
        padding: 2 4;
    }
    #modal-label {
        margin-bottom: 1;
    }
    #modal-buttons {
        margin-top: 1;
        align-horizontal: right;
        height: auto;
    }
    #modal-buttons Button {
        margin-left: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-container"):
            yield Label("Song title:", id="modal-label")
            yield Input(placeholder="My Song", id="title-input")
            with Horizontal(id="modal-buttons"):
                yield Button("Create", variant="primary", id="create-btn")
                yield Button("Cancel", id="cancel-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create-btn":
            val = self.query_one("#title-input", Input).value.strip()
            self.dismiss(val if val else None)
        else:
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        val = event.value.strip()
        self.dismiss(val if val else None)


class MainScreen(Screen):
    BINDINGS = [
        ("ctrl+q", "app.quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        ensure_songs_dir()
        yield Header()
        yield SongBrowser(songs_dir=SONGS_DIR, id="browser")
        yield SongEditor(id="editor")
        yield Footer()

    def on_song_browser_song_selected(self, event: SongBrowser.SongSelected) -> None:
        event.stop()
        song = load_song(event.path)
        self.query_one(SongEditor).load_song(song)

    def on_song_browser_new_song_requested(self, event: SongBrowser.NewSongRequested) -> None:
        event.stop()
        self.app.push_screen(NewSongModal(), self._on_new_song_from_browser)

    def _on_new_song_from_browser(self, title: str | None) -> None:
        if title:
            self.query_one(SongEditor)._on_new_song(title)


class LyrcApp(App):
    TITLE = "Lyrc"
    CSS_PATH = [
        Path(__file__).parent / "styles" / "app.tcss",
        Path(__file__).parent / "styles" / "editor.tcss",
        Path(__file__).parent / "styles" / "browser.tcss",
    ]
    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        self.push_screen(MainScreen())
