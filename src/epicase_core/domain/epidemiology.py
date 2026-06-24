"""Расчёты заболеваемости (Прил.23) и классификация СЭС (Прил.22).

Чистый домен: только stdlib, никаких зависимостей. Показатели — чистые функции над
параметрами кейса (их задаёт конструктор, не курсант), поэтому на некорректном входе здесь
допустимо падать ``ValueError`` (ADR-008 про «ошибка курсанта не блокирует» сюда не относится).

Прил.1 (пороги вспышки по нозологиям) в этот модуль НЕ входит — отдельная таблица.
"""
from __future__ import annotations

from enum import StrEnum


def _require_positive(value: int, name: str) -> None:
    """Параметр-знаменатель должен быть строго > 0, иначе ``ValueError``."""
    if value <= 0:
        raise ValueError(f"{name} должно быть > 0, получено {value}")


def _require_non_negative(value: float, name: str) -> None:
    """Счётчик не может быть отрицательным, иначе ``ValueError``."""
    if value < 0:
        raise ValueError(f"{name} не может быть отрицательным, получено {value}")


def intensive_indicator(cases: int, population: int, *, base: int = 1000) -> float:
    """Интенсивный показатель заболеваемости за полный год: ``cases * base / population``.

    ``base`` — основание показателя (1000 по умолчанию; допустимо 100 или 100000).
    """
    _require_non_negative(cases, "cases")
    _require_positive(population, "population")
    return cases * base / population


def intensive_indicator_period(
    cases: int, population: int, days: int, *, base: int = 1000
) -> float:
    """Годовая оценка интенсивного показателя по периоду в днях.

    ``cases * 365 * base / (population * days)`` — экстраполяция числа случаев за ``days``
    суток на календарный год.
    """
    _require_non_negative(cases, "cases")
    _require_positive(population, "population")
    _require_positive(days, "days")
    return cases * 365 * base / (population * days)


def extensive_indicator(part: int, total: int) -> float:
    """Экстенсивный показатель (доля в %): ``part * 100 / total``."""
    _require_non_negative(part, "part")
    _require_positive(total, "total")
    return part * 100 / total


class SesLevel(StrEnum):
    """Уровень санитарно-эпидемического состояния (Прил.22), по нарастанию тяжести."""

    WELL = "благополучное"
    UNSTABLE = "неустойчивое"
    TROUBLED = "неблагополучное"
    EMERGENCY = "чрезвычайное"

    @property
    def severity(self) -> int:
        """Ранг тяжести по порядку объявления: благополучное=0 … чрезвычайное=3."""
        return _SEVERITY_RANK[self]


_SEVERITY_RANK: dict[SesLevel, int] = {level: rank for rank, level in enumerate(SesLevel)}


def _morbidity_level(morbidity_per_1000: float) -> SesLevel:
    """Уровень по инфекционной заболеваемости за сутки на 1000 л/с."""
    if morbidity_per_1000 <= 1:
        return SesLevel.WELL
    if morbidity_per_1000 <= 20:
        return SesLevel.UNSTABLE
    if morbidity_per_1000 <= 40:
        return SesLevel.TROUBLED
    return SesLevel.EMERGENCY


def _deaths_level(deaths: int) -> SesLevel:
    """Уровень по числу смертей от инфекционных заболеваний."""
    if deaths <= 0:
        return SesLevel.WELL
    if deaths == 1:
        return SesLevel.UNSTABLE
    if deaths == 2:
        return SesLevel.TROUBLED
    return SesLevel.EMERGENCY


def _ooi_level(*, single_ooi: bool, repeated_ooi: bool) -> SesLevel:
    """Уровень по особо опасным инфекциям: повторные → чрезвычайное, единичный → неблагополучное."""
    if repeated_ooi:
        return SesLevel.EMERGENCY
    if single_ooi:
        return SesLevel.TROUBLED
    return SesLevel.WELL


def _sanitation_level(diagnosed_cases: int, *, sanitary_ok: bool) -> SesLevel:
    """Нарушение условий благополучного (диагноз >2 или сан. состояние неудовл.) → неустойчивое."""
    if diagnosed_cases > 2 or not sanitary_ok:
        return SesLevel.UNSTABLE
    return SesLevel.WELL


def classify_ses(
    morbidity_per_1000: float,
    deaths: int = 0,
    diagnosed_cases: int = 0,
    *,
    sanitary_ok: bool = True,
    single_ooi: bool = False,
    repeated_ooi: bool = False,
) -> SesLevel:
    """Классифицировать СЭС по Прил.22 — наиболее тяжёлый уровень по всем осям.

    Оси оцениваются независимо (заболеваемость, смерти, ООИ, санитарное состояние/диагнозы),
    возвращается максимум по тяжести. «Благополучное» возможно только когда все оси
    благополучны одновременно.
    """
    _require_non_negative(morbidity_per_1000, "morbidity_per_1000")
    _require_non_negative(deaths, "deaths")
    _require_non_negative(diagnosed_cases, "diagnosed_cases")

    levels = (
        _morbidity_level(morbidity_per_1000),
        _deaths_level(deaths),
        _ooi_level(single_ooi=single_ooi, repeated_ooi=repeated_ooi),
        _sanitation_level(diagnosed_cases, sanitary_ok=sanitary_ok),
    )
    return max(levels, key=lambda level: level.severity)
