"""Тесты ClinicalEditor: сборка ``ClinicalDraft`` из поиска и развилки."""
from __future__ import annotations

from pytestqt.qtbot import QtBot

from educase_constructor.ui.clinical_editor import ClinicalEditor


def test_add_and_remove_search_entry(qtbot: QtBot) -> None:
    """«Добавить точку поиска» увеличивает число редакторов, «Удалить последнюю» — уменьшает."""
    editor = ClinicalEditor()
    qtbot.addWidget(editor)
    search = editor.search_editor

    assert len(search.entry_editors) == 0
    search.add_entry_button.click()
    search.add_entry_button.click()
    assert len(search.entry_editors) == 2
    search.remove_entry_button.click()
    assert len(search.entry_editors) == 1
    # Удаление при пустом списке не падает.
    search.remove_entry_button.click()
    search.remove_entry_button.click()
    assert len(search.entry_editors) == 0


def test_add_and_remove_branch_option(qtbot: QtBot) -> None:
    """«Добавить вариант» увеличивает число редакторов опций, «Удалить последний» — уменьшает."""
    editor = ClinicalEditor()
    qtbot.addWidget(editor)
    branch = editor.branch_editor

    assert len(branch.option_editors) == 0
    branch.add_option_button.click()
    branch.add_option_button.click()
    assert len(branch.option_editors) == 2
    branch.remove_option_button.click()
    assert len(branch.option_editors) == 1
    branch.remove_option_button.click()
    branch.remove_option_button.click()
    assert len(branch.option_editors) == 0


def test_filled_editor_to_draft(qtbot: QtBot) -> None:
    """Заполненные точка поиска и опции развилки → корректный ``ClinicalDraft``."""
    editor = ClinicalEditor()
    qtbot.addWidget(editor)

    editor.intro_edit.setText("Осмотрите больных")

    editor.search_editor.optional_checkbox.setChecked(True)
    editor.search_editor.add_entry_button.click()
    entry = editor.search_editor.entry_editors[0]
    entry.triggers.canonical_edit.setText("температура")
    entry.triggers.synonyms_edit.setText("лихорадка, жар ,")  # пустые куски отбрасываются
    entry.reveal_text_edit.setText("38,5 °C")
    entry.reveal_assets_edit.setText("img_temp")

    editor.branch_editor.prompt_edit.setText("Предварительный диагноз?")
    editor.branch_editor.add_option_button.click()
    editor.branch_editor.add_option_button.click()
    correct, wrong = editor.branch_editor.option_editors
    correct.label_edit.setText("ОКИ")
    correct.correct_checkbox.setChecked(True)
    wrong.label_edit.setText("ОРВИ")

    draft = editor.to_draft()

    assert draft.intro == "Осмотрите больных"
    assert draft.search.optional is True
    assert len(draft.search.entries) == 1
    entry_draft = draft.search.entries[0]
    assert entry_draft.triggers.canonical == "температура"
    assert entry_draft.triggers.synonyms == ("лихорадка", "жар")
    assert entry_draft.reveal_text == "38,5 °C"
    assert entry_draft.reveal_assets == ("img_temp",)

    assert draft.branch.prompt == "Предварительный диагноз?"
    assert len(draft.branch.options) == 2
    assert draft.branch.options[0].label == "ОКИ"
    assert draft.branch.options[0].is_correct is True
    assert draft.branch.options[1].label == "ОРВИ"
    assert draft.branch.options[1].is_correct is False


def test_empty_editor_to_draft(qtbot: QtBot) -> None:
    """Пустой редактор → пустые поиск и развилка без записей и опций."""
    editor = ClinicalEditor()
    qtbot.addWidget(editor)

    draft = editor.to_draft()
    assert draft.intro == ""
    assert draft.search.entries == ()
    assert draft.search.optional is False
    assert draft.branch.prompt == ""
    assert draft.branch.options == ()
