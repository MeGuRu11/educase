"""Сборка доменного ``Case`` из «сырых» значений UI (этот срез: мета + этап «Пациенты»).

UI собирает значения виджетов в простые ``*Draft``-структуры, а доменные тонкости
(неизменяемость, конструирование этапов) живут здесь. Чистые функции без I/O — обратная
сторона (из ``Case`` в ``CaseDraft`` для будущего редактирования) пока не реализуется.
"""
from __future__ import annotations

import uuid
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
    Hotspot,
    HotspotShape,
    InspectionCheck,
    KeywordSearch,
    MatchRule,
    NumberMatch,
    PatientCard,
    SchemeDocument,
    SchemeView,
    SearchEntry,
    StageClinical,
    StageContacts,
    StageEnvironment,
    StageFinal,
    StagePatients,
    StageSes,
    SynonymSet,
    TextMatch,
    Timeline,
)


@dataclass(frozen=True)
class AssetRef:
    """Ссылка на ассет из UI (Вариант B): стабильный id + исходный путь + имя для показа.

    ``asset_id`` — стабильное имя ассета внутри архива (генерирует пикер). ``source_path`` —
    путь к исходному файлу на диске, по которому читаются байты (только в ``assets.py``, не в
    чистой сборке). ``display_name`` — исходное имя файла, используется лишь для отображения.
    """

    asset_id: str
    source_path: str
    display_name: str = ""


@dataclass(frozen=True)
class PatientDraft:
    """Сырые значения одной карточки пациента из UI.

    Технический ``id`` карточки не вводится преподавателем (пациенты не оцениваются, ссылок
    по id нет) — его генерирует ``build_case``.
    """

    title: str
    fields: tuple[tuple[str, str], ...] = ()
    assets: tuple[AssetRef, ...] = ()


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
    reveal_assets: tuple[AssetRef, ...] = ()


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
class HotspotDraft:
    """Сырые значения одной зоны схемы из UI: прямоугольник + подпись + вскрываемое + вложенный вид.

    Геометрия в долях [0..1] (левый верх ``x``, ``y`` и размеры ``w``, ``h``), подпись,
    вскрываемый текст и прикреплённые фото (``reveal_assets``). ``child`` — опциональный
    вложенный интерьерный вид зоны (свой фон + свои зоны, рекурсивно); ``None`` у плоской зоны
    (существующий плоский авторинг этого поля не задаёт). Иконку домен (``Hotspot``) получает
    по умолчанию через ``_build_hotspots``.
    """

    x: float
    y: float
    w: float
    h: float
    label: str = ""
    reveal_text: str = ""
    reveal_assets: tuple[AssetRef, ...] = ()
    child: SchemeViewDraft | None = None


@dataclass(frozen=True)
class SchemeViewDraft:
    """Сырые значения одного уровня вложенного вида схемы из UI: свой фон + свои зоны.

    ``background`` — ассет фонового изображения вложенного вида (``None``, если фон не выбран —
    тогда вид недостижим и билдер его отбрасывает). ``caption`` — подпись уровня. ``hotspots`` —
    зоны поверх фона; рекурсия общая — каждая такая зона тоже может иметь свой ``child`` (потолок
    глубины здесь не вводится — его задаёт UI R2.1-B).
    """

    background: AssetRef | None = None
    caption: str = ""
    hotspots: tuple[HotspotDraft, ...] = ()


@dataclass(frozen=True)
class ContactsDraft:
    """Сырые значения этапа «Обследование контактных лиц»: вступление, схема, зоны, осмотр."""

    intro: str = ""
    scheme: AssetRef | None = None
    hotspots: tuple[HotspotDraft, ...] = ()
    inspection: InspectionDraft = InspectionDraft()


@dataclass(frozen=True)
class EnvironmentDraft:
    """Сырые значения этапа «Объекты внешней среды»: схема, зоны, фото, документы, осмотр."""

    intro: str = ""
    scheme: AssetRef | None = None
    hotspots: tuple[HotspotDraft, ...] = ()
    photos: tuple[AssetRef, ...] = ()
    documents: tuple[DocumentTaskDraft, ...] = ()
    inspection: InspectionDraft = InspectionDraft()


@dataclass(frozen=True)
class TimelineDraft:
    """Сырые значения таймлайна: заголовок + события (пары «дата → событие»)."""

    title: str = ""
    events: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class SesDraft:
    """Сырые значения этапа «Оценка СЭС»: вступление, поиск, выбор уровня, документы."""

    intro: str = ""
    search: SearchDraft = SearchDraft()
    level_choice: FieldDraft | None = None
    documents: tuple[DocumentTaskDraft, ...] = ()


@dataclass(frozen=True)
class FinalDraft:
    """Сырые значения этапа «Окончательный диагноз»: поиск, документы, таймлайны."""

    intro: str = ""
    search: SearchDraft = SearchDraft()
    documents: tuple[DocumentTaskDraft, ...] = ()
    timelines: tuple[TimelineDraft, ...] = ()


