"""Виджет свободного вывода осмотра объектов (ADR-008/ADR-012)."""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from educase_core.domain.search import InspectionCheck


@dataclass(frozen=True)
class InspectionResult:
    """Результат осмотра: покрытие ожидаемых групп (для финального отчёта)."""

    covered: tuple[bool, ...]


class InspectionWidget(QWidget):
    """Свободный вывод осмотра: приглашение + поле ввода + кнопка сохранения.

    Ожидаемые ключевые слова не показываются курсанту (ADR-005).
    Сверка делегируется InspectionCheck.covered (ADR-006).
    Неверный или неполный осмотр не блокирует навигацию (ADR-008).
    """

    def __init__(self, inspection: InspectionCheck, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._inspection = inspection
        self._result: InspectionResult | None = None

        layout = QVBoxLayout(self)

        invite = QLabel("Опишите результаты осмотра:")
        invite.setWordWrap(True)
        layout.addWidget(invite)

        self.output = QPlainTextEdit()
        layout.addWidget(self.output)

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
    def result(self) -> InspectionResult | None:
        """Результат последнего on_submit; None до нажатия «Сохранить»."""
        return self._result

    def text(self) -> str:
        """Текущий текст вывода осмотра (сырой, без сверки)."""
        return self.output.toPlainText()

    def on_submit(self) -> None:
        """Сохранить результат; вердикт не показывать (ADR-005/ADR-008)."""
        text = self.output.toPlainText()
        self._result = InspectionResult(covered=self._inspection.covered(text))
        self._status_label.setText("Сохранено")
