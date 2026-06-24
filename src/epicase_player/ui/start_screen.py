"""Стартовый экран Player: приветствие + кнопка открытия кейса."""
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
    """Центральный виджет — первое, что видит курсант.

    Сигналы:
        open_requested — нажата кнопка «Открыть кейс…»
    """

    open_requested: Signal = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.setSpacing(0)

        center = QWidget()
        center.setMaximumWidth(440)
        col = QVBoxLayout(center)
        col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.setSpacing(12)

        title = QLabel("EduCase")
        title.setObjectName("startTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(title)

        subtitle = QLabel("Учебный тренажёр военного эпидемиолога")
        subtitle.setObjectName("startSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(subtitle)

        col.addSpacing(24)

        btn_open = QPushButton("Открыть кейс…")
        btn_open.setObjectName("startAccentButton")
        btn_open.clicked.connect(self.open_requested)
        col.addWidget(btn_open)

        col.addSpacing(8)

        hint = QLabel("Откройте файл .epicase, полученный от преподавателя")
        hint.setObjectName("startHint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setWordWrap(True)
        col.addWidget(hint)

        h = QHBoxLayout()
        h.addStretch()
        h.addWidget(center)
        h.addStretch()
        root.addLayout(h)
