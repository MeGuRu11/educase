"""Экран завершения кейса: две фазы — готов к сохранению / сохранено."""
from __future__ import annotations

from typing import ClassVar

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


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

    def _build_ready_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(16)

        title = QLabel("Все этапы пройдены")
        title.setObjectName("completionTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        subtitle = QLabel("Сохраните результат для передачи преподавателю")
        subtitle.setObjectName("completionSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        lay.addWidget(subtitle)

        btn_save = QPushButton("Сохранить результат")
        btn_save.setObjectName("completionSaveButton")
        btn_save.clicked.connect(self.save_requested)
        lay.addWidget(btn_save)

        return page

    def _build_saved_page(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(16)

        title = QLabel("Кейс пройден")
        title.setObjectName("completionDoneTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        saved_lbl = QLabel("Результат сохранён:")
        saved_lbl.setObjectName("completionSavedLabel")
        saved_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(saved_lbl)

        lay.addWidget(self._path_label)

        btn_new = QPushButton("Открыть другой кейс")
        btn_new.setObjectName("completionNewButton")
        btn_new.clicked.connect(self.new_case_requested)
        lay.addWidget(btn_new)

        btn_again = QPushButton("Сохранить ещё раз")
        btn_again.setObjectName("completionSaveAgainButton")
        btn_again.clicked.connect(self.save_requested)
        lay.addWidget(btn_again)

        return page

    def set_saved(self, path: str) -> None:
        """Переключить на фазу 'saved' и отобразить путь к файлу результата."""
        self._path_label.setText(path)
        self._stack.setCurrentIndex(self._SAVED)
