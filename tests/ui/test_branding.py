"""Tests for packaged EpiCase brand resources."""

import tomllib
from pathlib import Path

import pytest
from PySide6.QtCore import QByteArray
from PySide6.QtSvg import QSvgRenderer

from epicase_ui import BrandAsset, brand_svg_bytes


@pytest.mark.parametrize("asset", list(BrandAsset))
def test_brand_svg_bytes_returns_valid_svg(asset: BrandAsset) -> None:
    """Every declared brand asset is a valid packaged SVG document."""
    data = brand_svg_bytes(asset)

    assert data.startswith(b"<svg")
    assert QSvgRenderer(QByteArray(data)).isValid()


def test_application_brand_assets_use_distinct_palettes() -> None:
    """Constructor and Player variants are visually distinguishable."""
    constructor = brand_svg_bytes(BrandAsset.CONSTRUCTOR)
    player = brand_svg_bytes(BrandAsset.PLAYER)

    assert constructor != player
    assert b"#B49A56" in constructor
    assert b"#D9EEEB" in player


def test_epicase_ui_is_in_build_and_type_check_package_lists() -> None:
    """The shared presentation package ships in wheels and is type-checked."""
    pyproject_path = Path(__file__).parents[2] / "pyproject.toml"
    config = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

    wheel_packages = config["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"]
    mypy_packages = config["tool"]["mypy"]["packages"]

    assert "src/epicase_ui" in wheel_packages
    assert "epicase_ui" in mypy_packages
