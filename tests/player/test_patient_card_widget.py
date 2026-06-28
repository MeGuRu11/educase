"""Тесты PatientCardWidget: заголовок, подсказка по клику, сигнал clicked."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGroupBox, QLabel
from pytestqt.qtbot import QtBot

from epicase_core.domain.stages import PatientCard
from epicase_player.ui.patient_card_widget import PatientCardWidget


def test_title_displayed(qtbot: QtBot) -> None:
    """Заголовок карточки присутствует в QGroupBox."""
    card = PatientCard(id="p1", title="Пациент 1", fields=(("Диагноз", "ОРВИ"),))
    w = PatientCardWidget(card)
    qtbot.addWidget(w)

    groups: list[QGroupBox] = w.findChildren(QGroupBox)
    assert any(g.title() == "Пациент 1" for g in groups)


def test_fields_not_on_face(qtbot: QtBot) -> None:
    """Строки «ключ: значение» НЕ отображаются на лице карточки."""
    card = PatientCard(
        id="p1",
        title="Пациент 1",
        fields=(("Диагноз", "сальмонеллёз"), ("Возраст", "25 лет")),
    )
    w = PatientCardWidget(card)
    qtbot.addWidget(w)

    texts = [lbl.text() for lbl in w.findChildren(QLabel)]
    assert not any("Диагноз: сальмонеллёз" in t for t in texts)
    assert not any("Возраст: 25 лет" in t for t in texts)


def test_clicked_signal_emitted_on_mouse_press(qtbot: QtBot) -> None:
    """Сигнал clicked испускается при mousePressEvent."""
    card = PatientCard(id="p4", title="Пациент 4", fields=())
    w = PatientCardWidget(card)
    qtbot.addWidget(w)
    w.show()

    with qtbot.waitSignal(w.clicked, timeout=1000):
        qtbot.mouseClick(w, Qt.MouseButton.LeftButton)  # type: ignore[no-untyped-call]  # pytest-qt lacks stubs
