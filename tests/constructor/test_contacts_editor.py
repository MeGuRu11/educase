"""Тесты ContactsEditor: сборка ``ContactsDraft`` из схемы и групп осмотра."""
from __future__ import annotations

from pytestqt.qtbot import QtBot

from educase_constructor.ui.contacts_editor import ContactsEditor


def test_add_and_remove_inspection_group(qtbot: QtBot) -> None:
    """«Добавить группу» увеличивает число редакторов осмотра, «Удалить последнюю» — уменьшает."""
    editor = ContactsEditor()
    qtbot.addWidget(editor)
    inspection = editor.inspection_editor

    assert len(inspection.group_editors) == 0
    inspection.add_group_button.click()
    inspection.add_group_button.click()
    assert len(inspection.group_editors) == 2
    inspection.remove_group_button.click()
    assert len(inspection.group_editors) == 1
    # Удаление при пустом списке не падает.
    inspection.remove_group_button.click()
    inspection.remove_group_button.click()
    assert len(inspection.group_editors) == 0


def test_filled_editor_to_draft(qtbot: QtBot) -> None:
    """Заполненные схема и группа осмотра (канон + синонимы) → корректный ``ContactsDraft``."""
    editor = ContactsEditor()
    qtbot.addWidget(editor)

    editor.intro_edit.setText("Обследуйте контактных")
    editor.scheme_edit.setText("scheme_contacts")

    editor.inspection_editor.add_group_button.click()
    group = editor.inspection_editor.group_editors[0]
    group.canonical_edit.setText("сыпь")
    group.synonyms_edit.setText("высыпания, экзантема ,")  # пустые куски отбрасываются

    draft = editor.to_draft()

    assert draft.intro == "Обследуйте контактных"
    assert draft.scheme == "scheme_contacts"
    assert len(draft.inspection.groups) == 1
    assert draft.inspection.groups[0].canonical == "сыпь"
    assert draft.inspection.groups[0].synonyms == ("высыпания", "экзантема")


def test_empty_editor_to_draft(qtbot: QtBot) -> None:
    """Пустой редактор → пустые схема и осмотр без групп."""
    editor = ContactsEditor()
    qtbot.addWidget(editor)

    draft = editor.to_draft()
    assert draft.intro == ""
    assert draft.scheme == ""
    assert draft.inspection.groups == ()
