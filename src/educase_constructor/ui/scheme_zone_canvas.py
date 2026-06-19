"""Графическое ядро редактора зон схемы (Constructor, R2-B.1, ADR-013).

Холст «фоновое изображение + прямоугольные зоны в долях [0..1]»: рисование резиновой
рамкой, перемещение и изменение размера зон мышью (восемь ручек), пересчёт геометрии в
доли. Без UI-обёртки (список/кнопки/панель свойств) и без интеграции в редакторы этапов —
это R2-B.2. Зоны плоские, без вложенности (R2.1), без зума/панорамы (R3).

Отрисовка повторяет ``educase_player.ui.scheme_viewer`` (teal-обводка, лёгкая заливка,
фиксированный масштаб 1:1, фон шириной до ``_MAX_WIDTH``). Отличие: фон грузится из файла
на диске по ``AssetRef.source_path`` (байты ассета ещё не упакованы), а не из байт.

Только виджеты (без QML); перо/кисть ``QGraphicsItem`` задаются через API сцены — QSS на
графические элементы не распространяется. ``objectName`` вью — ``schemeView`` (визуальную
рамку рисует QSS-border темы).
"""
from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Any

from loguru import logger
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QMouseEvent, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsItem,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSceneHoverEvent,
    QGraphicsSceneMouseEvent,
    QGraphicsView,
    QStyleOptionGraphicsItem,
    QWidget,
)

from educase_core.application.case_builder import AssetRef

_MAX_WIDTH = 600

# Размер квадратной ручки resize в пикселях и минимальный размер зоны (по обеим осям).
_HANDLE = 8.0
_MIN_SIZE = 2.0 * _HANDLE

# Акцентные цвета зоны берём из общей темы: teal-обводка и лёгкая заливка (как в Player).
_ZONE_PEN = QColor("#0F766E")
_ZONE_FILL = QColor(15, 118, 110, 48)

_PLACEHOLDER_TEXT = "Сначала выберите фон схемы"


class _Handle(Enum):
    """Восемь ручек resize: четыре угла и четыре середины сторон."""

    TOP_LEFT = "top_left"
    TOP = "top"
    TOP_RIGHT = "top_right"
    LEFT = "left"
    RIGHT = "right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM = "bottom"
    BOTTOM_RIGHT = "bottom_right"


_LEFT_HANDLES = {_Handle.TOP_LEFT, _Handle.LEFT, _Handle.BOTTOM_LEFT}
_RIGHT_HANDLES = {_Handle.TOP_RIGHT, _Handle.RIGHT, _Handle.BOTTOM_RIGHT}
_TOP_HANDLES = {_Handle.TOP_LEFT, _Handle.TOP, _Handle.TOP_RIGHT}
_BOTTOM_HANDLES = {_Handle.BOTTOM_LEFT, _Handle.BOTTOM, _Handle.BOTTOM_RIGHT}

_HANDLE_CURSORS = {
    _Handle.TOP_LEFT: Qt.CursorShape.SizeFDiagCursor,
    _Handle.BOTTOM_RIGHT: Qt.CursorShape.SizeFDiagCursor,
    _Handle.TOP_RIGHT: Qt.CursorShape.SizeBDiagCursor,
    _Handle.BOTTOM_LEFT: Qt.CursorShape.SizeBDiagCursor,
    _Handle.TOP: Qt.CursorShape.SizeVerCursor,
    _Handle.BOTTOM: Qt.CursorShape.SizeVerCursor,
    _Handle.LEFT: Qt.CursorShape.SizeHorCursor,
    _Handle.RIGHT: Qt.CursorShape.SizeHorCursor,
}


def _clamp01(value: float) -> float:
    """Зажать долю в отрезок [0..1]."""
    return min(1.0, max(0.0, value))


def _fit_segment(
    lo: float, hi: float, bound_lo: float, bound_hi: float
) -> tuple[float, float]:
    """Вписать отрезок ``[lo, hi]`` в ``[bound_lo, bound_hi]`` с минимальной длиной.

    Сначала каждый край зажимается в границы, затем длина доводится до ``_MIN_SIZE``
    (растём в сторону, где есть место). Единый кламп для одной оси при resize и в тестах.
    """
    lo = min(max(lo, bound_lo), bound_hi)
    hi = min(max(hi, bound_lo), bound_hi)
    if hi - lo < _MIN_SIZE:
        hi = lo + _MIN_SIZE
        if hi > bound_hi:
            hi = bound_hi
            lo = max(bound_lo, hi - _MIN_SIZE)
    return lo, hi


