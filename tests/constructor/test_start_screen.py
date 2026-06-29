"""Smoke-тесты стартового экрана Constructor (C7)."""
from __future__ import annotations

from typing import cast
from unittest.mock import MagicMock

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout
from pytestqt.qtbot import QtBot

from epicase_constructor.ui.start_screen import StartScreen
from epicase_ui.animated_start import AnimatedStartWidget, StartVariant
from epicase_ui.brand_mark import BrandMarkWidget
from epicase_ui.branding import BrandAsset


def test_start_screen_creates(qtbot: QtBot) -> None:
    """StartScreen создаётся без исключений."""
    screen = StartScreen()
    qtbot.addWidget(screen)

    assert screen.objectName() == "constructorStartScreen"
    root = screen.layout()
    assert isinstance(root, QVBoxLayout)
    margins = root.contentsMargins()
    assert (margins.left(), margins.top(), margins.right(), margins.bottom()) == (
        0,
        0,
        0,
        0,
    )
    assert root.spacing() == 0
    assert root.count() == 1
    root_item = root.itemAt(0)
    assert root_item is not None
    assert isinstance(root_item.widget(), AnimatedStartWidget)


def test_start_screen_uses_constructor_animation_and_brand(qtbot: QtBot) -> None:
    """Экран использует Constructor-варианты анимации и бренд-знака."""
    screen = StartScreen()
    qtbot.addWidget(screen)

    animated = screen.findChild(AnimatedStartWidget)
    assert animated is not None
    assert animated.background.variant is StartVariant.CONSTRUCTOR

    mark = screen.findChild(BrandMarkWidget)
    assert mark is not None
    assert mark.asset is BrandAsset.CONSTRUCTOR
    assert mark.minimumSize().width() == 76
    assert mark.minimumSize().height() == 76
    assert mark.maximumSize().width() == 76
    assert mark.maximumSize().height() == 76


def test_start_screen_has_centered_branded_action_card(qtbot: QtBot) -> None:
    """Карточка действия содержит полную иерархию бренда Constructor."""
    screen = StartScreen()
    qtbot.addWidget(screen)

    card = screen.findChild(QFrame, "startActionCard")
    assert card is not None
    assert card.maximumWidth() == 520
    layout = card.layout()
    assert isinstance(layout, QVBoxLayout)
    margins = layout.contentsMargins()
    assert (margins.left(), margins.top(), margins.right(), margins.bottom()) == (
        30,
        24,
        30,
        24,
    )
    assert layout.spacing() == 8
    assert layout.alignment() == Qt.AlignmentFlag.AlignCenter

    mark = card.findChild(BrandMarkWidget)
    assert mark is not None
    mark_index = layout.indexOf(mark)
    assert mark_index >= 0
    mark_item = layout.itemAt(mark_index)
    assert mark_item is not None and mark_item.widget() is mark
    assert mark_item.alignment() == Qt.AlignmentFlag.AlignCenter

    expected_labels = {
        "startTitle": "EpiCase",
        "startProduct": "КОНСТРУКТОР",
        "startRole": "Рабочее место преподавателя",
    }
    for object_name, text in expected_labels.items():
        label = card.findChild(QLabel, object_name)
        assert label is not None
        assert label.text() == text
        assert label.alignment() == Qt.AlignmentFlag.AlignCenter

    role = card.findChild(QLabel, "startRole")
    create = card.findChild(QPushButton, "startAccentButton")
    secondary = card.findChildren(QPushButton, "startSecondaryButton")
    assert role is not None
    assert role.wordWrap()
    assert create is not None
    assert len(secondary) == 2

    role_index = layout.indexOf(role)
    create_index = layout.indexOf(create)
    open_index = layout.indexOf(secondary[0])
    check_index = layout.indexOf(secondary[1])
    assert role_index >= 0
    assert create_index == role_index + 2
    assert open_index == create_index + 1
    assert check_index == open_index + 1

    action_gap = layout.itemAt(role_index + 1)
    assert action_gap is not None
    spacer = action_gap.spacerItem()
    assert spacer is not None
    assert spacer.sizeHint().height() == 14


def test_start_screen_buttons_keep_contract_and_are_immediately_enabled(
    qtbot: QtBot,
) -> None:
    """Три действия сохраняют подписи, стили и доступны во время intro."""
    screen = StartScreen()
    qtbot.addWidget(screen)

    buttons = cast(list[QPushButton], screen.findChildren(QPushButton))
    buttons_by_text = {button.text(): button for button in buttons}
    expected_object_names = {
        "Создать новый кейс": "startAccentButton",
        "Открыть кейс для правки": "startSecondaryButton",
        "Проверить результат курсанта": "startSecondaryButton",
    }
    assert set(buttons_by_text) == set(expected_object_names)
    for text, object_name in expected_object_names.items():
        button = buttons_by_text[text]
        assert button.objectName() == object_name
        assert button.isEnabled()

    animated = screen.findChild(AnimatedStartWidget)
    assert animated is not None
    assert animated.background.intro_complete is False


def test_start_screen_buttons_emit_existing_signals(qtbot: QtBot) -> None:
    """Каждая кнопка испускает прежний публичный сигнал Constructor."""
    screen = StartScreen()
    qtbot.addWidget(screen)

    buttons = cast(list[QPushButton], screen.findChildren(QPushButton))
    buttons_by_text = {button.text(): button for button in buttons}
    create_handler = MagicMock()
    open_handler = MagicMock()
    check_handler = MagicMock()
    screen.create_requested.connect(create_handler)
    screen.open_requested.connect(open_handler)
    screen.check_result_requested.connect(check_handler)

    buttons_by_text["Создать новый кейс"].click()
    buttons_by_text["Открыть кейс для правки"].click()
    buttons_by_text["Проверить результат курсанта"].click()

    create_handler.assert_called_once()
    open_handler.assert_called_once()
    check_handler.assert_called_once()
