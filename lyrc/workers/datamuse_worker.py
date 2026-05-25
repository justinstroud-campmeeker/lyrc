"""Background worker for Datamuse API calls."""
from __future__ import annotations
from typing import Callable

from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class WorkerSignals(QObject):
    results_ready = Signal(list)
    error = Signal(str)


class DatamuseWorker(QRunnable):
    """Runs a Datamuse fetch function on a thread pool thread."""

    def __init__(self, fetcher: Callable[[str], list[str]], word: str) -> None:
        super().__init__()
        self.fetcher = fetcher
        self.word = word
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            results = self.fetcher(self.word)
            self.signals.results_ready.emit(results)
        except Exception as exc:
            self.signals.error.emit(str(exc))
