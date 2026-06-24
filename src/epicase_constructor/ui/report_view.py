"""Нейтральный read-only просмотр отчёта сверки результата (Constructor).

Секции по этапам в порядке отчёта; в каждой — строки по ``Finding``: статус элемента
(«верно»/«неверно» как факт данных), подпись и приглушённый контекст ответа. БЕЗ итогов,
баллов, процентов и вердикта pass/fail — формат оценивания кафедры подключится позже поверх
этой структуры. Только виджеты и layout-менеджеры, без inline-стиля.
"""
from __future__ import annotations

from PySide6.QtWidgets import QGroupBox, QLabel, QVBoxLayout, QWidget

from epicase_core.domain.report import CaseReport, Finding
from epicase_core.domain.stages import StageKind

_STAGE_TITLES: dict[StageKind, str] = {
    StageKind.PATIENTS: "Пациенты",
    StageKind.CLINICAL: "Клинико-эпидемиологический диагноз",
    StageKind.CONTACTS: "Обследование контактных лиц",
    StageKind.ENVIRONMENT: "Обследование объектов внешней среды",
    StageKind.SES: "Оценка СЭС",
    StageKind.FINAL: "Окончательный эпидемиологический диагноз",
}


class ReportView(QWidget):
    """Просмотр отчёта: по секции (``QGroupBox``) на этап, по строке на проверяемый элемент."""

    def __init__(self, report: CaseReport, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        for stage in report.stages:
            layout.addWidget(self._stage_box(stage.kind, stage.findings))
        layout.addStretch(1)

    def _stage_box(self, kind: StageKind, findings: tuple[Finding, ...]) -> QGroupBox:
        """Секция одного этапа: заголовок + строки findings (или плейсхолдер, если их нет)."""
        box = QGroupBox(_STAGE_TITLES.get(kind, kind.value))
        box_layout = QVBoxLayout(box)
        if not findings:
            box_layout.addWidget(QLabel("— нет проверяемых элементов —"))
        else:
            for finding in findings:
                box_layout.addWidget(QLabel(self._finding_text(finding)))
        return box

    @staticmethod
    def _finding_text(finding: Finding) -> str:
        """Строка элемента: статус + подпись (или id) + приглушённый контекст (если есть)."""
        status = "верно" if finding.correct else "неверно"
        name = finding.label or finding.element_id
        text = f"[{status}] {name}"
        if finding.detail:
            text += f" — {finding.detail}"
        return text
