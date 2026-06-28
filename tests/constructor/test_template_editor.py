"""Тесты TemplateEditor: переключатель режима, видимость полей и load/to_draft."""
from __future__ import annotations

from PySide6.QtWidgets import QCheckBox
from pytestqt.qtbot import QtBot

from epicase_constructor.ui.template_editor import TemplateEditor
from epicase_core.application.case_builder import TemplateDraft


def test_default_mode_is_attachment(qtbot: QtBot) -> None:
    """По умолчанию режим «Прикрепить файл», а контейнер полей скрыт."""
    w = TemplateEditor()
    qtbot.addWidget(w)
    w.show()
    assert w.mode_combo.currentData() == "attachment"
    assert not w._fields_container.isVisible()


def test_attachment_mode_has_no_allow_multiple_toggle(qtbot: QtBot) -> None:
    """Constructor не предлагает ограничить число вложений."""
    w = TemplateEditor()
    qtbot.addWidget(w)

    assert w.findChild(QCheckBox, "allowMultipleToggle") is None


def test_switch_to_fields_shows_container(qtbot: QtBot) -> None:
    """Переключение на «Поля» показывает контейнер полей."""
    w = TemplateEditor()
    qtbot.addWidget(w)
    w.show()
    w.mode_combo.setCurrentIndex(w.mode_combo.findData("fields"))
    assert w._fields_container.isVisible()


def test_switch_back_to_attachment_restores_visibility(qtbot: QtBot) -> None:
    """Возврат на «Прикрепить файл» скрывает контейнер полей."""
    w = TemplateEditor()
    qtbot.addWidget(w)
    w.show()
    w.mode_combo.setCurrentIndex(w.mode_combo.findData("fields"))
    assert w._fields_container.isVisible()
    w.mode_combo.setCurrentIndex(w.mode_combo.findData("attachment"))
    assert not w._fields_container.isVisible()


def test_to_draft_derives_allow_multiple_from_fill_mode(qtbot: QtBot) -> None:
    """Attachment допускает несколько файлов, fields — нет."""
    w = TemplateEditor()
    qtbot.addWidget(w)

    assert w.to_draft().fill_mode == "attachment"
    assert w.to_draft().allow_multiple is True

    w.mode_combo.setCurrentIndex(w.mode_combo.findData("fields"))
    assert w.to_draft().fill_mode == "fields"
    assert w.to_draft().allow_multiple is False


def test_load_old_single_attachment_normalizes_allow_multiple(qtbot: QtBot) -> None:
    """Старое attachment+False повторно сохраняется с новой политикой."""
    w = TemplateEditor()
    qtbot.addWidget(w)
    w.show()
    w.mode_combo.setCurrentIndex(w.mode_combo.findData("fields"))  # начальное ≠ attachment
    w.load(
        TemplateDraft(title="T", fields=(), fill_mode="attachment", allow_multiple=False)
    )
    assert w.mode_combo.currentData() == "attachment"
    assert not w._fields_container.isVisible()
    assert w.to_draft().allow_multiple is True


def test_load_fields_sets_combo_and_shows_container(qtbot: QtBot) -> None:
    """load с fill_mode="fields" выставляет combo и показывает поля."""
    w = TemplateEditor()
    qtbot.addWidget(w)
    w.show()
    w.load(TemplateDraft(title="T", fields=(), fill_mode="fields"))
    assert w.mode_combo.currentData() == "fields"
    assert w._fields_container.isVisible()


def test_load_legacy_free_text_falls_back_to_fields(qtbot: QtBot) -> None:
    """Легаси-шаблон free_text (его нет в UI) при загрузке откатывается на «Поля»."""
    w = TemplateEditor()
    qtbot.addWidget(w)
    w.load(TemplateDraft(title="Старый", fields=(), fill_mode="free_text"))
    assert w.mode_combo.currentData() == "fields"


def test_round_trip_preserves_attachment_and_allow_multiple(qtbot: QtBot) -> None:
    """load(draft) -> to_draft() сохраняет attachment и allow_multiple."""
    w = TemplateEditor()
    qtbot.addWidget(w)
    draft = TemplateDraft(
        title="Документ", fields=(), fill_mode="attachment", allow_multiple=True
    )
    w.load(draft)
    restored = w.to_draft()
    assert restored.fill_mode == "attachment"
    assert restored.allow_multiple is True


def test_round_trip_preserves_fill_mode_fields(qtbot: QtBot) -> None:
    """load(draft) -> to_draft() сохраняет fill_mode="fields"."""
    w = TemplateEditor()
    qtbot.addWidget(w)
    draft = TemplateDraft(title="Документ", fields=(), fill_mode="fields")
    w.load(draft)
    assert w.to_draft().fill_mode == "fields"
