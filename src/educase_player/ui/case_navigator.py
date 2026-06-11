"""Виджет навигации по шести фиксированным этапам кейса."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from educase_core.domain.case import Case
from educase_player.ui.stage_views import build_stage_view


class CaseNavigator(QWidget):
    """Навигатор по этапам: стек страниц + строка позиции + кнопки Назад/Далее.

    Навигация не блокируется ответами курсанта (ADR-005/008): свободный переход
    вперёд/назад по всем шести этапам независимо от введённых данных.
    """

    def __init__(self, case: Case, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        stages = case.ordered()
        self._titles: tuple[str, ...] = tuple(s.title for s in stages)

        layout = QVBoxLayout(self)

        self._position_label = QLabel()
        layout.addWidget(self._position_label)

        self.stack = QStackedWidget()
        for stage in stages:
            self.stack.addWidget(build_stage_view(stage))
        layout.addWidget(self.stack, 1)

        nav_layout = QHBoxLayout()
        self.btn_prev = QPushButton("Назад")
        self.btn_next = QPushButton("Далее")
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_next)
        layout.addLayout(nav_layout)

        self.btn_prev.clicked.connect(self._go_prev)
        self.btn_next.clicked.connect(self._go_next)

        self._refresh()

    @property
    def current_index(self) -> int:
        """Текущий индекс активного этапа (0-based)."""
        return self.stack.currentIndex()

    def _refresh(self) -> None:
        idx = self.stack.currentIndex()
        count = self.stack.count()
        self._position_label.setText(
            f"Этап {idx + 1} из {count} — {self._titles[idx]}"
        )
        self.btn_prev.setEnabled(idx > 0)
        self.btn_next.setEnabled(idx < count - 1)

    def _go_prev(self) -> None:
        idx = self.stack.currentIndex()
        if idx > 0:
            self.stack.setCurrentIndex(idx - 1)
            self._refresh()

    def _go_next(self) -> None:
        idx = self.stack.currentIndex()
        if idx < self.stack.count() - 1:
            self.stack.setCurrentIndex(idx + 1)
            self._refresh()
