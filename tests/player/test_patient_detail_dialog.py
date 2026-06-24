"""Тесты PatientDetailDialog: сборка без ошибок, отображение полей."""
from __future__ import annotations

from PySide6.QtWidgets import QLabel
from pytestqt.qtbot import QtBot

from epicase_core.domain.stages import PatientCard
from epicase_player.ui.patient_detail_dialog import PatientDetailDialog


def _card(*fields: tuple[str, str]) -> PatientCard:
    return PatientCard(id="p1", title="Иванов И.И.", fields=fields)


def test_builds_without_error(qtbot: QtBot) -> None:
    """Диалог строится с пустыми assets без исключений."""
    dlg = PatientDetailDialog(_card(("Диагноз", "грипп")), assets={})
    qtbot.addWidget(dlg)


def test_fields_shown_in_dialog(qtbot: QtBot) -> None:
    """Поля карты присутствуют среди дочерних QLabel."""
    card = _card(("Диагноз", "сальмонеллёз"), ("Возраст", "30 лет"))
    dlg = PatientDetailDialog(card, assets={})
    qtbot.addWidget(dlg)

    texts = [lbl.text() for lbl in dlg.findChildren(QLabel)]
    assert any("Диагноз: сальмонеллёз" in t for t in texts)
    assert any("Возраст: 30 лет" in t for t in texts)


def test_missing_asset_shows_placeholder(qtbot: QtBot) -> None:
    """Ассет, отсутствующий в assets, не роняет диалог — показывает заглушку."""
    card = PatientCard(id="p2", title="Петров", fields=(), assets=("photo_01",))
    dlg = PatientDetailDialog(card, assets={})
    qtbot.addWidget(dlg)

    texts = [lbl.text() for lbl in dlg.findChildren(QLabel)]
    assert any("недоступно" in t for t in texts)
