"""Тесты клинической плитки PatientCardWidget."""
from __future__ import annotations

import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QFrame, QLabel, QWidget
from pytestqt.qtbot import QtBot

from epicase_core.domain.stages import PatientCard
from epicase_player.ui.patient_card_widget import PatientCardWidget


def _label_text(widget: PatientCardWidget, object_name: str) -> str:
    label = widget.findChild(QLabel, object_name)
    assert label is not None
    return label.text()


def _patient_card() -> PatientCard:
    return PatientCard(
        id="patient-internal-731",
        title="Рядовой Иванов",
        fields=(("Диагноз", "Сальмонеллёз"), ("Температура", "39,2 °C")),
    )


def test_card_displays_only_identification(qtbot: QtBot) -> None:
    """На плитке остаются заголовок, тип карты и действие."""
    card = _patient_card()
    widget = PatientCardWidget(card)
    qtbot.addWidget(widget)

    assert _label_text(widget, "patientCardTitle") == card.title
    assert _label_text(widget, "patientCardType") == "Медицинская карта пациента"
    assert _label_text(widget, "patientCardAction") == "Открыть карту →"

    visible_text = " ".join(label.text() for label in widget.findChildren(QLabel))
    assert card.id not in visible_text
    for field_name, field_value in card.fields:
        assert field_name not in visible_text
        assert field_value not in visible_text


def test_card_displays_medical_marker(qtbot: QtBot) -> None:
    """Маркер однозначно обозначает медицинскую карту."""
    widget = PatientCardWidget(_patient_card())
    qtbot.addWidget(widget)

    assert _label_text(widget, "patientCardMarkerSymbol") == "+"
    assert _label_text(widget, "patientCardMarkerText") == "КАРТА"


def test_card_exposes_marker_and_content_structure(qtbot: QtBot) -> None:
    """Структура плитки доступна QSS и сохраняет заданные размеры."""
    widget = PatientCardWidget(_patient_card())
    qtbot.addWidget(widget)

    marker = widget.findChild(QFrame, "patientCardMarker")
    assert marker is not None
    assert marker.width() == 64
    assert marker.minimumWidth() == 64
    assert marker.maximumWidth() == 64

    content = widget.findChild(QWidget, "patientCardContent")
    assert content is not None

    title = widget.findChild(QLabel, "patientCardTitle")
    assert title is not None
    assert title.wordWrap() is True


def test_card_has_interactive_frame_contract(qtbot: QtBot) -> None:
    """Корневая рамка доступна с мыши и клавиатуры."""
    card = _patient_card()
    widget = PatientCardWidget(card)
    qtbot.addWidget(widget)

    assert isinstance(widget, QFrame)
    assert widget.objectName() == "patientCard"
    assert widget.cursor().shape() == Qt.CursorShape.PointingHandCursor
    assert widget.focusPolicy() == Qt.FocusPolicy.StrongFocus
    assert widget.accessibleName() == f"Открыть медицинскую карту: {card.title}"
    assert widget.minimumHeight() >= 120


def test_left_click_emits_clicked(qtbot: QtBot) -> None:
    """Левый клик открывает медицинскую карту ровно один раз."""
    widget = PatientCardWidget(_patient_card())
    qtbot.addWidget(widget)
    widget.show()
    clicked_spy = QSignalSpy(widget.clicked)

    qtbot.mouseClick(  # type: ignore[no-untyped-call]  # pytest-qt lacks stubs
        widget,
        Qt.MouseButton.LeftButton,
    )

    assert clicked_spy.count() == 1


def test_clicking_title_emits_clicked_once(qtbot: QtBot) -> None:
    """Клик по дочернему заголовку активирует всю поверхность плитки."""
    widget = PatientCardWidget(_patient_card())
    qtbot.addWidget(widget)
    widget.show()
    title = widget.findChild(QLabel, "patientCardTitle")
    assert title is not None
    clicked_spy = QSignalSpy(widget.clicked)

    qtbot.mouseClick(  # type: ignore[no-untyped-call]  # pytest-qt lacks stubs
        title,
        Qt.MouseButton.LeftButton,
    )

    assert clicked_spy.count() == 1


def test_right_click_does_not_emit_clicked(qtbot: QtBot) -> None:
    """Правая кнопка мыши не открывает медицинскую карту."""
    widget = PatientCardWidget(_patient_card())
    qtbot.addWidget(widget)
    widget.show()
    clicked_spy = QSignalSpy(widget.clicked)

    qtbot.mouseClick(  # type: ignore[no-untyped-call]  # pytest-qt lacks stubs
        widget,
        Qt.MouseButton.RightButton,
    )

    assert clicked_spy.count() == 0


@pytest.mark.parametrize(
    "key",
    [Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space],
)
def test_activation_key_emits_clicked_once(qtbot: QtBot, key: Qt.Key) -> None:
    """Return, Enter и Space открывают карту ровно один раз."""
    widget = PatientCardWidget(_patient_card())
    qtbot.addWidget(widget)
    widget.show()
    widget.setFocus()
    clicked_spy = QSignalSpy(widget.clicked)

    qtbot.keyClick(  # type: ignore[no-untyped-call]  # pytest-qt lacks stubs
        widget,
        key,
    )

    assert clicked_spy.count() == 1


def test_non_activation_key_does_not_emit_clicked(qtbot: QtBot) -> None:
    """Обычная клавиша не открывает медицинскую карту."""
    widget = PatientCardWidget(_patient_card())
    qtbot.addWidget(widget)
    widget.show()
    widget.setFocus()
    clicked_spy = QSignalSpy(widget.clicked)

    qtbot.keyClick(  # type: ignore[no-untyped-call]  # pytest-qt lacks stubs
        widget,
        Qt.Key.Key_A,
    )

    assert clicked_spy.count() == 0


def test_activation_key_event_is_accepted(qtbot: QtBot) -> None:
    """Обработанное нажатие принимается и не передаётся дальше."""
    widget = PatientCardWidget(_patient_card())
    qtbot.addWidget(widget)
    clicked_spy = QSignalSpy(widget.clicked)
    event = QKeyEvent(
        QEvent.Type.KeyPress,
        Qt.Key.Key_Return,
        Qt.KeyboardModifier.NoModifier,
    )
    event.ignore()
    assert event.isAccepted() is False

    widget.keyPressEvent(event)

    assert event.isAccepted() is True
    assert clicked_spy.count() == 1
