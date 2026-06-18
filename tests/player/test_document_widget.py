"""Тесты DocumentWidget: выбор документа из списка с обманками и заполнение полей."""
from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QLabel, QLineEdit
from pytestqt.qtbot import QtBot

from educase_core.domain.documents import (
    ChoiceMatch,
    DocumentField,
    DocumentOption,
    DocumentTask,
    DocumentTemplate,
    FieldType,
    TextMatch,
)
from educase_core.domain.search import SynonymSet
from educase_player.ui.document_widget import DocumentWidget


def _make_task() -> DocumentTask:
    """DocumentTask с правильным документом (TEXT + CHOICE поля) и обманкой (template=None)."""
    text_field = DocumentField(
        id="fld_diag",
        type=FieldType.TEXT,
        rule=TextMatch(keywords=SynonymSet(canonical="сальмонеллёз")),
        label="Диагноз",
    )
    choice_field = DocumentField(
        id="fld_level",
        type=FieldType.CHOICE,
        rule=ChoiceMatch(correct=("Неблагополучное",)),
        label="Уровень СЭС",
        options=("Благополучное", "Неустойчивое", "Неблагополучное", "Чрезвычайное"),
    )
    correct_opt = DocumentOption(
        id="opt_correct",
        title="Донесение ДМ4",
        is_correct=True,
        template=DocumentTemplate(
            id="tpl_dm4",
            title="ДМ4",
            fields=(text_field, choice_field),
        ),
    )
    decoy_opt = DocumentOption(
        id="opt_decoy",
        title="Форма Ф23",
        is_correct=False,
        template=None,
    )
    return DocumentTask(
        id="task1",
        prompt="Выберите нужный документ и заполните его поля.",
        options=(correct_opt, decoy_opt),
    )


def test_initial_state_no_fields_result_none(qtbot: QtBot) -> None:
    """При старте form_area пустой (нет виджетов полей) и result is None."""
    w = DocumentWidget(_make_task())
    qtbot.addWidget(w)
    assert w.result is None
    assert w.current_field_widgets() == []


def test_select_correct_option_builds_field_widgets(qtbot: QtBot) -> None:
    """Выбор документа с template → строятся DocumentFieldWidget по числу полей шаблона."""
    w = DocumentWidget(_make_task())
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(0)  # "Донесение ДМ4" (correct) — первая реальная опция
    assert len(w.current_field_widgets()) == 2


def test_select_decoy_option_no_fields_message(qtbot: QtBot) -> None:
    """Выбор обманки (template=None) → полей нет, сообщение об отсутствии полей."""
    w = DocumentWidget(_make_task())
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(1)  # "Форма Ф23" (decoy) — вторая реальная опция
    assert w.current_field_widgets() == []
    labels: list[QLabel] = w.form_area.findChildren(QLabel)
    texts = [lbl.text() for lbl in labels]
    assert any("Для этого документа" in t for t in texts)


def test_submit_correct_option_correct_answers(qtbot: QtBot) -> None:
    """on_submit с правильным документом и верными полями.

    Ожидается: option_correct True, все элементы fields_ok True.
    """
    w = DocumentWidget(_make_task())
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(0)  # correct option — первая реальная опция

    field_widgets = w.current_field_widgets()
    assert len(field_widgets) == 2

    text_fw = next(fw for fw in field_widgets if fw.field.type == FieldType.TEXT)
    assert isinstance(text_fw.input, QLineEdit)
    text_fw.input.setText("сальмонеллёз")

    # combo без фиктивного пункта: 0=Благополучное, 1=Неустойчивое, 2=Неблагополучное
    choice_fw = next(fw for fw in field_widgets if fw.field.type == FieldType.CHOICE)
    assert isinstance(choice_fw.input, QComboBox)
    choice_fw.input.setCurrentIndex(2)  # "Неблагополучное"

    w.btn_submit.click()

    result = w.result
    assert result is not None
    assert result.option_correct is True
    assert result.option_id == "opt_correct"
    assert all(ok for _, ok in result.fields_ok)


