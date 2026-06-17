"""Тесты доменной модели ``SchemeDocument`` (ADR-013): round-trip, hit-test, дефолт."""
from __future__ import annotations

from educase_core.domain.scheme import (
    Hotspot,
    HotspotShape,
    SchemeDocument,
    SchemeView,
    scheme_from_raw,
)
from educase_core.domain.stages import StageContacts, StageEnvironment


def _rich_scheme() -> SchemeDocument:
    """Схема с фоном, несколькими хотспотами и одним вложенным интерьерным видом."""
    return SchemeDocument(
        title="Схема казармы",
        root=SchemeView(
            background="scheme-1",
            caption="Общая схема объекта",
            hotspots=(
                Hotspot(
                    id="hs-beds",
                    shape=HotspotShape(x=0.1, y=0.1, w=0.2, h=0.2),
                    label="Спальное помещение",
                    reveal_text="Скученность коек.",
                ),
                Hotspot(
                    id="hs-kitchen",
                    shape=HotspotShape(x=0.5, y=0.5, w=0.3, h=0.3),
                    label="Пищеблок",
                    icon="zoom",
                    reveal_assets=("photo-1",),
                    child=SchemeView(
                        background="photo-kitchen",
                        caption="Интерьер пищеблока",
                        hotspots=(
                            Hotspot(
                                id="hs-fridge",
                                shape=HotspotShape(x=0.0, y=0.0, w=0.5, h=0.5),
                                label="Холодильная камера",
                                reveal_text="Нарушение температуры хранения.",
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )


def test_scheme_round_trip() -> None:
    """Полная схема (фон + хотспоты + вложенный child) переживает to_dict/from_dict."""
    scheme = _rich_scheme()
    assert SchemeDocument.from_dict(scheme.to_dict()) == scheme


def test_scheme_round_trip_preserves_nested_child() -> None:
    """Вложенный интерьерный вид и его хотспоты восстанавливаются дословно."""
    restored = SchemeDocument.from_dict(_rich_scheme().to_dict())
    child = restored.root.hotspots[1].child
    assert child is not None
    assert child.background == "photo-kitchen"
    assert child.hotspots[0].id == "hs-fridge"


def test_default_scheme_round_trip() -> None:
    """``SchemeDocument()`` по умолчанию сериализуется и десериализуется в равный объект."""
    scheme = SchemeDocument()
    restored = SchemeDocument.from_dict(scheme.to_dict())
    assert restored == scheme
    assert restored.root == SchemeView()
    assert restored.root.background is None
    assert restored.root.hotspots == ()


def test_hotspot_shape_contains_inside() -> None:
    """Точка внутри прямоугольника и на его границах — попадание."""
    shape = HotspotShape(x=0.2, y=0.2, w=0.4, h=0.4)
    assert shape.contains(0.4, 0.4) is True
    assert shape.contains(0.2, 0.2) is True  # левый верхний угол
    assert shape.contains(0.6, 0.6) is True  # правый нижний угол


def test_hotspot_shape_contains_outside() -> None:
    """Точка за пределами прямоугольника по любой стороне — не попадание."""
    shape = HotspotShape(x=0.2, y=0.2, w=0.4, h=0.4)
    assert shape.contains(0.1, 0.4) is False  # левее
    assert shape.contains(0.7, 0.4) is False  # правее
    assert shape.contains(0.4, 0.05) is False  # выше
    assert shape.contains(0.4, 0.9) is False  # ниже


def test_scheme_from_raw_none_is_none() -> None:
    """Отсутствие схемы (``None``) читается как ``None`` — этап без схемы."""
    assert scheme_from_raw(None) is None


def test_scheme_from_raw_legacy_string() -> None:
    """Старый формат: строка трактуется как id фонового изображения, без хотспотов."""
    scheme = scheme_from_raw("scheme-x")
    assert isinstance(scheme, SchemeDocument)
    assert scheme.root.background == "scheme-x"
    assert scheme.root.hotspots == ()


def test_scheme_from_raw_current_dict_matches_from_dict() -> None:
    """Текущий формат (Mapping) эквивалентен прямому ``SchemeDocument.from_dict``."""
    data = _rich_scheme().to_dict()
    assert scheme_from_raw(data) == SchemeDocument.from_dict(data)


def test_stage_contacts_reads_legacy_scheme_string() -> None:
    """``StageContacts.from_dict`` терпит старый строковый ``scheme`` (id фона)."""
    stage = StageContacts.from_dict({"scheme": "bg-id"})
    assert stage.scheme is not None
    assert stage.scheme.root.background == "bg-id"


def test_stage_environment_reads_legacy_scheme_string() -> None:
    """``StageEnvironment.from_dict`` терпит старый строковый ``scheme`` (id фона)."""
    stage = StageEnvironment.from_dict({"scheme": "bg-id"})
    assert stage.scheme is not None
    assert stage.scheme.root.background == "bg-id"
