"""Тесты read-only диалога медицинской карты пациента."""
from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QScrollArea
from pytestqt.qtbot import QtBot

from epicase_core.domain.stages import PatientCard
from epicase_player.ui.asset_image_widget import AssetImageWidget
from epicase_player.ui.patient_detail_dialog import PatientDetailDialog


def _card(*fields: tuple[str, str], assets: tuple[str, ...] = ()) -> PatientCard:
    return PatientCard(
        id="p1",
        title="Иванов И.И.",
        fields=fields,
        assets=assets,
    )


def _label(dialog: PatientDetailDialog, object_name: str) -> QLabel:
    label = dialog.findChild(QLabel, object_name)
    assert label is not None
    return label


def test_dialog_has_medical_card_identity(qtbot: QtBot) -> None:
    dialog = PatientDetailDialog(_card(), assets={})
    qtbot.addWidget(dialog)

    assert dialog.objectName() == "patientDetailDialog"
    assert dialog.windowTitle() == "Иванов И.И."
    assert dialog.minimumWidth() == 600
    assert dialog.size().width() == 720
    assert dialog.size().height() == 560
    assert dialog.findChild(QFrame, "patientDetailHeader") is not None
    scroll = dialog.findChild(QScrollArea, "patientDetailScroll")
    assert scroll is not None
    assert scroll.widgetResizable() is True
    assert dialog.findChild(QFrame, "patientDetailBody") is not None
    assert dialog.findChild(QFrame, "patientDetailFooter") is not None
    assert _label(dialog, "patientDetailEyebrow").text() == "Медицинская карта пациента"
    assert _label(dialog, "patientDetailTitle").text() == "Иванов И.И."


def test_fields_render_as_ordered_semantic_label_value_rows(qtbot: QtBot) -> None:
    dialog = PatientDetailDialog(
        _card(
            ("Диагноз", "Сальмонеллёз"),
            ("Анамнез", "Заболел остро после возвращения из командировки."),
        ),
        assets={},
    )
    qtbot.addWidget(dialog)

    rows = dialog.findChildren(QFrame, "patientFieldRow")
    names = dialog.findChildren(QLabel, "patientFieldName")
    values = dialog.findChildren(QLabel, "patientFieldValue")

    assert len(rows) == 2
    assert [label.text() for label in names] == ["Диагноз", "Анамнез"]
    assert [label.text() for label in values] == [
        "Сальмонеллёз",
        "Заболел остро после возвращения из командировки.",
    ]
    for row, expected in zip(
        rows,
        (
            ("Диагноз", "Сальмонеллёз"),
            ("Анамнез", "Заболел остро после возвращения из командировки."),
        ),
        strict=True,
    ):
        row_names = row.findChildren(QLabel, "patientFieldName")
        row_values = row.findChildren(QLabel, "patientFieldValue")
        assert [label.text() for label in row_names] == [expected[0]]
        assert [label.text() for label in row_values] == [expected[1]]
    assert all(label.wordWrap() for label in names)
    assert all(label.wordWrap() for label in values)
    assert all(
        label.textInteractionFlags()
        & Qt.TextInteractionFlag.TextSelectableByMouse
        for label in values
    )


def test_empty_fields_show_neutral_empty_state(qtbot: QtBot) -> None:
    dialog = PatientDetailDialog(_card(), assets={})
    qtbot.addWidget(dialog)

    assert (
        _label(dialog, "patientEmptyState").text()
        == "Первичные данные не заполнены"
    )
    assert dialog.findChildren(QLabel, "patientFieldName") == []
    assert dialog.findChildren(QLabel, "patientFieldValue") == []


def test_materials_heading_is_absent_without_assets(qtbot: QtBot) -> None:
    dialog = PatientDetailDialog(_card(("Диагноз", "ОРВИ")), assets={})
    qtbot.addWidget(dialog)

    assert dialog.findChild(QLabel, "patientMaterialsTitle") is None


def test_materials_heading_and_assets_keep_source_order(
    qtbot: QtBot,
    png_bytes: Callable[..., bytes],
) -> None:
    dialog = PatientDetailDialog(
        _card(assets=("missing", "available")),
        assets={"available": png_bytes()},
    )
    qtbot.addWidget(dialog)

    assert _label(dialog, "patientMaterialsTitle").text() == "Материалы пациента"
    asset_widgets = dialog.findChildren(AssetImageWidget)
    assert [widget.has_image() for widget in asset_widgets] == [False, True]


def test_missing_asset_still_shows_unavailable_placeholder(qtbot: QtBot) -> None:
    dialog = PatientDetailDialog(
        _card(assets=("photo_01",)),
        assets={},
    )
    qtbot.addWidget(dialog)

    texts = [label.text() for label in dialog.findChildren(QLabel)]
    assert any("недоступно" in text for text in texts)


def test_close_button_accepts_dialog_once(qtbot: QtBot) -> None:
    dialog = PatientDetailDialog(_card(), assets={})
    qtbot.addWidget(dialog)
    accepted_spy = QSignalSpy(dialog.accepted)

    close_button = dialog.findChild(QPushButton, "patientDetailClose")
    assert close_button is not None
    close_button.click()

    assert accepted_spy.count() == 1
