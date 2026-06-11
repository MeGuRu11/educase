from pathlib import Path

import pytest
from PySide6.QtWidgets import QMessageBox
from pytestqt.qtbot import QtBot

from educase_core.application.cases import save_case
from educase_core.domain.case import Case, CaseMeta
from educase_player.ui.case_navigator import CaseNavigator
from educase_player.ui.main_window import MainWindow


def test_player_window_title(qtbot: QtBot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.windowTitle() == "EduCase Player"


def test_load_case_from_path_success(qtbot: QtBot, tmp_path: Path) -> None:
    """load_case_from_path монтирует CaseNavigator с 6 страницами при успешной загрузке."""
    case = Case(meta=CaseMeta("c1", "Тест"))
    dst = tmp_path / "test.educase"
    save_case(case, dst)

    window = MainWindow()
    qtbot.addWidget(window)

    result = window.load_case_from_path(dst)

    assert result is True
    central = window.centralWidget()
    assert isinstance(central, CaseNavigator)
    assert central.stack.count() == 6


def test_load_case_from_path_corrupt(
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """load_case_from_path возвращает False при битом файле, без исключения."""
    corrupt = tmp_path / "bad.educase"
    corrupt.write_bytes(b"not a zip file")

    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: 0)

    window = MainWindow()
    qtbot.addWidget(window)

    result = window.load_case_from_path(corrupt)
    assert result is False
