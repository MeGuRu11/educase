"""Стартовый экран Player: приветствие + кнопка открытия кейса."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from epicase_ui.animated_start import AnimatedStartWidget, StartVariant
from epicase_ui.brand_mark import BrandMarkWidget
from epicase_ui.branding import BrandAsset


class StartScreen(QWidget):
    """Центральный виджет — первое, что видит курсант.

    Сигналы:
        open_requested — нажата кнопка «Открыть кейс…»
    """

    open_requested: Signal = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("playerStartScreen")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        card = QFrame()
        card.setMaximumWidth(460)
        col = QVBoxLayout(card)
        col.setContentsMargins(28, 24, 28, 24)
        col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.setSpacing(9)

        mark = BrandMarkWidget(BrandAsset.PLAYER)
        mark.setFixedSize(76, 76)
        col.addWidget(mark, alignment=Qt.AlignmentFlag.AlignCenter)

        title = QLabel("EpiCase")
        title.setObjectName("startTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(title)

        product = QLabel("PLAYER")
        product.setObjectName("startProduct")
        product.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(product)

        role = QLabel("Учебный тренажёр военного эпидемиолога")
        role.setObjectName("startRole")
        role.setAlignment(Qt.AlignmentFlag.AlignCenter)
        role.setWordWrap(True)
        col.addWidget(role)
        col.addSpacing(16)

        btn_open = QPushButton("Открыть кейс…")
        btn_open.setObjectName("startAccentButton")
        btn_open.clicked.connect(self.open_requested)
        col.addWidget(btn_open)

        hint = QLabel("Откройте файл .epicase, полученный от преподавателя")
        hint.setObjectName("startHint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setWordWrap(True)
        col.addWidget(hint)

        animated = AnimatedStartWidget(StartVariant.PLAYER, card, mark)
        root.addWidget(animated)
