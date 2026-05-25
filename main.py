import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from lyrc.app import LyrcMainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Lyrc")

    qss_path = Path(__file__).parent / "lyrc" / "styles" / "dark.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    window = LyrcMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