class ZoneItem(QGraphicsRectItem):
    """Одна прямоугольная зона схемы: перемещаемая, выделяемая, с ручками resize.

    Геометрия хранится в координатах сцены (``pos == (0, 0)``, ``rect()`` в пикселях
    сцены), поэтому ``mapRectToScene(rect())`` совпадает с ``sceneBoundingRect``. Ручки
    рисуются и активны только при выделении; их единый путь пересчёта — ``set_scene_rect``.
    """

    def __init__(self, rect: QRectF, on_change: Callable[[], None] | None = None) -> None:
        super().__init__(rect)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self._on_change = on_change
        self._active_handle: _Handle | None = None
        self._press_scene_rect = QRectF()

    # --- геометрия ручек -----------------------------------------------------

    def _handle_centers(self) -> dict[_Handle, QPointF]:
        """Центры восьми ручек в координатах элемента (по краям ``rect()``)."""
        r = self.rect()
        cx = r.center().x()
        cy = r.center().y()
        return {
            _Handle.TOP_LEFT: QPointF(r.left(), r.top()),
            _Handle.TOP: QPointF(cx, r.top()),
            _Handle.TOP_RIGHT: QPointF(r.right(), r.top()),
            _Handle.LEFT: QPointF(r.left(), cy),
            _Handle.RIGHT: QPointF(r.right(), cy),
            _Handle.BOTTOM_LEFT: QPointF(r.left(), r.bottom()),
            _Handle.BOTTOM: QPointF(cx, r.bottom()),
            _Handle.BOTTOM_RIGHT: QPointF(r.right(), r.bottom()),
        }

    def _handle_rect(self, center: QPointF) -> QRectF:
        """Квадрат ручки ``_HANDLE`` пикселей с центром в ``center``."""
        return QRectF(
            center.x() - _HANDLE / 2.0,
            center.y() - _HANDLE / 2.0,
            _HANDLE,
            _HANDLE,
        )

    def _handle_at(self, pos: QPointF) -> _Handle | None:
        """Ручка под точкой ``pos`` (координаты элемента) либо ``None``."""
        for handle, center in self._handle_centers().items():
            if self._handle_rect(center).contains(pos):
                return handle
        return None

    # --- отрисовка -----------------------------------------------------------

    def boundingRect(self) -> QRectF:
        """``rect()`` с запасом ``_HANDLE/2`` со всех сторон, чтобы ручки не обрезались."""
        margin = _HANDLE / 2.0
        return self.rect().adjusted(-margin, -margin, margin, margin)

    def shape(self) -> QPainterPath:
        """Область попадания: прямоугольник, плюс ручки при выделении (их можно схватить)."""
        path = QPainterPath()
        path.addRect(self.rect())
        if self.isSelected():
            for center in self._handle_centers().values():
                path.addRect(self._handle_rect(center))
        return path

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        """Прямоугольник зоны (без пунктира выделения Qt) и ручки при выделении."""
        selected = self.isSelected()
        painter.setPen(QPen(_ZONE_PEN, 3.0 if selected else 2.0))
        painter.setBrush(QBrush(_ZONE_FILL))
        painter.drawRect(self.rect())
        if selected:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(_ZONE_PEN))
            for center in self._handle_centers().values():
                painter.drawRect(self._handle_rect(center))

    # --- курсоры -------------------------------------------------------------

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        """Курсор: resize над ручкой, перемещение внутри (если выделено), иначе указатель."""
        if not self.isSelected():
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            handle = self._handle_at(event.pos())
            if handle is None:
                self.setCursor(Qt.CursorShape.SizeAllCursor)
            else:
                self.setCursor(_HANDLE_CURSORS[handle])
        super().hoverMoveEvent(event)

    # --- мышь ----------------------------------------------------------------

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Нажатие на ручку выделенной зоны начинает resize; иначе — штатное перемещение."""
        if self.isSelected():
            handle = self._handle_at(event.pos())
            if handle is not None:
                self._active_handle = handle
                self._press_scene_rect = self.mapRectToScene(self.rect())
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """При активной ручке — resize по курсору; иначе — перемещение (через базовый класс)."""
        if self._active_handle is not None:
            self._resize_to(event.scenePos())
            if self._on_change is not None:
                self._on_change()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Сбросить активную ручку и сообщить об изменении геометрии."""
        self._active_handle = None
        super().mouseReleaseEvent(event)
        if self._on_change is not None:
            self._on_change()

    def _resize_to(self, scene_pos: QPointF) -> None:
        """Пересчитать прямоугольник под активной ручкой, держа противоположный край фикс.

        Двигаются только края, которых касается ручка; противоположные остаются от
        стартовой геометрии. Минимум по оси соблюдается до общего клампа ``set_scene_rect``,
        чтобы зафиксированный край не «уезжал».
        """
        handle = self._active_handle
        start = self._press_scene_rect
        left, top, right, bottom = start.left(), start.top(), start.right(), start.bottom()
        if handle in _LEFT_HANDLES:
            left = min(scene_pos.x(), right - _MIN_SIZE)
        if handle in _RIGHT_HANDLES:
            right = max(scene_pos.x(), left + _MIN_SIZE)
        if handle in _TOP_HANDLES:
            top = min(scene_pos.y(), bottom - _MIN_SIZE)
        if handle in _BOTTOM_HANDLES:
            bottom = max(scene_pos.y(), top + _MIN_SIZE)
        self.set_scene_rect(QRectF(QPointF(left, top), QPointF(right, bottom)))

    # --- геометрия в координатах сцены --------------------------------------

    def _clamp_scene_rect(self, rect: QRectF) -> QRectF:
        """Нормализовать прямоугольник, вписать в ``sceneRect`` и довести до минимума."""
        r = rect.normalized()
        scene = self.scene()
        if scene is None:
            x0, x1 = r.left(), max(r.right(), r.left() + _MIN_SIZE)
            y0, y1 = r.top(), max(r.bottom(), r.top() + _MIN_SIZE)
        else:
            bounds = scene.sceneRect()
            x0, x1 = _fit_segment(r.left(), r.right(), bounds.left(), bounds.right())
            y0, y1 = _fit_segment(r.top(), r.bottom(), bounds.top(), bounds.bottom())
        return QRectF(x0, y0, x1 - x0, y1 - y0)

    def set_scene_rect(self, rect: QRectF) -> None:
        """Задать геометрию зоны в координатах сцены с клампом (минимум + границы).

        Обнуляет ``pos`` и кладёт ``rect()`` в координатах сцены — единый путь для логики
        ручек, резинового рисования и тестов.
        """
        clamped = self._clamp_scene_rect(rect)
        self.prepareGeometryChange()
        self.setRect(clamped)
        self.setPos(0.0, 0.0)

    def _clamp_position(self, new_pos: QPointF, bounds: QRectF) -> QPointF:
        """Зажать позицию так, чтобы ``sceneBoundingRect`` оставался внутри ``bounds``."""
        r = self.rect()
        min_x = bounds.left() - r.left()
        max_x = bounds.right() - r.right()
        min_y = bounds.top() - r.top()
        max_y = bounds.bottom() - r.bottom()
        return QPointF(
            min(max(new_pos.x(), min_x), max_x),
            min(max(new_pos.y(), min_y), max_y),
        )

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        """Кламп позиции при перемещении и уведомление об изменении геометрии."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            scene = self.scene()
            if scene is not None and isinstance(value, QPointF):
                value = self._clamp_position(value, scene.sceneRect())
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            if self._on_change is not None:
                self._on_change()
        return super().itemChange(change, value)

    def normalized(self, scene_w: float, scene_h: float) -> tuple[float, float, float, float]:
        """Геометрия зоны в долях [0..1] от размеров сцены (с клампом долей)."""
        r = self.mapRectToScene(self.rect())
        return (
            _clamp01(r.x() / scene_w),
            _clamp01(r.y() / scene_h),
            _clamp01(r.width() / scene_w),
            _clamp01(r.height() / scene_h),
        )


class SchemeZoneCanvas(QGraphicsView):
    """Холст схемы: фон из файла + прямоугольные зоны (рисование/перемещение/resize).

    Фиксированный масштаб 1:1 (зум/панорама — R3): размер вью равен размеру фона, скроллбары
    отключены. Без фона показывается плейсхолдер; рисование и добавление зон недоступны.
    """

    def __init__(
        self,
        on_zones_changed: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setObjectName("schemeView")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._pixmap_item: QGraphicsPixmapItem | None = None
        self._px_w: int = 0
        self._px_h: int = 0
        self._zones: list[ZoneItem] = []
        self._on_zones_changed = on_zones_changed
        self._draw_start: QPointF | None = None
        self._draft_zone: ZoneItem | None = None

        self.set_background(None)

    # --- фон -----------------------------------------------------------------

    def set_background(self, ref: AssetRef | None) -> None:
        """Сменить фон. Доли привязаны к фону, поэтому сначала всегда сбрасываем зоны.

        Нет ``ref`` или файл не грузится — плейсхолдер и нулевой размер фона. Иначе — pixmap
        (с масштабом до ``_MAX_WIDTH``), ``sceneRect`` и фиксированный размер по нему.
        """
        self._draw_start = None
        self._draft_zone = None
        self.clear_zones()

        if ref is None:
            self._show_placeholder()
            return

        pixmap = QPixmap(ref.source_path)
        if pixmap.isNull():
            logger.warning("Не удалось загрузить фон схемы из {}", ref.source_path)
            self._show_placeholder()
            return

        if pixmap.width() > _MAX_WIDTH:
            pixmap = pixmap.scaledToWidth(
                _MAX_WIDTH, Qt.TransformationMode.SmoothTransformation
            )
        self._scene.clear()
        self._pixmap_item = self._scene.addPixmap(pixmap)
        self._px_w = pixmap.width()
        self._px_h = pixmap.height()
        self._scene.setSceneRect(0.0, 0.0, float(self._px_w), float(self._px_h))
        self.setFixedSize(self._px_w, self._px_h)

    def _show_placeholder(self) -> None:
        """Очистить сцену и показать текст-плейсхолдер; размер фона — нулевой."""
        self._scene.clear()
        self._pixmap_item = None
        self._px_w = 0
        self._px_h = 0
        text_item = self._scene.addText(_PLACEHOLDER_TEXT)
        bounds = text_item.boundingRect()
        self._scene.setSceneRect(bounds)
        self.setFixedSize(max(1, int(bounds.width()) + 1), max(1, int(bounds.height()) + 1))

    def has_background(self) -> bool:
        """``True``, если фон успешно загружен (ненулевой размер)."""
        return self._px_w > 0 and self._px_h > 0

    # --- зоны ----------------------------------------------------------------

    def add_zone(self, nx: float, ny: float, nw: float, nh: float) -> ZoneItem | None:
        """Добавить зону из долей [0..1]. Без фона рисование невозможно — вернуть ``None``."""
        if not self.has_background():
            return None
        item = ZoneItem(QRectF(), on_change=self._on_zones_changed)
        self._scene.addItem(item)
        item.set_scene_rect(
            QRectF(nx * self._px_w, ny * self._px_h, nw * self._px_w, nh * self._px_h)
        )
        self._zones.append(item)
        return item

    def remove_selected(self) -> None:
        """Удалить выделенные зоны со сцены и из списка; уведомить об изменении."""
        for zone in [z for z in self._zones if z.isSelected()]:
            self._scene.removeItem(zone)
            self._zones.remove(zone)
        if self._on_zones_changed is not None:
            self._on_zones_changed()

    def clear_zones(self) -> None:
        """Удалить все зоны со сцены и из списка (внутренний сброс, без уведомления)."""
        for zone in self._zones:
            self._scene.removeItem(zone)
        self._zones.clear()

    def normalized_zones(self) -> list[tuple[float, float, float, float]]:
        """Доли [0..1] всех зон в порядке добавления (без фона — пусто)."""
        if not self.has_background():
            return []
        return [z.normalized(float(self._px_w), float(self._px_h)) for z in self._zones]

    # --- рисование резиновой рамкой -----------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """На пустом фоне ЛКМ начинает рисование; над зоной — событие отдаётся ей."""
        if (
            self.has_background()
            and event.button() == Qt.MouseButton.LeftButton
            and not isinstance(self.itemAt(event.position().toPoint()), ZoneItem)
        ):
            scene_pos = self.mapToScene(event.position().toPoint())
            self._draw_start = scene_pos
            zone = ZoneItem(QRectF(scene_pos, scene_pos), on_change=self._on_zones_changed)
            self._scene.addItem(zone)
            self._draft_zone = zone
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Тянуть временную зону от старт-точки к текущей (нормализуя прямоугольник)."""
        if self._draw_start is not None and self._draft_zone is not None:
            scene_pos = self.mapToScene(event.position().toPoint())
            self._draft_zone.set_scene_rect(QRectF(self._draw_start, scene_pos).normalized())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Завершить рисование: достаточный размер — оставить зону, иначе удалить временную."""
        if self._draw_start is not None and self._draft_zone is not None:
            zone = self._draft_zone
            self._draw_start = None
            self._draft_zone = None
            scene_rect = zone.mapRectToScene(zone.rect())
            if scene_rect.width() >= _MIN_SIZE and scene_rect.height() >= _MIN_SIZE:
                self._zones.append(zone)
                if self._on_zones_changed is not None:
                    self._on_zones_changed()
            else:
                self._scene.removeItem(zone)
            event.accept()
            return
        super().mouseReleaseEvent(event)
