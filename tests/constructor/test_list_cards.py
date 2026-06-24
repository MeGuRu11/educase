"""Тесты Этапа 2: карточки элементов списков в Constructor.

Проверяем, что после add_* карточки (_x_cards) синхронизированы с публичными редакторами
(x_editors), заголовок первой карточки корректен, а после remove до пустого оба списка
обнуляются и placeholder снова становится видимым.
"""
from __future__ import annotations

import pytest
from PySide6.QtWidgets import QGroupBox
from pytestqt.qtbot import QtBot

from epicase_constructor.ui.branch_editor import BranchEditor
from epicase_constructor.ui.case_editor import CaseEditor
from epicase_constructor.ui.inspection_editor import InspectionEditor
from epicase_constructor.ui.search_editor import SearchEditor
from epicase_constructor.ui.timeline_editor import TimelineListEditor

_CARD_PARAMS = [
    (
        SearchEditor, "add_entry", "remove_last_entry",
        "_entry_cards", "entry_editors", "Точка поиска 1",
    ),
    (
        BranchEditor, "add_option", "remove_last_option",
        "_option_cards", "option_editors", "Вариант 1",
    ),
    (
        InspectionEditor, "add_group", "remove_last_group",
        "_group_cards", "group_editors", "Группа 1",
    ),
    (
        TimelineListEditor, "add_timeline", "remove_last_timeline",
        "_timeline_cards", "timeline_editors", "Срок наблюдения 1",
    ),
    (
        CaseEditor, "add_patient", "remove_last_patient",
        "_patient_cards", "patient_editors", "Пациент 1",
    ),
]


@pytest.mark.parametrize(
    ("editor_cls", "add_method", "remove_method", "cards_attr", "editors_attr", "title1"),
    _CARD_PARAMS,
    ids=lambda v: v.__name__ if isinstance(v, type) else (v if isinstance(v, str) else ""),
)
def test_card_count_matches_editors_and_title_is_correct(
    qtbot: QtBot,
    editor_cls: type,
    add_method: str,
    remove_method: str,
    cards_attr: str,
    editors_attr: str,
    title1: str,
) -> None:
    """После add карточки синхронизированы с редакторами; заголовок первой карточки верный."""
    editor = editor_cls()
    qtbot.addWidget(editor)

    getattr(editor, add_method)()

    cards = getattr(editor, cards_attr)
    editors = getattr(editor, editors_attr)
    assert len(cards) == 1
    assert len(editors) == 1
    assert isinstance(cards[0], QGroupBox)
    assert cards[0].title() == title1


@pytest.mark.parametrize(
    ("editor_cls", "add_method", "remove_method", "cards_attr", "editors_attr", "title1"),
    _CARD_PARAMS,
    ids=lambda v: v.__name__ if isinstance(v, type) else (v if isinstance(v, str) else ""),
)
def test_remove_last_clears_cards_and_shows_placeholder(
    qtbot: QtBot,
    editor_cls: type,
    add_method: str,
    remove_method: str,
    cards_attr: str,
    editors_attr: str,
    title1: str,
) -> None:
    """После удаления всех элементов _cards и editors пусты, placeholder снова виден."""
    editor = editor_cls()
    qtbot.addWidget(editor)

    getattr(editor, add_method)()
    getattr(editor, add_method)()
    getattr(editor, remove_method)()
    getattr(editor, remove_method)()

    cards = getattr(editor, cards_attr)
    editors_list = getattr(editor, editors_attr)
    assert len(cards) == 0
    assert len(editors_list) == 0
    assert not editor._empty_label.isHidden()
