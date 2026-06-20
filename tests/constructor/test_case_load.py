"""Тесты открытия кейса на правку (L1): CaseEditor.load, пикеры, StartScreen, шов MainWindow."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from _pytest.monkeypatch import MonkeyPatch
from PySide6.QtWidgets import QMessageBox, QPushButton
from pytestqt.qtbot import QtBot

from educase_constructor.ui.asset_picker import AssetListPicker, AssetPicker
from educase_constructor.ui.case_editor import CaseEditor
from educase_constructor.ui.main_window import MainWindow
from educase_constructor.ui.start_screen import StartScreen
from educase_core.application.assets import read_asset_sources
from educase_core.application.case_builder import (
    AssetRef,
    CaseDraft,
    PatientDraft,
    build_case,
)
from educase_core.application.cases import save_case

_PAGE_START = 0
_PAGE_EDITOR = 1


def _draft_with_patient() -> CaseDraft:
    """Драфт кейса с заполненной метой и одним пациентом (ассет — байты из памяти)."""
    return CaseDraft(
        case_id="case-edit",
        title="Вспышка ОКИ",
        author="Иванов",
        nosology="Сальмонеллёз",
        unit_personnel=150,
        patients=(
            PatientDraft(
                title="Пациент 1",
                fields=(("Возраст", "25 лет"),),
                assets=(AssetRef("a1.png", "", display_name="a1.png", data=b"IMG"),),
            ),
        ),
    )


def test_case_editor_load_fills_meta_and_patients(qtbot: QtBot) -> None:
    """``CaseEditor.load``: мета выставлена, пациент с полями и ассетами; ``_case_id`` из драфта."""
    editor = CaseEditor()
    qtbot.addWidget(editor)

    editor.load(_draft_with_patient())

    assert editor._case_id == "case-edit"
    assert editor.title_edit.text() == "Вспышка ОКИ"
    assert editor.author_edit.text() == "Иванов"
    assert editor.nosology_edit.text() == "Сальмонеллёз"
    assert editor.unit_personnel_edit.text() == "150"

    assert len(editor.patient_editors) == 1
    patient = editor.patient_editors[0]
    assert patient.title_edit.text() == "Пациент 1"
    assert patient.fields_table.rowCount() == 1
    key_item = patient.fields_table.item(0, 0)
    value_item = patient.fields_table.item(0, 1)
    assert key_item is not None and value_item is not None
    assert key_item.text() == "Возраст"
    assert value_item.text() == "25 лет"
    refs = patient.assets_picker.value()
    assert len(refs) == 1
    assert refs[0].data == b"IMG"
    assert patient.assets_picker.files_list.count() == 1


def test_case_editor_load_blank_unit_personnel(qtbot: QtBot) -> None:
    """``unit_personnel=None`` → поле пустое (а не «None»)."""
    editor = CaseEditor()
    qtbot.addWidget(editor)

    editor.load(CaseDraft(case_id="c", title="T", unit_personnel=None))
    assert editor.unit_personnel_edit.text() == ""


def test_case_editor_load_replaces_previous_patients(qtbot: QtBot) -> None:
    """Повторный ``load`` заменяет прежних пациентов, не накапливая их."""
    editor = CaseEditor()
    qtbot.addWidget(editor)

    editor.add_patient()
    editor.add_patient()
    assert len(editor.patient_editors) == 2

    editor.load(_draft_with_patient())
    assert len(editor.patient_editors) == 1


def test_asset_picker_set_ref_shows_name(qtbot: QtBot) -> None:
    """``AssetPicker.set_ref`` фиксирует ссылку и показывает непустое имя."""
    picker = AssetPicker()
    qtbot.addWidget(picker)

    picker.set_ref(AssetRef("a1.png", "", display_name="a1.png", data=b"X"))
    assert picker.value() is not None
    assert picker.name_label.text() == "a1.png"


def test_asset_picker_set_ref_blank_name_fallback(qtbot: QtBot) -> None:
    """Пустой ``display_name`` → запасная подпись «вложение»."""
    picker = AssetPicker()
    qtbot.addWidget(picker)

    picker.set_ref(AssetRef("id", "", display_name="", data=b"X"))
    assert picker.name_label.text() == "вложение"


def test_asset_list_picker_load_shows_names(qtbot: QtBot) -> None:
    """``AssetListPicker.load`` заполняет список именами и значениями."""
    picker = AssetListPicker()
    qtbot.addWidget(picker)

    picker.load(
        [
            AssetRef("a.png", "", display_name="a.png", data=b"A"),
            AssetRef("b.png", "", display_name="b.png", data=b"B"),
        ]
    )
    assert len(picker.value()) == 2
    assert picker.files_list.count() == 2
    assert picker.files_list.item(0).text() == "a.png"
    assert picker.files_list.item(1).text() == "b.png"


def test_start_screen_has_open_button(qtbot: QtBot) -> None:
    """StartScreen содержит кнопку «Открыть кейс для правки»."""
    screen = StartScreen()
    qtbot.addWidget(screen)
    labels = [b.text() for b in screen.findChildren(QPushButton)]
    assert any("Открыть кейс для правки" in t for t in labels)


def test_start_screen_open_button_emits_signal(qtbot: QtBot) -> None:
    """Нажатие «Открыть кейс для правки» испускает ``open_requested``."""
    screen = StartScreen()
    qtbot.addWidget(screen)
    handler = MagicMock()
    screen.open_requested.connect(handler)

    btn = next(
        b for b in screen.findChildren(QPushButton) if "Открыть кейс для правки" in b.text()
    )
    btn.click()
    handler.assert_called_once()


def test_load_case_from_path_fills_editor(qtbot: QtBot, tmp_path: Path) -> None:
    """``load_case_from_path`` на реально сохранённом .educase → True и редактор заполнен."""
    draft = _draft_with_patient()
    case = build_case(draft)
    assets = read_asset_sources(draft)
    dst = tmp_path / "case.educase"
    save_case(case, dst, assets=assets)

    window = MainWindow()
    qtbot.addWidget(window)

    assert window.load_case_from_path(dst) is True
    assert window._stack.currentIndex() == _PAGE_EDITOR
    assert window.editor._case_id == "case-edit"
    assert window.editor.title_edit.text() == "Вспышка ОКИ"
    assert len(window.editor.patient_editors) == 1
    refs = window.editor.patient_editors[0].assets_picker.value()
    assert refs[0].data == b"IMG"


def test_load_case_from_path_broken_returns_false(
    qtbot: QtBot, tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Не-ZIP/битый файл → предупреждение, ``False``, редактор не открывается."""
    monkeypatch.setattr(
        QMessageBox, "warning", lambda *args, **kwargs: QMessageBox.StandardButton.Ok
    )
    bad = tmp_path / "broken.educase"
    bad.write_bytes(b"not a zip")

    window = MainWindow()
    qtbot.addWidget(window)

    assert window.load_case_from_path(bad) is False
    assert window._stack.currentIndex() == _PAGE_START