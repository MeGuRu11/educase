"""Тесты EnvironmentEditor: сборка ``EnvironmentDraft`` из схемы, фото, документов и осмотра."""
from __future__ import annotations

from pathlib import Path

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


def test_filled_editor_to_draft(qtbot: QtBot, tmp_path: Path) -> None:
    """Заполненные схема, фото, документ и осмотр → корректный ``EnvironmentDraft``."""
    editor = EnvironmentEditor()
    qtbot.addWidget(editor)

    source = tmp_path / "env.png"
    source.write_bytes(b"PNG")
    editor.intro_edit.setText("Обследуйте пищеблок")
    editor.scheme_picker.set_file(str(source))
    photo_one = tmp_path / "img_01.png"
    photo_one.write_bytes(b"1")
    photo_two = tmp_path / "img_02.png"
    photo_two.write_bytes(b"2")
    editor.photos_picker.add_file(str(photo_one))
    editor.photos_picker.add_file(str(photo_two))

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
    assert draft.scheme is not None
    assert draft.scheme.source_path == str(source)
    assert draft.scheme.display_name == "env.png"
    assert len(draft.photos) == 2
    assert draft.photos[0].display_name == "img_01.png"
    assert draft.photos[1].display_name == "img_02.png"
    assert len(draft.documents) == 1
    assert draft.documents[0].prompt == "Выберите акт"
    assert draft.documents[0].options[0].title == "Акт обследования"
    assert draft.documents[0].options[0].is_correct is True
    assert len(draft.inspection.groups) == 1
    assert draft.inspection.groups[0].canonical == "грязь"
    assert draft.inspection.groups[0].synonyms == ("антисанитария",)


def test_empty_editor_to_draft(qtbot: QtBot) -> None:
    """Пустой редактор → схема не выбрана (``None``), пустые фото, документы и осмотр."""
    editor = EnvironmentEditor()
    qtbot.addWidget(editor)

    draft = editor.to_draft()
    assert draft.intro == ""
    assert draft.scheme is None
    assert draft.photos == ()
    assert draft.documents == ()
    assert draft.inspection.groups == ()


# --- интеграция zone_editor --------------------------------------------------


def _make_png(tmp_path: Path, name: str = "bg.png") -> Path:
    """Сохранить настоящий PNG 80×60 (через Qt) и вернуть путь."""
    from PySide6.QtGui import QColor, QPixmap

    pixmap = QPixmap(80, 60)
    pixmap.fill(QColor("white"))
    path = tmp_path / name
    assert pixmap.save(str(path))
    return path


def test_scheme_picker_change_wires_zone_editor(qtbot: QtBot, tmp_path: Path) -> None:
    """Выбор фона через scheme_picker передаёт его в zone_editor; зоны добавляются."""
    editor = EnvironmentEditor()
    qtbot.addWidget(editor)

    bg = _make_png(tmp_path)
    editor.scheme_picker.set_file(str(bg))
    assert editor.zone_editor.canvas.has_background()

    editor.zone_editor._add_button.click()
    hotspots = editor.to_draft().hotspots
    assert len(hotspots) == 1
    assert 0.0 <= hotspots[0].x <= 1.0
    assert 0.0 <= hotspots[0].y <= 1.0


def test_no_scheme_hotspots_empty(qtbot: QtBot) -> None:
    """Без схемы to_draft().hotspots пуст ()."""
    editor = EnvironmentEditor()
    qtbot.addWidget(editor)
    assert editor.to_draft().hotspots == ()
