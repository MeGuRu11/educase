"""Экран завершения кейса: две фазы — готов к сохранению / сохранено."""
from __future__ import annotations

from typing import ClassVar

from PySide6.QtCore import QByteArray, Qt, Signal
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
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


class CompletionView(QWidget):
    """Две фазы завершения: 'ready' (до сохранения) и 'saved' (после сохранения).

    Сигналы:
        save_requested     — нажата кнопка «Сохранить результат» или «Сохранить ещё раз»
        new_case_requested — нажата кнопка «Открыть другой кейс»
    """

    save_requested: Signal = Signal()
    new_case_requested: Signal = Signal()

    _READY: ClassVar[int] = 0
    _SAVED: ClassVar[int] = 1

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        self._stack = QStackedWidget()
        layout.addWidget(self._stack)

        self._path_label = QLabel()
        self._path_label.setObjectName("completionPathLabel")
        self._path_label.setWordWrap(True)
        self._path_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        self._path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._stack.addWidget(self._build_ready_page())
        self._stack.addWidget(self._build_saved_page())
        self._stack.setCurrentIndex(self._READY)

    def _make_card(self) -> tuple[QFrame, QVBoxLayout]:
        """Создать QFrame#completionCard с VBox-inner и вернуть обоих."""
        card = QFrame()
        card.setObjectName("completionCard")
        card.setMaximumWidth(460)
        inner = QVBoxLayout(card)
        inner.setSpacing(14)
        inner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return card, inner

    @staticmethod
    def _centered_btn(btn: QPushButton, layout: QVBoxLayout) -> None:
        """Добавить кнопку в layout, обёрнутую в центрирующий HBox."""
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(btn)
        row.addStretch()
        layout.addLayout(row)

    def _build_ready_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.addStretch(1)

        card, inner = self._make_card()

        inner.addWidget(_success_badge())

        title = QLabel("Все этапы пройдены")
        title.setObjectName("completionTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner.addWidget(title)

        subtitle = QLabel("Сохраните результат для передачи преподавателю")
        subtitle.setObjectName("completionSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        inner.addWidget(subtitle)

        btn_save = QPushButton("Сохранить результат")
        btn_save.setObjectName("completionSaveButton")
        btn_save.setMinimumWidth(220)
        btn_save.clicked.connect(self.save_requested)
        self._centered_btn(btn_save, inner)

        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(card)
        row.addStretch()
        outer.addLayout(row)
        outer.addStretch(1)

        return page

    def _build_saved_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.addStretch(1)

        card, inner = self._make_card()

        inner.addWidget(_success_badge())

        title = QLabel("Кейс пройден")
        title.setObjectName("completionDoneTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner.addWidget(title)

        saved_lbl = QLabel("Результат сохранён:")
        saved_lbl.setObjectName("completionSavedLabel")
        saved_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner.addWidget(saved_lbl)

        inner.addWidget(self._path_label)

        btn_new = QPushButton("Открыть другой кейс")
        btn_new.setObjectName("completionNewButton")
        btn_new.clicked.connect(self.new_case_requested)
        self._centered_btn(btn_new, inner)

        btn_again = QPushButton("Сохранить ещё раз")
        btn_again.setObjectName("completionSaveAgainButton")
        btn_again.clicked.connect(self.save_requested)
        self._centered_btn(btn_again, inner)

        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(card)
        row.addStretch()
        outer.addLayout(row)
        outer.addStretch(1)

        return page

    def set_saved(self, path: str) -> None:
        """Переключить на фазу 'saved' и отобразить путь к файлу результата."""
        self._path_label.setText(path)
        self._stack.setCurrentIndex(self._SAVED)
