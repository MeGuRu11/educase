"""Сервис загрузки/сохранения кейса через кодек .epicase (слой приложения).

Оркестрация между доменной моделью ``Case`` и кодеком архива ``infrastructure/archive``:
склейка ``to_dict``/``from_dict`` с упаковкой ZIP. Бизнес-правил здесь нет (ADR-009).
Результаты курсантов ``.epiresult`` обслуживает отдельный модуль ``application.results``.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from epicase_core.domain.case import Case
from epicase_core.infrastructure.archive.codec import read_epicase, write_epicase
from epicase_core.infrastructure.archive.errors import ArchiveError


@dataclass(frozen=True)
class LoadedCase:
    """Загруженный кейс: доменная модель + ассеты архива (имя → байты)."""

    case: Case
    assets: dict[str, bytes]


def save_case(
    case: Case,
    dst: Path,
    *,
    assets: Mapping[str, bytes] | None = None,
    meta: Mapping[str, object] | None = None,
) -> Path:
    """Упаковать кейс в .epicase.

    По умолчанию в ``meta`` архива пишутся ``case_id`` и ``title`` кейса. Если передан
    ``meta``, он сливается поверх умолчаний (значения вызывающего важнее).
    """
    merged_meta: dict[str, object] = {
        "case_id": case.meta.id,
        "title": case.meta.title,
    }
    if meta is not None:
        merged_meta.update(meta)
    return write_epicase(case.to_dict(), dst, assets=assets, meta=merged_meta)


def load_case(src: Path) -> LoadedCase:
    """Прочитать .epicase и собрать доменный ``Case`` с ассетами.

    Ошибки формата/версии/типа архива поднимаются как ``ArchiveError`` (из кодека).
    """
    bundle = read_epicase(src)
    return LoadedCase(case=Case.from_dict(bundle.payload), assets=bundle.assets)


__all__ = ["ArchiveError", "LoadedCase", "load_case", "save_case"]