def test_submit_decoy_option(qtbot: QtBot) -> None:
    """on_submit с обманкой → option_correct False, fields_ok пустой."""
    w = DocumentWidget(_make_task())
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(1)  # decoy — вторая реальная опция
    w.btn_submit.click()

    result = w.result
    assert result is not None
    assert result.option_correct is False
    assert result.option_id == "opt_decoy"
    assert result.fields_ok == ()


def test_submit_wrong_answers_no_crash(qtbot: QtBot) -> None:
    """Неверное заполнение полей → fields_ok содержит False, виджет не падает (ADR-008)."""
    w = DocumentWidget(_make_task())
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(0)  # correct option

    field_widgets = w.current_field_widgets()
    text_fw = next(fw for fw in field_widgets if fw.field.type == FieldType.TEXT)
    assert isinstance(text_fw.input, QLineEdit)
    text_fw.input.setText("неверный диагноз")

    w.btn_submit.click()

    result = w.result
    assert result is not None
    assert any(not ok for _, ok in result.fields_ok)


def test_submit_neutral_message_no_verdict(qtbot: QtBot) -> None:
    """После on_submit отображается нейтральное «Ответ сохранён», вердикт не показан (ADR-005)."""
    w = DocumentWidget(_make_task())
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(0)
    w.btn_submit.click()

    all_labels: list[QLabel] = w.findChildren(QLabel)
    texts = [lbl.text() for lbl in all_labels]
    assert "Ответ сохранён" in texts
    assert not any("верн" in t.lower() or "неверн" in t.lower() for t in texts)


def test_result_none_before_submit(qtbot: QtBot) -> None:
    """result is None до первого нажатия «Готово»."""
    w = DocumentWidget(_make_task())
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(0)
    assert w.result is None


def test_selected_option_none_for_placeholder(qtbot: QtBot) -> None:
    """selected_option() → None при плейсхолдере (currentIndex == -1)."""
    w = DocumentWidget(_make_task())
    qtbot.addWidget(w)
    assert w.options_combo.currentIndex() == -1
    assert w.selected_option() is None


def test_switch_from_correct_to_decoy_clears_fields(qtbot: QtBot) -> None:
    """Переключение с шаблонного документа на обманку очищает виджеты полей."""
    w = DocumentWidget(_make_task())
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(0)  # correct — строятся поля
    assert len(w.current_field_widgets()) == 2
    w.options_combo.setCurrentIndex(1)  # decoy — поля должны пропасть
    assert w.current_field_widgets() == []


def test_field_widget_ids_match_template(qtbot: QtBot) -> None:
    """id полей виджетов совпадают с id полей шаблона."""
    w = DocumentWidget(_make_task())
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(0)
    field_widgets = w.current_field_widgets()
    ids = {fw.field.id for fw in field_widgets}
    assert ids == {"fld_diag", "fld_level"}


def test_submit_without_selection_sets_invalid_property(qtbot: QtBot) -> None:
    """Нажатие «Готово» без выбора — мягкая подсветка (invalid=True), не блокирует (ADR-008)."""
    w = DocumentWidget(_make_task())
    qtbot.addWidget(w)
    assert w.options_combo.currentIndex() == -1

    w.btn_submit.click()

    # result всё равно записан (ADR-008: не блокирует)
    assert w.result is not None
    assert w.result.option_id is None
    # комбобокс помечен как invalid
    assert w.options_combo.property("invalid") is True


def test_selection_after_invalid_clears_property(qtbot: QtBot) -> None:
    """Выбор варианта после подсветки ошибки сбрасывает свойство invalid."""
    w = DocumentWidget(_make_task())
    qtbot.addWidget(w)
    w.btn_submit.click()  # invalid=True
    assert w.options_combo.property("invalid") is True

    w.options_combo.setCurrentIndex(0)  # любой выбор → invalid сбрасывается
    assert w.options_combo.property("invalid") is False