@dataclass(frozen=True)
class CaseDraft:
    """Сырые значения кейса из UI (полный кейс: мета + пациенты + этапы 2–6)."""

    case_id: str
    title: str = ""
    author: str = ""
    nosology: str = ""
    unit_personnel: int | None = None
    patients: tuple[PatientDraft, ...] = ()
    clinical: ClinicalDraft | None = None
    contacts: ContactsDraft | None = None
    environment: EnvironmentDraft | None = None
    ses: SesDraft | None = None
    final: FinalDraft | None = None


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
                reveal_assets=tuple(ref.asset_id for ref in entry.reveal_assets),
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
    """Распарсить число знаков округления: пустая строка → ``None``, мусор → ``ValueError``.

    Отрицательное число знаков запрещено (округление до десятков/сотен — не задумано).
    """
    text = raw.strip()
    if not text:
        return None
    try:
        value = int(text)
    except ValueError:
        raise ValueError(f"поле {label!r}: некорректное число знаков") from None
    if value < 0:
        raise ValueError(f"поле {label!r}: число знаков не может быть отрицательным")
    return value


def _field_is_blank(draft: FieldDraft) -> bool:
    """Поле пусто, если нет подписи (после ``strip``) И нет значения правила по его типу.

    Значение правила по типу: TEXT → ``keywords.canonical``; NUMBER → ``number_value``;
    DATE → ``date_value``; CHOICE → ``choice_correct``. Для неизвестного ``field_type`` поле
    НЕ считается пустым (его соберёт ``_build_field`` со своей диагностикой). Используется для
    коллапса пустого выбора уровня (``_build_level``) и отбрасывания пустых полей шаблона
    (``_build_documents``).
    """
    if draft.label.strip():
        return False
    try:
        field_type = FieldType(draft.field_type)
    except ValueError:
        return False
    if field_type is FieldType.TEXT:
        return not draft.keywords.canonical.strip()
    if field_type is FieldType.NUMBER:
        return not draft.number_value.strip()
    if field_type is FieldType.DATE:
        return not draft.date_value.strip()
    return not draft.choice_correct


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
    формулировкой И нулём валидных вариантов — тоже. Пустые поля шаблона
    (``_field_is_blank``) отбрасываются ДО нумерации, чтобы id ``field-<i>`` шли без дыр по
    оставшимся полям. Нумерация сквозная от 1: задания ``doc-<i>``, варианты ``opt-<j>``,
    шаблон верного варианта ``tmpl-<j>``, поля ``field-<i>``. Шаблон собирается только для
    верного варианта; у обманки ``template=None``.
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
                        for i, field in enumerate(
                            f for f in option.template.fields if not _field_is_blank(f)
                        )
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


def _build_scheme_view(draft: SchemeViewDraft) -> SchemeView | None:
    """Собрать вложенный доменный ``SchemeView`` из ``SchemeViewDraft`` (или ``None`` без фона).

    Вид без фона недостижим — отбрасывается в ``None`` (та же логика, что роняет схему верхнего
    уровня без фона в ``build_contacts``/``build_environment``). Иначе фон сворачивается в
    ``asset_id``, ``caption`` копируется, а зоны собираются рекурсивно через ``_build_hotspots``
    (каждый уровень нумерует свои ``hotspot-<i>`` независимо с 1).
    """
    if draft.background is None:
        return None
    return SchemeView(
        background=draft.background.asset_id,
        caption=draft.caption,
        hotspots=_build_hotspots(draft.hotspots),
    )


def _build_hotspots(drafts: tuple[HotspotDraft, ...]) -> tuple[Hotspot, ...]:
    """Собрать доменные ``Hotspot`` из ``HotspotDraft`` со сквозными id (рекурсивно по ``child``).

    Геометрия копируется в ``HotspotShape`` (доли [0..1]); ``reveal_assets`` сворачиваются в
    кортеж ``asset_id`` (как в ``_build_search``). ``child`` собирается тем же
    ``_build_scheme_view`` (общая рекурсия); вложенный вид без фона схлопывается в ``None``.
    ``icon`` остаётся дефолтным. Нумерация сквозная в пределах ОДНОГО вида: ``hotspot-<i>`` от 1
    (каждый вложенный вид нумерует свои зоны независимо — id уникален лишь в своём ``SchemeView``).
    """
    spots: list[Hotspot] = []
    for d in drafts:
        child = _build_scheme_view(d.child) if d.child is not None else None
        spots.append(
            Hotspot(
                id=f"hotspot-{len(spots) + 1}",
                shape=HotspotShape(x=d.x, y=d.y, w=d.w, h=d.h),
                label=d.label,
                reveal_text=d.reveal_text,
                reveal_assets=tuple(ref.asset_id for ref in d.reveal_assets),
                child=child,
            )
        )
    return tuple(spots)


