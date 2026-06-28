"""Тесты доменной модели Attempt (ADR-008): round-trip to_dict/from_dict,
фиксированный порядок слотов, корректная сериализация Optional-полей."""
from __future__ import annotations

from epicase_core.domain import (
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
    TimelineResponse,
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


def test_document_response_ignores_legacy_free_text() -> None:
    """Старое поле читается без ошибки, но не переносится в актуальную модель/serde."""
    restored = DocumentResponse.from_dict(
        {"task_id": "doc-old", "free_text": "устаревший ответ"}
    )

    assert not hasattr(restored, "free_text")
    assert "free_text" not in restored.to_dict()


def test_document_response_attachments_round_trip() -> None:
    # ADR-015: пары (asset_id, имя_файла) режима ATTACHMENT переживают сериализацию.
    response = DocumentResponse(
        task_id="doc-att",
        attachments=(("att-1", "Форма23.pdf"), ("att-2", "Акт.pdf")),
    )
    restored = DocumentResponse.from_dict(response.to_dict())
    assert restored == response
    assert restored.attachments == (("att-1", "Форма23.pdf"), ("att-2", "Акт.pdf"))


def test_document_response_legacy_dict_attachments_defaults() -> None:
    # Старый ответ без ключа attachments читается с дефолтом () (обратная совместимость).
    restored = DocumentResponse.from_dict({"task_id": "doc-old"})
    assert restored.attachments == ()


def test_timeline_response_round_trip() -> None:
    # Заполненный курсантом таймлайн (пары «дата → событие») переживает сериализацию.
    response = TimelineResponse(
        timeline_id="tl-1",
        entries=(("01.01.2024", "Изоляция"), ("05.01.2024", "Снятие карантина")),
    )
    restored = TimelineResponse.from_dict(response.to_dict())
    assert restored == response
    assert restored.timeline_id == "tl-1"
    assert restored.entries == (
        ("01.01.2024", "Изоляция"),
        ("05.01.2024", "Снятие карантина"),
    )


def test_attempt_final_with_timelines_round_trip() -> None:
    # Непустые timelines в AttemptFinal переживают to_dict → from_dict.
    final = AttemptFinal(
        search=SearchLog(queries=("лихорадка",)),
        documents=(DocumentResponse(task_id="akt", chosen_option_id="opt-akt"),),
        timelines=(
            TimelineResponse(
                timeline_id="tl-1",
                entries=(("02.01.2024", "Госпитализация"),),
            ),
        ),
    )
    attempt = Attempt(meta=AttemptMeta("case-tl"), final=final)
    restored = Attempt.from_dict(attempt.to_dict())
    assert restored == attempt
    assert restored.final.timelines == final.timelines


def test_attempt_final_legacy_dict_timelines_defaults() -> None:
    # Старый ответ без ключа timelines читается с дефолтом () (обратная совместимость).
    restored = AttemptFinal.from_dict({"kind": "final"})
    assert restored.timelines == ()


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
