"""Tests for the scalable EpiCase brand mark widget."""

import pytest
from PySide6.QtCore import QPoint, QSize, Qt
from PySide6.QtGui import QPainter, QPixmap, QRegion
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QWidget
from pytestqt.qtbot import QtBot

import epicase_ui
import epicase_ui.brand_mark as brand_mark
from epicase_ui.brand_mark import BrandMarkWidget
from epicase_ui.branding import BrandAsset


def _render_transparent(widget: BrandMarkWidget) -> QPixmap:
    """Render only widget contents onto a transparent pixmap."""
    pixmap = QPixmap(widget.size())
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    try:
        widget.render(
            painter,
            QPoint(),
            QRegion(),
            QWidget.RenderFlag.DrawChildren,
        )
    finally:
        painter.end()
    return pixmap


def _alpha_bounds(pixmap: QPixmap) -> QRegion:
    """Return the non-transparent region of a rendered pixmap."""
    return QRegion(pixmap.mask())


@pytest.mark.parametrize(
    ("asset", "accessible_name"),
    [
        (BrandAsset.COMMON, "Логотип EpiCase"),
        (BrandAsset.CONSTRUCTOR, "Логотип EpiCase Constructor"),
        (BrandAsset.PLAYER, "Логотип EpiCase Player"),
    ],
)
def test_brand_mark_loads_asset_with_accessible_name(
    qtbot: QtBot,
    asset: BrandAsset,
    accessible_name: str,
) -> None:
    """The widget exposes its valid asset and application-specific label."""
    widget = BrandMarkWidget(asset)
    qtbot.addWidget(widget)

    assert widget.asset is asset
    assert widget.has_valid_svg is True
    assert widget.accessibleName() == accessible_name
    assert widget.objectName() == "brandMark"
    assert widget.minimumWidth() == 48
    assert widget.minimumHeight() == 48
    assert widget.findChild(QSvgRenderer) is not None
    assert epicase_ui.BrandMarkWidget is BrandMarkWidget


@pytest.mark.parametrize(
    ("progress", "expected"),
    [(-1.0, 0.0), (2.0, 1.0)],
)
def test_brand_mark_intro_progress_clamps_to_unit_interval(
    qtbot: QtBot,
    progress: float,
    expected: float,
) -> None:
    """Animation progress cannot leave the supported unit interval."""
    widget = BrandMarkWidget(BrandAsset.PLAYER)
    qtbot.addWidget(widget)

    widget.set_intro_progress(progress)

    assert widget.intro_progress == expected


@pytest.mark.parametrize("size", [32, 72, 144])
def test_brand_mark_renders_into_pixmap(qtbot: QtBot, size: int) -> None:
    """The scalable mark paints safely at every required target size."""
    widget = BrandMarkWidget(BrandAsset.PLAYER)
    qtbot.addWidget(widget)
    if size < widget.minimumWidth():
        widget.setMinimumSize(0, 0)
    widget.resize(size, size)
    pixmap = _render_transparent(widget)
    bounds = _alpha_bounds(pixmap).boundingRect()

    assert widget.size() == QSize(size, size)
    assert pixmap.size() == QSize(size, size)
    assert not bounds.isEmpty()
    assert pixmap.toImage().pixelColor(0, 0).alpha() == 0


def test_brand_mark_intro_progress_increases_rendered_bounds(qtbot: QtBot) -> None:
    """The completed intro renders larger than its initial state."""
    widget = BrandMarkWidget(BrandAsset.PLAYER)
    qtbot.addWidget(widget)
    widget.resize(144, 144)

    widget.set_intro_progress(0.0)
    initial_bounds = _alpha_bounds(_render_transparent(widget)).boundingRect()
    widget.set_intro_progress(1.0)
    complete_bounds = _alpha_bounds(_render_transparent(widget)).boundingRect()

    assert complete_bounds.width() > initial_bounds.width()
    assert complete_bounds.height() > initial_bounds.height()


def test_brand_mark_invalid_svg_uses_text_fallback(
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invalid packaged bytes fall back to centered EpiCase text."""

    def load_invalid_svg(_asset: BrandAsset) -> bytes:
        return b"not an svg"

    monkeypatch.setattr(brand_mark, "brand_svg_bytes", load_invalid_svg)
    widget = BrandMarkWidget(BrandAsset.PLAYER)
    qtbot.addWidget(widget)
    widget.resize(96, 96)
    pixmap = _render_transparent(widget)
    bounds = _alpha_bounds(pixmap).boundingRect()

    assert widget.has_valid_svg is False
    assert widget.fallback_text == "EpiCase"
    assert not bounds.isEmpty()
    assert pixmap.toImage().pixelColor(0, 0).alpha() == 0


def test_brand_mark_resource_oserror_uses_text_fallback(
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unavailable package data uses the same safe fallback."""

    def fail_to_load_svg(_asset: BrandAsset) -> bytes:
        raise OSError("resource unavailable")

    monkeypatch.setattr(brand_mark, "brand_svg_bytes", fail_to_load_svg)
    widget = BrandMarkWidget(BrandAsset.COMMON)
    qtbot.addWidget(widget)

    assert widget.has_valid_svg is False


def test_brand_mark_does_not_mask_programming_errors(
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unexpected loader failures remain visible to callers."""
    del qtbot

    def fail_with_programming_error(_asset: BrandAsset) -> bytes:
        raise ValueError("unexpected")

    monkeypatch.setattr(brand_mark, "brand_svg_bytes", fail_with_programming_error)

    with pytest.raises(ValueError, match="unexpected"):
        BrandMarkWidget(BrandAsset.COMMON)
