"""Стартовый экран Constructor: приветствие + два действия (ADR-009)."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


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

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.setSpacing(0)

        center = QWidget()
        center.setMaximumWidth(480)
        col = QVBoxLayout(center)
        col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.setSpacing(12)

        title = QLabel("EduCase — Конструктор")
        title.setObjectName("startTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(title)

        subtitle = QLabel("Сборка учебного кейса: шесть этапов")
        subtitle.setObjectName("startSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(subtitle)

        col.addSpacing(24)

        btn_create = QPushButton("Создать новый кейс")
        btn_create.setObjectName("startAccentButton")
        btn_create.clicked.connect(self.create_requested)
        col.addWidget(btn_create)

        col.addSpacing(8)

        btn_open = QPushButton("Открыть кейс для правки")
        btn_open.setObjectName("startSecondaryButton")
        btn_open.clicked.connect(self.open_requested)
        col.addWidget(btn_open)

        col.addSpacing(8)

        btn_check = QPushButton("Проверить результат курсанта")
        btn_check.setObjectName("startSecondaryButton")
        btn_check.clicked.connect(self.check_result_requested)
        col.addWidget(btn_check)

        h = QHBoxLayout()
        h.addStretch()
        h.addWidget(center)
        h.addStretch()
        root.addLayout(h)
