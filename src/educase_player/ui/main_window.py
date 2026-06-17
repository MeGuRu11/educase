"""Главное окно Player."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from loguru import logger
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from educase_core.application.cases import load_case
from educase_core.application.results import ArchiveError, record_attempt
from educase_core.domain.attempt import AttemptMeta
from educase_core.domain.case import Case
from educase_player.ui.case_navigator import CaseNavigator


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("EduCase Player")
        self.resize(1000, 700)
        self._navigator: CaseNavigator | None = None
        self._case: Case | None = None
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

        self._save_action = QAction("Сохранить результат…", self)
        self._save_action.setEnabled(False)  # активна только при загруженном кейсе
        self._save_action.triggered.connect(self.save_result_dialog)
        file_menu.addAction(self._save_action)

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
            QMessageBox.warning(self, "Ошибка открытия", str(exc))
            return False
        except Exception:  # граница приложения: любой повреждённый/несовместимый архив
            logger.exception("Не удалось открыть кейс: {}", path)
            QMessageBox.critical(
                self,
                "Не удалось открыть кейс",
                "Файл повреждён или имеет несовместимый формат.",
            )
            return False
        navigator = CaseNavigator(loaded.case, loaded.assets, self)
        self.setCentralWidget(navigator)
        self._navigator = navigator
        self._case = loaded.case
        self._save_action.setEnabled(True)
        return True

    def save_result_dialog(self) -> None:
        """Спросить подпись курсанта и путь, затем записать .eduresult."""
        if self._case is None or self._navigator is None:
            return
        trainee_label, ok = QInputDialog.getText(
            self,
            "Подпись курсанта",
            "Подпись (необязательно):",
        )
        if not ok:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить результат",
            "",
            "Результаты EduCase (*.eduresult)",
        )
        if path:
            self.save_result_to_path(Path(path), trainee_label)

    def save_result_to_path(self, path: Path, trainee_label: str = "") -> bool:
        """Собрать прохождение и записать .eduresult.

        Тестируемый шов: вызывается без диалогов. ``False``, если кейс не загружен
        или запись провалилась (битый путь / ошибка архива) — без исключения наружу.
        """
        if self._case is None or self._navigator is None:
            return False
        meta = AttemptMeta(
            case_id=self._case.meta.id,
            trainee_label=trainee_label,
            created_at=datetime.now().isoformat(timespec="seconds"),
        )
        attempt = self._navigator.collect_attempt(meta)
        try:
            record_attempt(attempt, path)
        except (ArchiveError, OSError) as exc:
            QMessageBox.warning(self, "Ошибка сохранения", str(exc))
            return False
        return True
