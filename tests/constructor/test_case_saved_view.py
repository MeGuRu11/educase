"""Тесты CaseSavedView: заголовок, set_path, сигналы."""
from __future__ import annotations

from PySide6.QtWidgets import QPushButton
from pytestqt.qtbot import QtBot

from epicase_constructor.ui.case_saved_view import CaseSavedView


def test_shows_done_title(qtbot: QtBot) -> None:
    """Заголовок 'Кейс сохранён' присутствует после создания."""
    from PySide6.QtWidgets import QLabel

    view = CaseSavedView()
    qtbot.addWidget(view)
    labels = view.findChildren(QLabel, "completionDoneTitle")
    assert any(lbl.text() == "Кейс сохранён" for lbl in labels)


def test_set_path_updates_label(qtbot: QtBot) -> None:
    """set_path проставляет путь в completionPathLabel."""
    view = CaseSavedView()
    qtbot.addWidget(view)

    view.set_path("C:/cases/my_case.epicase")

    assert view._path_label.text() == "C:/cases/my_case.epicase"


def test_continue_requested_signal(qtbot: QtBot) -> None:
    """Кнопка 'Продолжить редактирование' испускает continue_requested."""
    view = CaseSavedView()
    qtbot.addWidget(view)

    received: list[bool] = []
    view.continue_requested.connect(lambda: received.append(True))

    btns = view.findChildren(QPushButton, "primaryButton")
    assert len(btns) == 1
    btns[0].click()

    assert len(received) == 1


def test_home_requested_signal(qtbot: QtBot) -> None:
    """Кнопка 'На главный экран' испускает home_requested."""
    view = CaseSavedView()
    qtbot.addWidget(view)

    received: list[bool] = []
    view.home_requested.connect(lambda: received.append(True))

    # Кнопка «На главный экран» не имеет objectName — ищем по тексту.
    from PySide6.QtWidgets import QPushButton

    btns = [
        b for b in view.findChildren(QPushButton) if b.text() == "На главный экран"
    ]
    assert len(btns) == 1
    btns[0].click()

    assert len(received) == 1


def test_success_badge_fills_pixmap(qtbot: QtBot) -> None:
    """Бейдж заполняет весь pixmap: центр непрозрачен (регресс на 2x-обрезку)."""
    from epicase_constructor.ui.case_saved_view import _success_badge

    lbl = _success_badge()
    qtbot.addWidget(lbl)
    pixmap = lbl.pixmap()
    image = pixmap.toImage()
    center = image.pixelColor(pixmap.width() // 2, pixmap.height() // 2)
    assert center.alpha() == 255
