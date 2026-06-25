from pathlib import Path

import pytest
from PySide6.QtWidgets import QFileDialog, QMessageBox
from pytestqt.qtbot import QtBot

from epicase_core.application.cases import save_case
from epicase_core.application.results import load_result
from epicase_core.domain.case import Case, CaseMeta
from epicase_core.domain.documents import DocumentOption, DocumentTask, DocumentTemplate, FillMode
from epicase_core.domain.stages import StageClinical
from epicase_player.ui.case_navigator import CaseNavigator
from epicase_player.ui.document_widget import DocumentWidget
from epicase_player.ui.main_window import MainWindow


def test_player_window_title(qtbot: QtBot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.windowTitle() == "EpiCase Player"


def test_load_case_from_path_success(qtbot: QtBot, tmp_path: Path) -> None:
    """load_case_from_path монтирует CaseNavigator с 6 страницами при успешной загрузке."""
    case = Case(meta=CaseMeta("c1", "Тест"))
    dst = tmp_path / "test.epicase"
    save_case(case, dst)

    window = MainWindow()
    qtbot.addWidget(window)

    result = window.load_case_from_path(dst)

    assert result is True
    central = window.centralWidget()
    assert isinstance(central, CaseNavigator)
    assert central.stack.count() == 6


def test_load_case_from_path_corrupt(
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """load_case_from_path возвращает False при битом файле, без исключения."""
    corrupt = tmp_path / "bad.epicase"
    corrupt.write_bytes(b"not a zip file")

    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: 0)

    window = MainWindow()
    qtbot.addWidget(window)

    result = window.load_case_from_path(corrupt)
    assert result is False


def test_save_action_disabled_until_case_loaded(qtbot: QtBot, tmp_path: Path) -> None:
    """Пункт «Сохранить результат…» выключен до загрузки кейса и включается после."""
    case = Case(meta=CaseMeta("c1", "Тест"))
    dst = tmp_path / "test.epicase"
    save_case(case, dst)

    window = MainWindow()
    qtbot.addWidget(window)
    assert not window._save_action.isEnabled()

    assert window.load_case_from_path(dst) is True
    assert window._save_action.isEnabled()


def test_save_result_without_case_returns_false(qtbot: QtBot, tmp_path: Path) -> None:
    """save_result_to_path без загруженного кейса возвращает False, без записи."""
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.save_result_to_path(tmp_path / "res.epiresult") is False


def test_load_then_save_result_round_trip(qtbot: QtBot, tmp_path: Path) -> None:
    """Шов: load_case_from_path → save_result_to_path → файл читается load_result."""
    case = Case(meta=CaseMeta("c1", "Тест"))
    src = tmp_path / "test.epicase"
    save_case(case, src)

    window = MainWindow()
    qtbot.addWidget(window)
    assert window.load_case_from_path(src) is True

    out = tmp_path / "result.epiresult"
    assert window.save_result_to_path(out, "Курсант Иванов") is True

    loaded = load_result(out)
    assert loaded.attempt.meta.case_id == "c1"
    assert loaded.attempt.meta.trainee_label == "Курсант Иванов"


def test_save_result_round_trip_identity_fields(qtbot: QtBot, tmp_path: Path) -> None:
    """Шов: ФИО/звание/группа проходят через save_result_to_path в .epiresult."""
    case = Case(meta=CaseMeta("c1", "Тест"))
    src = tmp_path / "test.epicase"
    save_case(case, src)

    window = MainWindow()
    qtbot.addWidget(window)
    assert window.load_case_from_path(src) is True

    out = tmp_path / "result.epiresult"
    assert (
        window.save_result_to_path(out, "Иванов И.И.", rank="лейтенант", study_group="121")
        is True
    )

    loaded = load_result(out)
    assert loaded.attempt.meta.trainee_label == "Иванов И.И."
    assert loaded.attempt.meta.rank == "лейтенант"
    assert loaded.attempt.meta.study_group == "121"


def test_save_result_assets_round_trip(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Вложение ATTACHMENT курсанта доезжает save_result_to_path → load_result (ADR-015)."""
    att_file = tmp_path / "attach.txt"
    att_file.write_bytes(b"attachment content")

    att_opt = DocumentOption(
        id="opt_att",
        title="Акт",
        is_correct=True,
        template=DocumentTemplate(id="tpl_att", title="Акт", fill_mode=FillMode.ATTACHMENT),
    )
    task = DocumentTask(id="t_att", prompt="Прикрепите акт.", options=(att_opt,))
    case = Case(meta=CaseMeta("c_att", "АТТ"), clinical=StageClinical(documents=(task,)))
    src = tmp_path / "att.epicase"
    save_case(case, src)

    window = MainWindow()
    qtbot.addWidget(window)
    assert window.load_case_from_path(src) is True

    navigator = window._navigator
    assert navigator is not None
    doc_widgets: list[DocumentWidget] = navigator.findChildren(DocumentWidget)
    assert len(doc_widgets) == 1
    dw = doc_widgets[0]
    dw.options_combo.setCurrentIndex(0)

    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **kw: (str(att_file), ""))
    dw._pick_files(allow_multiple=False)

    out = tmp_path / "result.epiresult"
    assert window.save_result_to_path(out, "Курсант") is True

    loaded = load_result(out)
    assert loaded.attempt.meta.case_id == "c_att"
    assert len(loaded.assets) == 1
    assert list(loaded.assets.values()) == [b"attachment content"]
