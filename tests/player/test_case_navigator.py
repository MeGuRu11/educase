from collections.abc import Callable
from pathlib import Path

from pytestqt.qtbot import QtBot

from epicase_core.application.cases import load_case, save_case
from epicase_core.domain.attempt import AttemptMeta
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
    """Нажатие 'Завершить' на последнем этапе доводит до страницы завершения; btn_next disabled."""
    case = Case(meta=CaseMeta("c1", "Тест"))
    nav = CaseNavigator(case)
    qtbot.addWidget(nav)

    for _ in range(6):  # 5 × «Далее» + 1 × «Завершить» → completion page
        nav.btn_next.click()

    assert nav.current_index == 6
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

    assert nav.stack.count() == 7  # 6 этапов + 1 страница завершения

    for i in range(5):
        nav.btn_next.click()
        assert nav.current_index == i + 1

    assert nav.current_index == 5


def test_collect_assets_returns_empty_by_default(qtbot: QtBot) -> None:
    """collect_assets() пуст для кейса без прикреплённых файлов (ADR-015)."""
    case = Case(meta=CaseMeta("c1", "Тест"))
    nav = CaseNavigator(case)
    qtbot.addWidget(nav)
    assert nav.collect_assets() == {}


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


# --- Новые тесты для страницы завершения ---


def test_stack_count_is_stage_count_plus_one(qtbot: QtBot) -> None:
    """stack.count() == stage_count + 1 (страница завершения добавляется последней)."""
    case = Case(meta=CaseMeta("c1", "Тест"))
    nav = CaseNavigator(case)
    qtbot.addWidget(nav)
    assert nav.stack.count() == nav._stage_count + 1


def test_completion_page_position_and_button_state(qtbot: QtBot) -> None:
    """На странице завершения позиция 'Завершение', btn_next disabled, btn_prev enabled."""
    case = Case(meta=CaseMeta("c1", "Тест"))
    nav = CaseNavigator(case)
    qtbot.addWidget(nav)

    for _ in range(nav._stage_count):
        nav.btn_next.click()

    assert nav.stack.currentIndex() == nav._stage_count
    assert nav._position_label.text() == "Завершение"
    assert not nav.btn_next.isEnabled()
    assert nav.btn_prev.isEnabled()


def test_last_stage_button_says_завершить(qtbot: QtBot) -> None:
    """На последнем этапе кнопка 'Далее' отображает 'Завершить' и остаётся включённой."""
    case = Case(meta=CaseMeta("c1", "Тест"))
    nav = CaseNavigator(case)
    qtbot.addWidget(nav)

    for _ in range(nav._stage_count - 1):
        nav.btn_next.click()

    assert nav.stack.currentIndex() == nav._stage_count - 1
    assert nav.btn_next.text() == "Завершить"
    assert nav.btn_next.isEnabled()


def test_завершить_navigates_to_completion(qtbot: QtBot) -> None:
    """Клик 'Завершить' на последнем этапе переходит на страницу завершения."""
    case = Case(meta=CaseMeta("c1", "Тест"))
    nav = CaseNavigator(case)
    qtbot.addWidget(nav)

    for _ in range(nav._stage_count):
        nav.btn_next.click()

    assert nav.stack.currentIndex() == nav._stage_count
    assert nav._position_label.text() == "Завершение"


def test_collect_attempt_and_assets_do_not_crash_on_completion(qtbot: QtBot) -> None:
    """collect_attempt / collect_assets не падают, когда активна страница завершения."""
    case = Case(meta=CaseMeta("c1", "Тест"))
    nav = CaseNavigator(case)
    qtbot.addWidget(nav)

    for _ in range(nav._stage_count):
        nav.btn_next.click()

    meta = AttemptMeta(case_id="c1")
    attempt = nav.collect_attempt(meta)
    assert attempt.meta.case_id == "c1"
    assert nav.collect_assets() == {}


def test_mark_saved_switches_to_completion(qtbot: QtBot) -> None:
    """mark_saved переключает навигатор на страницу завершения и проставляет путь."""
    case = Case(meta=CaseMeta("c1", "Тест"))
    nav = CaseNavigator(case)
    qtbot.addWidget(nav)

    nav.mark_saved("/path/result.epiresult")

    assert nav.stack.currentIndex() == nav._stage_count
    assert nav._position_label.text() == "Завершение"
    assert nav._completion._path_label.text() == "/path/result.epiresult"


def test_save_requested_forwarded_from_completion(qtbot: QtBot) -> None:
    """save_requested от CompletionView пробрасывается через CaseNavigator."""
    case = Case(meta=CaseMeta("c1", "Тест"))
    nav = CaseNavigator(case)
    qtbot.addWidget(nav)

    received: list[bool] = []
    nav.save_requested.connect(lambda: received.append(True))
    nav._completion.save_requested.emit()

    assert len(received) == 1


def test_new_case_requested_forwarded_from_completion(qtbot: QtBot) -> None:
    """new_case_requested от CompletionView пробрасывается через CaseNavigator."""
    case = Case(meta=CaseMeta("c1", "Тест"))
    nav = CaseNavigator(case)
    qtbot.addWidget(nav)

    received: list[bool] = []
    nav.new_case_requested.connect(lambda: received.append(True))
    nav._completion.new_case_requested.emit()

    assert len(received) == 1
