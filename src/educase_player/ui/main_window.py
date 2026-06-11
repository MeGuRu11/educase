"""Главное окно Player."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from educase_core.application.cases import ArchiveError, load_case
from educase_player.ui.case_navigator import CaseNavigator


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("EduCase Player")
        self.resize(1000, 700)
        self._set_stub_central()
        self._build_menu()

    def _set_stub_central(self) -> None:
        central = QWidget(self)
        layout = QVBoxLayout(central)
        label = QLabel("EduCase Player — каркас.\nЗагрузите кейс (.educase).", central)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setCentralWidget(central)

    def _build_menu(self) -> None:
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("Файл")
        if file_menu is None:
            return
        open_action = QAction("Открыть кейс…", self)
        open_action.triggered.connect(self.open_case_dialog)
        file_menu.addAction(open_action)

    def open_case_dialog(self) -> None:
        """Показать диалог выбора файла .educase и загрузить кейс."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Открыть кейс",
            "",
            "Кейсы EduCase (*.educase)",
        )
        if path:
            self.load_case_from_path(Path(path))

    def load_case_from_path(self, path: Path) -> bool:
        """Загрузить кейс из .educase и смонтировать навигатор.

        Тестируемый шов: вызывается без диалога выбора файла.
        Загрузка синхронная — архив маленький, локальный; QThread нужен только
        когда появятся тяжёлые ассеты.
        """
        try:
            loaded = load_case(path)
        except ArchiveError as exc:
            QMessageBox.warning(self, "Ошибка загрузки", str(exc))
            return False
        self.setCentralWidget(CaseNavigator(loaded.case, self))
        return True
