"""Тесты пустого состояния списочных редакторов Constructor (UX-проход A1).

Каждый список показывает приглушённую подсказку, пока он пуст, и скрывает её, как только
появляется первый элемент. Видимость проверяем через ``isHidden()`` — окно не показываем,
поэтому ``isVisible()`` всегда был бы ``False`` и ничего не проверял.
"""
from __future__ import annotations

import pytest
from pytestqt.qtbot import QtBot

from epicase_constructor.ui.branch_editor import BranchEditor
from epicase_constructor.ui.case_editor import CaseEditor
from epicase_constructor.ui.document_editor import DocumentListEditor
from epicase_constructor.ui.inspection_editor import InspectionEditor
from epicase_constructor.ui.search_editor import SearchEditor
from epicase_constructor.ui.timeline_editor import TimelineListEditor

# (класс редактора, метод добавления, метод удаления последнего)
_LIST_EDITORS = [
    (SearchEditor, "add_entry", "remove_last_entry"),
    (BranchEditor, "add_option", "remove_last_option"),
    (DocumentListEditor, "add_task", "remove_last_task"),
    (InspectionEditor, "add_group", "remove_last_group"),
    (TimelineListEditor, "add_timeline", "remove_last_timeline"),
    (CaseEditor, "add_patient", "remove_last_patient"),
]


@pytest.mark.parametrize(
    ("editor_cls", "add_method", "remove_method"),
    _LIST_EDITORS,
    ids=lambda value: value.__name__ if isinstance(value, type) else value,
)
def test_placeholder_tracks_emptiness(
    qtbot: QtBot,
    editor_cls: type,
    add_method: str,
    remove_method: str,
) -> None:
    """Пусто → подсказка видна; после add — скрыта; после remove до пустого — снова видна."""
    editor = editor_cls()
    qtbot.addWidget(editor)

    # Список пуст сразу после создания — подсказка не скрыта.
    assert not editor._empty_label.isHidden()

    getattr(editor, add_method)()
    assert editor._empty_label.isHidden()

    getattr(editor, remove_method)()
    assert not editor._empty_label.isHidden()
