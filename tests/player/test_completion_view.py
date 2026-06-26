"""Тесты CompletionView: начальная фаза, сигналы, переключение в saved."""
from __future__ import annotations

from PySide6.QtWidgets import QPushButton
from pytestqt.qtbot import QtBot

from epicase_player.ui.completion_view import CompletionView


def test_initial_phase_is_ready(qtbot: QtBot) -> None:
    """На старте показывается фаза 'ready'."""
    view = CompletionView()
    qtbot.addWidget(view)
    assert view._stack.currentIndex() == CompletionView._READY


def test_save_requested_on_save_button(qtbot: QtBot) -> None:
    """Кнопка 'Сохранить результат' испускает save_requested."""
    view = CompletionView()
    qtbot.addWidget(view)

    received: list[bool] = []
    view.save_requested.connect(lambda: received.append(True))

    btns = view.findChildren(QPushButton, "completionSaveButton")
    assert len(btns) == 1
    btns[0].click()

    assert len(received) == 1


def test_set_saved_switches_phase_and_shows_path(qtbot: QtBot) -> None:
    """set_saved переключает на фазу 'saved' и показывает путь."""
    view = CompletionView()
    qtbot.addWidget(view)

    view.set_saved("C:/results/result.epiresult")

    assert view._stack.currentIndex() == CompletionView._SAVED
    assert view._path_label.text() == "C:/results/result.epiresult"


def test_new_case_requested_on_open_button(qtbot: QtBot) -> None:
    """Кнопка 'Открыть другой кейс' испускает new_case_requested."""
    view = CompletionView()
    qtbot.addWidget(view)
    view.set_saved("/path/result.epiresult")

    received: list[bool] = []
    view.new_case_requested.connect(lambda: received.append(True))

    btns = view.findChildren(QPushButton, "completionNewButton")
    assert len(btns) == 1
    btns[0].click()

    assert len(received) == 1
