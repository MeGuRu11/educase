"""Тесты доменной модели Attempt (ADR-008): round-trip to_dict/from_dict,
фиксированный порядок слотов, корректная сериализация Optional-полей."""
from __future__ import annotations

from educase_core.domain import (
    Attempt,
    AttemptClinical,
    AttemptContacts,
    AttemptEnvironment,
    AttemptFinal,
    AttemptMeta,
    AttemptPatients,
    AttemptSes,
    BranchResponse,
    ChoiceResponse,
    DocumentResponse,
    InspectionResponse,
    SearchLog,
    StageKind,
)


def _rich_attempt() -> Attempt:
    """Полностью заполненное прохождение: все шесть слотов, ветвление, осмотр, выбор уровня,
    непустые ответы по полям документов."""
    patients = AttemptPatients(
        search=SearchLog(queries=("температура", "диарея")),
    )

    clinical = AttemptClinical(
        search=SearchLog(queries=("понос",)),
        branch=BranchResponse(point_id="branch-1", chosen_option_id="b-ok"),
        documents=(
            DocumentResponse(
                task_id="dm4",
                chosen_option_id="opt-dm4",
                field_answers=(
                    ("f-diag", "диарея"),
                    ("f-count", "20"),
                    ("f-date", "2026-06-09"),
                ),
            ),
        ),
    )

    contacts = AttemptContacts(
        inspection=InspectionResponse(text="Скученность, плохая вентиляция"),
    )

    environment = AttemptEnvironment(
        documents=(DocumentResponse(task_id="gsen", chosen_option_id="opt-gsen"),),
        inspection=InspectionResponse(text="Антисанитария на пищеблоке"),
    )

    ses = AttemptSes(
        search=SearchLog(queries=("жар",)),
        level_choice=ChoiceResponse(answer="Неблагополучное"),
        documents=(DocumentResponse(task_id="plan", chosen_option_id="opt-plan"),),
    )

    final = AttemptFinal(
        search=SearchLog(queries=("лихорадка",)),
        documents=(DocumentResponse(task_id="akt", chosen_option_id="opt-akt"),),
    )

    return Attempt(
        meta=AttemptMeta(
            case_id="case-1",
            trainee_label="Курсант Петров",
            created_at="2026-06-16",
        ),
        patients=patients,
        clinical=clinical,
        contacts=contacts,
        environment=environment,
        ses=ses,
        final=final,
    )


def test_attempt_dict_round_trip() -> None:
    attempt = _rich_attempt()
    assert Attempt.from_dict(attempt.to_dict()) == attempt


def test_empty_attempt_round_trip() -> None:
    attempt = Attempt(AttemptMeta("case-0"))
    assert Attempt.from_dict(attempt.to_dict()) == attempt
    assert len(attempt.ordered()) == 6


def test_attempt_stage_kinds_fixed() -> None:
    attempt = _rich_attempt()
    kinds = tuple(stage.KIND for stage in attempt.ordered())
    assert kinds == (
        StageKind.PATIENTS,
        StageKind.CLINICAL,
        StageKind.CONTACTS,
        StageKind.ENVIRONMENT,
        StageKind.SES,
        StageKind.FINAL,
    )


def test_attempt_meta_identity_fields_round_trip() -> None:
    # Звание и учебная группа должны пережить сериализацию вместе с ФИО (trainee_label).
    attempt = Attempt(
        meta=AttemptMeta(
            case_id="case-3",
            trainee_label="Иванов Иван Иванович",
            rank="лейтенант",
            study_group="121",
        ),
    )
    restored = Attempt.from_dict(attempt.to_dict())
    assert restored == attempt
    assert restored.meta.rank == "лейтенант"
    assert restored.meta.study_group == "121"


def test_document_response_free_text_round_trip() -> None:
    # ADR-014: ответ в режиме свободного заполнения переживает сериализацию.
    response = DocumentResponse(
        task_id="doc-free",
        free_text="Свободный текст ответа курсанта",
    )
    restored = DocumentResponse.from_dict(response.to_dict())
    assert restored == response
    assert restored.free_text == "Свободный текст ответа курсанта"


def test_document_response_legacy_dict_free_text_defaults() -> None:
    # Старый ответ без ключа free_text читается с дефолтом "" (обратная совместимость).
    restored = DocumentResponse.from_dict({"task_id": "doc-old"})
    assert restored.free_text == ""


def test_attempt_optional_none_round_trip() -> None:
    # branch / inspection / level_choice = None должны пережить сериализацию как null.
    attempt = Attempt(
        meta=AttemptMeta("case-2"),
        clinical=AttemptClinical(branch=None),
        contacts=AttemptContacts(inspection=None),
        ses=AttemptSes(level_choice=None),
    )
    restored = Attempt.from_dict(attempt.to_dict())
    assert restored == attempt
    assert restored.clinical.branch is None
    assert restored.contacts.inspection is None
    assert restored.ses.level_choice is None
