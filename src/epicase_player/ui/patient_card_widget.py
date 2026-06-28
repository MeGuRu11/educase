"""Виджет карточки пациента: заголовок + подсказка по клику."""
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
    """Отображение карточки пациента: заголовок и подсказка о деталях по клику."""

    clicked = Signal()

    def __init__(self, card: PatientCard, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.card = card
        self.setObjectName("patientCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)

        group = QGroupBox(card.title)
        group_layout = QVBoxLayout(group)

        hint = QLabel("Подробности — по клику")
        hint.setObjectName("mutedHint")
        hint.setEnabled(False)
        group_layout.addWidget(hint)

        layout.addWidget(group)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.clicked.emit()
        super().mousePressEvent(event)
