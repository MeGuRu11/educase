"""Тесты TemplateEditor: переключатель режима заполнения, видимость полей, load/to_draft."""
from __future__ import annotations

from pytestqt.qtbot import QtBot

from educase_constructor.ui.template_editor import TemplateEditor
from educase_core.application.case_builder import TemplateDraft


def test_default_mode_is_free_text_and_container_hidden(qtbot: QtBot) -> None:
    """По умолчанию режим «Свободный ввод» и контейнер полей скрыт после show()."""
    w = TemplateEditor()
    qtbot.addWidget(w)
    w.show()
    assert w.mode_combo.currentData() == "free_text"
    assert not w._fields_container.isVisible()


def test_switch_to_fields_shows_container(qtbot: QtBot) -> None:
    """Переключение комбо на «Поля» показывает контейнер полей."""
    w = TemplateEditor()
    qtbot.addWidget(w)
    w.show()
    w.mode_combo.setCurrentIndex(w.mode_combo.findData("fields"))
    assert w._fields_container.isVisible()


def test_switch_back_to_free_text_hides_container(qtbot: QtBot) -> None:
    """Переключение обратно на «Свободный ввод» скрывает контейнер полей."""
    w = TemplateEditor()
    qtbot.addWidget(w)
    w.show()
    w.mode_combo.setCurrentIndex(w.mode_combo.findData("fields"))
    assert w._fields_container.isVisible()
    w.mode_combo.setCurrentIndex(w.mode_combo.findData("free_text"))
    assert not w._fields_container.isVisible()


def test_to_draft_returns_fill_mode(qtbot: QtBot) -> None:
    """to_draft() возвращает fill_mode, соответствующий выбранному пункту комбо."""
    w = TemplateEditor()
    qtbot.addWidget(w)

    assert w.to_draft().fill_mode == "free_text"

    w.mode_combo.setCurrentIndex(w.mode_combo.findData("fields"))
    assert w.to_draft().fill_mode == "fields"


def test_load_free_text_sets_combo_and_hides_container(qtbot: QtBot) -> None:
    """load с fill_mode="free_text" выставляет combo и скрывает контейнер полей."""
    w = TemplateEditor()
    qtbot.addWidget(w)
    w.show()
    w.mode_combo.setCurrentIndex(w.mode_combo.findData("fields"))  # начальное ≠ free_text
    w.load(TemplateDraft(title="T", fields=(), fill_mode="free_text"))
    assert w.mode_combo.currentData() == "free_text"
    assert not w._fields_container.isVisible()


def test_load_fields_sets_combo_and_shows_container(qtbot: QtBot) -> None:
    """load с fill_mode="fields" выставляет combo и показывает контейнер полей."""
    w = TemplateEditor()
    qtbot.addWidget(w)
    w.show()
    w.load(TemplateDraft(title="T", fields=(), fill_mode="fields"))
    assert w.mode_combo.currentData() == "fields"
    assert w._fields_container.isVisible()


def test_round_trip_preserves_fill_mode_free_text(qtbot: QtBot) -> None:
    """load(draft) -> to_draft() сохраняет fill_mode="free_text"."""
    w = TemplateEditor()
    qtbot.addWidget(w)
    draft = TemplateDraft(title="Документ", fields=(), fill_mode="free_text")
    w.load(draft)
    assert w.to_draft().fill_mode == "free_text"


def test_round_trip_preserves_fill_mode_fields(qtbot: QtBot) -> None:
    """load(draft) -> to_draft() сохраняет fill_mode="fields"."""
    w = TemplateEditor()
    qtbot.addWidget(w)
    draft = TemplateDraft(title="Документ", fields=(), fill_mode="fields")
    w.load(draft)
    assert w.to_draft().fill_mode == "fields"
