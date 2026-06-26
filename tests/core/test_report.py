"""Тесты движка сверки grade_case (ADR-008): поэлементное «верно/неверно» без весов,
вскрытие «Варианта B», устойчивость к дефолтному Attempt, round-trip отчёта."""
from __future__ import annotations

from epicase_core.domain import (
    Attempt,
    AttemptClinical,
    AttemptContacts,
    AttemptFinal,
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
    StageFinal,
    StageKind,
    StageReport,
    StageSes,
    SynonymSet,
    TextMatch,
    Timeline,
    TimelineResponse,
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


def _final_stage() -> StageFinal:
    """Этап 6 с двумя эталонными таймлайнами (на второй курсант не отвечает)."""
    return StageFinal(
        timelines=(
            Timeline(
                id="tl-outbreak",
                title="Сроки наблюдения за очагом",
                events=(("01.06", "первый случай"), ("03.06", "пик")),
            ),
            Timeline(
                id="tl-care",
                title="Динамика лечения",
                events=(("05.06", "выписка"),),
            ),
        ),
    )


def _final_attempt() -> Attempt:
    """Прохождение с ответом только на первый таймлайн."""
    return Attempt(
        AttemptMeta("case-final"),
        final=AttemptFinal(
            timelines=(
                TimelineResponse(
                    timeline_id="tl-outbreak",
                    entries=(("01.06", "заболел"), ("04.06", "госпитализация")),
                ),
            ),
        ),
    )


def test_final_timelines_compared_without_verdict() -> None:
    """Этап 6: таймлайны сопоставляются нейтрально — эталон из кейса, ввод курсанта рядом."""
    case = Case(CaseMeta("case-final"), final=_final_stage())
    final = _stage(grade_case(case, _final_attempt()), StageKind.FINAL)

    # Порядок — как в кейсе; нет авто-вердикта (нейтральная структура без correct).
    assert tuple(t.timeline_id for t in final.timelines) == ("tl-outbreak", "tl-care")
    outbreak = final.timelines[0]
    assert outbreak.title == "Сроки наблюдения за очагом"
    assert outbreak.authored == (("01.06", "первый случай"), ("03.06", "пик"))
    assert outbreak.cadet == (("01.06", "заболел"), ("04.06", "госпитализация"))
    assert not hasattr(outbreak, "correct")


def test_final_timeline_without_cadet_answer_has_empty_cadet() -> None:
    """Эталонный таймлайн без ответа курсанта → cadet пуст, эталон сохраняется."""
    case = Case(CaseMeta("case-final"), final=_final_stage())
    final = _stage(grade_case(case, _final_attempt()), StageKind.FINAL)

    care = final.timelines[1]
    assert care.timeline_id == "tl-care"
    assert care.cadet == ()
    assert care.authored == (("05.06", "выписка"),)


def test_final_timelines_round_trip() -> None:
    """to_dict/from_dict сохраняет таймлайны этапа 6 в отчёте."""
    case = Case(CaseMeta("case-final"), final=_final_stage())
    report = grade_case(case, _final_attempt())
    assert CaseReport.from_dict(report.to_dict()) == report


def test_stage_report_reads_legacy_serialization_without_timelines() -> None:
    """Старая сериализация без ключа «timelines» читается (default ())."""
    legacy = {"kind": StageKind.FINAL.value, "findings": []}
    assert StageReport.from_dict(legacy).timelines == ()


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
