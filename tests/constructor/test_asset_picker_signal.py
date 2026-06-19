"""Тест сигнала ``AssetPicker.changed``: эмитируется при ``set_file`` и ``clear``."""
from __future__ import annotations

from pathlib import Path

from pytestqt.qtbot import QtBot

from educase_constructor.ui.asset_picker import AssetPicker


def test_changed_emitted_on_set_file(qtbot: QtBot, tmp_path: Path) -> None:
    """``set_file`` эмитирует сигнал ``changed``."""
    picker = AssetPicker()
    qtbot.addWidget(picker)

    source = tmp_path / "img.png"
    source.write_bytes(b"PNG")

    with qtbot.waitSignal(picker.changed, timeout=500):
        picker.set_file(str(source))


def test_changed_emitted_on_clear(qtbot: QtBot, tmp_path: Path) -> None:
    """``clear`` эмитирует сигнал ``changed`` (в том числе при уже пустом пикере)."""
    picker = AssetPicker()
    qtbot.addWidget(picker)

    with qtbot.waitSignal(picker.changed, timeout=500):
        picker.clear()
