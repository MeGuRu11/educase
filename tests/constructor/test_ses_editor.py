"""Тесты SesEditor: сборка ``SesDraft`` из поиска, выбора уровня СЭС и документов."""
from __future__ import annotations

from pytestqt.qtbot import QtBot

from educase_constructor.ui.field_editor import FieldEditor
from educase_constructor.ui.ses_editor import SesEditor
from educase_core.application.case_builder import (
    DocumentOptionDraft,
    DocumentTaskDraft,
    FieldDraft,
    SearchDraft,
    SearchEntryDraft,
    SesDraft,
    SynonymSetDraft,
)


def _select_type(field: FieldEditor, value: str) -> None:
    """Выбрать тип поля по англ. значению (userData), не завязываясь на видимую подпись."""
    field.type_combo.setCurrentIndex(field.type_combo.findData(value))


def test_level_choice_present_when_checkbox_on(qtbot: QtBot) -> None:
    """Чекбокс включён → ``level_choice`` — непустой ``FieldDraft`` с типом и вариантами."""
    editor = SesEditor()
    qtbot.addWidget(editor)

    editor.include_level_checkbox.setChecked(True)
    field = editor.level_field_editor
    field.label_edit.setText("Уровень СЭС")
    _select_type(field, "choice")
    field.options_edit.setText(
        "благополучное, неустойчивое, неблагополучное, чрезвычайное"
    )
    field.correct_edit.setText("чрезвычайное")

    draft = editor.to_draft()
    assert draft.level_choice is not None
    assert draft.level_choice.label == "Уровень СЭС"
    assert draft.level_choice.field_type == "choice"
    assert draft.level_choice.choice_options == (
        "благополучное",
        "неустойчивое",
        "неблагополучное",
        "чрезвычайное",
    )
    assert draft.level_choice.choice_correct == ("чрезвычайное",)


def test_level_choice_none_when_checkbox_off(qtbot: QtBot) -> None:
    """Чекбокс выключен → ``level_choice`` равен ``None`` независимо от полей редактора."""
    editor = SesEditor()
    qtbot.addWidget(editor)

    editor.level_field_editor.label_edit.setText("Уровень СЭС")
    assert editor.include_level_checkbox.isChecked() is False

    draft = editor.to_draft()
    assert draft.level_choice is None


def test_filled_editor_collects_search_and_documents(qtbot: QtBot) -> None:
    """Заполненные поиск и документ собираются в ``SesDraft``."""
    editor = SesEditor()
    qtbot.addWidget(editor)

    editor.intro_edit.setText("Оцените состояние СЭС")

    editor.search_editor.add_entry_button.click()
    entry = editor.search_editor.entry_editors[0]
    entry.triggers.canonical_edit.setText("заболеваемость")

    editor.documents_editor.add_task_button.click()
    task = editor.documents_editor.task_editors[0]
    task.prompt_edit.setText("Выберите донесение")
    task.add_option_button.click()
    task.option_editors[0].title_edit.setText("Прил. 22")

    draft = editor.to_draft()
    assert draft.intro == "Оцените состояние СЭС"
    assert len(draft.search.entries) == 1
    assert draft.search.entries[0].triggers.canonical == "заболеваемость"
    assert len(draft.documents) == 1
    assert draft.documents[0].prompt == "Выберите донесение"
    assert draft.documents[0].options[0].title == "Прил. 22"


def test_empty_editor_to_draft(qtbot: QtBot) -> None:
    """Пустой редактор → пустые поиск/документы и ``level_choice`` равен ``None``."""
    editor = SesEditor()
    qtbot.addWidget(editor)

    draft = editor.to_draft()
    assert draft.intro == ""
    assert draft.search.entries == ()
    assert draft.level_choice is None
    assert draft.documents == ()


def test_load_round_trip_with_level(qtbot: QtBot) -> None:
    """``SesEditor.load`` с непустым уровнем: флаг включён, ``to_draft`` идемпотентен."""
    editor = SesEditor()
    qtbot.addWidget(editor)

    draft = SesDraft(
        intro="Оцените СЭС",
        search=SearchDraft(
            entries=(
                SearchEntryDraft(
                    triggers=SynonymSetDraft("заболеваемость", ("рост",)),
                    reveal_text="данные",
                ),
            )
        ),
        level_choice=FieldDraft(
            label="Уровень", field_type="number", number_value="2"
        ),
        documents=(
            DocumentTaskDraft(
                prompt="Выберите донесение",
                options=(
                    DocumentOptionDraft(title="Прил. 22", is_correct=True),
                    DocumentOptionDraft(title="Обманка"),
                ),
            ),
        ),
    )

    editor.load(draft)
    assert editor.include_level_checkbox.isChecked() is True
    assert editor.to_draft() == draft


def test_load_without_level_unchecks_flag(qtbot: QtBot) -> None:
    """``SesEditor.load`` без уровня снимает флаг; ``level_choice`` остаётся ``None``."""
    editor = SesEditor()
    qtbot.addWidget(editor)

    editor.include_level_checkbox.setChecked(True)  # был включён до загрузки
    editor.load(SesDraft(intro="Без уровня"))

    assert editor.include_level_checkbox.isChecked() is False
    assert editor.to_draft().level_choice is None
