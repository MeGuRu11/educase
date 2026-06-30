"""Shared presentation resources for EpiCase applications."""

from epicase_ui.animated_start import (
    AnimatedStartBackground,
    AnimatedStartWidget,
    StartVariant,
)
from epicase_ui.brand_mark import BrandMarkWidget
from epicase_ui.branding import BrandAsset, brand_svg_bytes
from epicase_ui.hotspot_icons import (
    DEFAULT_HOTSPOT_ICON_KEY,
    HotspotIconSpec,
    hotspot_icon_qicon,
    hotspot_icon_spec,
    hotspot_icon_specs,
    hotspot_icon_svg_bytes,
)
from epicase_ui.hotspot_marker import HotspotMarkerItem

__all__ = [
    "DEFAULT_HOTSPOT_ICON_KEY",
    "AnimatedStartBackground",
    "AnimatedStartWidget",
    "BrandAsset",
    "BrandMarkWidget",
    "HotspotIconSpec",
    "HotspotMarkerItem",
    "StartVariant",
    "brand_svg_bytes",
    "hotspot_icon_qicon",
    "hotspot_icon_spec",
    "hotspot_icon_specs",
    "hotspot_icon_svg_bytes",
]
