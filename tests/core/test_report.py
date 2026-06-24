"""Тесты движка сверки grade_case (ADR-008): поэлементное «верно/неверно» без весов,
вскрытие «Варианта B», устойчивость к дефолтному Attempt, round-trip отчёта."""
from __future__ import annotations

from epicase_core.domain import (
    Attempt,
    AttemptClinical,
    AttemptContacts,
    AttemptMeta,
    AttemptSes,
    BranchOption,
    BranchPoint,
    BranchResponse,
    Case,
    CaseMeta,
    CaseReport,
    ChoiceMatch,
    ChoiceResponse,
    DocumentField,
    DocumentOption,
    DocumentResponse,
    DocumentTask,
    DocumentTemplate,
    FieldType,
    FindingKind,
    InspectionCheck,
    InspectionResponse,
    StageClinical,
    StageContacts,
    StageKind,
    StageReport,
    StageSes,
    SynonymSet,
    TextMatch,
    grade_case,
)
from epicase_core.domain.report import Finding

DIARRHEA = SynonymSet(canonical="диарея", synonyms=("понос",))


def _stage(report: CaseReport, kind: StageKind) -> StageReport:
    """Отчёт нужного этапа из CaseReport."""
    return next(s for s in report.stages if s.kind == kind)


def _finding(stage: StageReport, kind: FindingKind) -> Finding:
    """Первая Finding нужного типа в отчёте этапа."""
    return next(f for f in stage.findings if f.kind == kind)


def _clinical_stage() -> StageClinical:
    """Клинический этап: верная ветвь + документ с одним TextMatch-полем и обманкой."""
    return StageClinical(
        branch=BranchPoint(
            id="branch-1",
            prompt="Выберите путь",
            options=(
                BranchOption(id="b-ok", label="Кишечная инфекция", is_correct=True),
                BranchOption(id="b-bad", label="Пищевое отравление"),
            ),
        ),
        documents=(
            DocumentTask(
                id="dm4",
                prompt="Выберите документ",
                options=(
                    DocumentOption(
                        id="opt-dm4",
                        title="Внеочередное донесение ДМ4",
                        is_correct=True,
                        template=DocumentTemplate(
                            id="tpl-dm4",
                            fields=(
                                DocumentField(
                                    id="f-diag",
                                    type=FieldType.TEXT,
                                    rule=TextMatch(keywords=DIARRHEA),
                                    label="Диагноз",
                                ),
                            ),
                        ),
                    ),
                    DocumentOption(id="opt-decoy", title="Рапорт командира части"),
                ),
            ),
        ),
    )


def test_clinical_all_correct() -> None:
    case = Case(CaseMeta("case-1"), clinical=_clinical_stage())
    attempt = Attempt(
        AttemptMeta("case-1"),
        clinical=AttemptClinical(
            branch=BranchResponse(point_id="branch-1", chosen_option_id="b-ok"),
            documents=(
                DocumentResponse(
                    task_id="dm4",
                    chosen_option_id="opt-dm4",
                    field_answers=(("f-diag", "понос"),),
                ),
            ),
        ),
    )

    clinical = _stage(grade_case(case, attempt), StageKind.CLINICAL)
    kinds = tuple(f.kind for f in clinical.findings)
    assert kinds == (
        FindingKind.BRANCH,
        FindingKind.DOCUMENT_CHOICE,
        FindingKind.DOCUMENT_FIELD,
    )
    assert all(f.correct for f in clinical.findings)


def test_clinical_all_wrong_reveals_branch() -> None:
    case = Case(CaseMeta("case-1"), clinical=_clinical_stage())
    attempt = Attempt(
        AttemptMeta("case-1"),
        clinical=AttemptClinical(
            branch=BranchResponse(point_id="branch-1", chosen_option_id="b-bad"),
            documents=(
                DocumentResponse(
                    task_id="dm4",
                    chosen_option_id="opt-decoy",
                    field_answers=(("f-diag", "грипп"),),
                ),
            ),
        ),
    )

    clinical = _stage(grade_case(case, attempt), StageKind.CLINICAL)
    assert all(not f.correct for f in clinical.findings)
    # Вскрытие «Варианта B»: неверный выбор ветви отражён в detail, прохождение не блокировал.
    branch = _finding(clinical, FindingKind.BRANCH)
    assert branch.correct is False
    assert branch.detail == "Пищевое отравление"


