"""Тесты сервиса Attempt↔.epiresult (слой приложения)."""
from __future__ import annotations

from pathlib import Path

import pytest

from epicase_core.application.results import load_result, record_attempt
from epicase_core.domain import (
    Attempt,
    AttemptFinal,
    AttemptMeta,
    AttemptPatients,
    DocumentResponse,
    SearchLog,
)
from epicase_core.infrastructure.archive.codec import read_epiresult, write_epicase
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
    bundle = read_epiresult(dst)
    assert bundle.manifest.meta["case_id"] == "case-7"


def test_attachment_refs_and_bytes_survive_result_round_trip(tmp_path: Path) -> None:
    # ADR-015 / RES-1: ссылки на вложения и их байты переживают полный цикл .epiresult.
    attempt = Attempt(
        meta=AttemptMeta(case_id="case-att", trainee_label="Курсант Петров"),
        final=AttemptFinal(
            documents=(
                DocumentResponse(
                    task_id="akt",
                    attachments=(("att-1", "Форма23.pdf"),),
                ),
            ),
        ),
    )
    dst = record_attempt(attempt, tmp_path / "res", assets={"att-1": b"%PDF-FAKE"})

    res = load_result(dst)

    response = res.attempt.final.documents[0]
    assert response.attachments == (("att-1", "Форма23.pdf"),)
    assert res.assets["att-1"] == b"%PDF-FAKE"


def test_load_epicase_raises_archive_error(tmp_path: Path) -> None:
    # .epicase — другой kind архива; load_result ждёт epiresult и поднимает ArchiveError.
    other = write_epicase({"x": 1}, tmp_path / "case")
    with pytest.raises(ArchiveError):
        load_result(other)
