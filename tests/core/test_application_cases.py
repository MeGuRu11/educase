"""Тесты сервиса Case↔.educase (FEATURE-03, слой приложения)."""
from __future__ import annotations

from pathlib import Path

import pytest

from epicase_core.application.cases import load_case, save_case
from epicase_core.domain import Case, CaseMeta
from epicase_core.infrastructure.archive.codec import read_educase, write_eduresult
from epicase_core.infrastructure.archive.errors import ArchiveError


def _case() -> Case:
    return Case(meta=CaseMeta(id="case-7", title="Вспышка ОКИ"))


def test_save_then_load_round_trip(tmp_path: Path) -> None:
    case = _case()
    assets = {"plan.png": b"\x89PNG\x00data", "doc.txt": "текст".encode()}
    dst = save_case(case, tmp_path / "case", assets=assets)
    loaded = load_case(dst)
    assert loaded.case == case
    assert loaded.assets == assets


def test_save_writes_case_id_into_meta(tmp_path: Path) -> None:
    dst = save_case(_case(), tmp_path / "case")
    bundle = read_educase(dst)
    assert bundle.manifest.meta["case_id"] == "case-7"


def test_caller_meta_overrides_default(tmp_path: Path) -> None:
    dst = save_case(_case(), tmp_path / "case", meta={"case_id": "override", "extra": "v"})
    bundle = read_educase(dst)
    assert bundle.manifest.meta["case_id"] == "override"  # значение вызывающего важнее
    assert bundle.manifest.meta["extra"] == "v"


def test_load_eduresult_raises_archive_error(tmp_path: Path) -> None:
    # .eduresult — другой kind архива; load_case ждёт educase и поднимает ArchiveError.
    other = write_eduresult({"x": 1}, tmp_path / "res")
    with pytest.raises(ArchiveError):
        load_case(other)
