"""Схема объекта «фон + хотспоты» (ADR-013, отменяет ADR-012).

Преподаватель даёт общую схему объекта изображением (ассет) и расставляет поверх
прямоугольные хотспоты в нормализованных координатах [0..1] (независимость от размера
картинки и зума). Хотспот раскрывает текст/ассеты или открывает вложенный интерьерный вид.
Оценивание осмотра здесь НЕ моделируется — оно живёт в ``InspectionCheck`` (search.py).
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from educase_core.domain._serde import (
    as_map,
    opt_str,
    opt_str_or_none,
    req_float,
    req_str,
    seq,
    str_tuple,
)


@dataclass(frozen=True)
class HotspotShape:
    """Прямоугольная зона на фоне в долях [0..1]: левый верх (x, y) и размеры (w, h)."""

    x: float
    y: float
    w: float
    h: float

    def contains(self, px: float, py: float) -> bool:
        """Лежит ли точка (в долях) внутри прямоугольника."""
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h

    def to_dict(self) -> dict[str, object]:
        return {"x": self.x, "y": self.y, "w": self.w, "h": self.h}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> HotspotShape:
        return cls(
            x=req_float(data, "x"),
            y=req_float(data, "y"),
            w=req_float(data, "w"),
            h=req_float(data, "h"),
        )


@dataclass(frozen=True)
class Hotspot:
    """Кликабельная зона: геометрия + раскрытие (текст/ассеты) и/или вложенный вид.

    ``reveal_text``/``reveal_assets`` показываются при клике (как ``SearchEntry``).
    ``child`` — вложенный интерьерный вид (например, фото объекта со своими хотспотами);
    ``None``, если хотспот только раскрывает информацию. ``label`` — подпись/тултип
    («Казарма», «Пищеблок»), ``icon`` — имя иконки действия (опционально).
    """

    id: str
    shape: HotspotShape
    label: str = ""
    icon: str = ""
    reveal_text: str = ""
    reveal_assets: tuple[str, ...] = ()
    child: SchemeView | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "shape": self.shape.to_dict(),
            "label": self.label,
            "icon": self.icon,
            "reveal_text": self.reveal_text,
            "reveal_assets": list(self.reveal_assets),
            "child": self.child.to_dict() if self.child is not None else None,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Hotspot:
        raw_child = data.get("child")
        return cls(
            id=req_str(data, "id"),
            shape=HotspotShape.from_dict(as_map(data["shape"])),
            label=opt_str(data, "label"),
            icon=opt_str(data, "icon"),
            reveal_text=opt_str(data, "reveal_text"),
            reveal_assets=str_tuple(data, "reveal_assets"),
            child=SchemeView.from_dict(as_map(raw_child)) if raw_child is not None else None,
        )


@dataclass(frozen=True)
class SchemeView:
    """Один уровень схемы: фоновое изображение (id ассета) + хотспоты поверх него."""

    background: str | None = None
    caption: str = ""
    hotspots: tuple[Hotspot, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "background": self.background,
            "caption": self.caption,
            "hotspots": [h.to_dict() for h in self.hotspots],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> SchemeView:
        return cls(
            background=opt_str_or_none(data, "background"),
            caption=opt_str(data, "caption"),
            hotspots=tuple(Hotspot.from_dict(as_map(item)) for item in seq(data, "hotspots")),
        )


@dataclass(frozen=True)
class SchemeDocument:
    """Схема объекта целиком: заголовок + корневой вид (общая схема объекта)."""

    title: str = ""
    root: SchemeView = SchemeView()

    def to_dict(self) -> dict[str, object]:
        return {"title": self.title, "root": self.root.to_dict()}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> SchemeDocument:
        raw_root = data.get("root")
        return cls(
            title=opt_str(data, "title"),
            root=SchemeView.from_dict(as_map(raw_root)) if raw_root is not None else SchemeView(),
        )


def scheme_from_raw(raw: object) -> SchemeDocument | None:
    """Терпимое чтение поля ``scheme`` из архива (совместимость форматов).

    - ``None`` → ``None`` (этап без схемы);
    - ``str``  → старый формат: строка трактуется как id фонового изображения;
    - ``Mapping`` → текущий формат ADR-013 (полный ``SchemeDocument``).
    """
    if raw is None:
        return None
    if isinstance(raw, str):
        return SchemeDocument(root=SchemeView(background=raw))
    return SchemeDocument.from_dict(as_map(raw))


__all__ = [
    "Hotspot",
    "HotspotShape",
    "SchemeDocument",
    "SchemeView",
    "scheme_from_raw",
]
