"""Access to packaged EpiCase brand assets."""

from enum import StrEnum
from importlib.resources import files


class BrandAsset(StrEnum):
    """Packaged EpiCase brand asset."""

    COMMON = "epicase"
    CONSTRUCTOR = "epicase_constructor"
    PLAYER = "epicase_player"


def brand_svg_bytes(asset: BrandAsset) -> bytes:
    """Return the packaged SVG bytes for a brand asset."""
    return (
        files("epicase_ui")
        .joinpath("resources", "brand", f"{asset.value}.svg")
        .read_bytes()
    )
