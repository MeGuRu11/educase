"""Тесты сбора Attempt из видов этапов и записи .eduresult (сквозной цикл)."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QComboBox, QLineEdit
from pytestqt.qtbot import QtBot

from epicase_core.application.results import load_result, record_attempt
from epicase_core.domain.attempt import AttemptMeta
from epicase_core.domain.case import Case, CaseMeta
from epicase_core.domain.documents import (
    ChoiceMatch,
    DocumentField,
    DocumentOption,
    DocumentTask,
    DocumentTemplate,
    FieldType,
    TextMatch,
)
from epicase_core.domain.report import grade_case
from epicase_core.domain.search import (
    InspectionCheck,
    KeywordSearch,
    SearchEntry,
    SynonymSet,
)
from epicase_core.domain.stages import (
    BranchOption,
    BranchPoint,
    StageClinical,
    StageContacts,
    StageFinal,
    StageSes,
)
from epicase_player.ui.branch_widget import BranchWidget
from epicase_player.ui.case_navigator import CaseNavigator
from epicase_player.ui.document_field_widget import DocumentFieldWidget
from epicase_player.ui.document_widget import DocumentWidget
from epicase_player.ui.inspection_widget import InspectionWidget
from epicase_player.ui.search_widget import SearchWidget


def _build_case() -> Case:
    """Синтетический кейс: ветвление, документы с обманкой+полем, осмотр, выбор уровня."""
    clinical = StageClinical(
        search=KeywordSearch(
            entries=(
                SearchEntry(
                    id="se1",
                    triggers=SynonymSet(canonical="вспышка"),
                    reveal_text="Данные о вспышке.",
                ),
            )
        ),
        branch=BranchPoint(
            id="bp1",
            prompt="Выберите диагноз",
            options=(
                BranchOption(id="b-correct", label="Верно", is_correct=True),
                BranchOption(id="b-wrong", label="Неверно"),
            ),
        ),
        documents=(
            DocumentTask(
                id="task-clin",
                prompt="Выберите документ",
                options=(
                    DocumentOption(
                        id="opt-correct",
                        title="Правильный документ",
                        is_correct=True,
                        template=DocumentTemplate(
                            id="tpl-clin",
                            title="Документ",
                            fields=(
                                DocumentField(
                                    id="f1",
                                    type=FieldType.TEXT,
                                    rule=TextMatch(keywords=SynonymSet(canonical="ответ")),
                                    label="Поле",
                                ),
                            ),
                        ),
                    ),
                    DocumentOption(id="opt-decoy", title="Обманка"),
                ),
            ),
        ),
    )
    contacts = StageContacts(
        inspection=InspectionCheck(
            expected=(
                SynonymSet(canonical="вода"),
                SynonymSet(canonical="туалет"),
            )
        ),
    )
    ses = StageSes(
        level_choice=DocumentField(
            id="lvl",
            type=FieldType.CHOICE,
            rule=ChoiceMatch(correct=("III",)),
            label="Уровень СЭС",
            options=("I", "II", "III"),
        ),
        documents=(
            DocumentTask(
                id="task-ses",
                prompt="Выберите приказ",
                options=(
                    DocumentOption(
                        id="ses-correct",
                        title="Приказ",
                        is_correct=True,
                        template=DocumentTemplate(id="tpl-ses", title="Приказ"),
                    ),
                    DocumentOption(id="ses-decoy", title="Обманка"),
                ),
            ),
        ),
    )
    final = StageFinal(
        documents=(
            DocumentTask(
                id="task-final",
                prompt="Окончательный документ",
                options=(
                    DocumentOption(
                        id="final-correct",
                        title="Итоговый",
                        is_correct=True,
                        template=DocumentTemplate(
                            id="tpl-final",
                            title="Итог",
                            fields=(
                                DocumentField(
                                    id="ff1",
                                    type=FieldType.TEXT,
                                    rule=TextMatch(keywords=SynonymSet(canonical="итог")),
                                    label="Итог",
                                ),
                            ),
                        ),
                    ),
                    DocumentOption(id="final-decoy", title="Обманка"),
                ),
            ),
        ),
    )
    return Case(
        meta=CaseMeta("c1", "Тест"),
        clinical=clinical,
        contacts=contacts,
        ses=ses,
        final=final,
    )


def _mount_and_fill(qtbot: QtBot) -> tuple[CaseNavigator, Case]:
    """Смонтировать навигатор по синтетическому кейсу и ввести верные ответы через виджеты."""
    case = _build_case()
    nav = CaseNavigator(case)
    qtbot.addWidget(nav)

    # Этап 2 «Клинический»: поиск, ветвление, документ + поле.
    clinical_view = nav.stack.widget(1)
    assert clinical_view is not None
    search_w: SearchWidget = clinical_view.findChildren(SearchWidget)[0]
    search_w.input.setText("вспышка")
    search_w.btn_search.click()

    branch_w: BranchWidget = clinical_view.findChildren(BranchWidget)[0]
    branch_w.options_combo.setCurrentIndex(0)  # «Верно» (b-correct) — первая реальная опция

    clin_doc_w: DocumentWidget = clinical_view.findChildren(DocumentWidget)[0]
    clin_doc_w.options_combo.setCurrentIndex(0)  # «Правильный документ» — первая реальная опция
    clin_field = clin_doc_w.current_field_widgets()[0].input
    assert isinstance(clin_field, QLineEdit)
    clin_field.setText("ответ")

    # Этап 3 «Контактные»: свободный осмотр.
    contacts_view = nav.stack.widget(2)
    assert contacts_view is not None
    insp_w: InspectionWidget = contacts_view.findChildren(InspectionWidget)[0]
    insp_w.output.setPlainText("вода загрязнена, туалет неисправен")

    # Этап 5 «СЭС»: выбор уровня + документ. Уровень — единственный DocumentFieldWidget вида.
    ses_view = nav.stack.widget(4)
    assert ses_view is not None
    level_input = ses_view.findChildren(DocumentFieldWidget)[0].input
    assert isinstance(level_input, QComboBox)
    level_input.setCurrentIndex(2)  # «III» (0=I, 1=II, 2=III — без фиктивного пункта)
    ses_doc_w: DocumentWidget = ses_view.findChildren(DocumentWidget)[0]
    ses_doc_w.options_combo.setCurrentIndex(0)  # «Приказ» (ses-correct) — первая реальная опция

    # Этап 6 «Окончательный»: документ + поле.
    final_view = nav.stack.widget(5)
    assert final_view is not None
    final_doc_w: DocumentWidget = final_view.findChildren(DocumentWidget)[0]
    final_doc_w.options_combo.setCurrentIndex(0)  # «Итоговый» (final-correct)
    final_field = final_doc_w.current_field_widgets()[0].input
    assert isinstance(final_field, QLineEdit)
    final_field.setText("итог")

    return nav, case


def test_collect_attempt_captures_raw_answers(qtbot: QtBot) -> None:
    """collect_attempt собирает сырые ответы из всех видов этапов."""
    nav, _ = _mount_and_fill(qtbot)

    attempt = nav.collect_attempt(AttemptMeta(case_id="c1"))

    assert attempt.meta.case_id == "c1"
    assert attempt.clinical.search.queries == ("вспышка",)
    assert attempt.clinical.branch is not None
    assert attempt.clinical.branch.point_id == "bp1"
    assert attempt.clinical.branch.chosen_option_id == "b-correct"
    assert attempt.clinical.documents[0].chosen_option_id == "opt-correct"
    assert attempt.clinical.documents[0].field_answers == (("f1", "ответ"),)
    assert attempt.contacts.inspection is not None
    assert attempt.contacts.inspection.text == "вода загрязнена, туалет неисправен"
    assert attempt.ses.level_choice is not None
    assert attempt.ses.level_choice.answer == "III"
    assert attempt.ses.documents[0].chosen_option_id == "ses-correct"
    assert attempt.final.documents[0].chosen_option_id == "final-correct"
    assert attempt.final.documents[0].field_answers == (("ff1", "итог"),)


def test_search_widget_accumulates_into_search_log(qtbot: QtBot) -> None:
    """Запросы виджета поиска попадают в SearchLog собранного Attempt."""
    nav, _ = _mount_and_fill(qtbot)

    attempt = nav.collect_attempt(AttemptMeta(case_id="c1"))

    assert attempt.clinical.search.queries  # непустой
    assert "вспышка" in attempt.clinical.search.queries


def test_collected_attempt_round_trips(qtbot: QtBot, tmp_path: Path) -> None:
    """record_attempt → load_result даёт равный Attempt и пустые ассеты."""
    nav, _ = _mount_and_fill(qtbot)
    attempt = nav.collect_attempt(AttemptMeta(case_id="c1", trainee_label="Курсант"))

    dst = record_attempt(attempt, tmp_path / "res")
    loaded = load_result(dst)

    assert loaded.attempt == attempt
    assert loaded.assets == {}


def test_grade_case_on_collected_attempt_all_correct(qtbot: QtBot) -> None:
    """grade_case по верно введённым ответам даёт correct=True для всех findings."""
    nav, case = _mount_and_fill(qtbot)
    attempt = nav.collect_attempt(AttemptMeta(case_id="c1"))

    report = grade_case(case, attempt)

    findings = [f for stage in report.stages for f in stage.findings]
    assert findings  # есть что проверять
    assert all(f.correct for f in findings)
