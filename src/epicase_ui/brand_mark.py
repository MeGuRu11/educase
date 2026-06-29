"""Scalable animated EpiCase brand mark widget."""

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QWidget

from epicase_ui.branding import BrandAsset, brand_svg_bytes

_ACCESSIBLE_NAMES = {
    BrandAsset.COMMON: "Логотип EpiCase",
    BrandAsset.CONSTRUCTOR: "Логотип EpiCase Constructor",
    BrandAsset.PLAYER: "Логотип EpiCase Player",
}


class BrandMarkWidget(QWidget):
    """Render a packaged EpiCase SVG with intro animation and text fallback."""

    def __init__(
        self,
        asset: BrandAsset = BrandAsset.COMMON,
        parent: QWidget | None = None,
    ) -> None:
        """Create a brand mark for the requested EpiCase application."""
        super().__init__(parent)
        self._asset = asset
        self._fallback_text = "EpiCase"
        self._intro_progress = 1.0
        try:
            svg_bytes = brand_svg_bytes(asset)
        except OSError:
            svg_bytes = b""
        self._renderer = QSvgRenderer(QByteArray(svg_bytes), self)

        self.setObjectName("brandMark")
        self.setAccessibleName(_ACCESSIBLE_NAMES[asset])
        self.setMinimumSize(48, 48)

    @property
    def asset(self) -> BrandAsset:
        """Return the packaged asset rendered by this widget."""
        return self._asset

    @property
    def fallback_text(self) -> str:
        """Return the text used when the packaged SVG is unavailable."""
        return self._fallback_text

    @property
    def has_valid_svg(self) -> bool:
        """Return whether the packaged asset is a valid SVG document."""
        return self._renderer.isValid()

    @property
    def intro_progress(self) -> float:
        """Return the clamped intro animation progress."""
        return self._intro_progress

    def set_intro_progress(self, progress: float) -> None:
        """Set intro animation progress, clamped to the unit interval."""
        self._intro_progress = min(1.0, max(0.0, progress))
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint the animated SVG or its safe text fallback."""
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self.has_valid_svg:
            font = painter.font()
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor("#1F2A33"))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                self._fallback_text,
            )
            return

        eased_progress = 1.0 - (1.0 - self._intro_progress) ** 3
        scale = 0.72 + 0.28 * eased_progress
        painter.setOpacity(0.25 + 0.75 * eased_progress)

        bounds = QRectF(self.contentsRect())
        side = min(bounds.width(), bounds.height()) * scale
        target = QRectF(0.0, 0.0, side, side)
        target.moveCenter(bounds.center())
        self._renderer.render(painter, target)
