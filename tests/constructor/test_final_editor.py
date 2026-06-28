"""Тесты FinalEditor и таймлайнов: сборка ``FinalDraft`` из поиска, документов и таймлайнов."""
from __future__ import annotations

from PySide6.QtWidgets import QTableWidgetItem
from pytestqt.qtbot import QtBot

from epicase_constructor.ui.final_editor import FinalEditor
from epicase_core.application.case_builder import (
    DocumentOptionDraft,
    DocumentTaskDraft,
    FinalDraft,
    SearchDraft,
    SearchEntryDraft,
    SynonymSetDraft,
    TimelineDraft,
    build_final,
)


def test_add_and_remove_timeline(qtbot: QtBot) -> None:
    """«Добавить таймлайн» увеличивает число редакторов, «Удалить последний» — уменьшает."""
    editor = FinalEditor()
    qtbot.addWidget(editor)
    timelines = editor.timelines_editor

    assert len(timelines.timeline_editors) == 0
    timelines.add_timeline_button.click()
    timelines.add_timeline_button.click()
    assert len(timelines.timeline_editors) == 2
    timelines.remove_timeline_button.click()
    assert len(timelines.timeline_editors) == 1
    # Удаление при пустом списке не падает.
    timelines.remove_timeline_button.click()
    timelines.remove_timeline_button.click()
    assert len(timelines.timeline_editors) == 0


def test_timeline_editor_collects_events(qtbot: QtBot) -> None:
    """TimelineEditor собирает заголовок и события (пары «дата/событие»)."""
    editor = FinalEditor()
    qtbot.addWidget(editor)

    editor.timelines_editor.add_timeline_button.click()
    timeline = editor.timelines_editor.timeline_editors[0]
    timeline.title_edit.setText("Сроки наблюдения")
    timeline.add_row_button.click()
    timeline.add_row_button.click()
    timeline.events_table.setItem(0, 0, QTableWidgetItem("2026-06-01"))
    timeline.events_table.setItem(0, 1, QTableWidgetItem("Первый случай"))
    timeline.events_table.setItem(1, 0, QTableWidgetItem("2026-06-10"))
    timeline.events_table.setItem(1, 1, QTableWidgetItem("Снятие карантина"))

    draft = timeline.to_draft()
    assert draft.title == "Сроки наблюдения"
    assert draft.events == (
        ("2026-06-01", "Первый случай"),
        ("2026-06-10", "Снятие карантина"),
    )


def test_filled_editor_to_draft(qtbot: QtBot) -> None:
    """Заполненные поиск, документ и таймлайн собираются в ``FinalDraft``."""
    editor = FinalEditor()
    qtbot.addWidget(editor)

    editor.intro_edit.setText("Сформулируйте окончательный диагноз")

    editor.search_editor.add_entry_button.click()
    editor.search_editor.entry_editors[0].triggers.canonical_edit.setText("источник")

    editor.documents_editor.add_task_button.click()
    task = editor.documents_editor.task_editors[0]
    task.prompt_edit.setText("Выберите акт расследования")
    task.add_option_button.click()
    task.option_editors[0].title_edit.setText("Акт расследования")

    editor.timelines_editor.add_timeline_button.click()
    timeline = editor.timelines_editor.timeline_editors[0]
    timeline.title_edit.setText("Очаг")
    timeline.add_row_button.click()
    timeline.events_table.setItem(0, 0, QTableWidgetItem("2026-06-01"))
    timeline.events_table.setItem(0, 1, QTableWidgetItem("Завоз"))

    draft = editor.to_draft()
    assert draft.intro == "Сформулируйте окончательный диагноз"
    assert len(draft.search.entries) == 1
    assert draft.search.entries[0].triggers.canonical == "источник"
    assert len(draft.documents) == 1
    assert draft.documents[0].options[0].title == "Акт расследования"
    assert len(draft.timelines) == 1
    assert draft.timelines[0].title == "Очаг"
    assert draft.timelines[0].events == (("2026-06-01", "Завоз"),)


def test_empty_editor_to_draft(qtbot: QtBot) -> None:
    """Пустой редактор → пустые поиск, документы и таймлайны."""
    editor = FinalEditor()
    qtbot.addWidget(editor)

    draft = editor.to_draft()
    assert draft.intro == ""
    assert draft.search.entries == ()
    assert draft.documents == ()
    assert draft.timelines == ()


def test_timeline_editor_drops_blank_rows(qtbot: QtBot) -> None:
    """Полностью пустая строка таблицы событий отбрасывается в ``to_draft`` (W6)."""
    editor = FinalEditor()
    qtbot.addWidget(editor)

    editor.timelines_editor.add_timeline_button.click()
    timeline = editor.timelines_editor.timeline_editors[0]
    timeline.add_row_button.click()  # пустая строка — без ввода
    timeline.add_row_button.click()
    timeline.events_table.setItem(1, 0, QTableWidgetItem("2026-06-01"))
    timeline.events_table.setItem(1, 1, QTableWidgetItem("Завоз"))

    draft = timeline.to_draft()
    assert draft.events == (("2026-06-01", "Завоз"),)


def test_build_final_drops_timeline_with_only_blank_rows(qtbot: QtBot) -> None:
    """Таймлайн с пустым заголовком и только пустыми строками отбрасывается билдером (W6)."""
    editor = FinalEditor()
    qtbot.addWidget(editor)

    editor.timelines_editor.add_timeline_button.click()
    timeline = editor.timelines_editor.timeline_editors[0]
    timeline.add_row_button.click()  # пустая строка, без ввода

    stage = build_final(editor.to_draft())
    assert stage.timelines == ()


def test_final_editor_load_round_trip(qtbot: QtBot) -> None:
    """``FinalEditor.load`` заполняет поиск, документы и таймлайны; ``to_draft`` идемпотентен."""
    editor = FinalEditor()
    qtbot.addWidget(editor)

    draft = FinalDraft(
        intro="Окончательный диагноз",
        search=SearchDraft(
            entries=(
                SearchEntryDraft(
                    triggers=SynonymSetDraft("источник"), reveal_text="вода"
                ),
            )
        ),
        documents=(
            DocumentTaskDraft(
                prompt="Выберите акт расследования",
                options=(
                    DocumentOptionDraft(title="Акт расследования", is_correct=True),
                ),
            ),
        ),
        timelines=(
            TimelineDraft(
                title="Наблюдение",
                events=(("01.06", "выявление"), ("03.06", "госпитализация")),
            ),
            TimelineDraft(title="Контроль", events=(("10.06", "снятие"),)),
        ),
    )

    editor.load(draft)
    assert len(editor.timelines_editor.timeline_editors) == 2
    assert editor.to_draft() == draft
