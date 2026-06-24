"""Smoke-тесты стартового экрана Constructor (C7)."""
from __future__ import annotations

from unittest.mock import MagicMock

from PySide6.QtWidgets import QPushButton
from pytestqt.qtbot import QtBot

from epicase_constructor.ui.start_screen import StartScreen


def test_start_screen_creates(qtbot: QtBot) -> None:
    """StartScreen создаётся без исключений."""
    screen = StartScreen()
    qtbot.addWidget(screen)
    assert screen is not None


def test_start_screen_has_create_button(qtbot: QtBot) -> None:
    """StartScreen содержит кнопку «Создать новый кейс»."""
    screen = StartScreen()
    qtbot.addWidget(screen)
    buttons: list[QPushButton] = screen.findChildren(QPushButton)
    labels = [b.text() for b in buttons]
    assert any("Создать новый кейс" in t for t in labels)


def test_start_screen_has_check_result_button(qtbot: QtBot) -> None:
    """StartScreen содержит кнопку «Проверить результат курсанта»."""
    screen = StartScreen()
    qtbot.addWidget(screen)
    buttons: list[QPushButton] = screen.findChildren(QPushButton)
    labels = [b.text() for b in buttons]
    assert any("Проверить результат" in t for t in labels)


def test_start_screen_create_button_emits_signal(qtbot: QtBot) -> None:
    """Нажатие «Создать новый кейс» испускает create_requested."""
    screen = StartScreen()
    qtbot.addWidget(screen)
    handler = MagicMock()
    screen.create_requested.connect(handler)

    buttons: list[QPushButton] = screen.findChildren(QPushButton)
    btn = next(b for b in buttons if "Создать новый кейс" in b.text())
    btn.click()

    handler.assert_called_once()


def test_start_screen_check_button_emits_signal(qtbot: QtBot) -> None:
    """Нажатие «Проверить результат курсанта» испускает check_result_requested."""
    screen = StartScreen()
    qtbot.addWidget(screen)
    handler = MagicMock()
    screen.check_result_requested.connect(handler)

    buttons: list[QPushButton] = screen.findChildren(QPushButton)
    btn = next(b for b in buttons if "Проверить результат" in b.text())
    btn.click()

    handler.assert_called_once()
