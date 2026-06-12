"""Сборка доменного ``Case`` из «сырых» значений UI (этот срез: мета + этап «Пациенты»).

UI собирает значения виджетов в простые ``*Draft``-структуры, а доменные тонкости
(неизменяемость, конструирование этапов) живут здесь. Чистые функции без I/O — обратная
сторона (из ``Case`` в ``CaseDraft`` для будущего редактирования) пока не реализуется.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from educase_core.domain import (
    BranchOption,
    BranchPoint,
    Case,
    CaseMeta,
    ChoiceMatch,
    DateMatch,
    DocumentField,
    DocumentOption,
    DocumentTask,
    DocumentTemplate,
    FieldType,
    InspectionCheck,
    KeywordSearch,
    MatchRule,
    NumberMatch,
    PatientCard,
    SearchEntry,
    StageClinical,
    StageContacts,
    StageEnvironment,
    StagePatients,
    SynonymSet,
    TextMatch,
)


@dataclass(frozen=True)
class PatientDraft:
    """Сырые значения одной карточки пациента из UI."""

    id: str
    title: str
    fields: tuple[tuple[str, str], ...] = ()
    assets: tuple[str, ...] = ()


@dataclass(frozen=True)
class SynonymSetDraft:
    """Сырые значения группы синонимов из UI: канонический термин + синонимы."""

    canonical: str
    synonyms: tuple[str, ...] = ()


@dataclass(frozen=True)
class SearchEntryDraft:
    """Сырые значения одной точки поиска: триггеры + что вскрывается (текст и ассеты)."""

    triggers: SynonymSetDraft
    reveal_text: str = ""
    reveal_assets: tuple[str, ...] = ()


@dataclass(frozen=True)
class SearchDraft:
    """Сырые значения поиска этапа: набор точек вскрытия + флаг необязательности."""

    entries: tuple[SearchEntryDraft, ...] = ()
    optional: bool = False


@dataclass(frozen=True)
class BranchOptionDraft:
    """Сырые значения одной опции развилки: подпись + флаг верного выбора."""

    label: str
    is_correct: bool = False


@dataclass(frozen=True)
class BranchDraft:
    """Сырые значения точки ветвления: формулировка + опции выбора."""

    prompt: str = ""
    options: tuple[BranchOptionDraft, ...] = ()


@dataclass(frozen=True)
class FieldDraft:
    """Сырые значения поля документа из UI.

    Числовые параметры (``number_*``) — сырые строки из полей ввода; парсинг и валидация —
    в ``_build_field``. Заполнены только параметры, относящиеся к ``field_type``.
    """

    label: str
    field_type: str
    required: bool = True
    keywords: SynonymSetDraft = SynonymSetDraft("")
    number_value: str = ""
    number_tolerance: str = ""
    number_ndigits: str = ""
    date_value: str = ""
    choice_options: tuple[str, ...] = ()
    choice_correct: tuple[str, ...] = ()


@dataclass(frozen=True)
class TemplateDraft:
    """Сырые значения шаблона документа: заголовок + поля."""

    title: str = ""
    fields: tuple[FieldDraft, ...] = ()


@dataclass(frozen=True)
class DocumentOptionDraft:
    """Сырые значения варианта выбора документа. Шаблон используется только при ``is_correct``."""

    title: str = ""
    is_correct: bool = False
    template: TemplateDraft = TemplateDraft()


@dataclass(frozen=True)
class DocumentTaskDraft:
    """Сырые значения задания выбрать документ: формулировка + варианты (с обманками)."""

    prompt: str = ""
    options: tuple[DocumentOptionDraft, ...] = ()


@dataclass(frozen=True)
class ClinicalDraft:
    """Сырые значения этапа «Клинический»: вступление, поиск, развилка, документы."""

    intro: str = ""
    search: SearchDraft = SearchDraft()
    branch: BranchDraft = BranchDraft()
    documents: tuple[DocumentTaskDraft, ...] = ()


@dataclass(frozen=True)
class InspectionDraft:
    """Сырые значения сверки осмотра: ожидаемые группы синонимов (этапы 3/4)."""

    groups: tuple[SynonymSetDraft, ...] = ()


@dataclass(frozen=True)
class ContactsDraft:
    """Сырые значения этапа «Обследование контактных лиц»: вступление, схема, осмотр."""

    intro: str = ""
    scheme: str = ""
    inspection: InspectionDraft = InspectionDraft()


@dataclass(frozen=True)
class EnvironmentDraft:
    """Сырые значения этапа «Объекты внешней среды»: схема, фото, документы, осмотр."""

    intro: str = ""
    scheme: str = ""
    photos: tuple[str, ...] = ()
    documents: tuple[DocumentTaskDraft, ...] = ()
    inspection: InspectionDraft = InspectionDraft()


@dataclass(frozen=True)
class CaseDraft:
    """Сырые значения кейса из UI (этот срез: мета + пациенты + этапы 2–4)."""

    case_id: str
    title: str = ""
    author: str = ""
    nosology: str = ""
    unit_personnel: int | None = None
    patients: tuple[PatientDraft, ...] = ()
    clinical: ClinicalDraft | None = None
    contacts: ContactsDraft | None = None
    environment: EnvironmentDraft | None = None


def _build_search(draft: SearchDraft) -> KeywordSearch | None:
    """Собрать ``KeywordSearch`` из ``SearchDraft`` (или ``None``, если поиск не задан).

    Записи с пустым каноническим термином (после ``strip``) отбрасываются. Если валидных
    записей не осталось И поиск не помечен необязательным — возвращается ``None`` (этапа
    поиска нет). Иначе — ``KeywordSearch`` со сквозной нумерацией ``entry-<i>`` от 1.
    """
    entries: list[SearchEntry] = []
    for entry in draft.entries:
        if not entry.triggers.canonical.strip():
            continue
        entries.append(
            SearchEntry(
                id=f"entry-{len(entries) + 1}",
                triggers=SynonymSet(
                    canonical=entry.triggers.canonical,
                    synonyms=entry.triggers.synonyms,
                ),
                reveal_text=entry.reveal_text,
                reveal_assets=entry.reveal_assets,
            )
        )
    if not entries and not draft.optional:
        return None
    return KeywordSearch(entries=tuple(entries), optional=draft.optional)


def _build_branch(draft: BranchDraft) -> BranchPoint | None:
    """Собрать ``BranchPoint`` из ``BranchDraft`` (или ``None``, если развилка не задана).

    Опции с пустой подписью (после ``strip``) отбрасываются. Если формулировка пуста И
    валидных опций нет — возвращается ``None``. Иначе — ``BranchPoint`` с фиксированным id
    ``branch`` и сквозной нумерацией опций ``opt-<i>`` от 1.
    """
    options: list[BranchOption] = []
    for option in draft.options:
        if not option.label.strip():
            continue
        options.append(
            BranchOption(
                id=f"opt-{len(options) + 1}",
                label=option.label,
                is_correct=option.is_correct,
            )
        )
    if not draft.prompt.strip() and not options:
        return None
    return BranchPoint(id="branch", prompt=draft.prompt, options=tuple(options))


def _parse_number(raw: str, label: str) -> float:
    """Распарсить число из строки UI (запятая допустима как разделитель).

    Пустая или непарсящаяся строка → ``ValueError`` с именем поля.
    """
    try:
        return float(raw.strip().replace(",", "."))
    except ValueError:
        raise ValueError(f"поле {label!r}: некорректное число") from None


def _parse_ndigits(raw: str, label: str) -> int | None:
    """Распарсить число знаков округления: пустая строка → ``None``, мусор → ``ValueError``."""
    text = raw.strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        raise ValueError(f"поле {label!r}: некорректное число знаков") from None


def _build_field(draft: FieldDraft, i: int) -> DocumentField:
    """Собрать ``DocumentField`` из ``FieldDraft`` с правилом сверки по ``field_type``.

    Неизвестный ``field_type`` и некорректные числовые параметры → ``ValueError``.
    """
    field_type = FieldType(draft.field_type)
    rule: MatchRule
    if field_type is FieldType.TEXT:
        rule = TextMatch(
            keywords=SynonymSet(
                canonical=draft.keywords.canonical,
                synonyms=draft.keywords.synonyms,
            )
        )
    elif field_type is FieldType.NUMBER:
        tolerance = (
            _parse_number(draft.number_tolerance, draft.label)
            if draft.number_tolerance.strip()
            else 0.0
        )
        rule = NumberMatch(
            value=_parse_number(draft.number_value, draft.label),
            tolerance=tolerance,
            ndigits=_parse_ndigits(draft.number_ndigits, draft.label),
        )
    elif field_type is FieldType.DATE:
        rule = DateMatch(value=draft.date_value)
    else:
        rule = ChoiceMatch(correct=draft.choice_correct)
    return DocumentField(
        id=f"field-{i}",
        type=field_type,
        rule=rule,
        label=draft.label,
        options=draft.choice_options if field_type is FieldType.CHOICE else (),
        required=draft.required,
    )


def _build_documents(
    drafts: tuple[DocumentTaskDraft, ...],
) -> tuple[DocumentTask, ...]:
    """Собрать задания по документам из драфтов.

    Варианты с пустым заголовком (после ``strip``) отбрасываются; задания с пустой
    формулировкой И нулём валидных вариантов — тоже. Нумерация сквозная от 1: задания
    ``doc-<i>``, варианты ``opt-<j>``, шаблон верного варианта ``tmpl-<j>``, поля
    ``field-<i>``. Шаблон собирается только для верного варианта; у обманки ``template=None``.
    """
    tasks: list[DocumentTask] = []
    for task in drafts:
        options: list[DocumentOption] = []
        for option in task.options:
            if not option.title.strip():
                continue
            j = len(options) + 1
            template = (
                DocumentTemplate(
                    id=f"tmpl-{j}",
                    title=option.template.title,
                    fields=tuple(
                        _build_field(field, i + 1)
                        for i, field in enumerate(option.template.fields)
                    ),
                )
                if option.is_correct
                else None
            )
            options.append(
                DocumentOption(
                    id=f"opt-{j}",
                    title=option.title,
                    is_correct=option.is_correct,
                    template=template,
                )
            )
        if not task.prompt.strip() and not options:
            continue
        tasks.append(
            DocumentTask(
                id=f"doc-{len(tasks) + 1}",
                prompt=task.prompt,
                options=tuple(options),
            )
        )
    return tuple(tasks)


def build_clinical(draft: ClinicalDraft) -> StageClinical:
    """Собрать этап «Клинико-эпидемиологический диагноз» из ``ClinicalDraft``."""
    return StageClinical(
        intro=draft.intro,
        search=_build_search(draft.search),
        branch=_build_branch(draft.branch),
        documents=_build_documents(draft.documents),
    )


def _build_inspection(draft: InspectionDraft) -> InspectionCheck | None:
    """Собрать ``InspectionCheck`` из ``InspectionDraft`` (или ``None``, если групп нет).

    Группы с пустым каноническим термином (после ``strip``) отбрасываются. Если валидных
    групп не осталось — возвращается ``None`` (сверки осмотра нет).
    """
    groups = [
        SynonymSet(canonical=group.canonical, synonyms=group.synonyms)
        for group in draft.groups
        if group.canonical.strip()
    ]
    if not groups:
        return None
    return InspectionCheck(expected=tuple(groups))


def build_contacts(draft: ContactsDraft) -> StageContacts:
    """Собрать этап «Обследование контактных лиц» из ``ContactsDraft``."""
    return StageContacts(
        intro=draft.intro,
        scheme=draft.scheme.strip() or None,
        inspection=_build_inspection(draft.inspection),
    )


def build_environment(draft: EnvironmentDraft) -> StageEnvironment:
    """Собрать этап «Обследование объектов внешней среды» из ``EnvironmentDraft``."""
    photos = tuple(p.strip() for p in draft.photos if p.strip())
    return StageEnvironment(
        intro=draft.intro,
        scheme=draft.scheme.strip() or None,
        photos=photos,
        documents=_build_documents(draft.documents),
        inspection=_build_inspection(draft.inspection),
    )


def build_case(draft: CaseDraft) -> Case:
    """Собрать доменный ``Case`` из ``CaseDraft``.

    Валидируется только обязательный непустой идентификатор кейса. Этот срез трогает мету,
    этап «Пациенты» и этапы 2–4; остальные этапы — дефолтные пустые. Чистая функция без I/O.
    """
    case_id = draft.case_id.strip()
    if not case_id:
        raise ValueError("нужен идентификатор кейса")

    meta = CaseMeta(
        id=case_id,
        title=draft.title,
        author=draft.author,
        nosology=draft.nosology,
        unit_personnel=draft.unit_personnel,
        created_at=date.today().isoformat(),
    )
    patients = StagePatients(
        patients=tuple(
            PatientCard(id=p.id, title=p.title, fields=p.fields, assets=p.assets)
            for p in draft.patients
        )
    )
    clinical = (
        build_clinical(draft.clinical)
        if draft.clinical is not None
        else StageClinical()
    )
    contacts = (
        build_contacts(draft.contacts)
        if draft.contacts is not None
        else StageContacts()
    )
    environment = (
        build_environment(draft.environment)
        if draft.environment is not None
        else StageEnvironment()
    )
    return Case(
        meta=meta,
        patients=patients,
        clinical=clinical,
        contacts=contacts,
        environment=environment,
    )


__all__ = [
    "BranchDraft",
    "BranchOptionDraft",
    "CaseDraft",
    "ClinicalDraft",
    "ContactsDraft",
    "DocumentOptionDraft",
    "DocumentTaskDraft",
    "EnvironmentDraft",
    "FieldDraft",
    "InspectionDraft",
    "PatientDraft",
    "SearchDraft",
    "SearchEntryDraft",
    "SynonymSetDraft",
    "TemplateDraft",
    "build_case",
    "build_clinical",
    "build_contacts",
    "build_environment",
]
