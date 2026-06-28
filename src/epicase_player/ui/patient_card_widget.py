"""Интерактивная плитка медицинской карты пациента."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QMouseEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from epicase_core.domain.stages import PatientCard


class PatientCardWidget(QFrame):
    """Плитка-идентификатор для открытия медицинской карты пациента."""

    clicked = Signal()

    def __init__(self, card: PatientCard, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.card = card
        self.setObjectName("patientCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(f"Открыть медицинскую карту: {card.title}")
        self.setMinimumHeight(124)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        marker = QFrame()
        marker.setObjectName("patientCardMarker")
        marker.setFixedWidth(64)
        marker_layout = QVBoxLayout(marker)

        marker_symbol = QLabel("+")
        marker_symbol.setObjectName("patientCardMarkerSymbol")
        marker_symbol.setAlignment(Qt.AlignmentFlag.AlignCenter)
        marker_layout.addWidget(marker_symbol)

        marker_text = QLabel("КАРТА")
        marker_text.setObjectName("patientCardMarkerText")
        marker_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        marker_layout.addWidget(marker_text)

        content = QWidget()
        content.setObjectName("patientCardContent")
        content_layout = QVBoxLayout(content)

        title = QLabel(card.title)
        title.setObjectName("patientCardTitle")
        title.setWordWrap(True)
        content_layout.addWidget(title)

        card_type = QLabel("Медицинская карта пациента")
        card_type.setObjectName("patientCardType")
        content_layout.addWidget(card_type)

        action = QLabel("Открыть карту →")
        action.setObjectName("patientCardAction")
        content_layout.addWidget(action)

        layout.addWidget(marker)
        layout.addWidget(content, 1)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Испустить clicked при нажатии основной кнопки мыши."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Испустить clicked при стандартной клавиатурной активации."""
        if event.key() in (
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
            Qt.Key.Key_Space,
        ):
            self.clicked.emit()
            event.accept()
            return
        super().keyPressEvent(event)
