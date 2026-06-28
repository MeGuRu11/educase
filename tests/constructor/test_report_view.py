"""Тесты ReportView: секции по этапам, строки findings, плейсхолдер для пустого этапа,
нейтральные заметки и блок вложений курсанта (открыть/сохранить)."""
from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QFrame, QGroupBox, QLabel, QPushButton
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
from epicase_core.theme import load_qss

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


def test_finding_render_marks_unanswered_as_neutral(qtbot: QtBot) -> None:
    """Пропуск получает нейтральный стиль/статус без дублирования detail-плейсхолдера."""
    finding = Finding(
        FindingKind.DOCUMENT_CHOICE,
        "document",
        correct=False,
        detail="— не выбрано —",
    )
    label = ReportView._finding_label(finding)
    qtbot.addWidget(label)

    text = ReportView._finding_text(finding)
    assert label.objectName() == "findingSkip"
    assert "не отвечено" in text
    assert "— не выбрано —" not in text


def test_finding_render_marks_answered_error_as_bad(qtbot: QtBot) -> None:
    """Реальная ошибка сохраняет красный стиль, статус и контекст ответа."""
    finding = Finding(
        FindingKind.DOCUMENT_FIELD,
        "field",
        correct=False,
        detail="неправильный ответ",
    )
    label = ReportView._finding_label(finding)
    qtbot.addWidget(label)

    text = ReportView._finding_text(finding)
    assert label.objectName() == "findingBad"
    assert "неверно" in text
    assert "неправильный ответ" in text


def test_finding_render_marks_correct_as_ok(qtbot: QtBot) -> None:
    """Верный ответ сохраняет зелёный стиль."""
    finding = Finding(FindingKind.BRANCH, "branch", correct=True)
    label = ReportView._finding_label(finding)
    qtbot.addWidget(label)

    assert label.objectName() == "findingOk"


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


# --- Нейтральные заметки и вложения курсанта ---


def _attachment_report() -> CaseReport:
    """Отчёт, где клинический этап несёт одно вложение курсанта."""
    return CaseReport(
        case_id="case-att",
        stages=(
            StageReport(
                StageKind.CLINICAL,
                attachments=(("att-1", "донесение.pdf"),),
            ),
        ),
    )


def test_report_view_renders_notes(qtbot: QtBot) -> None:
    """Заметки этапа показываются приглушённой строкой «подпись: значение»."""
    report = CaseReport(
        case_id="case-notes",
        stages=(
            StageReport(
                StageKind.PATIENTS,
                notes=(("Поисковые запросы", "диарея, рвота"),),
            ),
        ),
    )
    view = ReportView(report)
    qtbot.addWidget(view)

    texts = [lbl.text() for lbl in view.findChildren(QLabel)]
    assert any("Поисковые запросы: диарея, рвота" in t for t in texts)


def test_report_view_renders_attachment_buttons(qtbot: QtBot) -> None:
    """Вложение с байтами отображается карточкой с метаданными и активными действиями."""
    view = ReportView(_attachment_report(), {"att-1": b"x" * 1536})
    qtbot.addWidget(view)

    cards = [
        frame
        for frame in view.findChildren(QFrame)
        if frame.objectName() == "attachmentCard"
    ]
    assert len(cards) == 1
    assert {label.text() for label in cards[0].findChildren(QLabel)} >= {
        "PDF",
        "донесение.pdf",
        "1,5 КБ",
    }
    header = view.findChild(QLabel, "attachmentSectionTitle")
    assert header is not None
    assert header.text() == "Вложенные документы · 1"
    buttons = view.findChildren(QPushButton)
    labels = {b.text() for b in buttons}
    assert "Открыть" in labels
    assert "Сохранить как…" in labels
    assert all(b.isEnabled() for b in buttons)


def test_report_view_missing_asset_disables_buttons(qtbot: QtBot) -> None:
    """Вложения нет в архиве → кнопки задизейблены, подпись помечена «(файл отсутствует…)»."""
    view = ReportView(_attachment_report(), {})  # байтов нет
    qtbot.addWidget(view)

    buttons = view.findChildren(QPushButton)
    assert buttons
    assert all(not b.isEnabled() for b in buttons)
    warning = view.findChild(QLabel, "attachmentWarning")
    assert warning is not None
    assert warning.text() == "(файл отсутствует в архиве)"


def test_missing_attachment_actions_have_explicit_disabled_style() -> None:
    """Missing-asset actions stay visibly disabled despite ID selector precedence."""
    qss = load_qss()
    disabled_rule = """QPushButton#attachmentOpenButton:disabled,
QPushButton#attachmentSaveButton:disabled {
    background: #F6F8FA;
    color: #9AA5AF;
    border: 1px solid #E1E6EA;
}"""

    assert disabled_rule in qss
    assert qss.index(disabled_rule) > qss.index("QPushButton#attachmentOpenButton {")


def test_report_view_save_attachment_writes_file(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Кнопка «Сохранить как…» пишет байты вложения в выбранный файл."""
    payload = b"PDF-BYTES-123"
    view = ReportView(_attachment_report(), {"att-1": payload})
    qtbot.addWidget(view)

    destination = tmp_path / "saved.pdf"
    monkeypatch.setattr(
        "epicase_constructor.ui.report_view.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(destination), ""),
    )
    save_button = next(
        b
        for b in view.findChildren(QPushButton)
        if b.objectName() == "attachmentSaveButton"
    )
    save_button.click()

    assert destination.read_bytes() == payload
