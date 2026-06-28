"""Тесты открытия кейса на правку (L1): CaseEditor.load, пикеры, StartScreen, шов MainWindow."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from _pytest.monkeypatch import MonkeyPatch
from PySide6.QtWidgets import QMessageBox, QPushButton
from pytestqt.qtbot import QtBot

from epicase_constructor.ui.asset_picker import AssetListPicker, AssetPicker
from epicase_constructor.ui.case_editor import CaseEditor
from epicase_constructor.ui.clinical_editor import ClinicalEditor
from epicase_constructor.ui.contacts_editor import ContactsEditor
from epicase_constructor.ui.environment_editor import EnvironmentEditor
from epicase_constructor.ui.field_editor import FieldEditor
from epicase_constructor.ui.main_window import MainWindow
from epicase_constructor.ui.scheme_zone_canvas import SchemeZoneCanvas
from epicase_constructor.ui.scheme_zone_editor import SchemeZoneEditor
from epicase_constructor.ui.start_screen import StartScreen
from epicase_core.application.assets import read_asset_sources
from epicase_core.application.case_builder import (
    AssetRef,
    BranchDraft,
    BranchOptionDraft,
    CaseDraft,
    ClinicalDraft,
    ContactsDraft,
    DocumentOptionDraft,
    DocumentTaskDraft,
    EnvironmentDraft,
    FieldDraft,
    HotspotDraft,
    InspectionDraft,
    PatientDraft,
    SchemeViewDraft,
    SearchDraft,
    SearchEntryDraft,
    SynonymSetDraft,
    build_case,
)
from epicase_core.application.cases import save_case

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


def _clinical_draft() -> ClinicalDraft:
    """Непустой ``ClinicalDraft`` для проверки заполнения под-редакторов этапа 2."""
    return ClinicalDraft(
        intro="Введение",
        search=SearchDraft(
            entries=(
                SearchEntryDraft(
                    triggers=SynonymSetDraft("температура", ("жар",)),
                    reveal_text="38.5",
                ),
            ),
            optional=True,
        ),
        branch=BranchDraft(
            prompt="Выбор пути",
            options=(
                BranchOptionDraft("Верный", is_correct=True),
                BranchOptionDraft("Неверный", is_correct=False),
            ),
        ),
        documents=(
            DocumentTaskDraft(
                prompt="Документ",
                options=(DocumentOptionDraft(title="ДМ-4", is_correct=True),),
            ),
        ),
    )


def test_field_editor_load_sets_type_and_subform(qtbot: QtBot) -> None:
    """``FieldEditor.load`` выставляет тип (страницу rule_stack) и значения под-формы."""
    editor = FieldEditor()
    qtbot.addWidget(editor)

    editor.load(
        FieldDraft(
            label="Число заболевших",
            field_type="number",
            required=False,
            number_value="25",
            number_tolerance="2",
            number_ndigits="0",
        )
    )

    assert editor.label_edit.text() == "Число заболевших"
    assert editor.type_combo.currentData() == "number"
    # Страница number в rule_stack (порядок FieldType: text=0, number=1, date=2, choice=3).
    assert editor.rule_stack.currentIndex() == 1
    assert editor.required_checkbox.isChecked() is False
    assert editor.number_value_edit.text() == "25"
    assert editor.tolerance_edit.text() == "2"
    assert editor.ndigits_edit.text() == "0"


def test_clinical_editor_load_fills_sections(qtbot: QtBot) -> None:
    """``ClinicalEditor.load`` заполняет вступление, поиск, ветку и документы."""
    editor = ClinicalEditor()
    qtbot.addWidget(editor)

    editor.load(_clinical_draft())

    assert editor.intro_edit.text() == "Введение"
    assert editor.search_editor.optional_checkbox.isChecked() is True
    assert len(editor.search_editor.entry_editors) == 1
    assert editor.search_editor.entry_editors[0].reveal_text_edit.text() == "38.5"
    assert editor.branch_editor.prompt_edit.text() == "Выбор пути"
    assert len(editor.branch_editor.option_editors) == 2
    assert editor.branch_editor.option_editors[0].correct_checkbox.isChecked() is True
    assert len(editor.documents_editor.task_editors) == 1
    option = editor.documents_editor.task_editors[0].option_editors[0]
    assert option.title_edit.text() == "ДМ-4"
    assert option.correct_checkbox.isChecked() is True


def test_case_editor_load_fills_clinical_tab(qtbot: QtBot) -> None:
    """``CaseEditor.load`` с непустым clinical заполняет вкладку «Клинический»."""
    editor = CaseEditor()
    qtbot.addWidget(editor)

    editor.load(CaseDraft(case_id="c", title="T", clinical=_clinical_draft()))

    assert editor.clinical_editor.intro_edit.text() == "Введение"
    assert editor.clinical_editor.branch_editor.prompt_edit.text() == "Выбор пути"


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
    """``load_case_from_path`` на реально сохранённом .epicase → True и редактор заполнен."""
    draft = _draft_with_patient()
    case = build_case(draft)
    assets = read_asset_sources(draft)
    dst = tmp_path / "case.epicase"
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
    window._stack.setCurrentIndex(_PAGE_START)


def test_load_case_from_path_broken_returns_false(
    qtbot: QtBot, tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Не-ZIP/битый файл → предупреждение, ``False``, редактор не открывается."""
    monkeypatch.setattr(
        QMessageBox, "warning", lambda *args, **kwargs: QMessageBox.StandardButton.Ok
    )
    bad = tmp_path / "broken.epicase"
    bad.write_bytes(b"not a zip")

    window = MainWindow()
    qtbot.addWidget(window)

    assert window.load_case_from_path(bad) is False
    assert window._stack.currentIndex() == _PAGE_START


