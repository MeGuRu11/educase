"""Виджет карточки пациента: поля + заглушка ассетов (ADR-012)."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from epicase_core.domain.stages import PatientCard


class PatientCardWidget(QWidget):
    """Отображение карточки пациента: заголовок, строки «ключ: значение», ассеты-заглушка."""

    clicked = Signal()

    def __init__(self, card: PatientCard, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.card = card
        self.setObjectName("patientCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)

        group = QGroupBox(card.title)
        group_layout = QVBoxLayout(group)

        for key, value in card.fields:
            row = QLabel(f"{key}: {value}")
            row.setWordWrap(True)
            group_layout.addWidget(row)

        if card.assets:
            asset_ids = ", ".join(card.assets)
            stub = QLabel(f"Материалы: {asset_ids}")  # TODO ADR-012 рендер ассетов
            stub.setEnabled(False)
            group_layout.addWidget(stub)

        layout.addWidget(group)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.clicked.emit()
        super().mousePressEvent(event)