def _rich_case() -> Case:
    """Кейс с оцениваемыми элементами в нескольких этапах (для дефолтного Attempt)."""
    return Case(
        CaseMeta("case-2"),
        clinical=_clinical_stage(),
        contacts=StageContacts(
            inspection=InspectionCheck(
                expected=(
                    SynonymSet(canonical="скученность"),
                    SynonymSet(canonical="вентиляция"),
                ),
            ),
        ),
        ses=StageSes(
            level_choice=DocumentField(
                id="ses-level",
                type=FieldType.CHOICE,
                rule=ChoiceMatch(correct=("Неблагополучное",)),
                label="Уровень СЭС",
            ),
        ),
    )


def test_default_attempt_does_not_crash_all_incorrect() -> None:
    case = _rich_case()
    report = grade_case(case, Attempt(AttemptMeta("case-2")))
    findings = [f for stage in report.stages for f in stage.findings]
    assert findings  # есть что проверять
    assert all(not f.correct for f in findings)


def test_inspection_partial_coverage() -> None:
    case = Case(
        CaseMeta("case-3"),
        contacts=StageContacts(
            inspection=InspectionCheck(
                expected=(
                    SynonymSet(canonical="скученность"),
                    SynonymSet(canonical="вентиляция"),
                ),
            ),
        ),
    )
    attempt = Attempt(
        AttemptMeta("case-3"),
        contacts=AttemptContacts(inspection=InspectionResponse(text="Выявлена скученность")),
    )

    contacts = _stage(grade_case(case, attempt), StageKind.CONTACTS)
    assert tuple(f.correct for f in contacts.findings) == (True, False)
    assert tuple(f.kind for f in contacts.findings) == (
        FindingKind.INSPECTION,
        FindingKind.INSPECTION,
    )


def _ses_case() -> Case:
    return Case(
        CaseMeta("case-4"),
        ses=StageSes(
            level_choice=DocumentField(
                id="ses-level",
                type=FieldType.CHOICE,
                rule=ChoiceMatch(correct=("Неблагополучное",)),
                label="Уровень СЭС",
            ),
        ),
    )


def test_ses_level_choice_correct() -> None:
    attempt = Attempt(
        AttemptMeta("case-4"),
        ses=AttemptSes(level_choice=ChoiceResponse(answer="Неблагополучное")),
    )
    ses = _stage(grade_case(_ses_case(), attempt), StageKind.SES)
    level = _finding(ses, FindingKind.LEVEL_CHOICE)
    assert level.correct is True
    assert level.detail == "Неблагополучное"


def test_ses_level_choice_wrong() -> None:
    attempt = Attempt(
        AttemptMeta("case-4"),
        ses=AttemptSes(level_choice=ChoiceResponse(answer="Благополучное")),
    )
    ses = _stage(grade_case(_ses_case(), attempt), StageKind.SES)
    level = _finding(ses, FindingKind.LEVEL_CHOICE)
    assert level.correct is False


def test_grade_case_defaults_six_stages_in_order() -> None:
    case = Case(CaseMeta("c0"))
    report = grade_case(case, Attempt(AttemptMeta("c0")))
    assert report.case_id == "c0"
    assert tuple(s.kind for s in report.stages) == tuple(
        stage.KIND for stage in case.ordered()
    )
    patients = _stage(report, StageKind.PATIENTS)
    assert patients.findings == ()


def test_case_report_round_trip() -> None:
    case = Case(CaseMeta("case-1"), clinical=_clinical_stage())
    attempt = Attempt(
        AttemptMeta("case-1"),
        clinical=AttemptClinical(
            branch=BranchResponse(point_id="branch-1", chosen_option_id="b-ok"),
            documents=(
                DocumentResponse(
                    task_id="dm4",
                    chosen_option_id="opt-dm4",
                    field_answers=(("f-diag", "понос"),),
                ),
            ),
        ),
    )
    report = grade_case(case, attempt)
    assert CaseReport.from_dict(report.to_dict()) == report