def test_canvas_set_background_from_data(
    qtbot: QtBot, png_bytes: Callable[..., bytes]
) -> None:
    """``SchemeZoneCanvas.set_background`` с data-backed ``AssetRef`` рендерит фон из памяти."""
    canvas = SchemeZoneCanvas()
    qtbot.addWidget(canvas)

    canvas.set_background(AssetRef("bg.png", "", data=png_bytes(200, 150)))
    assert canvas.has_background() is True


def _contacts_ui_draft(png: bytes) -> ContactsDraft:
    """``ContactsDraft`` с data-backed фоном (PNG) и 2 зонами; первая — с вложенным видом."""
    return ContactsDraft(
        intro="Контакты",
        scheme=AssetRef("ct-bg.png", "", data=png),
        hotspots=(
            HotspotDraft(
                x=0.1,
                y=0.2,
                w=0.3,
                h=0.25,
                label="Казарма",
                reveal_text="Спальное",
                child=SchemeViewDraft(
                    background=AssetRef("ct-int.png", "", data=png),
                    hotspots=(
                        HotspotDraft(
                            x=0.4,
                            y=0.4,
                            w=0.2,
                            h=0.2,
                            label="Койка",
                            reveal_text="Место",
                        ),
                    ),
                ),
            ),
            HotspotDraft(
                x=0.55,
                y=0.5,
                w=0.25,
                h=0.3,
                label="Пищеблок",
                reveal_text="Кухня",
            ),
        ),
        inspection=InspectionDraft(groups=(SynonymSetDraft("вентиляция"),)),
    )