def build_contacts(draft: ContactsDraft) -> StageContacts:
    """Собрать этап «Обследование контактных лиц» из ``ContactsDraft``.

    Зоны (``hotspots``) пакуются в ``SchemeView`` только при заданном фоне; без фона схема —
    ``None`` и зоны игнорируются (зона без фона недостижима).
    """
    return StageContacts(
        intro=draft.intro,
        scheme=(
            SchemeDocument(
                root=SchemeView(
                    background=draft.scheme.asset_id,
                    hotspots=_build_hotspots(draft.hotspots),
                )
            )
            if draft.scheme is not None
            else None
        ),
        inspection=_build_inspection(draft.inspection),
    )


def build_environment(draft: EnvironmentDraft) -> StageEnvironment:
    """Собрать этап «Обследование объектов внешней среды» из ``EnvironmentDraft``.

    Зоны (``hotspots``) пакуются в ``SchemeView`` только при заданном фоне; без фона схема —
    ``None`` и зоны игнорируются. ``photos``/``documents``/``inspection`` — как раньше.
    """
    photos = tuple(ref.asset_id for ref in draft.photos)
    return StageEnvironment(
        intro=draft.intro,
        scheme=(
            SchemeDocument(
                root=SchemeView(
                    background=draft.scheme.asset_id,
                    hotspots=_build_hotspots(draft.hotspots),
                )
            )
            if draft.scheme is not None
            else None
        ),
        photos=photos,
        documents=_build_documents(draft.documents),
        inspection=_build_inspection(draft.inspection),
    )


def _build_level(draft: FieldDraft | None) -> DocumentField | None:
    """Собрать поле выбора уровня СЭС из ``FieldDraft`` (или ``None``, если он не задан).

    Единичное поле с фиксированным id ``field-1``; правило сверки выбирает ``_build_field``.
    Пустое поле (``_field_is_blank``) тоже коллапсирует в ``None``: иначе включённый флаг при
    незаполненном поле создал бы обязательное поле с невыполнимым правилом.
    """
    if draft is None or _field_is_blank(draft):
        return None
    return _build_field(draft, 1)


def _build_timelines(drafts: tuple[TimelineDraft, ...]) -> tuple[Timeline, ...]:
    """Собрать таймлайны из драфтов.

    Таймлайны с пустым заголовком (после ``strip``) И нулём событий отбрасываются. Остальным
    присваивается сквозной id ``tl-<i>`` от 1.
    """
    timelines: list[Timeline] = []
    for tl in drafts:
        if not tl.title.strip() and not tl.events:
            continue
        timelines.append(
            Timeline(id=f"tl-{len(timelines) + 1}", title=tl.title, events=tl.events)
        )
    return tuple(timelines)


def build_ses(draft: SesDraft) -> StageSes:
    """Собрать этап «Оценка СЭС» из ``SesDraft``."""
    return StageSes(
        intro=draft.intro,
        search=_build_search(draft.search),
        level_choice=_build_level(draft.level_choice),
        documents=_build_documents(draft.documents),
    )


def build_final(draft: FinalDraft) -> StageFinal:
    """Собрать этап «Окончательный эпидемиологический диагноз» из ``FinalDraft``."""
    return StageFinal(
        intro=draft.intro,
        search=_build_search(draft.search),
        documents=_build_documents(draft.documents),
        timelines=_build_timelines(draft.timelines),
    )


def build_case(draft: CaseDraft) -> Case:
    """Собрать доменный ``Case`` из ``CaseDraft``.

    Идентификатор кейса служебный и преподавателем не вводится: непустой ``case_id`` из драфта
    используется как есть (стабильность в пределах сессии редактирования обеспечивает UI),
    пустой — автогенерируется. Этот срез собирает мету, этап «Пациенты» и этапы 2–6. Чистая
    функция без I/O.
    """
    case_id = draft.case_id.strip() or uuid.uuid4().hex

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
            PatientCard(
                id=uuid.uuid4().hex,
                title=p.title,
                fields=p.fields,
                assets=tuple(ref.asset_id for ref in p.assets),
            )
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
    ses = build_ses(draft.ses) if draft.ses is not None else StageSes()
    final = build_final(draft.final) if draft.final is not None else StageFinal()
    return Case(
        meta=meta,
        patients=patients,
        clinical=clinical,
        contacts=contacts,
        environment=environment,
        ses=ses,
        final=final,
    )


__all__ = [
    "AssetRef",
    "BranchDraft",
    "BranchOptionDraft",
    "CaseDraft",
    "ClinicalDraft",
    "ContactsDraft",
    "DocumentOptionDraft",
    "DocumentTaskDraft",
    "EnvironmentDraft",
    "FieldDraft",
    "FinalDraft",
    "HotspotDraft",
    "InspectionDraft",
    "PatientDraft",
    "SchemeViewDraft",
    "SearchDraft",
    "SearchEntryDraft",
    "SesDraft",
    "SynonymSetDraft",
    "TemplateDraft",
    "TimelineDraft",
    "build_case",
    "build_clinical",
    "build_contacts",
    "build_environment",
    "build_final",
    "build_ses",
]
