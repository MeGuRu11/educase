"""Стартовый экран Constructor: приветствие + два действия (ADR-009)."""
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
    """Центральный виджет — первое, что видит преподаватель.

    Сигналы:
        create_requested — нажата кнопка «Создать новый кейс»
        open_requested — нажата кнопка «Открыть кейс для правки»
        check_result_requested — нажата кнопка «Проверить результат курсанта»
    """

    create_requested: Signal = Signal()
    open_requested: Signal = Signal()
    check_result_requested: Signal = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("constructorStartScreen")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        card = QFrame()
        card.setMaximumWidth(520)
        col = QVBoxLayout(card)
        col.setContentsMargins(30, 24, 30, 24)
        col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.setSpacing(8)

        mark = BrandMarkWidget(BrandAsset.CONSTRUCTOR)
        mark.setFixedSize(76, 76)
        col.addWidget(mark, alignment=Qt.AlignmentFlag.AlignCenter)

        title = QLabel("EpiCase")
        title.setObjectName("startTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(title)

        product = QLabel("КОНСТРУКТОР")
        product.setObjectName("startProduct")
        product.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(product)

        role = QLabel("Рабочее место преподавателя")
        role.setObjectName("startRole")
        role.setAlignment(Qt.AlignmentFlag.AlignCenter)
        role.setWordWrap(True)
        col.addWidget(role)

        col.addSpacing(14)

        btn_create = QPushButton("Создать новый кейс")
        btn_create.setObjectName("startAccentButton")
        btn_create.clicked.connect(self.create_requested)
        col.addWidget(btn_create)

        btn_open = QPushButton("Открыть кейс для правки")
        btn_open.setObjectName("startSecondaryButton")
        btn_open.clicked.connect(self.open_requested)
        col.addWidget(btn_open)

        btn_check = QPushButton("Проверить результат курсанта")
        btn_check.setObjectName("startSecondaryButton")
        btn_check.clicked.connect(self.check_result_requested)
        col.addWidget(btn_check)

        animated = AnimatedStartWidget(StartVariant.CONSTRUCTOR, card, mark)
        root.addWidget(animated)
