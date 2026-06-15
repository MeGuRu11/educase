"""Виджет точки ветвления «Вариант B» (ADR-005/ADR-008)."""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from educase_core.domain.stages import BranchOption, BranchPoint


@dataclass(frozen=True)
class BranchResult:
    """Результат выбора в точке ветвления (для финального отчёта)."""

    option_id: str | None
    option_correct: bool


class BranchWidget(QWidget):
    """Равноправный блок ветвления: выбор варианта, нейтральный ответ, без блокировки (ADR-005/008).

    Паттерн идентичен DocumentWidget: выбор → «Сохранить» → нейтральное сообщение.
    Вердикт курсанту не показывается.
    """

    def __init__(self, branch: BranchPoint, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._branch = branch
        self._result: BranchResult | None = None

        layout = QVBoxLayout(self)

        prompt_label = QLabel(branch.prompt)
        prompt_label.setWordWrap(True)
        layout.addWidget(prompt_label)

        self.options_combo = QComboBox()
        self.options_combo.addItem("— выберите —")
        for option in branch.options:
            self.options_combo.addItem(option.label)
        layout.addWidget(self.options_combo)

        self.btn_submit = QPushButton("Сохранить")
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.btn_submit)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._status_label = QLabel()
        self._status_label.setObjectName("mutedHint")
        layout.addWidget(self._status_label)

        self.btn_submit.clicked.connect(self.on_submit)

    @property
    def result(self) -> BranchResult | None:
        """Результат последнего on_submit; None до нажатия «Сохранить»."""
        return self._result

    def selected_option(self) -> BranchOption | None:
        """Выбранный BranchOption; None при плейсхолдере (индекс 0)."""
        idx = self.options_combo.currentIndex()
        if idx == 0:
            return None
        return self._branch.options[idx - 1]

    def on_submit(self) -> None:
        """Сохранить выбор; вердикт не показывать (ADR-005/ADR-008)."""
        option = self.selected_option()
        self._result = BranchResult(
            option_id=option.id if option is not None else None,
            option_correct=option is not None and option.is_correct,
        )
        self._status_label.setText("Сохранено")
