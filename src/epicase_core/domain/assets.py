"""Реестр ассетов кейса. Все ссылки на ассеты в домене — по строковому id;
сам реестр (id → путь/тип) живёт только в ``Case.assets``."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from epicase_core.domain._serde import opt_str, req_str


class AssetKind(StrEnum):
    """Тип ассета в реестре кейса."""

    PHOTO = "photo"
    DOCUMENT = "document"
    SCHEME = "scheme"


@dataclass(frozen=True)
class AssetRef:
    """Запись реестра ассетов: связь строкового id с путём внутри архива и типом."""

    id: str
    path: str
    kind: AssetKind = AssetKind.PHOTO

    def to_dict(self) -> dict[str, object]:
        return {"id": self.id, "path": self.path, "kind": self.kind.value}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> AssetRef:
        return cls(
            id=req_str(data, "id"),
            path=req_str(data, "path"),
            kind=AssetKind(opt_str(data, "kind", AssetKind.PHOTO.value)),
        )
