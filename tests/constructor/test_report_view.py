"""Тесты ReportView: секции по этапам, строки findings, плейсхолдер для пустого этапа."""
from __future__ import annotations

from PySide6.QtWidgets import QGroupBox, QLabel
from pytestqt.qtbot import QtBot

from epicase_constructor.ui.report_view import ReportView
from epicase_core.domain.report import CaseReport, Finding, FindingKind, StageReport
from epicase_core.domain.stages import StageKind

_CLINICAL_TITLE = "Клинико-эпидемиологический диагноз"


def _report() -> CaseReport:
    """Отчёт из шести этапов: клинический с findings, остальные — пустые."""
    return CaseReport(
        case_id="case-1",
        stages=(
            StageReport(StageKind.PATIENTS, ()),
            StageReport(
                StageKind.CLINICAL,
                (
                    Finding(
                        kind=FindingKind.BRANCH,
                        element_id="branch",
                        correct=True,
                        label="Выберите путь",
                    ),
                    Finding(
                        kind=FindingKind.DOCUMENT_CHOICE,
                        element_id="doc-1",
                        correct=False,
                        label="Выберите документ",
                        detail="Рапорт командира",
                    ),
                ),
            ),
            StageReport(StageKind.CONTACTS, ()),
            StageReport(StageKind.ENVIRONMENT, ()),
            StageReport(StageKind.SES, ()),
            StageReport(StageKind.FINAL, ()),
        ),
    )


def _box(view: ReportView, title: str) -> QGroupBox:
    return next(b for b in view.findChildren(QGroupBox) if b.title() == title)


def test_report_view_renders_six_stage_boxes(qtbot: QtBot) -> None:
    """Шесть StageReport → шесть QGroupBox с человекочитаемыми заголовками этапов."""
    view = ReportView(_report())
    qtbot.addWidget(view)

    boxes = view.findChildren(QGroupBox)
    assert len(boxes) == 6
    titles = {b.title() for b in boxes}
    assert _CLINICAL_TITLE in titles
    assert "Пациенты" in titles
    assert "Окончательный эпидемиологический диагноз" in titles


def test_report_view_stage_with_findings_shows_rows(qtbot: QtBot) -> None:
    """Этап с findings показывает строки: подпись, статус и приглушённый контекст."""
    view = ReportView(_report())
    qtbot.addWidget(view)

    texts = [lbl.text() for lbl in _box(view, _CLINICAL_TITLE).findChildren(QLabel)]
    assert any("Выберите путь" in t and "верно" in t for t in texts)
    # Неверный выбор документа: статус «неверно» + приглушённый контекст ответа.
    assert any("неверно" in t and "Рапорт командира" in t for t in texts)


def test_report_view_empty_stage_shows_placeholder(qtbot: QtBot) -> None:
    """Этап без findings показывает плейсхолдер вместо строк."""
    view = ReportView(_report())
    qtbot.addWidget(view)

    texts = [lbl.text() for lbl in _box(view, "Пациенты").findChildren(QLabel)]
    assert texts == ["— нет проверяемых элементов —"]
