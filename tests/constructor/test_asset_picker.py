"""Тесты пикеров ассетов: стабильные id-ссылки на файлы без дёрганья ``QFileDialog``."""
from __future__ import annotations

from pathlib import Path

from pytestqt.qtbot import QtBot

from epicase_constructor.ui.asset_picker import AssetListPicker, AssetPicker


def test_value_none_by_default(qtbot: QtBot) -> None:
    """До выбора файла ``value()`` равен ``None``."""
    picker = AssetPicker()
    qtbot.addWidget(picker)
    assert picker.value() is None


def test_set_file_builds_ref(qtbot: QtBot, tmp_path: Path) -> None:
    """``set_file`` даёт ``AssetRef``: непустой id, путь и имя файла сохранены."""
    picker = AssetPicker()
    qtbot.addWidget(picker)

    source = tmp_path / "scheme.png"
    source.write_bytes(b"PNG")
    picker.set_file(str(source))

    ref = picker.value()
    assert ref is not None
    assert ref.asset_id  # непустой стабильный id
    assert ref.asset_id.endswith(".png")  # расширение исходного файла сохранено
    assert ref.source_path == str(source)
    assert ref.display_name == "scheme.png"


def test_clear_resets_value(qtbot: QtBot, tmp_path: Path) -> None:
    """``clear()`` сбрасывает ссылку обратно в ``None``."""
    picker = AssetPicker()
    qtbot.addWidget(picker)

    source = tmp_path / "scheme.jpg"
    source.write_bytes(b"JPG")
    picker.set_file(str(source))
    assert picker.value() is not None

    picker.clear()
    assert picker.value() is None


def test_list_value_empty_by_default(qtbot: QtBot) -> None:
    """До выбора файлов ``value()`` мульти-пикера — пустой кортеж."""
    picker = AssetListPicker()
    qtbot.addWidget(picker)
    assert picker.value() == ()


def test_list_add_file_twice_distinct_ids(qtbot: QtBot, tmp_path: Path) -> None:
    """Два ``add_file`` → два ``AssetRef`` с разными id и сохранёнными путями/именами.

    Оба файла с ОДНИМ расширением: различие id обязано идти от ``uuid4``-префикса, а не суффикса.
    """
    picker = AssetListPicker()
    qtbot.addWidget(picker)

    first = tmp_path / "a.png"
    first.write_bytes(b"A")
    second = tmp_path / "b.png"
    second.write_bytes(b"B")
    picker.add_file(str(first))
    picker.add_file(str(second))

    refs = picker.value()
    assert len(refs) == 2
    assert refs[0].asset_id != refs[1].asset_id  # uuid4-префикс уникален при равных суффиксах
    assert refs[0].asset_id.endswith(".png")
    assert refs[1].asset_id.endswith(".png")
    assert refs[0].source_path == str(first)
    assert refs[0].display_name == "a.png"
    assert refs[1].display_name == "b.png"


def test_list_remove_last(qtbot: QtBot, tmp_path: Path) -> None:
    """«Удалить последний» убирает один файл; на пустом списке не падает."""
    picker = AssetListPicker()
    qtbot.addWidget(picker)

    for name in ("a.png", "b.png"):
        source = tmp_path / name
        source.write_bytes(b"X")
        picker.add_file(str(source))
    assert len(picker.value()) == 2

    picker.remove_button.click()
    assert len(picker.value()) == 1
    picker.remove_button.click()
    picker.remove_button.click()  # пустой список — без падения
    assert picker.value() == ()


def test_list_clear(qtbot: QtBot, tmp_path: Path) -> None:
    """``clear()`` сбрасывает список выбранных файлов."""
    picker = AssetListPicker()
    qtbot.addWidget(picker)

    source = tmp_path / "a.png"
    source.write_bytes(b"X")
    picker.add_file(str(source))
    assert len(picker.value()) == 1

    picker.clear()
    assert picker.value() == ()
