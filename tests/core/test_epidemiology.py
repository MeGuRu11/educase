"""Тесты расчётов заболеваемости (Прил.23) и классификации СЭС (Прил.22).

Показатели — чистые функции; на некорректном входе конструктора кейса падаем ``ValueError``
(это параметры преподавателя, не ответы курсанта).
"""
from __future__ import annotations

import pytest

from epicase_core.domain import (
    SesLevel,
    classify_ses,
    extensive_indicator,
    intensive_indicator,
    intensive_indicator_period,
)

# --- Прил.23: интенсивный/экстенсивный показатели ---------------------------------------


def test_intensive_indicator_per_year() -> None:
    assert intensive_indicator(36, 1000) == 36.0


def test_intensive_indicator_custom_base() -> None:
    assert intensive_indicator(36, 1000, base=100000) == 3600.0


def test_intensive_indicator_zero_population_raises() -> None:
    with pytest.raises(ValueError):
        intensive_indicator(36, 0)


def test_intensive_indicator_negative_cases_raises() -> None:
    with pytest.raises(ValueError):
        intensive_indicator(-1, 1000)


def test_intensive_indicator_period_annualizes() -> None:
    # 5 случаев за 50 суток среди 140 человек → годовая оценка на 1000.
    result = intensive_indicator_period(5, 140, 50)
    assert result == pytest.approx(5 * 365 * 1000 / (140 * 50))
    assert result == pytest.approx(260.714285, abs=1e-5)


def test_intensive_indicator_period_zero_days_raises() -> None:
    with pytest.raises(ValueError):
        intensive_indicator_period(5, 140, 0)


def test_extensive_indicator_share_percent() -> None:
    assert extensive_indicator(30, 120) == 25.0


def test_extensive_indicator_zero_total_raises() -> None:
    with pytest.raises(ValueError):
        extensive_indicator(30, 0)


# --- Прил.22: классификация СЭС ---------------------------------------------------------


def test_classify_ses_all_clean_is_well() -> None:
    assert classify_ses(0.0) is SesLevel.WELL


def test_classify_ses_morbidity_unstable() -> None:
    assert classify_ses(15.0) is SesLevel.UNSTABLE


def test_classify_ses_one_death_unstable() -> None:
    assert classify_ses(0.0, deaths=1) is SesLevel.UNSTABLE


def test_classify_ses_single_ooi_troubled() -> None:
    assert classify_ses(0.0, single_ooi=True) is SesLevel.TROUBLED


def test_classify_ses_high_morbidity_emergency() -> None:
    assert classify_ses(50.0) is SesLevel.EMERGENCY


def test_classify_ses_repeated_ooi_emergency() -> None:
    assert classify_ses(0.0, repeated_ooi=True) is SesLevel.EMERGENCY


def test_classify_ses_most_severe_axis_wins() -> None:
    # Низкая заболеваемость (неустойчивое), но 3 смерти (чрезвычайное) → максимум побеждает.
    assert classify_ses(2.0, deaths=3) is SesLevel.EMERGENCY


def test_classify_ses_diagnosed_cases_blocks_well() -> None:
    # Заболеваемость благополучная, но больных с диагнозом > 2 → минимум неустойчивое.
    assert classify_ses(0.0, diagnosed_cases=5) is SesLevel.UNSTABLE


def test_classify_ses_unsanitary_blocks_well() -> None:
    assert classify_ses(0.0, sanitary_ok=False) is SesLevel.UNSTABLE


def test_classify_ses_negative_morbidity_raises() -> None:
    with pytest.raises(ValueError):
        classify_ses(-1.0)


def test_classify_ses_boundary_one_is_well() -> None:
    assert classify_ses(1.0) is SesLevel.WELL


def test_classify_ses_boundary_twenty_is_unstable() -> None:
    assert classify_ses(20.0) is SesLevel.UNSTABLE


def test_classify_ses_boundary_forty_is_troubled() -> None:
    assert classify_ses(40.0) is SesLevel.TROUBLED
