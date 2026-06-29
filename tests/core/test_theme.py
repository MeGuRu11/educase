"""Тесты загрузчика темы: ресурс читается и содержит ключевые селекторы."""
from __future__ import annotations

import re

from epicase_core.theme import load_qss


def _qss_rule_body(qss: str, selector: str) -> str:
    pattern = rf"(?ms)^{re.escape(selector)}\s*\{{(?P<body>.*?)^\}}"
    match = re.search(pattern, qss)
    assert match is not None, f"Missing exact QSS selector: {selector}"
    return match.group("body")


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


def test_load_qss_contains_branded_start_card_contract() -> None:
    qss = load_qss()
    expected_rules = {
        "QFrame#startActionCard": (
            "background: #FFFFFF;",
            "border: 1px solid #D4DAE0;",
            "border-radius: 14px;",
        ),
        "QLabel#startTitle": (
            "font-size: 28px;",
            "font-weight: bold;",
            "color: #1F2A33;",
        ),
        "QLabel#startProduct": (
            "font-size: 11px;",
            "font-weight: bold;",
        ),
        "QLabel#startRole": (
            "font-size: 14px;",
            "color: #66727E;",
        ),
        "QLabel#startHint": (
            "font-size: 12px;",
            "color: #9AA5AF;",
        ),
        "QLabel#startSubtitle": (
            "font-size: 15px;",
            "color: #66727E;",
        ),
        "QWidget#playerStartScreen QLabel#startProduct": ("color: #0F766E;",),
    }

    for selector, declarations in expected_rules.items():
        body = _qss_rule_body(qss, selector)
        for declaration in declarations:
            assert declaration in body

    assert "letter-spacing" not in _qss_rule_body(qss, "QLabel#startProduct")
