"""Кодеки ZIP-архивов обмена EpiCase (.epicase / .epiresult).

Документная модель (ADR-009): архив — единственная персистентность. Никакого сетевого I/O,
только локальная файловая система. JSON не показывается пользователю.

Раскладка архива::

    <имя>.epicase|.epiresult  (ZIP)
    ├── manifest.json   — конверт (метаданные + контрольная сумма data.json)
    ├── data.json       — payload (внутреннее представление)
    └── assets/         — бинарные ассеты (фото, документы)
"""
from __future__ import annotations

import json
import zipfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from epicase_core.infrastructure.archive import (
    ASSETS_DIR,
    DATA_NAME,
    EPICASE_EXT,
    EPIRESULT_EXT,
    FORMAT_VERSION,
    MANIFEST_NAME,
)
from epicase_core.infrastructure.archive.errors import (
    ArchiveError,
    CorruptedArchiveError,
    IncompatibleVersionError,
)
from epicase_core.infrastructure.archive.manifest import Manifest, data_checksum

KIND_EPICASE = "epicase"
KIND_EPIRESULT = "epiresult"


@dataclass(frozen=True)
class ArchiveBundle:
    """Результат чтения архива: конверт + payload + ассеты (имя → байты)."""

    manifest: Manifest
    payload: dict[str, object]
    assets: dict[str, bytes]


def _ensure_suffix(dst: Path, ext: str) -> Path:
    return dst if dst.suffix == ext else dst.with_suffix(ext)


def _write_archive(
    kind: str,
    ext: str,
    payload: Mapping[str, object],
    dst: Path,
    assets: Mapping[str, bytes] | None,
    meta: Mapping[str, object] | None,
) -> Path:
    dst = _ensure_suffix(dst, ext)
    data_bytes = json.dumps(dict(payload), ensure_ascii=False, indent=2).encode("utf-8")
    manifest = Manifest(kind=kind, checksum=data_checksum(data_bytes), meta=dict(meta or {}))

    dst.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dst, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(MANIFEST_NAME, manifest.to_json_bytes())
        zf.writestr(DATA_NAME, data_bytes)
        for name, blob in (assets or {}).items():
            zf.writestr(f"{ASSETS_DIR}/{name}", blob)
    logger.info("Записан архив {} ({} ассетов)", dst.name, len(assets or {}))
    return dst


def _read_archive(expected_kind: str, src: Path) -> ArchiveBundle:
    if not zipfile.is_zipfile(src):
        raise CorruptedArchiveError(f"Не ZIP-архив: {src}")

    with zipfile.ZipFile(src, "r") as zf:
        names = set(zf.namelist())
        if MANIFEST_NAME not in names or DATA_NAME not in names:
            raise CorruptedArchiveError("В архиве нет manifest.json или data.json")

        manifest = Manifest.from_json_bytes(zf.read(MANIFEST_NAME))
        if manifest.format_version > FORMAT_VERSION:
            raise IncompatibleVersionError(
                f"Версия формата {manifest.format_version} новее поддерживаемой {FORMAT_VERSION}"
            )
        if manifest.kind != expected_kind:
            raise ArchiveError(
                f"Ожидался архив '{expected_kind}', в манифесте '{manifest.kind}'"
            )

        data_bytes = zf.read(DATA_NAME)
        if data_checksum(data_bytes) != manifest.checksum:
            raise CorruptedArchiveError("Контрольная сумма data.json не совпадает")

        try:
            payload_obj = json.loads(data_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CorruptedArchiveError("data.json не читается как JSON") from exc
        if not isinstance(payload_obj, dict):
            raise CorruptedArchiveError("data.json: ожидался объект")

        prefix = f"{ASSETS_DIR}/"
        assets = {
            n[len(prefix):]: zf.read(n)
            for n in names
            if n.startswith(prefix) and not n.endswith("/")
        }

    logger.info("Прочитан архив {} ({} ассетов)", src.name, len(assets))
    return ArchiveBundle(manifest=manifest, payload=payload_obj, assets=assets)


def write_epicase(
    payload: Mapping[str, object],
    dst: Path,
    *,
    assets: Mapping[str, bytes] | None = None,
    meta: Mapping[str, object] | None = None,
) -> Path:
    """Упаковать кейс в .epicase (ZIP с manifest.json + data.json + ассеты)."""
    return _write_archive(KIND_EPICASE, EPICASE_EXT, payload, dst, assets, meta)


def read_epicase(src: Path) -> ArchiveBundle:
    """Прочитать и провалидировать .epicase."""
    return _read_archive(KIND_EPICASE, src)


def write_epiresult(
    payload: Mapping[str, object],
    dst: Path,
    *,
    assets: Mapping[str, bytes] | None = None,
    meta: Mapping[str, object] | None = None,
) -> Path:
    """Упаковать результат прохождения в .epiresult."""
    return _write_archive(KIND_EPIRESULT, EPIRESULT_EXT, payload, dst, assets, meta)


def read_epiresult(src: Path) -> ArchiveBundle:
    """Прочитать и провалидировать .epiresult."""
    return _read_archive(KIND_EPIRESULT, src)


__all__ = [
    "ArchiveBundle",
    "read_epicase",
    "read_epiresult",
    "write_epicase",
    "write_epiresult",
]
