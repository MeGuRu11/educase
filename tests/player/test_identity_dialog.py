from pytestqt.qtbot import QtBot

from epicase_player.ui.identity_dialog import IdentityDialog


def test_save_button_disabled_until_fio_present(qtbot: QtBot) -> None:
    """Кнопка «Сохранить» выключена при пустом ФИО и включается после ввода."""
    dialog = IdentityDialog()
    qtbot.addWidget(dialog)

    assert not dialog._save_btn.isEnabled()

    dialog._fio.setText("Иванов")
    assert dialog._save_btn.isEnabled()


def test_getters_return_stripped_values(qtbot: QtBot) -> None:
    """Геттеры возвращают обрезанные значения полей."""
    dialog = IdentityDialog()
    qtbot.addWidget(dialog)

    dialog._fio.setText(" Иванов И.И. ")
    dialog._rank.setText(" лейтенант ")
    dialog._group.setText(" 121 ")

    assert dialog.full_name() == "Иванов И.И."
    assert dialog.rank() == "лейтенант"
    assert dialog.study_group() == "121"
