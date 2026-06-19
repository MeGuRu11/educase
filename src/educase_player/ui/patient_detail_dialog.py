"""Модальный диалог полной информации о пациенте (read-only, ADR-008)."""
from __future__ import annotations

from collections.abc import Mapping

from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from educase_core.domain.stages import PatientCard
from educase_player.ui.asset_image_widget import AssetImageWidget


class PatientDetailDialog(QDialog):
    """Полная карточка пациента: все поля и фото в натуральном размере."""

    def __init__(
        self,
        card: PatientCard,
        assets: Mapping[str, bytes],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("schemeReveal")
        self.setWindowTitle(card.title)
        self.setMinimumWidth(420)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(10)

        title_label = QLabel(card.title)
        title_label.setObjectName("schemeRevealTitle")
        title_label.setWordWrap(True)
        outer.addWidget(title_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        card_frame = QFrame()
        card_frame.setObjectName("schemeRevealCard")
        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(8)

        for key, value in card.fields:
            field_label = QLabel(f"{key}: {value}")
            field_label.setWordWrap(True)
            card_layout.addWidget(field_label)

        for asset_id in card.assets:
            card_layout.addWidget(AssetImageWidget(asset_id, assets))

        scroll.setWidget(card_frame)
        outer.addWidget(scroll)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Закрыть")
        close_btn.setObjectName("schemeRevealClose")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        outer.addLayout(btn_row)