def test_contacts_editor_load_restores_scheme_zones(
    qtbot: QtBot, png_bytes: Callable[..., bytes]
) -> None:
    """``ContactsEditor.load`` восстанавливает фон, зоны (координаты ~), карточки, вложенный вид."""
    editor = ContactsEditor()
    qtbot.addWidget(editor)

    editor.load(_contacts_ui_draft(png_bytes(200, 150)))

    assert editor.intro_edit.text() == "Контакты"
    # Фон восстановлен из байтов памяти → холст имеет фон, зоны созданы.
    assert editor.zone_editor.canvas.has_background() is True
    assert len(editor.zone_editor.cards) == 2
    assert editor.zone_editor.cards[0].label_edit.text() == "Казарма"
    assert editor.zone_editor.cards[0].reveal_text_edit.text() == "Спальное"
    assert editor.zone_editor.cards[1].label_edit.text() == "Пищеблок"

    # Координаты зон близки к исходным (пиксельное округление холста).
    coords = editor.zone_editor.canvas.normalized_zones()
    assert coords[0][0] == pytest.approx(0.1, abs=0.02)
    assert coords[0][1] == pytest.approx(0.2, abs=0.02)
    assert coords[0][2] == pytest.approx(0.3, abs=0.02)
    assert coords[0][3] == pytest.approx(0.25, abs=0.02)

    # Вложенный вид первой зоны восстановлен: фон + 1 зона.
    nested = editor.zone_editor.cards[0].nested_editor
    assert nested.canvas.has_background() is True
    assert len(nested.cards) == 1
    assert nested.cards[0].label_edit.text() == "Койка"

    # Осмотр восстановлен.
    assert len(editor.inspection_editor.group_editors) == 1


def test_environment_editor_load_fills_photos_documents_inspection(
    qtbot: QtBot, png_bytes: Callable[..., bytes]
) -> None:
    """``EnvironmentEditor.load`` заполняет фон/зоны, фото, документы и осмотр."""
    editor = EnvironmentEditor()
    qtbot.addWidget(editor)

    editor.load(
        EnvironmentDraft(
            intro="Среда",
            scheme=AssetRef("env-bg.png", "", data=png_bytes(200, 150)),
            hotspots=(
                HotspotDraft(
                    x=0.2,
                    y=0.2,
                    w=0.2,
                    h=0.2,
                    label="Колодец",
                    reveal_text="Вода",
                ),
            ),
            photos=(
                AssetRef("p1.png", "", display_name="p1.png", data=b"P1"),
                AssetRef("p2.png", "", display_name="p2.png", data=b"P2"),
            ),
            documents=(
                DocumentTaskDraft(
                    prompt="Документ",
                    options=(DocumentOptionDraft(title="Протокол", is_correct=True),),
                ),
            ),
            inspection=InspectionDraft(groups=(SynonymSetDraft("санитария"),)),
        )
    )

    assert editor.intro_edit.text() == "Среда"
    assert editor.zone_editor.canvas.has_background() is True
    assert len(editor.zone_editor.cards) == 1
    assert editor.photos_picker.files_list.count() == 2
    assert len(editor.photos_picker.value()) == 2
    assert len(editor.documents_editor.task_editors) == 1
    assert len(editor.inspection_editor.group_editors) == 1


def test_load_hotspots_without_background_is_crash_safe(qtbot: QtBot) -> None:
    """``load_hotspots`` без фона не падает (пояс ``strict=False``): зон нет, карточек 0."""
    editor = SchemeZoneEditor()
    qtbot.addWidget(editor)

    # Фон не установлен → каждый ``add_zone`` вернёт None, карточки не создаются.
    editor.load_hotspots(
        (HotspotDraft(x=0.1, y=0.1, w=0.2, h=0.2, label="X", reveal_text="Y"),)
    )

    assert editor.canvas.has_background() is False
    assert len(editor.cards) == 0


def test_case_editor_load_fills_contacts_and_environment_tabs(qtbot: QtBot) -> None:
    """``CaseEditor.load`` с contacts+environment заполняет вкладки «Контакты» и «Среда»."""
    editor = CaseEditor()
    qtbot.addWidget(editor)

    editor.load(
        CaseDraft(
            case_id="c",
            title="T",
            contacts=ContactsDraft(intro="Контакты-введение"),
            environment=EnvironmentDraft(intro="Среда-введение"),
        )
    )

    assert editor.contacts_editor.intro_edit.text() == "Контакты-введение"
    assert editor.environment_editor.intro_edit.text() == "Среда-введение"
