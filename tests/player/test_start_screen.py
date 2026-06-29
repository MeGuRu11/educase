"""Smoke-тесты стартового экрана Player (C8)."""
from __future__ import annotations

from unittest.mock import MagicMock

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout
from pytestqt.qtbot import QtBot

from epicase_player.ui.start_screen import StartScreen
from epicase_ui.animated_start import AnimatedStartWidget, StartVariant
from epicase_ui.brand_mark import BrandMarkWidget
from epicase_ui.branding import BrandAsset


def test_start_screen_creates(qtbot: QtBot) -> None:
    """StartScreen создаётся без исключений."""
    screen = StartScreen()
    qtbot.addWidget(screen)

    assert screen.objectName() == "playerStartScreen"
    root = screen.layout()
    assert isinstance(root, QVBoxLayout)
    margins = root.contentsMargins()
    assert (margins.left(), margins.top(), margins.right(), margins.bottom()) == (
        0,
        0,
        0,
        0,
    )
    assert root.count() == 1


def test_start_screen_uses_player_animation_and_brand(qtbot: QtBot) -> None:
    """Экран использует Player-варианты анимации и бренд-знака."""
    screen = StartScreen()
    qtbot.addWidget(screen)

    animated = screen.findChild(AnimatedStartWidget)
    assert animated is not None
    assert animated.background.variant is StartVariant.PLAYER

    mark = screen.findChild(BrandMarkWidget)
    assert mark is not None
    assert mark.asset is BrandAsset.PLAYER
    assert mark.minimumSize().width() == 76
    assert mark.minimumSize().height() == 76
    assert mark.maximumSize().width() == 76
    assert mark.maximumSize().height() == 76


def test_start_screen_has_centered_branded_action_card(qtbot: QtBot) -> None:
    """Карточка действия содержит полную иерархию бренда Player."""
    screen = StartScreen()
    qtbot.addWidget(screen)

    card = screen.findChild(QFrame, "startActionCard")
    assert card is not None
    assert card.maximumWidth() == 460
    layout = card.layout()
    assert isinstance(layout, QVBoxLayout)
    margins = layout.contentsMargins()
    assert (margins.left(), margins.top(), margins.right(), margins.bottom()) == (
        28,
        24,
        28,
        24,
    )
    assert layout.spacing() == 9
    assert layout.alignment() == Qt.AlignmentFlag.AlignCenter

    mark = card.findChild(BrandMarkWidget)
    assert mark is not None
    mark_item = layout.itemAt(0)
    assert mark_item is not None and mark_item.widget() is mark
    assert mark_item.alignment() == Qt.AlignmentFlag.AlignCenter

    expected_labels = {
        "startTitle": "EpiCase",
        "startProduct": "PLAYER",
        "startRole": "Учебный тренажёр военного эпидемиолога",
        "startHint": "Откройте файл .epicase, полученный от преподавателя",
    }
    for object_name, text in expected_labels.items():
        label = card.findChild(QLabel, object_name)
        assert label is not None
        assert label.text() == text
        assert label.alignment() == Qt.AlignmentFlag.AlignCenter

    role = card.findChild(QLabel, "startRole")
    hint = card.findChild(QLabel, "startHint")
    assert role is not None and role.wordWrap()
    assert hint is not None and hint.wordWrap()

    button = card.findChild(QPushButton, "startAccentButton")
    assert button is not None
    role_index = layout.indexOf(role)
    button_index = layout.indexOf(button)
    assert role_index >= 0
    assert button_index == role_index + 2
    role_item = layout.itemAt(role_index)
    button_item = layout.itemAt(button_index)
    assert role_item is not None and role_item.widget() is role
    assert button_item is not None and button_item.widget() is button

    action_gap = layout.itemAt(role_index + 1)
    assert action_gap is not None
    spacer = action_gap.spacerItem()
    assert spacer is not None
    assert spacer.sizeHint().height() == 16


def test_start_screen_has_open_button(qtbot: QtBot) -> None:
    """StartScreen содержит кнопку «Открыть кейс…»."""
    screen = StartScreen()
    qtbot.addWidget(screen)

    button = screen.findChild(QPushButton, "startAccentButton")
    assert button is not None
    assert button.text() == "Открыть кейс…"
    animated = screen.findChild(AnimatedStartWidget)
    assert animated is not None
    assert animated.background.intro_complete is False
    assert button.isEnabled()


def test_start_screen_open_button_emits_signal(qtbot: QtBot) -> None:
    """Нажатие кнопки «Открыть кейс…» испускает open_requested."""
    screen = StartScreen()
    qtbot.addWidget(screen)
    handler = MagicMock()
    screen.open_requested.connect(handler)

    button = screen.findChild(QPushButton, "startAccentButton")
    assert button is not None
    button.click()

    handler.assert_called_once()
