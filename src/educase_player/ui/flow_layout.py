"""Канонический FlowLayout: дочерние виджеты идут плиткой слева направо с переносом.

Реализует heightForWidth + _do_layout по образцу примера Qt FlowLayout.
"""
from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import QLayout, QLayoutItem, QWidget


class FlowLayout(QLayout):
    """QLayout с переносом: дети укладываются в ряды, следующий ряд — при нехватке ширины."""

    def __init__(
        self,
        parent: QWidget | None = None,
        h_spacing: int = 8,
        v_spacing: int = 8,
    ) -> None:
        super().__init__(parent)
        self._items: list[QLayoutItem] = []
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing

    # --- QLayout abstract API ---

    def addItem(self, item: QLayoutItem) -> None:
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int) -> QLayoutItem | None:
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int) -> QLayoutItem | None:
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        return size + QSize(m.left() + m.right(), m.top() + m.bottom())

    def expandingDirections(self) -> Qt.Orientation:
        return Qt.Orientation(0)

    # --- внутренняя укладка ---

    def _do_layout(self, rect: QRect, *, test_only: bool) -> int:
        m = self.contentsMargins()
        x = rect.x() + m.left()
        y = rect.y() + m.top()
        line_height = 0

        for item in self._items:
            item_size = item.sizeHint()
            iw = item_size.width()
            ih = item_size.height()
            next_x = x + iw + self._h_spacing
            if next_x - self._h_spacing > rect.right() and line_height > 0:
                x = rect.x() + m.left()
                y = y + line_height + self._v_spacing
                next_x = x + iw + self._h_spacing
                line_height = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item_size))
            x = next_x
            line_height = max(line_height, ih)

        return y + line_height - rect.y() + m.bottom()
