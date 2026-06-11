from pytestqt.qtbot import QtBot

from educase_core.domain.case import Case, CaseMeta
from educase_player.ui.case_navigator import CaseNavigator


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
