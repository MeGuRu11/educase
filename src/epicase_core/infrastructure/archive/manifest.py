"""Конверт архива обмена: manifest.json (метаданные + контрольная сумма payload)."""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime

from epicase_core.infrastructure.archive import FORMAT_VERSION
from epicase_core.infrastructure.archive.errors import CorruptedArchiveError


def data_checksum(data_bytes: bytes) -> str:
    """Контрольная сумма payload в формате 'sha256:<hex>'."""
    return "sha256:" + hashlib.sha256(data_bytes).hexdigest()


@dataclass(frozen=True)
class Manifest:
    """Конверт архива. Не показывается пользователю — внутреннее представление."""

    kind: str
    checksum: str
    format_version: int = FORMAT_VERSION
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    meta: dict[str, object] = field(default_factory=dict)

    def to_json_bytes(self) -> bytes:
        payload = {
            "format_version": self.format_version,
            "kind": self.kind,
            "created_at": self.created_at,
            "checksum": self.checksum,
            "meta": self.meta,
        }
        return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")

    @classmethod
    def from_json_bytes(cls, raw: bytes) -> Manifest:
        try:
            obj = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CorruptedArchiveError("manifest.json не читается как JSON") from exc
        if not isinstance(obj, Mapping):
            raise CorruptedArchiveError("manifest.json: ожидался объект")
        try:
            return cls(
                kind=str(obj["kind"]),
                checksum=str(obj["checksum"]),
                format_version=int(obj["format_version"]),
                created_at=str(obj["created_at"]),
                meta=dict(obj.get("meta", {})),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise CorruptedArchiveError("manifest.json: отсутствуют или неверны поля") from exc
