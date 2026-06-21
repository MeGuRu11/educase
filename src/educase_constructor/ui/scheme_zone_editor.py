"""Редактор зон схемы (Constructor, R2-B.2): холст + список карточек свойств зон.

Холст (``SchemeZoneCanvas``) рисует зоны, список карточек (``ZonePropsCard``) позволяет
задать подпись и вскрываемое содержимое для каждой зоны. Число карточек всегда совпадает с
числом зон на холсте — reconcile происходит при каждом изменении холста. Сборка в кортеж
``HotspotDraft`` — через ``to_hotspots()``.

Без интеграции в этапы (это contacts_editor / environment_editor, R2-B.2-шаг 4/5).
"""
from __future__ import annotations

from loguru import logger
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from educase_constructor.ui.asset_picker import AssetListPicker, AssetPicker
from educase_constructor.ui.icons import load_icon
from educase_constructor.ui.list_helpers import make_placeholder, refresh_placeholder, wrap_in_card
from educase_constructor.ui.scheme_zone_canvas import SchemeZoneCanvas
from educase_core.application.case_builder import AssetRef, HotspotDraft, SchemeViewDraft


class ZonePropsCard(QWidget):
    """Карточка свойств одной зоны: подпись, вскрываемый текст и прикреплённые фото.

    При ``allow_nested=True`` (верхний уровень) дополнительно показывает секцию
    вложенного интерьерного вида: выбор фона + вложенный ``SchemeZoneEditor`` без
    дальнейшей вложенности (``allow_nested=False``).
    """

    def __init__(self, parent: QWidget | None = None, allow_nested: bool = False) -> None:
        super().__init__(parent)
        self._allow_nested = allow_nested

        self.label_edit = QLineEdit(self)
        self.label_edit.setPlaceholderText("Подпись зоны, например: Спальное помещение")

        self.reveal_text_edit = QLineEdit(self)
        self.reveal_text_edit.setPlaceholderText("Текст, который откроется курсанту")

        self.assets_picker = AssetListPicker(self)

        form = QFormLayout()
        form.addRow("Подпись", self.label_edit)
        form.addRow("Вскрываемый текст", self.reveal_text_edit)
        form.addRow("Фото зоны", self.assets_picker)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form)

        if allow_nested:
            nested_box = QGroupBox("Вложенный вид (интерьер, необязательно)", self)
            nested_layout = QVBoxLayout(nested_box)

            self.nested_scheme_picker = AssetPicker(nested_box)
            self.nested_editor = SchemeZoneEditor(nested_box, allow_nested=False)
            self.nested_scheme_picker.changed.connect(
                lambda: self.nested_editor.set_background(self.nested_scheme_picker.value())
            )

            nested_form = QFormLayout()
            nested_form.addRow("Фон интерьера", self.nested_scheme_picker)
            nested_layout.addLayout(nested_form)
            nested_layout.addWidget(self.nested_editor)

            main_layout.addWidget(nested_box)

    def load(self, draft: HotspotDraft) -> None:
        """Заполнить карточку значениями ``HotspotDraft`` (открытие кейса на правку).

        При ``allow_nested`` и наличии вложенного вида (``child``): фон интерьера через
        ``set_ref``/``clear`` (сигнал ``changed`` поставит фон вложенному холсту), затем
        рекурсивно зоны вложенного редактора через ``load_hotspots`` (ПОСЛЕ установки фона).
        """
        self.label_edit.setText(draft.label)
        self.reveal_text_edit.setText(draft.reveal_text)
        self.assets_picker.load(draft.reveal_assets)
        if self._allow_nested and draft.child is not None:
            if draft.child.background is not None:
                self.nested_scheme_picker.set_ref(draft.child.background)
            else:
                self.nested_scheme_picker.clear()
            self.nested_editor.load_hotspots(draft.child.hotspots)

    def to_child(self) -> SchemeViewDraft | None:
        """Собрать вложенный ``SchemeViewDraft`` или ``None`` без интерьерного фона."""
        if not self._allow_nested:
            return None
        ref = self.nested_scheme_picker.value()
        if ref is None:
            return None
        return SchemeViewDraft(background=ref, hotspots=self.nested_editor.to_hotspots())


class SchemeZoneEditor(QWidget):
    """Холст схемы + список карточек свойств зон + кнопки «Добавить»/«Удалить».

    Карточки синхронизируются с холстом автоматически при каждом изменении состава зон
    (``_on_canvas_changed``). Порядок карточки i = зоне i: оба растут/убывают с конца.

    ``allow_nested=True`` (по умолчанию) — карточки верхнего уровня, имеют секцию
    интерьерного вида. ``allow_nested=False`` — карточки только reveal (без вложенности).
    """

    def __init__(self, parent: QWidget | None = None, allow_nested: bool = True) -> None:
        super().__init__(parent)
        self._allow_nested = allow_nested

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
        self._update_buttons()

    def _update_buttons(self) -> None:
        """Синхронизировать доступность кнопок с состоянием холста."""
        has_bg = self.canvas.has_background()
        self._add_button.setEnabled(has_bg)
        self._delete_button.setEnabled(has_bg and len(self.cards) > 0)

    def _add_zone_clicked(self) -> None:
        """Добавить зону по центру холста (если фон загружен); on_zones_changed синхронизирует."""
        self.canvas.add_zone(0.4, 0.4, 0.2, 0.15)

    def _on_canvas_changed(self) -> None:
        """Привести число карточек к числу зон на холсте (reconcile по длине)."""
        n = len(self.canvas.normalized_zones())
        while len(self.cards) < n:
            card = ZonePropsCard(allow_nested=self._allow_nested, parent=self)
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
        self._update_buttons()

    def set_background(self, ref: AssetRef | None) -> None:
        """Сменить фон холста; фон сбрасывает зоны, что синхронизирует карточки в 0."""
        self.canvas.set_background(ref)
        self._on_canvas_changed()
        self._update_buttons()

    def load_hotspots(self, hotspots: tuple[HotspotDraft, ...]) -> None:
        """Восстановить зоны на холсте и карточки свойств из драфтов (открытие кейса на правку).

        Фон должен быть уже установлен (``set_background``) — без фона ``add_zone`` вернёт
        ``None`` и зоны не восстановятся. Холст и карточки сбрасываются в 0, затем каждая зона
        добавляется по долям (каждый успешный ``add_zone`` реконсилит +1 карточку), и карточки
        заполняются по порядку. Пояс на случай битого/невостановленного фона: соединяем только
        фактически созданные зоны (``strict=False``) и предупреждаем при рассинхроне — вместо
        падения; зоны при этом не теряются молча (см. ``logger.warning``).
        """
        self.canvas.clear_zones()
        self._on_canvas_changed()
        for draft in hotspots:
            self.canvas.add_zone(draft.x, draft.y, draft.w, draft.h)
        if len(self.cards) != len(hotspots):
            logger.warning(
                "Восстановлено {} зон схемы из {} — фон не загрузился, часть зон пропущена",
                len(self.cards),
                len(hotspots),
            )
        for card, draft in zip(self.cards, hotspots, strict=False):
            card.load(draft)

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
                child=card.to_child(),
            )
            for (x, y, w, h), card in zip(
                self.canvas.normalized_zones(), self.cards, strict=True
            )
        )
