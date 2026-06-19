"""Редактор зон схемы (Constructor, R2-B.2): холст + список карточек свойств зон.

Холст (``SchemeZoneCanvas``) рисует зоны, список карточек (``ZonePropsCard``) позволяет
задать подпись и вскрываемое содержимое для каждой зоны. Число карточек всегда совпадает с
числом зон на холсте — reconcile происходит при каждом изменении холста. Сборка в кортеж
``HotspotDraft`` — через ``to_hotspots()``.

Без интеграции в этапы (это contacts_editor / environment_editor, R2-B.2-шаг 4/5).
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from educase_constructor.ui.asset_picker import AssetListPicker
from educase_constructor.ui.icons import load_icon
from educase_constructor.ui.list_helpers import make_placeholder, refresh_placeholder, wrap_in_card
from educase_constructor.ui.scheme_zone_canvas import SchemeZoneCanvas
from educase_core.application.case_builder import AssetRef, HotspotDraft


class ZonePropsCard(QWidget):
    """Карточка свойств одной зоны: подпись, вскрываемый текст и прикреплённые фото."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.label_edit = QLineEdit(self)
        self.label_edit.setPlaceholderText("Подпись зоны, например: Спальное помещение")

        self.reveal_text_edit = QLineEdit(self)
        self.reveal_text_edit.setPlaceholderText("Текст, который откроется курсанту")

        self.assets_picker = AssetListPicker(self)

        form = QFormLayout(self)
        form.addRow("Подпись", self.label_edit)
        form.addRow("Вскрываемый текст", self.reveal_text_edit)
        form.addRow("Фото зоны", self.assets_picker)


class SchemeZoneEditor(QWidget):
    """Холст схемы + список карточек свойств зон + кнопки «Добавить»/«Удалить».

    Карточки синхронизируются с холстом автоматически при каждом изменении состава зон
    (``_on_canvas_changed``). Порядок карточки i = зоне i: оба растут/убывают с конца.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.canvas = SchemeZoneCanvas(on_zones_changed=self._on_canvas_changed, parent=self)
        self.cards: list[ZonePropsCard] = []
        self._card_boxes: list[QGroupBox] = []

        self._add_button = QPushButton("Добавить зону", self)
        self._add_button.setIcon(load_icon("add"))
        self._add_button.clicked.connect(self._add_zone_clicked)

        self._delete_button = QPushButton("Удалить зону", self)
        self._delete_button.setIcon(load_icon("delete"))
        self._delete_button.clicked.connect(self.canvas.remove_last)

        buttons = QHBoxLayout()
        buttons.addWidget(self._add_button)
        buttons.addWidget(self._delete_button)
        buttons.addStretch(1)

        self._empty_label = make_placeholder("Пока не добавлено ни одной зоны")

        self._cards_layout = QVBoxLayout()

        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)
        layout.addLayout(buttons)
        layout.addWidget(self._empty_label)
        layout.addLayout(self._cards_layout)

        refresh_placeholder(self._empty_label, is_empty=True)

    def _add_zone_clicked(self) -> None:
        """Добавить зону по центру холста (если фон загружен); on_zones_changed синхронизирует."""
        self.canvas.add_zone(0.4, 0.4, 0.2, 0.15)

    def _on_canvas_changed(self) -> None:
        """Привести число карточек к числу зон на холсте (reconcile по длине)."""
        n = len(self.canvas.normalized_zones())
        while len(self.cards) < n:
            card = ZonePropsCard(self)
            box = wrap_in_card(card, f"Зона {len(self.cards) + 1}")
            self.cards.append(card)
            self._card_boxes.append(box)
            self._cards_layout.addWidget(box)
        while len(self.cards) > n:
            self.cards.pop()
            box = self._card_boxes.pop()
            self._cards_layout.removeWidget(box)
            box.deleteLater()
        refresh_placeholder(self._empty_label, is_empty=len(self.cards) == 0)

    def set_background(self, ref: AssetRef | None) -> None:
        """Сменить фон холста; фон сбрасывает зоны, что синхронизирует карточки в 0."""
        self.canvas.set_background(ref)
        self._on_canvas_changed()

    def to_hotspots(self) -> tuple[HotspotDraft, ...]:
        """Собрать ``HotspotDraft`` для каждой зоны из долей холста и карточки свойств."""
        return tuple(
            HotspotDraft(
                x=x,
                y=y,
                w=w,
                h=h,
                label=card.label_edit.text(),
                reveal_text=card.reveal_text_edit.text(),
                reveal_assets=card.assets_picker.value(),
            )
            for (x, y, w, h), card in zip(
                self.canvas.normalized_zones(), self.cards, strict=True
            )
        )
