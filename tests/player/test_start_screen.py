"""Smoke-тесты стартового экрана Player (C8)."""
from __future__ import annotations

from unittest.mock import MagicMock

from PySide6.QtWidgets import QPushButton
from pytestqt.qtbot import QtBot

from epicase_player.ui.start_screen import StartScreen


def test_start_screen_creates(qtbot: QtBot) -> None:
    """StartScreen создаётся без исключений."""
    screen = StartScreen()
    qtbot.addWidget(screen)
    assert screen is not None


def test_start_screen_has_open_button(qtbot: QtBot) -> None:
    """StartScreen содержит кнопку «Открыть кейс…»."""
    screen = StartScreen()
    qtbot.addWidget(screen)
    buttons: list[QPushButton] = screen.findChildren(QPushButton)
    labels = [b.text() for b in buttons]
    assert any("Открыть кейс" in t for t in labels)


def test_start_screen_open_button_emits_signal(qtbot: QtBot) -> None:
    """Нажатие кнопки «Открыть кейс…» испускает open_requested."""
    screen = StartScreen()
    qtbot.addWidget(screen)
    handler = MagicMock()
    screen.open_requested.connect(handler)

    buttons: list[QPushButton] = screen.findChildren(QPushButton)
    btn = next(b for b in buttons if "Открыть кейс" in b.text())
    btn.click()

    handler.assert_called_once()
