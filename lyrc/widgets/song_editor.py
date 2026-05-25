"""Main editing surface — owns the Song model."""
from __future__ import annotations

import copy

from PySide6.QtCore import QPoint, Qt, QThreadPool
from PySide6.QtWidgets import (
    QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from lyrc.models.rhyme_scheme import assign_rhyme_groups
from lyrc.models.song import LyricLine, Section, Song
from lyrc.services.clipboard import copy_section, copy_song
from lyrc.services.datamuse import fetch_rhymes, fetch_synonyms
from lyrc.services.song_storage import save_song
from lyrc.services.syllable_counter import count_line_syllables
from lyrc.widgets.line_editor import LineEditorWidget
from lyrc.widgets.section_widget import SectionWidget
from lyrc.widgets.stage_direction_popup import StageDirectionPopup
from lyrc.widgets.word_suggestion_popup import WordSuggestionPopup
from lyrc.workers.datamuse_worker import DatamuseWorker


class SongEditorWidget(QWidget):
    """Scrollable editor containing SectionWidget instances."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._song: Song | None = None
        self._dropdown_source_line: LineEditorWidget | None = None
        self._dropdown_source_section: SectionWidget | None = None
        self._popup_source_line: LineEditorWidget | None = None
        self._popup_word_start: int = 0
        self._popup_word_end: int = 0

        # scroll area
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setObjectName("editorScroll")

        self._container = QWidget()
        self._container.setObjectName("editorContainer")
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setContentsMargins(8, 8, 8, 8)
        self._container_layout.setSpacing(0)
        self._container_layout.addStretch(1)
        self._scroll.setWidget(self._container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._scroll)

        # empty state label
        self._empty_label = QLabel(
            "No song open.\n\nPress Ctrl+N to create one,\nor select a song from the browser."
        )
        self._empty_label.setObjectName("emptyState")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._container_layout.insertWidget(0, self._empty_label)

        # popups (parented to this widget; Popup flag makes them float)
        self._stage_popup = StageDirectionPopup(self)
        self._stage_popup.direction_selected.connect(self._on_direction_selected)
        self._stage_popup.dismissed.connect(self._on_stage_popup_dismissed)

        self._word_popup = WordSuggestionPopup(self)
        self._word_popup.word_selected.connect(self._on_word_selected)
        self._word_popup.dismissed.connect(self._on_word_popup_dismissed)

    # ── public API ─────────────────────────────────────────────────────────────

    def load_song(self, song: Song) -> None:
        self._song = song
        self._recompute_all(song)
        self._rebuild()

    def notify(self, message: str) -> None:
        """Show a status-bar style notification (delegated to main window)."""
        window = self.window()
        if hasattr(window, "statusBar"):
            window.statusBar().showMessage(message, 3000)

    # ── build / rebuild ────────────────────────────────────────────────────────

    def _rebuild(self, focus_section: int | None = None) -> None:
        """Clear and re-populate the container from self._song."""
        # remove all section widgets
        for sw in self._section_widgets():
            self._container_layout.removeWidget(sw)
            sw.deleteLater()

        if self._song is None:
            self._empty_label.setVisible(True)
            return

        self._empty_label.setVisible(False)
        # insert before the trailing stretch (last item)
        stretch_idx = self._container_layout.count() - 1
        for i, section in enumerate(self._song.sections):
            sw = self._make_section_widget(section)
            self._container_layout.insertWidget(stretch_idx + i, sw)

        # focus
        sections = self._section_widgets()
        if sections:
            target_idx = focus_section if focus_section is not None else 0
            target_idx = max(0, min(target_idx, len(sections) - 1))
            sections[target_idx].focus_first_line()

    def _make_section_widget(self, section: Section) -> SectionWidget:
        sw = SectionWidget(section, parent=self._container)
        sw.line_text_changed.connect(self._on_line_text_changed)
        sw.new_line_inserted.connect(self._on_new_line_inserted)
        sw.line_removed.connect(self._on_line_removed)
        sw.focus_crossed_top.connect(self._on_focus_crossed_top)
        sw.focus_crossed_bottom.connect(self._on_focus_crossed_bottom)
        sw.open_bracket_in_line.connect(self._on_open_bracket_in_line)
        sw.thesaurus_requested.connect(self._on_thesaurus_requested)
        sw.rhyme_requested.connect(self._on_rhyme_requested)
        sw.request_move_up.connect(self._on_move_up)
        sw.request_move_down.connect(self._on_move_down)
        sw.request_duplicate.connect(self._on_duplicate)
        sw.request_copy.connect(self._on_copy)
        return sw

    # ── helpers ────────────────────────────────────────────────────────────────

    def _section_widgets(self) -> list[SectionWidget]:
        result = []
        for i in range(self._container_layout.count()):
            item = self._container_layout.itemAt(i)
            if item and isinstance(item.widget(), SectionWidget):
                result.append(item.widget())
        return result

    def _section_index_of(self, sw: SectionWidget) -> int:
        return self._section_widgets().index(sw)

    def _recompute_all(self, song: Song) -> None:
        for line in song.all_lines():
            line.syllable_count = count_line_syllables(line.text)
        assign_rhyme_groups(song.all_lines(), song.rhyme_scheme)

    def _sync_badges(self) -> None:
        if self._song is None:
            return
        all_model_lines = self._song.all_lines()
        idx = 0
        for sw in self._section_widgets():
            for lw in sw.line_widgets():
                if idx < len(all_model_lines):
                    ml = all_model_lines[idx]
                    lw.set_rhyme_group(ml.rhyme_group)
                    lw.set_syllable_count(ml.syllable_count)
                    idx += 1

    # ── section signal handlers ────────────────────────────────────────────────

    def _on_line_text_changed(self, sw: SectionWidget, line_idx: int, text: str) -> None:
        if self._song is None:
            return
        sec_idx = self._section_index_of(sw)
        section_model = self._song.sections[sec_idx]
        if line_idx < len(section_model.lines):
            line_model = section_model.lines[line_idx]
            line_model.text = text
            line_model.syllable_count = count_line_syllables(text)
        assign_rhyme_groups(self._song.all_lines(), self._song.rhyme_scheme)
        self._sync_badges()

    def _on_new_line_inserted(self, sw: SectionWidget, after_idx: int, before: str, after: str) -> None:
        if self._song is None:
            return
        sec_idx = self._section_index_of(sw)
        section_model = self._song.sections[sec_idx]

        if after_idx < len(section_model.lines):
            section_model.lines[after_idx].text = before
            sw.set_line_value(after_idx, before)

        new_line = LyricLine(text=after, line_index=after_idx + 1, rhyme_group="")
        insert_pos = after_idx + 1
        section_model.lines.insert(insert_pos, new_line)

        assign_rhyme_groups(self._song.all_lines(), self._song.rhyme_scheme)
        for line in self._song.all_lines():
            line.syllable_count = count_line_syllables(line.text)

        new_widget = sw.add_line_widget(
            text=after,
            rhyme_group=new_line.rhyme_group,
            after_index=after_idx,
        )
        new_widget.focus_input()
        self._sync_badges()

    def _on_line_removed(self, sw: SectionWidget, line_idx: int) -> None:
        if self._song is None:
            return
        sec_idx = self._section_index_of(sw)
        section_model = self._song.sections[sec_idx]
        focus_idx = max(0, line_idx - 1)

        if len(section_model.lines) <= 1 and len(self._song.sections) > 1:
            self._song.sections.pop(sec_idx)
            self._container_layout.removeWidget(sw)
            sw.deleteLater()
            assign_rhyme_groups(self._song.all_lines(), self._song.rhyme_scheme)
            self._sync_badges()
            sections = self._section_widgets()
            if sections:
                target = sections[min(sec_idx, len(sections) - 1)]
                target.focus_last_line()
        else:
            section_model.lines.pop(line_idx)
            sw.remove_line_widget(line_idx)
            assign_rhyme_groups(self._song.all_lines(), self._song.rhyme_scheme)
            self._sync_badges()
            sw.focus_line(focus_idx)

    def _on_focus_crossed_top(self, sw: SectionWidget) -> None:
        sections = self._section_widgets()
        idx = self._section_index_of(sw)
        if idx > 0:
            sections[idx - 1].focus_last_line()

    def _on_focus_crossed_bottom(self, sw: SectionWidget) -> None:
        sections = self._section_widgets()
        idx = self._section_index_of(sw)
        if idx < len(sections) - 1:
            sections[idx + 1].focus_first_line()

    def _on_open_bracket_in_line(self, sw: SectionWidget, lw: LineEditorWidget) -> None:
        self._dropdown_source_line = lw
        self._dropdown_source_section = sw
        # position popup near the line widget
        global_pos = lw.mapToGlobal(QPoint(40, lw.height()))
        self._stage_popup.show_at(global_pos, filter_text="")

    def _on_move_up(self, sw: SectionWidget) -> None:
        if self._song is None:
            return
        idx = self._section_index_of(sw)
        if idx == 0:
            return
        s = self._song.sections
        s[idx], s[idx - 1] = s[idx - 1], s[idx]
        s[idx].section_index = idx
        s[idx - 1].section_index = idx - 1
        self._rebuild(focus_section=idx - 1)

    def _on_move_down(self, sw: SectionWidget) -> None:
        if self._song is None:
            return
        idx = self._section_index_of(sw)
        if idx >= len(self._song.sections) - 1:
            return
        s = self._song.sections
        s[idx], s[idx + 1] = s[idx + 1], s[idx]
        s[idx].section_index = idx
        s[idx + 1].section_index = idx + 1
        self._rebuild(focus_section=idx + 1)

    def _on_duplicate(self, sw: SectionWidget) -> None:
        if self._song is None:
            return
        idx = self._section_index_of(sw)
        original = self._song.sections[idx]
        dup = copy.deepcopy(original)
        dup.section_index = idx + 1
        self._song.sections.insert(idx + 1, dup)
        for i, sec in enumerate(self._song.sections):
            sec.section_index = i
        self._rebuild(focus_section=idx + 1)

    def _on_copy(self, sw: SectionWidget) -> None:
        copy_section(sw.section_model)
        self.notify("Section copied!")

    # ── stage direction popup ──────────────────────────────────────────────────

    def _on_direction_selected(self, direction: str) -> None:
        if self._song is None:
            return
        lw = self._dropdown_source_line
        sw = self._dropdown_source_section
        self._dropdown_source_line = None
        self._dropdown_source_section = None
        if lw is None or sw is None:
            return

        sec_idx = self._section_index_of(sw)
        line_idx = sw.line_index(lw)

        # strip trailing '[' from current line
        current_text = lw.get_value()
        if current_text.endswith("["):
            new_text = current_text[:-1]
            lw.set_value(new_text)
            model_sec = self._song.sections[sec_idx]
            if line_idx < len(model_sec.lines):
                model_sec.lines[line_idx].text = new_text

        new_section = Section(
            direction=direction,
            lines=[LyricLine(text="", line_index=0, rhyme_group="")],
            section_index=sec_idx + 1,
        )
        self._song.sections.insert(sec_idx + 1, new_section)
        for i, sec in enumerate(self._song.sections):
            sec.section_index = i
        self._rebuild(focus_section=sec_idx + 1)

    def _on_stage_popup_dismissed(self) -> None:
        lw = self._dropdown_source_line
        self._dropdown_source_line = None
        self._dropdown_source_section = None
        if lw is not None:
            lw.focus_input()

    # ── word suggestion popup ──────────────────────────────────────────────────

    def _on_thesaurus_requested(self, sw: SectionWidget, lw: LineEditorWidget,
                                word: str, start: int, end: int) -> None:
        self._start_suggestion(lw, word, start, end, f"Synonyms: {word}", fetch_synonyms)

    def _on_rhyme_requested(self, sw: SectionWidget, lw: LineEditorWidget,
                            word: str, start: int, end: int) -> None:
        self._start_suggestion(lw, word, start, end, f"Rhymes: {word}", fetch_rhymes)

    def _start_suggestion(self, lw: LineEditorWidget, word: str, start: int,
                          end: int, title: str, fetcher) -> None:
        self._popup_source_line = lw
        self._popup_word_start = start
        self._popup_word_end = end
        global_pos = lw.mapToGlobal(QPoint(40, lw.height()))
        self._word_popup.show_loading(title, global_pos)
        worker = DatamuseWorker(fetcher, word)
        worker.signals.results_ready.connect(self._word_popup.set_results)
        QThreadPool.globalInstance().start(worker)

    def _on_word_selected(self, word: str) -> None:
        source = self._popup_source_line
        start, end = self._popup_word_start, self._popup_word_end
        self._popup_source_line = None
        if source is not None:
            source.replace_word(start, end, word)
            source.focus_input()

    def _on_word_popup_dismissed(self) -> None:
        source = self._popup_source_line
        self._popup_source_line = None
        if source is not None:
            source.focus_input()

    # ── actions (called from main window) ─────────────────────────────────────

    def action_save(self) -> None:
        if self._song is None:
            return
        path = save_song(self._song)
        self.notify(f"Saved: {path.name}")

    def action_copy_all(self) -> None:
        if self._song is None:
            return
        copy_song(self._song)
        self.notify("Copied to clipboard!")

    def current_song(self) -> Song | None:
        return self._song
