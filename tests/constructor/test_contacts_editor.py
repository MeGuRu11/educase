"""Тесты ContactsEditor: сборка ``ContactsDraft`` из схемы и групп осмотра."""
from __future__ import annotations

from pathlib import Path

from pytestqt.qtbot import QtBot

from epicase_constructor.ui.contacts_editor import ContactsEditor


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


def test_filled_editor_to_draft(qtbot: QtBot, tmp_path: Path) -> None:
    """Заполненные схема и группа осмотра (канон + синонимы) → корректный ``ContactsDraft``."""
    editor = ContactsEditor()
    qtbot.addWidget(editor)

    source = tmp_path / "scheme.png"
    source.write_bytes(b"PNG")
    editor.intro_edit.setText("Обследуйте контактных")
    editor.scheme_picker.set_file(str(source))

    editor.inspection_editor.add_group_button.click()
    group = editor.inspection_editor.group_editors[0]
    group.canonical_edit.setText("сыпь")
    group.synonyms_edit.setText("высыпания, экзантема ,")  # пустые куски отбрасываются

    draft = editor.to_draft()

    assert draft.intro == "Обследуйте контактных"
    assert draft.scheme is not None
    assert draft.scheme.source_path == str(source)
    assert draft.scheme.display_name == "scheme.png"
    assert len(draft.inspection.groups) == 1
    assert draft.inspection.groups[0].canonical == "сыпь"
    assert draft.inspection.groups[0].synonyms == ("высыпания", "экзантема")


def test_empty_editor_to_draft(qtbot: QtBot) -> None:
    """Пустой редактор → схема не выбрана (``None``) и осмотр без групп."""
    editor = ContactsEditor()
    qtbot.addWidget(editor)

    draft = editor.to_draft()
    assert draft.intro == ""
    assert draft.scheme is None
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
    editor = ContactsEditor()
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
    editor = ContactsEditor()
    qtbot.addWidget(editor)
    assert editor.to_draft().hotspots == ()
