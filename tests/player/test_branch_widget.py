"""Тесты BranchWidget: выбор варианта, сохранение, нейтральное сообщение."""
from __future__ import annotations

from PySide6.QtWidgets import QLabel
from pytestqt.qtbot import QtBot

from epicase_core.domain.stages import BranchOption, BranchPoint
from epicase_player.ui.branch_widget import BranchWidget


def _make_branch() -> BranchPoint:
    return BranchPoint(
        id="bp1",
        prompt="Выберите клинико-эпидемиологический диагноз",
        options=(
            BranchOption(id="opt_correct", label="Сальмонеллёз", is_correct=True),
            BranchOption(id="opt_decoy", label="Грипп", is_correct=False),
        ),
    )


def test_initial_result_is_none(qtbot: QtBot) -> None:
    """До нажатия «Сохранить» result is None."""
    w = BranchWidget(_make_branch())
    qtbot.addWidget(w)
    assert w.result is None


def test_correct_option_submit(qtbot: QtBot) -> None:
    """Выбор верной опции → submit → option_correct True."""
    w = BranchWidget(_make_branch())
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(0)  # "Сальмонеллёз" (correct) — первая реальная опция
    w.btn_submit.click()

    result = w.result
    assert result is not None
    assert result.option_correct is True
    assert result.option_id == "opt_correct"


def test_decoy_option_submit(qtbot: QtBot) -> None:
    """Выбор обманки → submit → option_correct False."""
    w = BranchWidget(_make_branch())
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(1)  # "Грипп" (decoy) — вторая реальная опция
    w.btn_submit.click()

    result = w.result
    assert result is not None
    assert result.option_correct is False
    assert result.option_id == "opt_decoy"


def test_placeholder_submit(qtbot: QtBot) -> None:
    """Плейсхолдер (currentIndex == -1) → submit → option_id None, option_correct False."""
    w = BranchWidget(_make_branch())
    qtbot.addWidget(w)
    assert w.options_combo.currentIndex() == -1
    w.btn_submit.click()

    result = w.result
    assert result is not None
    assert result.option_id is None
    assert result.option_correct is False


def test_neutral_message_no_verdict(qtbot: QtBot) -> None:
    """После submit — «Сохранено», без слов «верно»/«неверно» (ADR-005)."""
    w = BranchWidget(_make_branch())
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(0)
    w.btn_submit.click()

    texts = [lbl.text() for lbl in w.findChildren(QLabel)]
    assert "Сохранено" in texts
    assert not any("верн" in t.lower() or "неверн" in t.lower() for t in texts)


def test_selected_option_none_for_placeholder(qtbot: QtBot) -> None:
    """selected_option() → None при плейсхолдере."""
    w = BranchWidget(_make_branch())
    qtbot.addWidget(w)
    assert w.selected_option() is None


def test_selected_option_returns_correct_branch_option(qtbot: QtBot) -> None:
    """selected_option() возвращает BranchOption при непустом выборе."""
    w = BranchWidget(_make_branch())
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(0)
    opt = w.selected_option()
    assert opt is not None
    assert opt.id == "opt_correct"
