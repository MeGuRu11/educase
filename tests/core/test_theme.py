"""Тесты загрузчика темы: ресурс читается и содержит ключевые селекторы."""
from __future__ import annotations

import re

from epicase_core.theme import load_qss


def test_load_qss_returns_nonempty_string() -> None:
    qss = load_qss()
    assert isinstance(qss, str)
    assert qss.strip()


def test_load_qss_contains_key_selectors() -> None:
    qss = load_qss()
    assert "QGroupBox" in qss
    assert ":disabled" in qss
    assert "QPushButton" in qss
    assert "#criticalToggle" in qss
    assert ":focus" in qss
    assert "QHeaderView::section" in qss


def test_load_qss_contains_patient_medical_card_selectors() -> None:
    qss = load_qss()
    required_selectors = (
        "QFrame#patientCard",
        "QFrame#patientCard:hover",
        "QFrame#patientCard:focus",
        "QFrame#patientCardMarker",
        "QLabel#patientCardTitle",
        "QFrame#patientDetailHeader",
        "QLabel#patientFieldName",
        "QPushButton#patientDetailClose",
    )
    for selector in required_selectors:
        pattern = rf"{re.escape(selector)}\s*\{{"
        assert re.search(pattern, qss) is not None
