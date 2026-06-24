"""Тесты редакторов документов Constructor: сборка драфтов поля/шаблона/задания."""
from __future__ import annotations

from pytestqt.qtbot import QtBot

from epicase_constructor.ui.document_editor import (
    DocumentListEditor,
    DocumentOptionEditor,
    DocumentTaskEditor,
)
from epicase_constructor.ui.field_editor import FieldEditor
from epicase_constructor.ui.template_editor import TemplateEditor
from epicase_core.application.case_builder import _build_field
from epicase_core.domain import ChoiceMatch, DateMatch, NumberMatch, TextMatch


def _select_type(field: FieldEditor, value: str) -> None:
    """Выбрать тип поля по англ. значению (userData), не завязываясь на видимую подпись."""
    field.type_combo.setCurrentIndex(field.type_combo.findData(value))


def test_field_editor_text_rule(qtbot: QtBot) -> None:
    """Тип ``text`` → ключевые слова попадают в ``keywords`` драфта."""
    editor = FieldEditor()
    qtbot.addWidget(editor)

    editor.label_edit.setText("Диагноз")
    _select_type(editor, "text")
    editor.keywords_editor.canonical_edit.setText("сальмонеллёз")
    editor.keywords_editor.synonyms_edit.setText("salmonella, сальмонелла ,")

    draft = editor.to_draft()
    assert draft.label == "Диагноз"
    assert draft.field_type == "text"
    assert draft.required is True
    assert draft.keywords.canonical == "сальмонеллёз"
    assert draft.keywords.synonyms == ("salmonella", "сальмонелла")


def test_field_editor_number_rule(qtbot: QtBot) -> None:
    """Тип ``number`` → значение, допуск и знаки округления как сырые строки."""
    editor = FieldEditor()
    qtbot.addWidget(editor)

    editor.label_edit.setText("Температура")
    _select_type(editor, "number")
    editor.required_checkbox.setChecked(False)
    editor.number_value_edit.setText("38,5")
    editor.tolerance_edit.setText("0,2")
    editor.ndigits_edit.setText("1")

    draft = editor.to_draft()
    assert draft.field_type == "number"
    assert draft.required is False
    assert draft.number_value == "38,5"
    assert draft.number_tolerance == "0,2"
    assert draft.number_ndigits == "1"


def test_field_editor_date_rule(qtbot: QtBot) -> None:
    """Тип ``date`` → ISO-дата попадает в ``date_value``."""
    editor = FieldEditor()
    qtbot.addWidget(editor)

    editor.label_edit.setText("Дата заболевания")
    _select_type(editor, "date")
    editor.date_value_edit.setText("2026-06-11")

    draft = editor.to_draft()
    assert draft.field_type == "date"
    assert draft.date_value == "2026-06-11"


def test_field_editor_choice_rule(qtbot: QtBot) -> None:
    """Тип ``choice`` → варианты и верные значения разбиваются по запятой."""
    editor = FieldEditor()
    qtbot.addWidget(editor)

    editor.label_edit.setText("Тяжесть")
    _select_type(editor, "choice")
    editor.options_edit.setText("лёгкая, средняя, тяжёлая")
    editor.correct_edit.setText("средняя, тяжёлая ,")

    draft = editor.to_draft()
    assert draft.field_type == "choice"
    assert draft.choice_options == ("лёгкая", "средняя", "тяжёлая")
    assert draft.choice_correct == ("средняя", "тяжёлая")


def test_field_editor_type_switches_stack(qtbot: QtBot) -> None:
    """Смена типа в комбобоксе переключает страницу стека правил."""
    editor = FieldEditor()
    qtbot.addWidget(editor)

    _select_type(editor, "text")
    assert editor.rule_stack.currentWidget() is editor.keywords_editor
    _select_type(editor, "choice")
    assert editor.rule_stack.currentIndex() == 3


def test_field_editor_combo_localized_labels_and_data(qtbot: QtBot) -> None:
    """Combo показывает русские подписи, но хранит англ. значения ``FieldType`` в userData."""
    editor = FieldEditor()
    qtbot.addWidget(editor)

    combo = editor.type_combo
    pairs = [(combo.itemText(i), combo.itemData(i)) for i in range(combo.count())]
    assert pairs == [
        ("Текст", "text"),
        ("Число", "number"),
        ("Дата", "date"),
        ("Выбор", "choice"),
    ]


def test_field_editor_draft_builds_correct_rule_type(qtbot: QtBot) -> None:
    """Русификация combo не ломает доменный маппинг: каждый тип → правильный класс правила."""
    editor = FieldEditor()
    qtbot.addWidget(editor)
    editor.label_edit.setText("Поле")

    _select_type(editor, "text")
    editor.keywords_editor.canonical_edit.setText("термин")
    text_field = _build_field(editor.to_draft(), 1)
    assert text_field.type.value == "text"
    assert isinstance(text_field.rule, TextMatch)

    _select_type(editor, "number")
    editor.number_value_edit.setText("10")
    assert isinstance(_build_field(editor.to_draft(), 1).rule, NumberMatch)

    _select_type(editor, "date")
    editor.date_value_edit.setText("2026-06-11")
    assert isinstance(_build_field(editor.to_draft(), 1).rule, DateMatch)

    _select_type(editor, "choice")
    editor.options_edit.setText("а, б")
    editor.correct_edit.setText("а")
    assert isinstance(_build_field(editor.to_draft(), 1).rule, ChoiceMatch)


