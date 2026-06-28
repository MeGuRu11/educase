"""Модальный read-only диалог медицинской карты пациента."""
from __future__ import annotations

from collections.abc import Mapping

from PySide6.QtCore import Qt
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

from epicase_core.domain.stages import PatientCard
from epicase_player.ui.asset_image_widget import AssetImageWidget


class PatientDetailDialog(QDialog):
    """Показывает первичные данные и материалы пациента без редактирования."""

    def __init__(
        self,
        card: PatientCard,
        assets: Mapping[str, bytes],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("patientDetailDialog")
        self.setWindowTitle(card.title)
        self.setModal(True)
        self.setMinimumWidth(600)
        self.resize(720, 560)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QFrame()
        header.setObjectName("patientDetailHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(24, 18, 24, 18)

        eyebrow = QLabel("Медицинская карта пациента")
        eyebrow.setObjectName("patientDetailEyebrow")
        header_layout.addWidget(eyebrow)

        title = QLabel(card.title)
        title.setObjectName("patientDetailTitle")
        title.setWordWrap(True)
        header_layout.addWidget(title)
        outer.addWidget(header)

        scroll = QScrollArea()
        scroll.setObjectName("patientDetailScroll")
        scroll.setWidgetResizable(True)

        body = QFrame()
        body.setObjectName("patientDetailBody")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(24, 20, 24, 20)

        if card.fields:
            for name, value in card.fields:
                field_row = QFrame()
                field_row.setObjectName("patientFieldRow")
                field_layout = QVBoxLayout(field_row)
                field_layout.setContentsMargins(0, 0, 0, 0)

                name_label = QLabel(name)
                name_label.setObjectName("patientFieldName")
                name_label.setWordWrap(True)
                field_layout.addWidget(name_label)

                value_label = QLabel(value)
                value_label.setObjectName("patientFieldValue")
                value_label.setWordWrap(True)
                value_label.setTextInteractionFlags(
                    Qt.TextInteractionFlag.TextSelectableByMouse
                )
                field_layout.addWidget(value_label)

                body_layout.addWidget(field_row)
        else:
            empty_state = QLabel("Первичные данные не заполнены")
            empty_state.setObjectName("patientEmptyState")
            empty_state.setWordWrap(True)
            body_layout.addWidget(empty_state)

        if card.assets:
            materials_title = QLabel("Материалы пациента")
            materials_title.setObjectName("patientMaterialsTitle")
            body_layout.addWidget(materials_title)

            for asset_id in card.assets:
                body_layout.addWidget(AssetImageWidget(asset_id, assets))

        body_layout.addStretch()
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

        footer = QFrame()
        footer.setObjectName("patientDetailFooter")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(24, 16, 24, 16)
        footer_layout.addStretch()

        close_button = QPushButton("Закрыть")
        close_button.setObjectName("patientDetailClose")
        close_button.clicked.connect(self.accept)
        footer_layout.addWidget(close_button)
        outer.addWidget(footer)
