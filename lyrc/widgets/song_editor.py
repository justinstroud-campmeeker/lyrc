from __future__ import annotations

import copy

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widgets import Static

from lyrc.models.rhyme_scheme import assign_rhyme_groups
from lyrc.models.song import LyricLine, Section, Song
from lyrc.services.clipboard import copy_section, copy_song
from lyrc.services.song_storage import save_song
from lyrc.services.syllable_counter import count_line_syllables
from lyrc.widgets.line_editor import LyricLineWidget
from lyrc.widgets.section_widget import SectionWidget
from lyrc.widgets.stage_direction_dropdown import StageDirectionDropdown


class SongEditor(VerticalScroll):
    """Main editing surface owning the Song model."""

    BINDINGS = [
        ("ctrl+s", "save",           "Save"),
        ("ctrl+y", "copy_all",       "Copy all"),
        ("ctrl+n", "new_song",       "New song"),
        ("ctrl+b", "toggle_browser", "Browser"),
    ]

    _song: Song | None = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        if self._song is None:
            yield Static(
                "No song open.\n\nPress [bold]Ctrl+N[/bold] to create one, "
                "or select a song from the browser.",
                id="empty-state",
            )
            return

        for section in self._song.sections:
            yield SectionWidget(
                section,
                id=f"sec-{section.section_index}",
                classes="section-block",
            )

        yield StageDirectionDropdown(id="sd-dropdown")

    # ── Public API ────────────────────────────────────────────────────────────

    def load_song(self, song: Song) -> None:
        self._song = song
        self._recompute_all(song)
        self._rebuild()

    def _rebuild(self) -> None:
        """Tear down and recompose the editor contents."""
        self.remove_children()
        for widget in self.compose():
            self.mount(widget)
        # Focus first line of first section
        self.call_after_refresh(self._focus_first_line)

    def _focus_first_line(self) -> None:
        sections = list(self.query(SectionWidget))
        if sections:
            sections[0].focus_first_line()

    # ── Model helpers ─────────────────────────────────────────────────────────

    def _recompute_all(self, song: Song) -> None:
        for line in song.all_lines():
            line.syllable_count = count_line_syllables(line.text)
        assign_rhyme_groups(song.all_lines(), song.rhyme_scheme)

    def _sync_badges(self) -> None:
        """Push rhyme groups from model to visible widgets."""
        if self._song is None:
            return
        all_lines = self._song.all_lines()
        all_widgets = list(self.query(LyricLineWidget))
        for widget, model_line in zip(all_widgets, all_lines):
            widget.rhyme_group = model_line.rhyme_group
            widget.syllable_count = model_line.syllable_count

    def _section_widgets(self) -> list[SectionWidget]:
        return list(self.query(SectionWidget))

    def _section_index_of(self, sw: SectionWidget) -> int:
        return self._section_widgets().index(sw)

    # ── SectionWidget events ──────────────────────────────────────────────────

    def on_section_widget_line_text_changed(self, event: SectionWidget.LineTextChanged) -> None:
        event.stop()
        if self._song is None:
            return
        sec_idx = self._section_index_of(event.section)
        section_model = self._song.sections[sec_idx]
        if event.line_index < len(section_model.lines):
            line_model = section_model.lines[event.line_index]
            line_model.text = event.text
            line_model.syllable_count = count_line_syllables(event.text)
        assign_rhyme_groups(self._song.all_lines(), self._song.rhyme_scheme)
        self._sync_badges()

    def on_section_widget_new_line_inserted(self, event: SectionWidget.NewLineInserted) -> None:
        event.stop()
        if self._song is None:
            return
        sec_idx = self._section_index_of(event.section)
        section_model = self._song.sections[sec_idx]

        # Update the current line's text in the model
        if event.after_line_index < len(section_model.lines):
            section_model.lines[event.after_line_index].text = event.text_before
            event.section._line_widgets()[event.after_line_index].set_input_value(event.text_before)

        # Insert new line into model
        new_line = LyricLine(
            text=event.text_after,
            line_index=event.after_line_index + 1,
            rhyme_group="",
        )
        insert_pos = event.after_line_index + 1
        section_model.lines.insert(insert_pos, new_line)

        # Recompute groups and syllables
        assign_rhyme_groups(self._song.all_lines(), self._song.rhyme_scheme)
        for line in self._song.all_lines():
            line.syllable_count = count_line_syllables(line.text)

        # Mount new widget
        new_widget = event.section.add_line_widget(
            text=event.text_after,
            rhyme_group=new_line.rhyme_group,
            after_index=event.after_line_index,
            line_model_index=insert_pos,
        )

        # Focus the new widget
        self.call_after_refresh(lambda: new_widget.focus_input())
        self.call_after_refresh(self._sync_badges)

    def on_section_widget_line_removed(self, event: SectionWidget.LineRemoved) -> None:
        event.stop()
        if self._song is None:
            return
        sec_idx = self._section_index_of(event.section)
        section_model = self._song.sections[sec_idx]

        focus_idx = max(0, event.line_index - 1)

        if len(section_model.lines) <= 1 and len(self._song.sections) > 1:
            # Remove whole section
            self._song.sections.pop(sec_idx)
            event.section.remove()
            assign_rhyme_groups(self._song.all_lines(), self._song.rhyme_scheme)
            self._sync_badges()
            # Focus adjacent section
            sections = self._section_widgets()
            if sections:
                target = sections[min(sec_idx, len(sections) - 1)]
                self.call_after_refresh(target.focus_last_line)
        else:
            section_model.lines.pop(event.line_index)
            event.section.remove_line_widget(event.line_index)
            assign_rhyme_groups(self._song.all_lines(), self._song.rhyme_scheme)
            self._sync_badges()
            self.call_after_refresh(lambda: event.section.focus_line(focus_idx))

    def on_section_widget_request_move_up(self, event: SectionWidget.RequestMoveUp) -> None:
        event.stop()
        if self._song is None:
            return
        idx = self._section_index_of(event.section)
        if idx == 0:
            return
        s = self._song.sections
        s[idx], s[idx - 1] = s[idx - 1], s[idx]
        s[idx].section_index = idx
        s[idx - 1].section_index = idx - 1
        self._rebuild()
        self.call_after_refresh(
            lambda: self._section_widgets()[idx - 1].focus_first_line()
        )

    def on_section_widget_request_move_down(self, event: SectionWidget.RequestMoveDown) -> None:
        event.stop()
        if self._song is None:
            return
        idx = self._section_index_of(event.section)
        if idx >= len(self._song.sections) - 1:
            return
        s = self._song.sections
        s[idx], s[idx + 1] = s[idx + 1], s[idx]
        s[idx].section_index = idx
        s[idx + 1].section_index = idx + 1
        self._rebuild()
        self.call_after_refresh(
            lambda: self._section_widgets()[idx + 1].focus_first_line()
        )

    def on_section_widget_request_duplicate(self, event: SectionWidget.RequestDuplicate) -> None:
        event.stop()
        if self._song is None:
            return
        idx = self._section_index_of(event.section)
        original = self._song.sections[idx]
        dup = copy.deepcopy(original)
        dup.section_index = idx + 1
        self._song.sections.insert(idx + 1, dup)
        # Re-index all
        for i, sec in enumerate(self._song.sections):
            sec.section_index = i
        self._rebuild()
        self.call_after_refresh(
            lambda: self._section_widgets()[idx + 1].focus_first_line()
        )

    def on_section_widget_request_copy(self, event: SectionWidget.RequestCopy) -> None:
        event.stop()
        copy_section(event.section.section_model)
        self.app.notify("Section copied!", severity="information")

    def on_section_widget_open_bracket_in_line(self, event: SectionWidget.OpenBracketInLine) -> None:
        event.stop()
        dropdown = self.query_one("#sd-dropdown", StageDirectionDropdown)
        dropdown.show(filter_text="", offset=event.offset)

    def on_section_widget_focus_crossed_bottom(self, event: SectionWidget.FocusCrossedBottom) -> None:
        event.stop()
        sections = self._section_widgets()
        idx = self._section_index_of(event.section)
        if idx < len(sections) - 1:
            sections[idx + 1].focus_first_line()

    def on_section_widget_focus_crossed_top(self, event: SectionWidget.FocusCrossedTop) -> None:
        event.stop()
        sections = self._section_widgets()
        idx = self._section_index_of(event.section)
        if idx > 0:
            sections[idx - 1].focus_last_line()

    # ── StageDirectionDropdown events ─────────────────────────────────────────

    def on_stage_direction_dropdown_direction_selected(
        self, event: StageDirectionDropdown.DirectionSelected
    ) -> None:
        event.stop()
        if self._song is None:
            return

        direction = event.direction

        # Find currently focused LyricLineWidget
        focused_line: LyricLineWidget | None = None
        focused = self.app.focused
        if focused is not None:
            # The focused widget is an Input inside a LyricLineWidget
            parent = focused.parent
            if isinstance(parent, LyricLineWidget):
                focused_line = parent

        if focused_line is None:
            return

        # Find which section and line this is
        focused_section: SectionWidget | None = None
        for sw in self._section_widgets():
            if focused_line in sw._line_widgets():
                focused_section = sw
                break

        if focused_section is None:
            return

        line_idx = focused_section._line_index(focused_line)
        sec_idx = self._section_index_of(focused_section)

        # Remove the trailing '[' from the current line
        current_text = focused_line.get_input_value()
        if current_text.endswith("["):
            new_text = current_text[:-1]
            focused_line.set_input_value(new_text)
            if self._song:
                model_sec = self._song.sections[sec_idx]
                if line_idx < len(model_sec.lines):
                    model_sec.lines[line_idx].text = new_text

        # Insert a new section after the current one
        new_section = Section(
            direction=direction,
            lines=[LyricLine(text="", line_index=0, rhyme_group="")],
            section_index=sec_idx + 1,
        )
        self._song.sections.insert(sec_idx + 1, new_section)
        for i, sec in enumerate(self._song.sections):
            sec.section_index = i

        self._rebuild()
        self.call_after_refresh(
            lambda: self._section_widgets()[sec_idx + 1].focus_first_line()
        )

    def on_stage_direction_dropdown_dismissed(self, event: StageDirectionDropdown.Dismissed) -> None:
        event.stop()
        # Return focus to last focused line
        sections = self._section_widgets()
        if sections:
            sections[0].focus_first_line()

    # ── Actions ───────────────────────────────────────────────────────────────

    def action_save(self) -> None:
        if self._song is None:
            return
        path = save_song(self._song)
        self.app.notify(f"Saved: {path.name}", severity="information")
        # Refresh browser if present
        try:
            from lyrc.widgets.song_browser import SongBrowser
            browser = self.app.query_one(SongBrowser)
            browser.refresh_tree()
        except Exception:
            pass

    def action_copy_all(self) -> None:
        if self._song is None:
            return
        copy_song(self._song)
        self.app.notify("Copied to clipboard!", severity="information")

    def action_new_song(self) -> None:
        from lyrc.app import NewSongModal
        self.app.push_screen(NewSongModal(), self._on_new_song)

    def _on_new_song(self, title: str | None) -> None:
        if not title:
            return
        from lyrc.models.song import Song, Section, LyricLine
        from lyrc.services.song_storage import save_song
        song = Song(
            title=title,
            sections=[
                Section(
                    direction="Verse 1",
                    lines=[LyricLine(text="", line_index=0, rhyme_group="")],
                    section_index=0,
                )
            ],
        )
        save_song(song)
        self.load_song(song)
        try:
            from lyrc.widgets.song_browser import SongBrowser
            self.app.query_one(SongBrowser).refresh_tree()
        except Exception:
            pass

    def action_toggle_browser(self) -> None:
        try:
            from lyrc.widgets.song_browser import SongBrowser
            browser = self.app.query_one(SongBrowser)
            browser.display = not browser.display
        except Exception:
            pass
