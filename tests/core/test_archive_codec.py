"""Тесты кодеков .epicase / .epiresult (FEATURE-01)."""
from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pytest

from epicase_core.infrastructure.archive import DATA_NAME, MANIFEST_NAME
from epicase_core.infrastructure.archive.codec import (
    read_epicase,
    read_epiresult,
    write_epicase,
    write_epiresult,
)
from epicase_core.infrastructure.archive.errors import (
    ArchiveError,
    CorruptedArchiveError,
    IncompatibleVersionError,
)

_PAYLOAD: dict[str, object] = {"title": "Тестовый кейс", "stages": [1, 2, 3]}
_ASSETS: dict[str, bytes] = {"plan.png": b"\x89PNG\x00binary", "doc.txt": "текст".encode()}


def test_epicase_round_trip(tmp_path: Path) -> None:
    dst = write_epicase(_PAYLOAD, tmp_path / "case", assets=_ASSETS, meta={"case_id": "42"})
    assert dst.suffix == ".epicase"
    bundle = read_epicase(dst)
    assert bundle.payload == _PAYLOAD
    assert bundle.assets == _ASSETS
    assert bundle.manifest.kind == "epicase"
    assert bundle.manifest.meta["case_id"] == "42"


def test_epiresult_round_trip(tmp_path: Path) -> None:
    dst = write_epiresult(_PAYLOAD, tmp_path / "res", assets=_ASSETS)
    assert dst.suffix == ".epiresult"
    bundle = read_epiresult(dst)
    assert bundle.payload == _PAYLOAD
    assert bundle.manifest.kind == "epiresult"


def test_suffix_is_forced(tmp_path: Path) -> None:
    dst = write_epicase(_PAYLOAD, tmp_path / "case.zip")
    assert dst.name == "case.epicase"


def test_tampered_data_fails_checksum(tmp_path: Path) -> None:
    dst = write_epicase(_PAYLOAD, tmp_path / "case")
    # Перепаковываем архив с подменённым data.json (manifest.checksum остаётся прежним).
    with zipfile.ZipFile(dst, "r") as zf:
        items = {n: zf.read(n) for n in zf.namelist()}
    items[DATA_NAME] = json.dumps({"title": "подмена"}).encode("utf-8")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, blob in items.items():
            zf.writestr(name, blob)
    dst.write_bytes(buf.getvalue())

    with pytest.raises(CorruptedArchiveError):
        read_epicase(dst)


def test_future_version_rejected(tmp_path: Path) -> None:
    dst = write_epicase(_PAYLOAD, tmp_path / "case")
    with zipfile.ZipFile(dst, "r") as zf:
        items = {n: zf.read(n) for n in zf.namelist()}
    manifest = json.loads(items[MANIFEST_NAME].decode("utf-8"))
    manifest["format_version"] = 99
    items[MANIFEST_NAME] = json.dumps(manifest, ensure_ascii=False).encode("utf-8")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, blob in items.items():
            zf.writestr(name, blob)
    dst.write_bytes(buf.getvalue())

    with pytest.raises(IncompatibleVersionError):
        read_epicase(dst)


def test_kind_mismatch_rejected(tmp_path: Path) -> None:
    dst = write_epiresult(_PAYLOAD, tmp_path / "res")
    with pytest.raises(ArchiveError):
        read_epicase(dst)


def test_not_a_zip_rejected(tmp_path: Path) -> None:
    bad = tmp_path / "broken.epicase"
    bad.write_bytes("это не zip-архив".encode())
    with pytest.raises(CorruptedArchiveError):
        read_epicase(bad)


def test_missing_parts_rejected(tmp_path: Path) -> None:
    bad = tmp_path / "empty.epicase"
    with zipfile.ZipFile(bad, "w") as zf:
        zf.writestr("readme.txt", b"nothing useful")
    with pytest.raises(CorruptedArchiveError):
        read_epicase(bad)
