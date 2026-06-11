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
    KeywordSearch,
    PatientCard,
    SearchEntry,
    StageClinical,
    StagePatients,
    SynonymSet,
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
class ClinicalDraft:
    """Сырые значения этапа «Клинико-эпидемиологический диагноз»: вступление, поиск, развилка."""

    intro: str = ""
    search: SearchDraft = SearchDraft()
    branch: BranchDraft = BranchDraft()


@dataclass(frozen=True)
class CaseDraft:
    """Сырые значения кейса из UI (этот срез: мета + пациенты + этап «Клинический»)."""

    case_id: str
    title: str = ""
    author: str = ""
    nosology: str = ""
    unit_personnel: int | None = None
    patients: tuple[PatientDraft, ...] = ()
    clinical: ClinicalDraft | None = None


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


def build_clinical(draft: ClinicalDraft) -> StageClinical:
    """Собрать этап «Клинико-эпидемиологический диагноз» из ``ClinicalDraft``.

    Документы (``documents``) в этом срезе пусты — их заполняет отдельный заход.
    """
    return StageClinical(
        intro=draft.intro,
        search=_build_search(draft.search),
        branch=_build_branch(draft.branch),
        documents=(),
    )


def build_case(draft: CaseDraft) -> Case:
    """Собрать доменный ``Case`` из ``CaseDraft``.

    Валидируется только обязательный непустой идентификатор кейса. Этот срез трогает мету,
    этап «Пациенты» и этап «Клинический»; остальные этапы — дефолтные пустые. Чистая
    функция без I/O.
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
    return Case(meta=meta, patients=patients, clinical=clinical)


__all__ = [
    "BranchDraft",
    "BranchOptionDraft",
    "CaseDraft",
    "ClinicalDraft",
    "PatientDraft",
    "SearchDraft",
    "SearchEntryDraft",
    "SynonymSetDraft",
    "build_case",
    "build_clinical",
]
