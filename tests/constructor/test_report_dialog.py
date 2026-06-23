"""Тесты диалога отчёта: шапка идентичности курсанта."""
from pytestqt.qtbot import QtBot

from educase_constructor.ui.report_dialog import ReportDialog
from educase_core.domain.report import CaseReport


def test_identity_header_shows_rank_and_group(qtbot: QtBot) -> None:
    """Шапка отчёта показывает ФИО, звание и группу курсанта."""
    dialog = ReportDialog(CaseReport(case_id="c1"), "Иванов И.И.", "лейтенант", "121")
    qtbot.addWidget(dialog)
    text = dialog.identity_label.text()
    assert "Иванов И.И." in text
    assert "лейтенант" in text
    assert "121" in text


def test_identity_header_without_signature(qtbot: QtBot) -> None:
    """Без ФИО шапка показывает «(без подписи)»."""
    dialog = ReportDialog(CaseReport(case_id="c1"))
    qtbot.addWidget(dialog)
    assert "(без подписи)" in dialog.identity_label.text()
