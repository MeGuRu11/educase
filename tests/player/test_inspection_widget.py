"""Тесты InspectionWidget: свободный осмотр, покрытие, нейтральное сообщение."""
from __future__ import annotations

from PySide6.QtWidgets import QLabel
from pytestqt.qtbot import QtBot

from epicase_core.domain.search import InspectionCheck, SynonymSet
from epicase_player.ui.inspection_widget import InspectionWidget


def _make_inspection() -> InspectionCheck:
    return InspectionCheck(
        expected=(
            SynonymSet(canonical="вода", synonyms=("водопровод",)),
            SynonymSet(canonical="туалет"),
        )
    )


def test_text_with_all_keys_covered(qtbot: QtBot) -> None:
    """Текст со всеми ожидаемыми ключами → все covered True."""
    w = InspectionWidget(_make_inspection())
    qtbot.addWidget(w)
    w.output.setPlainText("Осмотрен водопровод и туалет")
    w.btn_submit.click()

    result = w.result
    assert result is not None
    assert result.covered == (True, True)


def test_empty_text_all_false(qtbot: QtBot) -> None:
    """Пустой ввод → все covered False."""
    w = InspectionWidget(_make_inspection())
    qtbot.addWidget(w)
    w.output.setPlainText("")
    w.btn_submit.click()

    result = w.result
    assert result is not None
    assert all(not c for c in result.covered)


def test_partial_coverage(qtbot: QtBot) -> None:
    """Только один ключ найден → соответствующая позиция True, остальные False."""
    w = InspectionWidget(_make_inspection())
    qtbot.addWidget(w)
    w.output.setPlainText("Осмотрена вода")
    w.btn_submit.click()

    result = w.result
    assert result is not None
    assert result.covered[0] is True
    assert result.covered[1] is False


def test_result_none_before_submit(qtbot: QtBot) -> None:
    """result is None до первого нажатия «Сохранить»."""
    w = InspectionWidget(_make_inspection())
    qtbot.addWidget(w)
    assert w.result is None


def test_expected_keys_not_visible_in_ui(qtbot: QtBot) -> None:
    """Ожидаемые ключи («вода», «туалет») не видны в UI (ADR-005)."""
    w = InspectionWidget(_make_inspection())
    qtbot.addWidget(w)

    all_text = " ".join(lbl.text() for lbl in w.findChildren(QLabel))
    assert "вода" not in all_text
    assert "туалет" not in all_text


def test_neutral_message_after_submit(qtbot: QtBot) -> None:
    """После on_submit отображается нейтральное «Сохранено» (ADR-005)."""
    w = InspectionWidget(_make_inspection())
    qtbot.addWidget(w)
    w.btn_submit.click()

    texts = [lbl.text() for lbl in w.findChildren(QLabel)]
    assert "Сохранено" in texts
