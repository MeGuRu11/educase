"""Тесты сервиса Attempt↔.epiresult (слой приложения)."""
from __future__ import annotations

from pathlib import Path

import pytest

from epicase_core.application.results import load_result, record_attempt
from epicase_core.domain import Attempt, AttemptMeta, AttemptPatients, SearchLog
from epicase_core.infrastructure.archive.codec import read_eduresult, write_educase
from epicase_core.infrastructure.archive.errors import ArchiveError


def _attempt() -> Attempt:
    return Attempt(
        meta=AttemptMeta(case_id="case-7", trainee_label="Курсант Петров"),
        patients=AttemptPatients(search=SearchLog(queries=("температура",))),
    )


def test_record_then_load_round_trip(tmp_path: Path) -> None:
    attempt = _attempt()
    assets = {"scan.png": b"\x89PNG\x00data", "note.txt": "текст".encode()}
    dst = record_attempt(attempt, tmp_path / "res", assets=assets)
    loaded = load_result(dst)
    assert loaded.attempt == attempt
    assert loaded.assets == assets


def test_record_writes_case_id_into_meta(tmp_path: Path) -> None:
    dst = record_attempt(_attempt(), tmp_path / "res")
    bundle = read_eduresult(dst)
    assert bundle.manifest.meta["case_id"] == "case-7"


def test_load_educase_raises_archive_error(tmp_path: Path) -> None:
    # .epicase — другой kind архива; load_result ждёт eduresult и поднимает ArchiveError.
    other = write_educase({"x": 1}, tmp_path / "case")
    with pytest.raises(ArchiveError):
        load_result(other)
