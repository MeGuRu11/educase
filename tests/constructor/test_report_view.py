"""Тесты ReportView: секции по этапам, строки findings, плейсхолдер для пустого этапа."""
from __future__ import annotations

from PySide6.QtWidgets import QGroupBox, QLabel
from pytestqt.qtbot import QtBot

from epicase_constructor.ui.report_view import ReportView
from epicase_core.domain.report import (
    CaseReport,
    Finding,
    FindingKind,
    StageReport,
    TimelineComparison,
)
from epicase_core.domain.stages import StageKind

_CLINICAL_TITLE = "Клинико-эпидемиологический диагноз"
_FINAL_TITLE = "Окончательный эпидемиологический диагноз"


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


def _timeline_report() -> CaseReport:
    """Отчёт, где этап 6 несёт сопоставление таймлайнов (эталон + ввод курсанта)."""
    return CaseReport(
        case_id="case-tl",
        stages=(
            StageReport(StageKind.PATIENTS, ()),
            StageReport(StageKind.CLINICAL, ()),
            StageReport(StageKind.CONTACTS, ()),
            StageReport(StageKind.ENVIRONMENT, ()),
            StageReport(StageKind.SES, ()),
            StageReport(
                StageKind.FINAL,
                (),
                timelines=(
                    TimelineComparison(
                        timeline_id="tl-1",
                        title="Сроки наблюдения за очагом",
                        authored=(("01.06", "первый случай"),),
                        cadet=(("01.06", "заболел"),),
                    ),
                ),
            ),
        ),
    )


def test_report_view_final_renders_timeline_columns(qtbot: QtBot) -> None:
    """Этап 6 с таймлайном: заголовок + обе колонки построчно, без пометок верно/неверно."""
    view = ReportView(_timeline_report())
    qtbot.addWidget(view)

    final_box = _box(view, _FINAL_TITLE)
    card_titles = {b.title() for b in final_box.findChildren(QGroupBox)}
    assert "Сроки наблюдения за очагом" in card_titles

    texts = [lbl.text() for lbl in final_box.findChildren(QLabel)]
    assert "Эталон" in texts
    assert "Введено курсантом" in texts
    assert any("первый случай" in t for t in texts)
    assert any("заболел" in t for t in texts)
    # Нейтральное сопоставление: никаких вердиктов «верно»/«неверно».
    assert not any("верно" in t for t in texts)


def test_report_view_final_timeline_without_cadet_shows_not_filled(qtbot: QtBot) -> None:
    """Пустой ввод курсанта в таймлайне → колонка показывает «не заполнено»."""
    report = CaseReport(
        case_id="case-tl",
        stages=(
            StageReport(StageKind.PATIENTS, ()),
            StageReport(StageKind.CLINICAL, ()),
            StageReport(StageKind.CONTACTS, ()),
            StageReport(StageKind.ENVIRONMENT, ()),
            StageReport(StageKind.SES, ()),
            StageReport(
                StageKind.FINAL,
                (),
                timelines=(
                    TimelineComparison(
                        timeline_id="tl-1",
                        title="Динамика лечения",
                        authored=(("05.06", "выписка"),),
                        cadet=(),
                    ),
                ),
            ),
        ),
    )
    view = ReportView(report)
    qtbot.addWidget(view)

    texts = [lbl.text() for lbl in _box(view, _FINAL_TITLE).findChildren(QLabel)]
    assert "не заполнено" in texts
    assert any("выписка" in t for t in texts)
