"""Тесты шва сведения результата с кейсом ``report_for_result`` (Qt-free, слой приложения).

Проверяем: верные ответы дают ``correct=True`` findings; ``case_id_matches`` отражает
соответствие кейсов; чужой тип архива (.epicase по пути результата) → ``ArchiveError``.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from epicase_core.application.cases import save_case
from epicase_core.application.grading import ArchiveError, report_for_result
from epicase_core.application.results import record_attempt
from epicase_core.domain import (
    Attempt,
    AttemptClinical,
    AttemptMeta,
    BranchOption,
    BranchPoint,
    BranchResponse,
    Case,
    CaseMeta,
    DocumentField,
    DocumentOption,
    DocumentResponse,
    DocumentTask,
    DocumentTemplate,
    FieldType,
    Finding,
    FindingKind,
    StageClinical,
    StageKind,
    StageReport,
    SynonymSet,
    TextMatch,
)

DIARRHEA = SynonymSet(canonical="диарея", synonyms=("понос",))


def _case() -> Case:
    """Кейс с клиническим этапом: верная ветвь + документ с TextMatch-полем и обманкой."""
    return Case(
        meta=CaseMeta(id="case-1", title="Вспышка ОКИ"),
        clinical=StageClinical(
            branch=BranchPoint(
                id="branch",
                prompt="Выберите путь",
                options=(
                    BranchOption(id="b-ok", label="Кишечная инфекция", is_correct=True),
                    BranchOption(id="b-bad", label="Пищевое отравление"),
                ),
            ),
            documents=(
                DocumentTask(
                    id="doc-1",
                    prompt="Выберите документ",
                    options=(
                        DocumentOption(
                            id="opt-1",
                            title="Донесение ДМ4",
                            is_correct=True,
                            template=DocumentTemplate(
                                id="tmpl-1",
                                fields=(
                                    DocumentField(
                                        id="field-1",
                                        type=FieldType.TEXT,
                                        rule=TextMatch(keywords=DIARRHEA),
                                        label="Диагноз",
                                    ),
                                ),
                            ),
                        ),
                        DocumentOption(id="opt-2", title="Рапорт командира"),
                    ),
                ),
            ),
        ),
    )


def _attempt(case_id: str = "case-1") -> Attempt:
    """Прохождение с верными ответами на клиническом этапе."""
    return Attempt(
        meta=AttemptMeta(
            case_id=case_id, trainee_label="Иванов", rank="лейтенант", study_group="121"
        ),
        clinical=AttemptClinical(
            branch=BranchResponse(point_id="branch", chosen_option_id="b-ok"),
            documents=(
                DocumentResponse(
                    task_id="doc-1",
                    chosen_option_id="opt-1",
                    field_answers=(("field-1", "диарея"),),
                ),
            ),
        ),
    )


def _clinical_findings(
    stages: tuple[StageReport, ...], kind: FindingKind
) -> Finding:
    clinical = next(s for s in stages if s.kind == StageKind.CLINICAL)
    return next(f for f in clinical.findings if f.kind == kind)


def test_report_for_result_grades_correct_attempt(tmp_path: Path) -> None:
    """Верные ответы → correct=True findings; case_id_matches True; подпись курсанта донесена."""
    case_path = save_case(_case(), tmp_path / "case")
    result_path = record_attempt(_attempt(), tmp_path / "result")

    graded = report_for_result(result_path, case_path)

    assert graded.case_id == "case-1"
    assert graded.attempt_case_id == "case-1"
    assert graded.trainee_label == "Иванов"
    assert graded.rank == "лейтенант"
    assert graded.study_group == "121"
    assert graded.case_id_matches is True
    assert graded.report.case_id == "case-1"
    assert len(graded.report.stages) == 6

    assert _clinical_findings(graded.report.stages, FindingKind.BRANCH).correct is True
    assert _clinical_findings(
        graded.report.stages, FindingKind.DOCUMENT_CHOICE
    ).correct is True
    assert _clinical_findings(
        graded.report.stages, FindingKind.DOCUMENT_FIELD
    ).correct is True


def test_report_for_result_case_id_mismatch(tmp_path: Path) -> None:
    """Результат с другим case_id → ``case_id_matches`` False (оценка всё равно строится)."""
    case_path = save_case(_case(), tmp_path / "case")
    result_path = record_attempt(_attempt(case_id="case-OTHER"), tmp_path / "result")

    graded = report_for_result(result_path, case_path)

    assert graded.case_id == "case-1"
    assert graded.attempt_case_id == "case-OTHER"
    assert graded.case_id_matches is False


def test_report_for_result_wrong_archive_type_raises(tmp_path: Path) -> None:
    """`.epicase`, поданный как путь результата, → ``ArchiveError`` (несовпадение типа архива)."""
    case_path = save_case(_case(), tmp_path / "case")
    with pytest.raises(ArchiveError):
        report_for_result(case_path, case_path)
