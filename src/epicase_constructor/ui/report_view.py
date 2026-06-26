"""Нейтральный read-only просмотр отчёта сверки результата (Constructor).

Секции по этапам в порядке отчёта; в каждой — строки по ``Finding``: статус элемента
(«верно»/«неверно» как факт данных), подпись и приглушённый контекст ответа. На этапе 6
дополнительно показываются ``TimelineComparison`` — эталон кейса рядом с вводом курсанта,
БЕЗ пометок верно/неверно. БЕЗ итогов, баллов, процентов и вердикта pass/fail — формат
оценивания кафедры подключится позже поверх этой структуры. Только виджеты и
layout-менеджеры, без inline-стиля.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from epicase_core.domain.report import (
    CaseReport,
    Finding,
    StageReport,
    TimelineComparison,
)
from epicase_core.domain.stages import StageKind

_STAGE_TITLES: dict[StageKind, str] = {
    StageKind.PATIENTS: "Пациенты",
    StageKind.CLINICAL: "Клинико-эпидемиологический диагноз",
    StageKind.CONTACTS: "Обследование контактных лиц",
    StageKind.ENVIRONMENT: "Обследование объектов внешней среды",
    StageKind.SES: "Оценка СЭС",
    StageKind.FINAL: "Окончательный эпидемиологический диагноз",
}

_TIMELINES_HEADER = "Эпидемиологические таймлайны"
_AUTHORED_CAPTION = "Эталон"
_CADET_CAPTION = "Введено курсантом"
_EMPTY_COLUMN = "не заполнено"


class ReportView(QWidget):
    """Просмотр отчёта: по секции (``QGroupBox``) на этап, по строке на проверяемый элемент."""

    def __init__(self, report: CaseReport, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        for stage in report.stages:
            layout.addWidget(self._stage_box(stage))
        layout.addStretch(1)

    def _stage_box(self, stage: StageReport) -> QGroupBox:
        """Секция этапа: строки findings + (для этапа 6) таймлайны, либо плейсхолдер пустоты."""
        box = QGroupBox(_STAGE_TITLES.get(stage.kind, stage.kind.value))
        box_layout = QVBoxLayout(box)
        if not stage.findings and not stage.timelines:
            box_layout.addWidget(QLabel("— нет проверяемых элементов —"))
            return box
        for finding in stage.findings:
            box_layout.addWidget(QLabel(self._finding_text(finding)))
        if stage.timelines:
            box_layout.addWidget(self._timelines_section(stage.timelines))
        return box

    def _timelines_section(self, timelines: tuple[TimelineComparison, ...]) -> QWidget:
        """Секция таймлайнов этапа 6: заголовок + карточка на каждое сопоставление."""
        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        header = QLabel(_TIMELINES_HEADER)
        header.setObjectName("schemeTitle")
        section_layout.addWidget(header)
        for comparison in timelines:
            section_layout.addWidget(self._timeline_card(comparison))
        return section

    def _timeline_card(self, comparison: TimelineComparison) -> QGroupBox:
        """Карточка таймлайна: заголовок + две колонки «Эталон» | «Введено курсантом».

        Колонки выводятся построчно «дата — событие», без пометок верно/неверно: это
        нейтральное сопоставление, вердикт остаётся за преподавателем.
        """
        card = QGroupBox(comparison.title or comparison.timeline_id)
        columns = QHBoxLayout(card)
        columns.addLayout(self._timeline_column(_AUTHORED_CAPTION, comparison.authored), 1)
        columns.addLayout(self._timeline_column(_CADET_CAPTION, comparison.cadet), 1)
        return card

    @staticmethod
    def _timeline_column(
        caption: str, entries: tuple[tuple[str, str], ...]
    ) -> QVBoxLayout:
        """Колонка таймлайна: подпись + строки «дата — событие» (или «не заполнено», если пусто)."""
        column = QVBoxLayout()
        title = QLabel(caption)
        title.setObjectName("schemeCaption")
        column.addWidget(title)
        if not entries:
            placeholder = QLabel(_EMPTY_COLUMN)
            placeholder.setObjectName("mutedHint")
            column.addWidget(placeholder)
        else:
            for date, event in entries:
                column.addWidget(QLabel(f"{date} — {event}"))
        column.addStretch(1)
        return column

    @staticmethod
    def _finding_text(finding: Finding) -> str:
        """Строка элемента: статус + подпись (или id) + приглушённый контекст (если есть)."""
        status = "верно" if finding.correct else "неверно"
        name = finding.label or finding.element_id
        text = f"[{status}] {name}"
        if finding.detail:
            text += f" — {finding.detail}"
        return text
