"""Тесты PatientEditor: UX-правки таблицы полей и пояснительных подсказок."""
from __future__ import annotations

from PySide6.QtWidgets import QHeaderView
from pytestqt.qtbot import QtBot

from educase_constructor.ui.patient_editor import PatientEditor


def test_fields_table_columns_stretch(qtbot: QtBot) -> None:
    """Обе колонки таблицы «Поле/Значение» растягиваются на всю ширину."""
    editor = PatientEditor()
    qtbot.addWidget(editor)

    header = editor.fields_table.horizontalHeader()
    assert header.sectionResizeMode(0) == QHeaderView.ResizeMode.Stretch
    assert header.sectionResizeMode(1) == QHeaderView.ResizeMode.Stretch


def test_fields_table_has_minimum_height(qtbot: QtBot) -> None:
    """Таблица полей имеет разумную минимальную высоту (видно несколько строк)."""
    editor = PatientEditor()
    qtbot.addWidget(editor)

    assert editor.fields_table.minimumHeight() >= 140


def test_title_field_has_placeholder(qtbot: QtBot) -> None:
    """Поле заголовка снабжено непустой подсказкой-примером."""
    editor = PatientEditor()
    qtbot.addWidget(editor)

    assert editor.title_edit.placeholderText() != ""


def test_fields_hint_is_muted(qtbot: QtBot) -> None:
    """Подсказка над таблицей существует и приглушена (objectName «mutedHint»)."""
    editor = PatientEditor()
    qtbot.addWidget(editor)

    assert editor.fields_hint is not None
    assert editor.fields_hint.objectName() == "mutedHint"
