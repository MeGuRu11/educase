"""Сведение результата с эталонным кейсом для предварительной проверки (слой приложения).

Qt-free шов между сервисами загрузки (``load_result``/``load_case``) и движком сверки
``grade_case``: читает .epiresult и .epicase, возвращает отчёт плюс контекст соответствия
кейсов. Машинные статусы служат подсказкой преподавателю; итоговой оценки, баллов и
pass/fail нет (ADR-016). Чистая оркестрация без сети и БД.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from epicase_core.application.cases import load_case
from epicase_core.application.results import load_result
from epicase_core.domain.report import CaseReport, grade_case

# ArchiveError реэкспортируется (как в cases/results), чтобы UI ловил один тип ошибки.
from epicase_core.infrastructure.archive.errors import ArchiveError


@dataclass(frozen=True)
class GradedResult:
    """Предварительная сверка + контекст соответствия кейсов (без итоговой оценки).

    ``case_id`` — id выбранного эталонного кейса; ``attempt_case_id`` — id кейса, к которому
    относится результат; их несовпадение — повод предупредить преподавателя, не ошибка.
    ``assets`` — ассеты архива результата (имя → байты), включая вложения курсанта: отчёту
    нужны байты, чтобы их можно было открыть или сохранить.
    """

    report: CaseReport
    case_id: str
    attempt_case_id: str
    trainee_label: str
    rank: str
    study_group: str
    assets: dict[str, bytes]

    @property
    def case_id_matches(self) -> bool:
        """Совпадает ли выбранный кейс с тем, к которому относится результат."""
        return self.case_id == self.attempt_case_id


def report_for_result(result_path: Path, case_path: Path) -> GradedResult:
    """Свести .epiresult с .epicase в предварительный ``CaseReport`` и контекст.

    Загружает прохождение и кейс готовыми сервисами и гоняет ``grade_case``. Ошибки формата
    или типа архива (``ArchiveError`` из ``load_*``) пробрасываются наверх.
    """
    loaded = load_result(result_path)
    attempt = loaded.attempt
    case = load_case(case_path).case
    return GradedResult(
        report=grade_case(case, attempt),
        case_id=case.meta.id,
        attempt_case_id=attempt.meta.case_id,
        trainee_label=attempt.meta.trainee_label,
        rank=attempt.meta.rank,
        study_group=attempt.meta.study_group,
        assets=loaded.assets,
    )


__all__ = ["ArchiveError", "GradedResult", "report_for_result"]
