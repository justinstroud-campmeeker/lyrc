from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, DirectoryTree, Label


class MdOnlyDirectoryTree(DirectoryTree):
    def filter_paths(self, paths):
        return [p for p in paths if p.is_dir() or p.suffix == ".md"]


class SongBrowser(Widget):
    """Left-panel song file browser."""

    class SongSelected(Message):
        def __init__(self, path: Path) -> None:
            super().__init__()
            self.path = path

    class NewSongRequested(Message):
        pass

    def __init__(self, songs_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self._songs_dir = songs_dir

    def compose(self) -> ComposeResult:
        yield Label("Songs", id="browser-title")
        yield MdOnlyDirectoryTree(str(self._songs_dir), id="song-tree")
        yield Button("+ New Song", id="new-song-btn", variant="primary")

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        event.stop()
        self.post_message(self.SongSelected(event.path))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "new-song-btn":
            event.stop()
            self.post_message(self.NewSongRequested())

    def refresh_tree(self) -> None:
        try:
            tree = self.query_one("#song-tree", MdOnlyDirectoryTree)
            tree.reload()
        except Exception:
            pass
