"""Тесты FlowLayout и PatientsStageView с плиточной раскладкой (C3)."""
from __future__ import annotations

from PySide6.QtWidgets import QLabel, QWidget
from pytestqt.qtbot import QtBot

from epicase_core.domain.stages import PatientCard, StagePatients
from epicase_player.ui.flow_layout import FlowLayout
from epicase_player.ui.patient_card_widget import PatientCardWidget
from epicase_player.ui.stage_views import build_stage_view


def test_flow_layout_smoke(qtbot: QtBot) -> None:
    """FlowLayout создаётся и принимает дочерние виджеты."""
    container = QWidget()
    qtbot.addWidget(container)
    layout = FlowLayout(container)
    for i in range(3):
        label = QLabel(f"Item {i}", container)
        layout.addWidget(label)
    assert layout.count() == 3


def test_flow_layout_item_at(qtbot: QtBot) -> None:
    """itemAt возвращает элемент по индексу и None за границей."""
    container = QWidget()
    qtbot.addWidget(container)
    layout = FlowLayout(container)
    label = QLabel("X", container)
    layout.addWidget(label)
    assert layout.itemAt(0) is not None
    assert layout.itemAt(1) is None
    assert layout.itemAt(-1) is None


def test_flow_layout_take_at(qtbot: QtBot) -> None:
    """takeAt удаляет и возвращает элемент; count уменьшается."""
    container = QWidget()
    qtbot.addWidget(container)
    layout = FlowLayout(container)
    layout.addWidget(QLabel("A", container))
    layout.addWidget(QLabel("B", container))
    assert layout.count() == 2
    item = layout.takeAt(0)
    assert item is not None
    assert layout.count() == 1


def test_patients_stage_view_flow_container(qtbot: QtBot) -> None:
    """PatientsStageView с N пациентами строит flow-контейнер с N PatientCardWidget."""
    cards = [
        PatientCard(id=f"p{i}", title=f"Пациент {i}", fields=(("Диагноз", "ОКИ"),))
        for i in range(4)
    ]
    stage = StagePatients(patients=tuple(cards))
    view = build_stage_view(stage)
    qtbot.addWidget(view)

    widgets: list[PatientCardWidget] = view.findChildren(PatientCardWidget)
    assert len(widgets) == 4


def test_patients_stage_view_card_max_width(qtbot: QtBot) -> None:
    """Карточки пациентов ограничены по ширине (setMaximumWidth)."""
    card = PatientCard(id="p1", title="Пациент 1", fields=(("Диагноз", "ОРВИ"),))
    stage = StagePatients(patients=(card,))
    view = build_stage_view(stage)
    qtbot.addWidget(view)

    widgets: list[PatientCardWidget] = view.findChildren(PatientCardWidget)
    assert len(widgets) == 1
    assert widgets[0].maximumWidth() <= 340
