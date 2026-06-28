"""Сервис записи/чтения результата прохождения через кодек .epiresult (слой приложения).

Оркестрация между доменной моделью ``Attempt`` и кодеком архива ``infrastructure/archive``:
склейка ``to_dict``/``from_dict`` с упаковкой ZIP. Бизнес-правил и сверки ответов здесь нет:
предварительная проверка выполняется отдельно в ``domain.report`` (ADR-016).
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from epicase_core.domain.attempt import Attempt
from epicase_core.infrastructure.archive.codec import read_epiresult, write_epiresult
from epicase_core.infrastructure.archive.errors import ArchiveError


@dataclass(frozen=True)
class LoadedResult:
    """Загруженный результат: доменная модель + ассеты архива (имя → байты)."""

    attempt: Attempt
    assets: dict[str, bytes]


def record_attempt(
    attempt: Attempt,
    dst: Path,
    *,
    assets: Mapping[str, bytes] | None = None,
    meta: Mapping[str, object] | None = None,
) -> Path:
    """Упаковать прохождение в .epiresult.

    По умолчанию в ``meta`` архива пишутся ``case_id`` и ``trainee_label`` прохождения.
    Если передан ``meta``, он сливается поверх умолчаний (значения вызывающего важнее).
    """
    merged_meta: dict[str, object] = {
        "case_id": attempt.meta.case_id,
        "trainee_label": attempt.meta.trainee_label,
    }
    if meta is not None:
        merged_meta.update(meta)
    return write_epiresult(attempt.to_dict(), dst, assets=assets, meta=merged_meta)


def load_result(src: Path) -> LoadedResult:
    """Прочитать .epiresult и собрать доменный ``Attempt`` с ассетами.

    Ошибки формата/версии/типа архива поднимаются как ``ArchiveError`` (из кодека).
    """
    bundle = read_epiresult(src)
    return LoadedResult(attempt=Attempt.from_dict(bundle.payload), assets=bundle.assets)


__all__ = ["ArchiveError", "LoadedResult", "load_result", "record_attempt"]
