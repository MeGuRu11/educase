"""Тесты редактора таймлайна Constructor: минимальная высота таблицы и сборка драфта."""
from __future__ import annotations

from pytestqt.qtbot import QtBot

from epicase_constructor.ui.timeline_editor import TimelineEditor, TimelineListEditor
from epicase_core.application.case_builder import TimelineDraft


def test_timeline_editor_events_table_minimum_height(qtbot: QtBot) -> None:
    """Таблица событий имеет minimumHeight >= 140 — видно несколько строк без скролла."""
    editor = TimelineEditor()
    qtbot.addWidget(editor)
    assert editor.events_table.minimumHeight() >= 140


def test_timeline_editor_add_remove_rows(qtbot: QtBot) -> None:
    """«+ строка» добавляет строку в таблицу, «− строка» удаляет последнюю."""
    editor = TimelineEditor()
    qtbot.addWidget(editor)

    assert editor.events_table.rowCount() == 0
    editor.add_row_button.click()
    editor.add_row_button.click()
    assert editor.events_table.rowCount() == 2
    editor.remove_row_button.click()
    assert editor.events_table.rowCount() == 1
    editor.remove_row_button.click()
    editor.remove_row_button.click()
    assert editor.events_table.rowCount() == 0


def test_timeline_list_editor_add_remove(qtbot: QtBot) -> None:
    """«Добавить таймлайн» и «Удалить последний» управляют списком редакторов."""
    editor = TimelineListEditor()
    qtbot.addWidget(editor)

    assert len(editor.timeline_editors) == 0
    editor.add_timeline_button.click()
    editor.add_timeline_button.click()
    assert len(editor.timeline_editors) == 2
    editor.remove_timeline_button.click()
    assert len(editor.timeline_editors) == 1


def test_timeline_editor_load_round_trip(qtbot: QtBot) -> None:
    """``TimelineEditor.load`` заполняет заголовок и таблицу; ``to_draft`` идемпотентен."""
    editor = TimelineEditor()
    qtbot.addWidget(editor)

    draft = TimelineDraft(
        title="Наблюдение",
        events=(("01.06", "выявление"), ("03.06", "госпитализация")),
    )
    editor.load(draft)

    assert editor.title_edit.text() == "Наблюдение"
    assert editor.events_table.rowCount() == 2
    assert editor.to_draft() == draft


def test_timeline_list_editor_load_round_trip(qtbot: QtBot) -> None:
    """``TimelineListEditor.load`` пересобирает список таймлайнов; ``to_draft`` идемпотентен."""
    editor = TimelineListEditor()
    qtbot.addWidget(editor)

    drafts = (
        TimelineDraft(title="Наблюдение", events=(("01.06", "выявление"),)),
        TimelineDraft(title="Контроль", events=(("10.06", "снятие"),)),
    )
    editor.load(drafts)

    assert len(editor.timeline_editors) == 2
    assert editor.to_draft() == drafts
