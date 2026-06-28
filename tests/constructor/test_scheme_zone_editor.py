"""Тесты UI-обёртки редактора зон схемы (Constructor, R2-B.2).

Реальные виджеты (pytest-qt): карточки синхронизируются с холстом, to_hotspots возвращает
корректные HotspotDraft с геометрией и свойствами. R2.1-B: вложенный интерьерный вид.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QColor, QPixmap
from pytestqt.qtbot import QtBot

from epicase_constructor.ui.scheme_zone_editor import SchemeZoneEditor, ZonePropsCard
from epicase_core.application.case_builder import AssetRef, SchemeViewDraft


def _make_ref(tmp_path: Path, name: str = "bg.png") -> AssetRef:
    """Сохранить PNG 80×60 на диск и вернуть AssetRef."""
    pixmap = QPixmap(80, 60)
    pixmap.fill(QColor("white"))
    path = tmp_path / name
    assert pixmap.save(str(path))
    return AssetRef(asset_id=name, source_path=str(path), display_name=name)


def test_add_zone_creates_card(qtbot: QtBot, tmp_path: Path) -> None:
    """После выбора фона «Добавить зону» создаёт одну карточку."""
    editor = SchemeZoneEditor()
    qtbot.addWidget(editor)
    editor.set_background(_make_ref(tmp_path))

    assert len(editor.cards) == 0
    editor._add_button.click()
    assert len(editor.cards) == 1


def test_card_fields_round_trip_to_hotspots(qtbot: QtBot, tmp_path: Path) -> None:
    """Заполненные поля карточки → to_hotspots()[0] содержит label, reveal_text, assets."""
    editor = SchemeZoneEditor()
    qtbot.addWidget(editor)
    editor.set_background(_make_ref(tmp_path))
    editor._add_button.click()

    card = editor.cards[0]
    card.label_edit.setText("Спальня")
    card.reveal_text_edit.setText("Место проживания")
    photo = tmp_path / "zone.png"
    photo.write_bytes(b"PNG")
    card.assets_picker.add_file(str(photo))

    hotspots = editor.to_hotspots()
    assert len(hotspots) == 1
    h = hotspots[0]
    assert h.label == "Спальня"
    assert h.reveal_text == "Место проживания"
    assert len(h.reveal_assets) == 1
    assert h.reveal_assets[0].display_name == "zone.png"
    # Геометрия должна быть в [0..1]
    assert 0.0 <= h.x <= 1.0
    assert 0.0 <= h.y <= 1.0
    assert h.w > 0.0
    assert h.h > 0.0


def test_two_zones_two_cards(qtbot: QtBot, tmp_path: Path) -> None:
    """Добавление двух зон → две карточки, to_hotspots() длины 2."""
    editor = SchemeZoneEditor()
    qtbot.addWidget(editor)
    editor.set_background(_make_ref(tmp_path))
    editor._add_button.click()
    editor._add_button.click()
    assert len(editor.cards) == 2
    assert len(editor.to_hotspots()) == 2


def test_delete_last_zone_removes_card(qtbot: QtBot, tmp_path: Path) -> None:
    """«Удалить зону» убирает последнюю зону и её карточку."""
    editor = SchemeZoneEditor()
    qtbot.addWidget(editor)
    editor.set_background(_make_ref(tmp_path))
    editor._add_button.click()
    editor._add_button.click()
    assert len(editor.cards) == 2

    editor._delete_button.click()
    assert len(editor.cards) == 1
    assert len(editor.to_hotspots()) == 1


def test_set_background_none_clears_cards(qtbot: QtBot, tmp_path: Path) -> None:
    """set_background(None) сбрасывает зоны и карточки; to_hotspots() пуст."""
    editor = SchemeZoneEditor()
    qtbot.addWidget(editor)
    editor.set_background(_make_ref(tmp_path))
    editor._add_button.click()
    assert len(editor.cards) == 1

    editor.set_background(None)
    assert len(editor.cards) == 0
    assert editor.to_hotspots() == ()
    assert not editor._empty_label.isHidden()


def test_to_hotspots_empty_without_background(qtbot: QtBot) -> None:
    """Без фона холст не хранит зон; to_hotspots() возвращает пустой кортеж."""
    editor = SchemeZoneEditor()
    qtbot.addWidget(editor)
    assert editor.to_hotspots() == ()
    assert len(editor.cards) == 0


def test_buttons_disabled_without_background(qtbot: QtBot) -> None:
    """Без фона обе кнопки недоступны."""
    editor = SchemeZoneEditor()
    qtbot.addWidget(editor)
    assert not editor._add_button.isEnabled()
    assert not editor._delete_button.isEnabled()


def test_add_enabled_after_background_delete_disabled_when_no_zones(
    qtbot: QtBot, tmp_path: Path
) -> None:
    """После выбора фона «Добавить» доступна; «Удалить» ещё недоступна (зон нет)."""
    editor = SchemeZoneEditor()
    qtbot.addWidget(editor)
    editor.set_background(_make_ref(tmp_path))
    assert editor._add_button.isEnabled()
    assert not editor._delete_button.isEnabled()


def test_delete_enabled_after_add_zone(qtbot: QtBot, tmp_path: Path) -> None:
    """После добавления зоны «Удалить» становится доступной."""
    editor = SchemeZoneEditor()
    qtbot.addWidget(editor)
    editor.set_background(_make_ref(tmp_path))
    editor._add_button.click()
    assert editor._delete_button.isEnabled()


def test_delete_disabled_after_removing_last_zone(qtbot: QtBot, tmp_path: Path) -> None:
    """После удаления последней зоны «Удалить» снова недоступна."""
    editor = SchemeZoneEditor()
    qtbot.addWidget(editor)
    editor.set_background(_make_ref(tmp_path))
    editor._add_button.click()
    editor._delete_button.click()
    assert len(editor.cards) == 0
    assert not editor._delete_button.isEnabled()


def test_both_disabled_after_set_background_none(qtbot: QtBot, tmp_path: Path) -> None:
    """set_background(None) снова отключает обе кнопки."""
    editor = SchemeZoneEditor()
    qtbot.addWidget(editor)
    editor.set_background(_make_ref(tmp_path))
    editor._add_button.click()
    editor.set_background(None)
    assert not editor._add_button.isEnabled()
    assert not editor._delete_button.isEnabled()


def test_hotspot_geometry_in_unit_range(qtbot: QtBot, tmp_path: Path) -> None:
    """Геометрия всех добавленных зон → доли x,y,w,h строго в [0..1]."""
    editor = SchemeZoneEditor()
    qtbot.addWidget(editor)
    editor.set_background(_make_ref(tmp_path))
    editor._add_button.click()
    editor._add_button.click()

    for h in editor.to_hotspots():
        assert 0.0 <= h.x <= 1.0, f"x={h.x}"
        assert 0.0 <= h.y <= 1.0, f"y={h.y}"
        assert 0.0 < h.w <= 1.0, f"w={h.w}"
        assert 0.0 < h.h <= 1.0, f"h={h.h}"
        assert h.x + h.w <= 1.0 + 1e-6, f"x+w={h.x + h.w}"
        assert h.y + h.h <= 1.0 + 1e-6, f"y+h={h.y + h.h}"


# ---------------------------------------------------------------------------
# R2.1-B: вложенный интерьерный вид
# ---------------------------------------------------------------------------


def test_zone_props_card_allow_nested_true_has_nested_attrs(qtbot: QtBot) -> None:
    """ZonePropsCard(allow_nested=True) создаёт nested_scheme_picker и nested_editor."""
    card = ZonePropsCard(allow_nested=True)
    qtbot.addWidget(card)
    assert hasattr(card, "nested_scheme_picker")
    assert hasattr(card, "nested_editor")


def test_zone_props_card_allow_nested_true_to_child_none_without_bg(qtbot: QtBot) -> None:
    """to_child() == None, если интерьерный фон не выбран."""
    card = ZonePropsCard(allow_nested=True)
    qtbot.addWidget(card)
    assert card.to_child() is None


def test_zone_props_card_allow_nested_true_to_child_with_bg(
    qtbot: QtBot, tmp_path: Path
) -> None:
    """to_child() возвращает SchemeViewDraft с фоном и зонами после заполнения."""
    card = ZonePropsCard(allow_nested=True)
    qtbot.addWidget(card)

    interior_ref = _make_ref(tmp_path, "interior.png")
    card.nested_scheme_picker.set_file(interior_ref.source_path)

    card.nested_editor.canvas.add_zone(0.4, 0.4, 0.2, 0.15)
    nested_card = card.nested_editor.cards[0]
    nested_card.label_edit.setText("Кровать")
    nested_card.reveal_text_edit.setText("Место сна")

    child = card.to_child()
    assert child is not None
    assert child.background is not None
    assert len(child.hotspots) == 1
    assert child.hotspots[0].label == "Кровать"
    assert child.hotspots[0].reveal_text == "Место сна"


def test_zone_props_card_allow_nested_false_no_nesting(qtbot: QtBot) -> None:
    """ZonePropsCard(allow_nested=False): to_child() == None; нет атрибута nested_editor."""
    card = ZonePropsCard(allow_nested=False)
    qtbot.addWidget(card)
    assert card.to_child() is None
    assert not hasattr(card, "nested_editor")


def test_top_level_editor_hotspot_child_with_nested(qtbot: QtBot, tmp_path: Path) -> None:
    """SchemeZoneEditor (верхний, allow_nested=True): to_hotspots()[0].child — SchemeViewDraft."""
    editor = SchemeZoneEditor()  # allow_nested=True по умолчанию
    qtbot.addWidget(editor)
    editor.set_background(_make_ref(tmp_path))
    editor._add_button.click()

    card = editor.cards[0]
    interior_ref = _make_ref(tmp_path, "interior.png")
    card.nested_scheme_picker.set_file(interior_ref.source_path)
    card.nested_editor.canvas.add_zone(0.4, 0.4, 0.2, 0.15)

    hotspots = editor.to_hotspots()
    assert len(hotspots) == 1
    assert isinstance(hotspots[0].child, SchemeViewDraft)


def test_top_level_editor_hotspot_child_none_without_interior(
    qtbot: QtBot, tmp_path: Path
) -> None:
    """Зона без настроенного интерьера → to_hotspots()[0].child is None."""
    editor = SchemeZoneEditor()
    qtbot.addWidget(editor)
    editor.set_background(_make_ref(tmp_path))
    editor._add_button.click()

    assert editor.to_hotspots()[0].child is None


def test_nested_editor_cards_have_no_further_nesting(qtbot: QtBot, tmp_path: Path) -> None:
    """Карточки вложенного SchemeZoneEditor имеют allow_nested=False."""
    editor = SchemeZoneEditor()
    qtbot.addWidget(editor)
    editor.set_background(_make_ref(tmp_path))
    editor._add_button.click()

    card = editor.cards[0]
    interior_ref = _make_ref(tmp_path, "interior.png")
    card.nested_scheme_picker.set_file(interior_ref.source_path)
    card.nested_editor.canvas.add_zone(0.4, 0.4, 0.2, 0.15)

    nested_card = card.nested_editor.cards[0]
    assert nested_card.to_child() is None
    assert not hasattr(nested_card, "nested_editor")
