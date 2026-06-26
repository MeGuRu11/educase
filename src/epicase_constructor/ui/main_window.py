"""Главное окно Constructor: стартовый экран → редактор кейса + сохранение в .epicase."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QStackedWidget

from epicase_constructor.ui.case_editor import CaseEditor
from epicase_constructor.ui.case_saved_view import CaseSavedView
from epicase_constructor.ui.icons import load_icon
from epicase_constructor.ui.report_dialog import ReportDialog
from epicase_constructor.ui.start_screen import StartScreen
from epicase_core.application.assets import read_asset_sources
from epicase_core.application.case_builder import build_case
from epicase_core.application.case_loader import case_to_draft
from epicase_core.application.cases import load_case, save_case
from epicase_core.application.grading import ArchiveError, report_for_result

_PAGE_START = 0
_PAGE_EDITOR = 1
_PAGE_SAVED = 2


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("EpiCase Constructor")
        self.resize(1000, 700)

        self.editor = CaseEditor()
        self._stack = QStackedWidget(self)
        start = StartScreen(self._stack)
        start.create_requested.connect(self._open_editor)
        start.open_requested.connect(self.open_case_dialog)
        start.check_result_requested.connect(self.open_result_dialog)
        self._stack.addWidget(start)        # page 0
        self._stack.addWidget(self.editor)  # page 1
        self._saved_view = CaseSavedView()
        self._saved_view.continue_requested.connect(
            lambda: self._stack.setCurrentIndex(_PAGE_EDITOR)
        )
        self._saved_view.home_requested.connect(
            lambda: self._stack.setCurrentIndex(_PAGE_START)
        )
        self._stack.addWidget(self._saved_view)  # page 2
        self._stack.setCurrentIndex(_PAGE_START)
        self.setCentralWidget(self._stack)
        self._build_menu()

    def _open_editor(self) -> None:
        self._stack.setCurrentIndex(_PAGE_EDITOR)

    def _build_menu(self) -> None:
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("Файл")
        if file_menu is None:
            return
        save_action = QAction("Сохранить кейс…", self)
        save_action.setIcon(load_icon("save"))
        save_action.triggered.connect(self.save_case_dialog)
        file_menu.addAction(save_action)

        open_case_action = QAction("Открыть кейс…", self)
        open_case_action.setIcon(load_icon("open"))
        open_case_action.triggered.connect(self.open_case_dialog)
        file_menu.addAction(open_case_action)

        open_result_action = QAction("Открыть результат…", self)
        open_result_action.setIcon(load_icon("open"))
        open_result_action.triggered.connect(self.open_result_dialog)
        file_menu.addAction(open_result_action)

    def _show_case_saved(self, path: str) -> None:
        """Переключить стек на экран подтверждения сохранения.

        Тестируемый шов: вызывается без файловых диалогов.
        """
        self._saved_view.set_path(path)
        self._stack.setCurrentIndex(_PAGE_SAVED)

    def save_case_dialog(self) -> None:
        """Показать диалог сохранения и записать кейс в выбранный .epicase."""
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить кейс",
            "",
            "Кейсы EpiCase (*.epicase)",
        )
        if path and self.save_case_to_path(Path(path)):
            self._show_case_saved(path)

    def save_case_to_path(self, path: Path) -> bool:
        """Собрать кейс из редактора и записать в .epicase.

        Тестируемый шов: вызывается без диалога выбора файла. При некорректном значении поля
        документа (``build_case`` → ``ValueError``) или недоступном файле-ассете
        (``read_asset_sources`` → ``OSError``) — предупреждение и ``False``, файл не пишется.
        Идентификатор кейса автогенерируется, поэтому пустым он быть не может. Запись
        синхронная: архив маленький и локальный — QThread не нужен.
        """
        draft = self.editor.to_draft()
        try:
            case = build_case(draft)
            assets = read_asset_sources(draft)
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, "Не удалось сохранить", str(exc))
            return False
        save_case(case, path, assets=assets)
        return True

    def open_case_dialog(self) -> None:
        """Показать диалог открытия и загрузить выбранный .epicase в редактор."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Открыть кейс",
            "",
            "Кейсы EpiCase (*.epicase)",
        )
        if path:
            self.load_case_from_path(Path(path))

    def load_case_from_path(self, path: Path) -> bool:
        """Загрузить .epicase и заполнить редактор (этот срез: мета + пациенты).

        Тестируемый шов: вызывается без диалога выбора файла (как ``save_case_to_path``). При
        ошибке формата/типа/версии архива (``load_case`` → ``ArchiveError``) — предупреждение и
        ``False``, редактор не меняется. Ассеты восстанавливаются из памяти (байты архива): путь
        к исходному файлу и его имя при загрузке утрачены.
        """
        try:
            loaded = load_case(path)
            draft = case_to_draft(loaded)
        except ArchiveError as exc:
            QMessageBox.warning(self, "Не удалось открыть кейс", str(exc))
            return False
        self.editor.load(draft)
        self._stack.setCurrentIndex(_PAGE_EDITOR)
        return True

    def open_result_dialog(self) -> None:
        """Открыть .epiresult + эталонный .epicase и показать нейтральный отчёт сверки."""
        result_path, _ = QFileDialog.getOpenFileName(
            self,
            "Открыть результат",
            "",
            "Результаты EpiCase (*.epiresult)",
        )
        if not result_path:
            return
        case_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите кейс для оценки",
            "",
            "Кейсы EpiCase (*.epicase)",
        )
        if not case_path:
            return
        try:
            graded = report_for_result(Path(result_path), Path(case_path))
        except ArchiveError as exc:
            QMessageBox.warning(self, "Не удалось открыть результат", str(exc))
            return
        if not graded.case_id_matches:
            answer = QMessageBox.question(
                self,
                "Кейс не совпадает",
                f"Результат относится к кейсу '{graded.attempt_case_id}', "
                f"выбран кейс '{graded.case_id}'. Оценить всё равно?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        ReportDialog(
            graded.report,
            graded.trainee_label,
            graded.rank,
            graded.study_group,
            graded.assets,
            self,
        ).exec()

    def report_dialog_for(
        self, result_path: Path, case_path: Path
    ) -> ReportDialog | None:
        """Тестируемый шов: собрать диалог отчёта без файловых диалогов и mismatch-вопроса.

        ``ArchiveError`` из загрузки → ``None`` (по образцу ``save_case_to_path`` с ``False``).
        """
        try:
            graded = report_for_result(result_path, case_path)
        except ArchiveError:
            return None
        return ReportDialog(
            graded.report,
            graded.trainee_label,
            graded.rank,
            graded.study_group,
            graded.assets,
            self,
        )
