"""Тесты EnvironmentEditor: сборка ``EnvironmentDraft`` из схемы, фото, документов и осмотра."""
from __future__ import annotations

from pytestqt.qtbot import QtBot

from educase_constructor.ui.environment_editor import EnvironmentEditor


def test_add_and_remove_inspection_group(qtbot: QtBot) -> None:
    """«Добавить группу» увеличивает число редакторов осмотра, «Удалить последнюю» — уменьшает."""
    editor = EnvironmentEditor()
    qtbot.addWidget(editor)
    inspection = editor.inspection_editor

    assert len(inspection.group_editors) == 0
    inspection.add_group_button.click()
    inspection.add_group_button.click()
    assert len(inspection.group_editors) == 2
    inspection.remove_group_button.click()
    assert len(inspection.group_editors) == 1
    inspection.remove_group_button.click()
    inspection.remove_group_button.click()
    assert len(inspection.group_editors) == 0


def test_filled_editor_to_draft(qtbot: QtBot) -> None:
    """Заполненные схема, фото, документ и осмотр → корректный ``EnvironmentDraft``."""
    editor = EnvironmentEditor()
    qtbot.addWidget(editor)

    editor.intro_edit.setText("Обследуйте пищеблок")
    editor.scheme_edit.setText("scheme_env")
    editor.photos_edit.setText("img_01, img_02 ,")  # пустые куски отбрасываются

    editor.documents_editor.add_task_button.click()
    task = editor.documents_editor.task_editors[0]
    task.prompt_edit.setText("Выберите акт")
    task.add_option_button.click()
    option = task.option_editors[0]
    option.title_edit.setText("Акт обследования")
    option.correct_checkbox.setChecked(True)

    editor.inspection_editor.add_group_button.click()
    group = editor.inspection_editor.group_editors[0]
    group.canonical_edit.setText("грязь")
    group.synonyms_edit.setText("антисанитария")

    draft = editor.to_draft()

    assert draft.intro == "Обследуйте пищеблок"
    assert draft.scheme == "scheme_env"
    assert draft.photos == ("img_01", "img_02")
    assert len(draft.documents) == 1
    assert draft.documents[0].prompt == "Выберите акт"
    assert draft.documents[0].options[0].title == "Акт обследования"
    assert draft.documents[0].options[0].is_correct is True
    assert len(draft.inspection.groups) == 1
    assert draft.inspection.groups[0].canonical == "грязь"
    assert draft.inspection.groups[0].synonyms == ("антисанитария",)


def test_empty_editor_to_draft(qtbot: QtBot) -> None:
    """Пустой редактор → пустые схема, фото, документы и осмотр."""
    editor = EnvironmentEditor()
    qtbot.addWidget(editor)

    draft = editor.to_draft()
    assert draft.intro == ""
    assert draft.scheme == ""
    assert draft.photos == ()
    assert draft.documents == ()
    assert draft.inspection.groups == ()
