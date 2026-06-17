"""Просмотрщик схемы объекта «фон + хотспоты» для Player (ADR-013).

Read-only вьюер ``SchemeDocument``: рисует фоновое изображение из байт ассета (тем же
способом, что ``AssetImageWidget``) и поверх него — кликабельные прямоугольные хотспоты
в долях [0..1]. Клик по хотспоту с ``child`` открывает вложенный интерьерный вид (стек
страниц с кнопкой «Назад»); хотспот с ``reveal_text``/``reveal_assets`` открывает диалог
раскрытия (текст + изображения через ``AssetImageWidget``). Нет фона/байт — плейсхолдер,
без падения (как в ``AssetImageWidget``). Зум/панорама/hover отложены на R3.

Только виджеты (без QML); QSS-стили по ``objectName`` (без inline-стилей в Python).
Перо/кисть графических элементов (``QGraphicsRectItem``) задаются через API сцены —
QSS на ``QGraphicsItem`` не распространяется, это единственный способ их отрисовать.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QMouseEvent, QPen, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from educase_core.domain.scheme import Hotspot, HotspotShape, SchemeDocument, SchemeView
from educase_player.ui.asset_image_widget import AssetImageWidget

_MAX_WIDTH = 600

# Акцентные цвета хотспота берём из общей темы (theme.qss): teal-обводка и лёгкая заливка.
_HOTSPOT_PEN = QColor("#0F766E")
_HOTSPOT_FILL = QColor(15, 118, 110, 48)
_HOTSPOT_TEXT = QColor("#1F2A33")


def _hotspot_rect(shape: HotspotShape, px_w: int, px_h: int) -> QRectF:
    """Геометрия хотспота в пикселях: доли [0..1] × размер pixmap."""
    return QRectF(shape.x * px_w, shape.y * px_h, shape.w * px_w, shape.h * px_h)


class _SchemeGraphicsView(QGraphicsView):
    """Сцена с фоном и хотспотами; клик переводит точку в доли и ищет попадание.

    Фиксированный масштаб 1:1 (зум/панорама — R3): размер вью равен размеру pixmap,
    скроллбары отключены. Hit-test переиспользует ``HotspotShape.contains`` в долях.
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
        self.setObjectName("schemeView")
        # Без рамки QFrame: viewport совпадает с pixmap 1:1, край сцены не обрезается
        # (визуальную рамку рисует QSS-border #schemeView). Скроллбары не нужны.
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSceneRect(0.0, 0.0, float(px_w), float(px_h))
        self.setFixedSize(px_w, px_h)

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        """Клик: перевести в доли pixmap и активировать первый накрытый хотспот."""
        if event is None:
            return
        scene_pos = self.mapToScene(event.position().toPoint())
        nx = scene_pos.x() / self._px_w if self._px_w else 0.0
        ny = scene_pos.y() / self._px_h if self._px_h else 0.0
        for hotspot in self._hotspots:
            if hotspot.shape.contains(nx, ny):
                self._on_hotspot(hotspot)
                return
        super().mousePressEvent(event)


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
        """Немодальный диалог раскрытия: текст и изображения хотспота (без блокировки).

        Предыдущий диалог раскрытия удаляется, чтобы они не накапливались за сессию
        (одновременно открыт максимум один).
        """
        if self._reveal is not None:
            self._reveal.deleteLater()
            self._reveal = None
        dialog = QDialog(self)
        dialog.setObjectName("schemeReveal")
        if hotspot.label:
            dialog.setWindowTitle(hotspot.label)
        dlg_layout = QVBoxLayout(dialog)
        if hotspot.reveal_text:
            text = QLabel(hotspot.reveal_text)
            text.setObjectName("schemeRevealText")
            text.setWordWrap(True)
            dlg_layout.addWidget(text)
        for asset_id in hotspot.reveal_assets:
            dlg_layout.addWidget(AssetImageWidget(asset_id, self._assets))
        close = QPushButton("Закрыть")
        close.clicked.connect(dialog.accept)
        dlg_layout.addWidget(close)
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
