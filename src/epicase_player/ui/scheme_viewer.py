"""Просмотрщик схемы объекта «фон + хотспоты» для Player (ADR-013).

Read-only вьюер ``SchemeDocument``: рисует фоновое изображение из байт ассета (тем же
способом, что ``AssetImageWidget``) и поверх него — кликабельные прямоугольные хотспоты
в долях [0..1]. Клик по хотспоту с ``child`` открывает вложенный интерьерный вид (стек
страниц с кнопкой «Назад»); хотспот с ``reveal_text``/``reveal_assets`` открывает диалог
раскрытия (текст + изображения через ``AssetImageWidget``). Нет фона/байт — плейсхолдер,
без падения (как в ``AssetImageWidget``). Зум колёсиком (вокруг курсора) и панорама
перетаскиванием фона включены (R3); hover отложен.

Только виджеты (без QML); QSS-стили по ``objectName`` (без inline-стилей в Python).
Перо/кисть графических элементов (``QGraphicsRectItem``) задаются через API сцены —
QSS на ``QGraphicsItem`` не распространяется, это единственный способ их отрисовать.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping

from PySide6.QtCore import QPoint, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QMouseEvent, QPainter, QPen, QPixmap, QWheelEvent
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from epicase_core.domain.scheme import Hotspot, HotspotShape, SchemeDocument, SchemeView
from epicase_player.ui.asset_image_widget import AssetImageWidget

_MAX_WIDTH = 600

# Акцентные цвета хотспота берём из общей темы (theme.qss): teal-обводка и лёгкая заливка.
_HOTSPOT_PEN = QColor("#0F766E")
_HOTSPOT_FILL = QColor(15, 118, 110, 48)
_HOTSPOT_TEXT = QColor("#1F2A33")

# Зум вьюера схемы (R3): шаг колеса и пределы масштаба относительно базового 1:1.
_ZOOM_STEP = 1.15
_ZOOM_MIN = 1.0
_ZOOM_MAX = 6.0


def _hotspot_rect(shape: HotspotShape, px_w: int, px_h: int) -> QRectF:
    """Геометрия хотспота в пикселях: доли [0..1] × размер pixmap."""
    return QRectF(shape.x * px_w, shape.y * px_h, shape.w * px_w, shape.h * px_h)


class _SchemeGraphicsView(QGraphicsView):
    """Сцена с фоном и хотспотами; клик переводит точку в доли и ищет попадание.

    Базовый масштаб 1:1; вью имеет фиксированный размер pixmap как видимое окно (R3).
    Зум колёсиком вокруг курсора (``AnchorUnderMouse``) в пределах [``_ZOOM_MIN``..
    ``_ZOOM_MAX``); панорама — перетаскиванием фона левой кнопкой, скроллбары по мере
    необходимости. Hit-test переиспользует ``HotspotShape.contains`` в долях и остаётся
    корректным при любом масштабе/сдвиге: ``mapToScene`` учитывает текущую трансформацию.
    """

    def __init__(
        self,
        scene: QGraphicsScene,
        px_w: int,
        px_h: int,
        hotspots: tuple[Hotspot, ...],
        on_hotspot: Callable[[Hotspot], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(scene, parent)
        self._px_w = px_w
        self._px_h = px_h
        self._hotspots = hotspots
        self._on_hotspot = on_hotspot
        self._zoom: float = 1.0
        self._panning: bool = False
        self._pan_start: QPoint = QPoint()
        self.setObjectName("schemeView")
        # Без рамки QFrame: видимое окно равно pixmap 1:1, при зуме контент масштабируется
        # и скроллится внутри окна (визуальную рамку рисует QSS-border #schemeView).
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setSceneRect(0.0, 0.0, float(px_w), float(px_h))
        self.setFixedSize(px_w, px_h)

    def _apply_zoom(self, factor: float) -> None:
        """Применить относительный коэффициент масштаба с ограничением сверху и снизу."""
        new = min(_ZOOM_MAX, max(_ZOOM_MIN, self._zoom * factor))
        if new == self._zoom:
            return
        self.scale(new / self._zoom, new / self._zoom)
        self._zoom = new

    def zoom_in(self) -> None:
        """Шаг приближения (для кнопок/тестов)."""
        self._apply_zoom(_ZOOM_STEP)

    def zoom_out(self) -> None:
        """Шаг отдаления (для кнопок/тестов)."""
        self._apply_zoom(1.0 / _ZOOM_STEP)

    def reset_zoom(self) -> None:
        """Сбросить масштаб к базовому 1:1."""
        self.resetTransform()
        self._zoom = 1.0

    def current_zoom(self) -> float:
        """Текущий уровень масштаба (1.0 == базовый 1:1)."""
        return self._zoom

    def wheelEvent(self, event: QWheelEvent | None) -> None:
        """Колесо мыши: зум вокруг курсора (``AnchorUnderMouse``) в пределах масштаба."""
        if event is None:
            return
        factor = _ZOOM_STEP if event.angleDelta().y() > 0 else 1.0 / _ZOOM_STEP
        self._apply_zoom(factor)
        event.accept()

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        """Левая кнопка: сначала hit-test хотспота (как раньше), иначе старт панорамы фона."""
        if event is None:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.position().toPoint())
            nx = scene_pos.x() / self._px_w if self._px_w else 0.0
            ny = scene_pos.y() / self._px_h if self._px_h else 0.0
            for hotspot in self._hotspots:
                if hotspot.shape.contains(nx, ny):
                    self._on_hotspot(hotspot)
                    return
            self._panning = True
            self._pan_start = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:
        """При активной панораме перетаскивание сдвигает содержимое через скроллбары."""
        if event is None:
            return
        if self._panning:
            pos = event.position().toPoint()
            delta = pos - self._pan_start
            hbar = self.horizontalScrollBar()
            vbar = self.verticalScrollBar()
            hbar.setValue(hbar.value() - delta.x())
            vbar.setValue(vbar.value() - delta.y())
            self._pan_start = pos
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent | None) -> None:
        """Отпускание левой кнопки завершает панораму и возвращает обычный курсор."""
        if event is None:
            return
        if self._panning and event.button() == Qt.MouseButton.LeftButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)


class SchemeViewerWidget(QWidget):
    """Интерактивный просмотрщик ``SchemeDocument``: фон + хотспоты, вложенные виды.

    Корневой вид — страница 0 стека; вход в ``child`` добавляет страницу и показывает
    кнопку «Назад». Навигация по схеме не влияет на сбор ответа (ADR-008): осмотр —
    отдельный ``InspectionWidget``.
    """

    def __init__(
        self,
        scheme: SchemeDocument,
        assets: Mapping[str, bytes] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._assets: Mapping[str, bytes] = assets if assets is not None else {}
        self._has_background = False
        self._reveal: QDialog | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if scheme.title:
            title = QLabel(scheme.title)
            title.setObjectName("schemeTitle")
            title.setWordWrap(True)
            layout.addWidget(title)

        self._back = QPushButton("← Назад к общей схеме")
        self._back.setObjectName("schemeBack")
        self._back.clicked.connect(self._go_back)
        layout.addWidget(self._back)

        self._stack = QStackedWidget()
        layout.addWidget(self._stack)

        self._push_view(scheme.root)

    def has_background(self) -> bool:
        """``True``, если хотя бы один показанный вид успешно загрузил фон (для тестов)."""
        return self._has_background

    def _push_view(self, view: SchemeView) -> None:
        """Построить страницу для вида, показать её и обновить кнопку «Назад»."""
        page = self._build_page(view)
        self._stack.addWidget(page)
        self._stack.setCurrentWidget(page)
        self._update_back()

    def _go_back(self) -> None:
        """Снять верхнюю страницу стека и вернуться к предыдущему виду."""
        idx = self._stack.currentIndex()
        if idx > 0:
            page = self._stack.widget(idx)
            self._stack.setCurrentIndex(idx - 1)
            if page is not None:
                self._stack.removeWidget(page)
                page.deleteLater()
        self._update_back()

    def _update_back(self) -> None:
        self._back.setVisible(self._stack.count() > 1)

    def _build_page(self, view: SchemeView) -> QWidget:
        """Страница одного уровня: подпись + сцена с фоном и хотспотами или плейсхолдер."""
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)

        if view.caption:
            caption = QLabel(view.caption)
            caption.setObjectName("schemeCaption")
            caption.setWordWrap(True)
            page_layout.addWidget(caption)

        pixmap = self._load_pixmap(view.background)
        if pixmap is None:
            placeholder = QLabel("Схема недоступна")
            placeholder.setObjectName("mutedHint")
            placeholder.setEnabled(False)
            page_layout.addWidget(placeholder)
            return page

        self._has_background = True
        scene = QGraphicsScene(page)
        scene.addPixmap(pixmap)
        for hotspot in view.hotspots:
            self._add_hotspot(scene, hotspot, pixmap.width(), pixmap.height())
        gview = _SchemeGraphicsView(
            scene,
            pixmap.width(),
            pixmap.height(),
            view.hotspots,
            self._activate_hotspot,
        )
        page_layout.addWidget(gview)
        return page

    def _add_hotspot(
        self, scene: QGraphicsScene, hotspot: Hotspot, px_w: int, px_h: int
    ) -> None:
        """Нарисовать зону хотспота (рамка + лёгкая заливка) и подпись-тултип."""
        rect_item = QGraphicsRectItem(_hotspot_rect(hotspot.shape, px_w, px_h))
        rect_item.setPen(QPen(_HOTSPOT_PEN, 2))
        rect_item.setBrush(QBrush(_HOTSPOT_FILL))
        rect_item.setCursor(Qt.CursorShape.PointingHandCursor)
        tooltip = " ".join(part for part in (hotspot.icon, hotspot.label) if part)
        if tooltip:
            rect_item.setToolTip(tooltip)
        scene.addItem(rect_item)
        if hotspot.label:
            text_item = QGraphicsSimpleTextItem(hotspot.label, rect_item)
            text_item.setBrush(QBrush(_HOTSPOT_TEXT))
            text_item.setPos(hotspot.shape.x * px_w + 2.0, hotspot.shape.y * px_h + 2.0)

    def _activate_hotspot(self, hotspot: Hotspot) -> None:
        """Клик по зоне: открыть вложенный вид либо панель раскрытия (текст/ассеты)."""
        if hotspot.child is not None:
            self._push_view(hotspot.child)
        elif hotspot.reveal_text or hotspot.reveal_assets:
            self._open_reveal(hotspot)

    def _open_reveal(self, hotspot: Hotspot) -> None:
        """Немодальный диалог раскрытия: заголовок, карточка с текстом/ассетами, кнопка.

        Предыдущий диалог раскрытия удаляется, чтобы они не накапливались за сессию
        (одновременно открыт максимум один).
        """
        if self._reveal is not None:
            self._reveal.deleteLater()
            self._reveal = None

        dialog = QDialog(self)
        dialog.setObjectName("schemeReveal")
        dialog.setMinimumWidth(360)
        if hotspot.label:
            dialog.setWindowTitle(hotspot.label)

        outer_layout = QVBoxLayout(dialog)
        outer_layout.setContentsMargins(16, 16, 16, 16)
        outer_layout.setSpacing(10)

        if hotspot.label:
            title_label = QLabel(hotspot.label)
            title_label.setObjectName("schemeRevealTitle")
            title_label.setWordWrap(True)
            outer_layout.addWidget(title_label)

        card = QFrame()
        card.setObjectName("schemeRevealCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(8)

        if hotspot.reveal_text:
            text = QLabel(hotspot.reveal_text)
            text.setObjectName("schemeRevealText")
            text.setWordWrap(True)
            card_layout.addWidget(text)

        for asset_id in hotspot.reveal_assets:
            card_layout.addWidget(AssetImageWidget(asset_id, self._assets))

        outer_layout.addWidget(card)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close = QPushButton("Закрыть")
        close.setObjectName("schemeRevealClose")
        close.clicked.connect(dialog.accept)
        btn_row.addWidget(close)
        outer_layout.addLayout(btn_row)

        self._reveal = dialog
        dialog.open()

    def _load_pixmap(self, background: str | None) -> QPixmap | None:
        """Загрузить фон из байт ассета (как ``AssetImageWidget``); ``None`` при недоступности."""
        if not background:
            return None
        data = self._assets.get(background)
        if data is None:
            return None
        pixmap = QPixmap()
        if not pixmap.loadFromData(data):
            return None
        if pixmap.width() > _MAX_WIDTH:
            pixmap = pixmap.scaledToWidth(
                _MAX_WIDTH, Qt.TransformationMode.SmoothTransformation
            )
        return pixmap
