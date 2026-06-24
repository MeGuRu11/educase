"""Тесты PatientCardWidget: отображение полей, заглушки ассетов и сигнал clicked."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel
from pytestqt.qtbot import QtBot

from epicase_core.domain.stages import PatientCard
from epicase_player.ui.patient_card_widget import PatientCardWidget


def test_fields_displayed(qtbot: QtBot) -> None:
    """Поля карты отображаются как строки «ключ: значение»."""
    card = PatientCard(
        id="p1",
        title="Пациент 1",
        fields=(("Диагноз", "сальмонеллёз"), ("Возраст", "25 лет")),
    )
    w = PatientCardWidget(card)
    qtbot.addWidget(w)

    texts = [lbl.text() for lbl in w.findChildren(QLabel)]
    assert any("Диагноз: сальмонеллёз" in t for t in texts)
    assert any("Возраст: 25 лет" in t for t in texts)


def test_assets_stub_shown_when_present(qtbot: QtBot) -> None:
    """При наличии ассетов отображается приглушённая строка-заглушка с id."""
    card = PatientCard(
        id="p2",
        title="Пациент 2",
        fields=(),
        assets=("img_01", "img_02"),
    )
    w = PatientCardWidget(card)
    qtbot.addWidget(w)

    texts = [lbl.text() for lbl in w.findChildren(QLabel)]
    assert any("Материалы:" in t and "img_01" in t for t in texts)


def test_no_assets_stub_when_absent(qtbot: QtBot) -> None:
    """Без ассетов строка «Материалы:» не появляется."""
    card = PatientCard(id="p3", title="Пациент 3", fields=(), assets=())
    w = PatientCardWidget(card)
    qtbot.addWidget(w)

    texts = [lbl.text() for lbl in w.findChildren(QLabel)]
    assert not any("Материалы:" in t for t in texts)


def test_clicked_signal_emitted_on_mouse_press(qtbot: QtBot) -> None:
    """Сигнал clicked испускается при mousePressEvent."""
    card = PatientCard(id="p4", title="Пациент 4", fields=())
    w = PatientCardWidget(card)
    qtbot.addWidget(w)
    w.show()

    with qtbot.waitSignal(w.clicked, timeout=1000):
        qtbot.mouseClick(w, Qt.MouseButton.LeftButton)  # type: ignore[no-untyped-call]  # pytest-qt lacks stubs
