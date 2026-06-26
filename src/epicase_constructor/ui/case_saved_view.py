"""Экран подтверждения сохранения кейса в Конструкторе."""
from __future__ import annotations

from PySide6.QtCore import QByteArray, Qt, Signal
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

_SUCCESS_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 72 72" width="72" height="72">'
    b'<circle cx="36" cy="36" r="34" fill="#E6F2F1" stroke="#0F766E" stroke-width="2"/>'
    b'<path d="M22 37 l9 9 l19 -21" fill="none" stroke="#0F766E" stroke-width="5"'
    b' stroke-linecap="round" stroke-linejoin="round"/></svg>'
)


def _success_badge(size: int = 72) -> QLabel:
    """Отрендерить SVG-бейдж в QLabel с pixmap 2× для чёткости на HiDPI."""
    renderer = QSvgRenderer(QByteArray(_SUCCESS_SVG))
    px = QPixmap(size * 2, size * 2)
    px.setDevicePixelRatio(2.0)
    px.fill(Qt.GlobalColor.transparent)
    painter = QPainter(px)
    renderer.render(painter)
    painter.end()
    lbl = QLabel()
    lbl.setPixmap(px)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return lbl


class CaseSavedView(QWidget):
    """Экран подтверждения: кейс успешно сохранён.

    Сигналы:
        continue_requested — нажата кнопка «Продолжить редактирование»
        home_requested     — нажата кнопка «На главный экран»
    """

    continue_requested: Signal = Signal()
    home_requested: Signal = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._path_label = QLabel()
        self._path_label.setObjectName("completionPathLabel")
        self._path_label.setWordWrap(True)
        self._path_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        self._path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        outer = QVBoxLayout(self)
        outer.addStretch(1)

        card = QFrame()
        card.setObjectName("completionCard")
        card.setMaximumWidth(460)
        inner = QVBoxLayout(card)
        inner.setSpacing(14)
        inner.setAlignment(Qt.AlignmentFlag.AlignCenter)

        inner.addWidget(_success_badge())

        title = QLabel("Кейс сохранён")
        title.setObjectName("completionDoneTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner.addWidget(title)

        saved_lbl = QLabel("Файл кейса сохранён:")
        saved_lbl.setObjectName("completionSavedLabel")
        saved_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner.addWidget(saved_lbl)

        inner.addWidget(self._path_label)

        btn_continue = QPushButton("Продолжить редактирование")
        btn_continue.setObjectName("primaryButton")
        btn_continue.setMinimumWidth(220)
        btn_continue.clicked.connect(self.continue_requested)
        row_continue = QHBoxLayout()
        row_continue.addStretch()
        row_continue.addWidget(btn_continue)
        row_continue.addStretch()
        inner.addLayout(row_continue)

        btn_home = QPushButton("На главный экран")
        btn_home.clicked.connect(self.home_requested)
        row_home = QHBoxLayout()
        row_home.addStretch()
        row_home.addWidget(btn_home)
        row_home.addStretch()
        inner.addLayout(row_home)

        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(card)
        row.addStretch()
        outer.addLayout(row)
        outer.addStretch(1)

    def set_path(self, path: str) -> None:
        """Проставить путь к сохранённому файлу кейса."""
        self._path_label.setText(path)
