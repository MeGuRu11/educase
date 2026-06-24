from collections.abc import Callable
from pathlib import Path

from pytestqt.qtbot import QtBot

from epicase_core.application.cases import load_case, save_case
from epicase_core.domain.case import Case, CaseMeta
from epicase_core.domain.scheme import SchemeDocument, SchemeView
from epicase_core.domain.stages import StageContacts
from epicase_player.ui.case_navigator import CaseNavigator
from epicase_player.ui.scheme_viewer import SchemeViewerWidget


def test_initial_state(qtbot: QtBot) -> None:
    """На старте активен первый этап, кнопка 'Назад' задизейблена."""
    case = Case(meta=CaseMeta("c1", "Тест"))
    nav = CaseNavigator(case)
    qtbot.addWidget(nav)

    assert nav.current_index == 0
    assert not nav.btn_prev.isEnabled()
    assert nav.btn_next.isEnabled()


def test_forward_to_last_stage(qtbot: QtBot) -> None:
    """Последовательные нажатия 'Далее' проходят все 6 этапов; на последнем 'Далее' задизейблена."""
    case = Case(meta=CaseMeta("c1", "Тест"))
    nav = CaseNavigator(case)
    qtbot.addWidget(nav)

    for _ in range(5):
        nav.btn_next.click()

    assert nav.current_index == 5
    assert not nav.btn_next.isEnabled()


def test_backward_from_second_stage(qtbot: QtBot) -> None:
    """'Назад' уменьшает индекс и снова включает 'Далее'."""
    case = Case(meta=CaseMeta("c1", "Тест"))
    nav = CaseNavigator(case)
    qtbot.addWidget(nav)

    nav.btn_next.click()
    nav.btn_prev.click()

    assert nav.current_index == 0
    assert nav.btn_next.isEnabled()


def test_non_blocking_navigation(qtbot: QtBot) -> None:
    """Проход всех шести этапов вперёд без блокировки (ADR-005/008)."""
    case = Case(meta=CaseMeta("c1", "Тест"))
    nav = CaseNavigator(case)
    qtbot.addWidget(nav)

    assert nav.stack.count() == 6

    for i in range(5):
        nav.btn_next.click()
        assert nav.current_index == i + 1

    assert nav.current_index == 5


def test_scheme_image_round_trips_to_navigator(
    qtbot: QtBot, tmp_path: Path, png_bytes: Callable[..., bytes]
) -> None:
    """Сквозная цепочка: .epicase со схемой-картинкой → CaseNavigator рисует фон схемы."""
    case = Case(
        meta=CaseMeta("c1", "Тест"),
        contacts=StageContacts(scheme=SchemeDocument(root=SchemeView(background="scheme-1"))),
    )
    dst = tmp_path / "case.epicase"
    save_case(case, dst, assets={"scheme-1": png_bytes()})

    loaded = load_case(dst)
    scheme = loaded.case.contacts.scheme
    assert scheme is not None
    assert scheme.root.background == "scheme-1"

    nav = CaseNavigator(loaded.case, loaded.assets)
    qtbot.addWidget(nav)

    viewers: list[SchemeViewerWidget] = nav.findChildren(SchemeViewerWidget)
    assert any(v.has_background() for v in viewers)
