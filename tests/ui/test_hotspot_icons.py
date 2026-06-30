"""Общий каталог инфраструктурных SVG-иконок."""
from __future__ import annotations

from PySide6.QtCore import QByteArray
from PySide6.QtSvg import QSvgRenderer
from pytestqt.qtbot import QtBot

from epicase_ui.hotspot_icons import (
    DEFAULT_HOTSPOT_ICON_KEY,
    hotspot_icon_qicon,
    hotspot_icon_spec,
    hotspot_icon_specs,
    hotspot_icon_svg_bytes,
)


def test_registry_contains_approved_icon_keys() -> None:
    """Allowlist содержит утверждённые ключи в порядке Constructor combo."""
    assert tuple(spec.key for spec in hotspot_icon_specs()) == (
        "inspect",
        "barracks",
        "canteen",
        "medical",
        "water",
        "sanitary",
        "storage",
        "cold_storage",
        "waste",
        "entrance",
    )


def test_all_hotspot_svg_resources_are_valid() -> None:
    """Каждый package resource читается валидным QSvgRenderer."""
    for spec in hotspot_icon_specs():
        renderer = QSvgRenderer(QByteArray(hotspot_icon_svg_bytes(spec.key)))
        assert renderer.isValid(), spec.key


def test_unknown_and_empty_keys_fall_back_to_inspect() -> None:
    """Пустые, legacy и path-like ключи не выходят за allowlist."""
    assert DEFAULT_HOTSPOT_ICON_KEY == "inspect"
    assert hotspot_icon_spec("").key == "inspect"
    assert hotspot_icon_spec("zoom").key == "inspect"
    assert hotspot_icon_spec("../../secret").key == "inspect"


def test_hotspot_icon_qicon_renders_known_and_unknown_keys(qtbot: QtBot) -> None:
    """Combo получает ненулевую иконку и для известного ключа, и для fallback."""
    assert not hotspot_icon_qicon("water").isNull()
    assert not hotspot_icon_qicon("unknown").isNull()
