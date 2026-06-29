"""Точка входа Player."""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from epicase_core.logging import setup_logging
from epicase_core.theme import load_qss
from epicase_player.ui.main_window import MainWindow


def main() -> int:
    setup_logging("player")
    app = QApplication(sys.argv)
    app.setStyleSheet(load_qss())
    window = MainWindow()
    window.showMaximized()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