def test_document_option_correct_checkbox_object_name(qtbot: QtBot) -> None:
    """correct_checkbox имеет objectName "criticalToggle" для CSS-таргетинга темы."""
    editor = DocumentOptionEditor()
    qtbot.addWidget(editor)
    assert editor.correct_checkbox.objectName() == "criticalToggle"


def test_field_editor_required_checkbox_object_name(qtbot: QtBot) -> None:
    """required_checkbox имеет objectName "criticalToggle" для CSS-таргетинга темы."""
    editor = FieldEditor()
    qtbot.addWidget(editor)
    assert editor.required_checkbox.objectName() == "criticalToggle"


def test_task_editor_add_remove_options(qtbot: QtBot) -> None:
    """«Добавить вариант» увеличивает число редакторов опций, «Удалить» — уменьшает."""
    editor = DocumentTaskEditor()
    qtbot.addWidget(editor)

    assert len(editor.option_editors) == 0
    editor.add_option_button.click()
    editor.add_option_button.click()
    assert len(editor.option_editors) == 2
    editor.remove_option_button.click()
    assert len(editor.option_editors) == 1
    editor.remove_option_button.click()
    editor.remove_option_button.click()
    assert len(editor.option_editors) == 0


def test_list_editor_add_remove_tasks(qtbot: QtBot) -> None:
    """«Добавить задание» увеличивает число редакторов заданий, «Удалить» — уменьшает."""
    editor = DocumentListEditor()
    qtbot.addWidget(editor)

    assert len(editor.task_editors) == 0
    editor.add_task_button.click()
    editor.add_task_button.click()
    assert len(editor.task_editors) == 2
    editor.remove_task_button.click()
    assert len(editor.task_editors) == 1
    editor.remove_task_button.click()
    editor.remove_task_button.click()
    assert len(editor.task_editors) == 0


def test_list_editor_to_draft_correct_and_decoy(qtbot: QtBot) -> None:
    """Задание с верным вариантом (шаблон + поле) и обманкой → корректные драфты."""
    editor = DocumentListEditor()
    qtbot.addWidget(editor)

    editor.add_task_button.click()
    task = editor.task_editors[0]
    task.prompt_edit.setText("Выберите донесение")

    task.add_option_button.click()
    task.add_option_button.click()
    correct, decoy = task.option_editors

    correct.title_edit.setText("Внеочередное донесение")
    correct.correct_checkbox.setChecked(True)
    correct.template_editor.title_edit.setText("ДМ-4")
    correct.template_editor.add_field_button.click()
    field = correct.template_editor.field_editors[0]
    field.label_edit.setText("Дата")
    _select_type(field, "date")
    field.date_value_edit.setText("2026-06-11")

    decoy.title_edit.setText("Обычная справка")

    drafts = editor.to_draft()
    assert len(drafts) == 1
    task_draft = drafts[0]
    assert task_draft.prompt == "Выберите донесение"
    assert len(task_draft.options) == 2

    correct_draft, decoy_draft = task_draft.options
    assert correct_draft.title == "Внеочередное донесение"
    assert correct_draft.is_correct is True
    assert correct_draft.template.title == "ДМ-4"
    assert len(correct_draft.template.fields) == 1
    assert correct_draft.template.fields[0].field_type == "date"
    assert correct_draft.template.fields[0].date_value == "2026-06-11"

    assert decoy_draft.title == "Обычная справка"
    assert decoy_draft.is_correct is False


# --- Уровень 3a: условный шаблон ---


def test_option_editor_template_hidden_by_default(qtbot: QtBot) -> None:
    """По умолчанию шаблон скрыт (вариант считается обманкой)."""
    editor = DocumentOptionEditor()
    qtbot.addWidget(editor)
    assert editor.template_editor.isHidden()


def test_option_editor_template_shown_when_correct_checked(qtbot: QtBot) -> None:
    """Отметка «Верный документ» делает редактор шаблона видимым."""
    editor = DocumentOptionEditor()
    qtbot.addWidget(editor)
    editor.correct_checkbox.setChecked(True)
    assert not editor.template_editor.isHidden()


def test_option_editor_template_hidden_when_correct_unchecked(qtbot: QtBot) -> None:
    """Снятие галочки снова скрывает редактор шаблона."""
    editor = DocumentOptionEditor()
    qtbot.addWidget(editor)
    editor.correct_checkbox.setChecked(True)
    editor.correct_checkbox.setChecked(False)
    assert editor.template_editor.isHidden()


# --- Уровень 3a: карточки-номера ---


def test_task_editor_option_cards_numbered(qtbot: QtBot) -> None:
    """add_option_button создаёт карточку «Документ N» синхронно с option_editors."""
    editor = DocumentTaskEditor()
    qtbot.addWidget(editor)
    editor.add_option_button.click()
    assert len(editor._option_cards) == 1
    assert editor._option_cards[0].title() == "Документ 1"


def test_list_editor_task_cards_numbered(qtbot: QtBot) -> None:
    """add_task_button создаёт карточку «Задание N» синхронно с task_editors."""
    editor = DocumentListEditor()
    qtbot.addWidget(editor)
    editor.add_task_button.click()
    assert editor._task_cards[0].title() == "Задание 1"
    assert len(editor._task_cards) == len(editor.task_editors)


def test_template_editor_field_cards_numbered(qtbot: QtBot) -> None:
    """add_field_button создаёт карточку «Поле N» синхронно с field_editors."""
    editor = TemplateEditor()
    qtbot.addWidget(editor)
    editor.add_field_button.click()
    assert editor._field_cards[0].title() == "Поле 1"
