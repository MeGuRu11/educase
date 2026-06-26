from __future__ import annotations

from PySide6.QtWidgets import QDialog, QLabel, QPushButton
from pytestqt.qtbot import QtBot

from epicase_constructor.ui.confirm_dialog import ConfirmDialog


def test_confirm_dialog_renders_labels(qtbot: QtBot) -> None:
    """ConfirmDialog показывает переданные title, message, confirm_label, cancel_label."""
    dlg = ConfirmDialog(
        title="Тест",
        message="Вопрос?",
        confirm_label="Да",
        cancel_label="Нет",
    )
    qtbot.addWidget(dlg)

    assert dlg.windowTitle() == "Тест"

    title_lbl = dlg.findChild(QLabel, "confirmTitle")
    msg_lbl = dlg.findChild(QLabel, "confirmText")
    confirm_btn = dlg.findChild(QPushButton, "confirmDiscardButton")
    cancel_btn = dlg.findChild(QPushButton, "confirmCancelButton")

    assert title_lbl is not None and title_lbl.text() == "Тест"
    assert msg_lbl is not None and msg_lbl.text() == "Вопрос?"
    assert confirm_btn is not None and confirm_btn.text() == "Да"
    assert cancel_btn is not None and cancel_btn.text() == "Нет"


def test_confirm_dialog_confirm_click_accepts(qtbot: QtBot) -> None:
    """Клик confirm-кнопки выставляет результат Accepted."""
    dlg = ConfirmDialog(title="Тест", message="Вопрос?", confirm_label="Да")
    qtbot.addWidget(dlg)

    confirm_btn = dlg.findChild(QPushButton, "confirmDiscardButton")
    assert confirm_btn is not None
    confirm_btn.click()

    assert dlg.result() == QDialog.DialogCode.Accepted


def test_confirm_dialog_cancel_click_rejects(qtbot: QtBot) -> None:
    """Клик cancel-кнопки выставляет результат Rejected."""
    dlg = ConfirmDialog(title="Тест", message="Вопрос?", confirm_label="Да")
    qtbot.addWidget(dlg)

    # Сначала ставим Accepted, чтобы убедиться, что cancel действительно его меняет.
    dlg.setResult(QDialog.DialogCode.Accepted)

    cancel_btn = dlg.findChild(QPushButton, "confirmCancelButton")
    assert cancel_btn is not None
    cancel_btn.click()

    assert dlg.result() == QDialog.DialogCode.Rejected
