"""Shared presentation resources for EpiCase applications."""

from epicase_ui.animated_start import (
    AnimatedStartBackground,
    AnimatedStartWidget,
    StartVariant,
)
from epicase_ui.brand_mark import BrandMarkWidget
from epicase_ui.branding import BrandAsset, brand_svg_bytes

__all__ = [
    "AnimatedStartBackground",
    "AnimatedStartWidget",
    "BrandAsset",
    "BrandMarkWidget",
    "StartVariant",
    "brand_svg_bytes",
]
