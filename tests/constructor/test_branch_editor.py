"""Тесты редактора точки ветвления Constructor: сборка драфтов и objectName чекбокса."""
from __future__ import annotations

from pytestqt.qtbot import QtBot

from epicase_constructor.ui.branch_editor import BranchEditor, BranchOptionEditor


def test_branch_option_correct_checkbox_object_name(qtbot: QtBot) -> None:
    """correct_checkbox имеет objectName "criticalToggle" для CSS-таргетинга темы."""
    editor = BranchOptionEditor()
    qtbot.addWidget(editor)
    assert editor.correct_checkbox.objectName() == "criticalToggle"


def test_branch_editor_add_remove_options(qtbot: QtBot) -> None:
    """«Добавить вариант» увеличивает число редакторов опций, «Удалить» — уменьшает."""
    editor = BranchEditor()
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


def test_branch_editor_to_draft(qtbot: QtBot) -> None:
    """Формулировка и флаг верного варианта попадают в драфт."""
    editor = BranchEditor()
    qtbot.addWidget(editor)

    editor.prompt_edit.setText("Поставьте предварительный диагноз")
    editor.add_option_button.click()
    editor.add_option_button.click()
    opt_a, opt_b = editor.option_editors
    opt_a.label_edit.setText("Сальмонеллёз")
    opt_a.correct_checkbox.setChecked(True)
    opt_b.label_edit.setText("Дизентерия")

    draft = editor.to_draft()
    assert draft.prompt == "Поставьте предварительный диагноз"
    assert len(draft.options) == 2
    assert draft.options[0].label == "Сальмонеллёз"
    assert draft.options[0].is_correct is True
    assert draft.options[1].label == "Дизентерия"
    assert draft.options[1].is_correct is False
