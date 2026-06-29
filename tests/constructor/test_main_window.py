from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch
from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QGuiApplication
from PySide6.QtWidgets import QFileDialog, QMessageBox, QTableWidgetItem
from pytestqt.qtbot import QtBot

from epicase_constructor.ui.case_saved_view import CaseSavedView
from epicase_constructor.ui.field_editor import FieldEditor
from epicase_constructor.ui.main_window import _PAGE_EDITOR, _PAGE_SAVED, _PAGE_START, MainWindow
from epicase_constructor.ui.report_dialog import ReportDialog
from epicase_core.application.case_builder import build_case
from epicase_core.application.cases import load_case, save_case
from epicase_core.application.results import record_attempt
from epicase_core.domain import (
    Attempt,
    AttemptClinical,
    AttemptMeta,
    Case,
    CaseMeta,
    DocumentResponse,
)
from epicase_ui.animated_start import AnimatedStartWidget


def _select_type(field: FieldEditor, value: str) -> None:
    """Выбрать тип поля по англ. значению (userData), не завязываясь на видимую подпись."""
    field.type_combo.setCurrentIndex(field.type_combo.findData(value))


def test_constructor_window_title(qtbot: QtBot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.windowTitle() == "EpiCase Constructor"


def test_save_then_load_round_trip(qtbot: QtBot, tmp_path: Path) -> None:
    """Сквозной цикл Constructor → .epicase → back: мета и пациенты совпадают."""
    window = MainWindow()
    qtbot.addWidget(window)

    window.editor.title_edit.setText("Вспышка ОКИ")
    window.editor.add_patient_button.click()
    window.editor.patient_editors[0].title_edit.setText("Пациент 1")
    expected_id = window.editor._case_id  # автогенерированный служебный id кейса

    dst = tmp_path / "case.epicase"
    assert window.save_case_to_path(dst) is True
    assert dst.exists()

    loaded = load_case(dst)
    assert loaded.case.meta.id == expected_id
    assert loaded.case.meta.title == "Вспышка ОКИ"
    assert len(loaded.case.patients.patients) == 1
    assert loaded.case.patients.patients[0].id  # автогенерированный id пациента


def test_save_then_load_full_six_stages(qtbot: QtBot, tmp_path: Path) -> None:
    """Полный 6-этапный цикл через окно: load_case восстанавливает все шесть этапов."""
    window = MainWindow()
    qtbot.addWidget(window)
    editor = window.editor

    editor.title_edit.setText("Полный кейс")

    # 1 — Пациенты.
    editor.add_patient_button.click()
    editor.patient_editors[0].title_edit.setText("Пациент 1")

    # 2 — Клинический.
    clinical = editor.clinical_editor
    clinical.intro_edit.setText("Осмотрите больных")
    clinical.search_editor.add_entry_button.click()
    clinical.search_editor.entry_editors[0].triggers.canonical_edit.setText("температура")
    clinical.branch_editor.prompt_edit.setText("Диагноз?")
    clinical.branch_editor.add_option_button.click()
    clinical.branch_editor.option_editors[0].label_edit.setText("ОКИ")

    # 3 — Контактные лица.
    contacts_scheme = tmp_path / "scheme_contacts.png"
    contacts_scheme.write_bytes(b"CONTACTS")
    contacts = editor.contacts_editor
    contacts.scheme_picker.set_file(str(contacts_scheme))
    contacts.inspection_editor.add_group_button.click()
    contacts.inspection_editor.group_editors[0].canonical_edit.setText("сыпь")

    # 4 — Объекты внешней среды.
    env_scheme = tmp_path / "scheme_env.png"
    env_scheme.write_bytes(b"ENV")
    env_photo = tmp_path / "photo_01.png"
    env_photo.write_bytes(b"PHOTO")
    environment = editor.environment_editor
    environment.scheme_picker.set_file(str(env_scheme))
    environment.photos_picker.add_file(str(env_photo))
    environment.inspection_editor.add_group_button.click()
    environment.inspection_editor.group_editors[0].canonical_edit.setText("грязь")

    # 5 — Оценка СЭС.
    ses = editor.ses_editor
    ses.intro_edit.setText("Оцените СЭС")
    ses.include_level_checkbox.setChecked(True)
    ses.level_field_editor.label_edit.setText("Уровень СЭС")
    _select_type(ses.level_field_editor, "choice")
    ses.level_field_editor.options_edit.setText("благополучное, чрезвычайное")
    ses.level_field_editor.correct_edit.setText("чрезвычайное")

    # 6 — Окончательный диагноз.
    final = editor.final_editor
    final.intro_edit.setText("Окончательный диагноз")
    final.timelines_editor.add_timeline_button.click()
    timeline = final.timelines_editor.timeline_editors[0]
    timeline.title_edit.setText("Очаг")
    timeline.add_row_button.click()
    timeline.events_table.setItem(0, 0, QTableWidgetItem("2026-06-01"))
    timeline.events_table.setItem(0, 1, QTableWidgetItem("Завоз"))

    expected = build_case(editor.to_draft())

    dst = tmp_path / "case.epicase"
    assert window.save_case_to_path(dst) is True
    loaded = load_case(dst)

    # id пациентов автогенерируются заново при каждой сборке кейса, поэтому карточки сверяем
    # без id (заголовок/поля/ассеты); этапы 2–6 имеют детерминированные id — сверяем целиком.
    assert [
        (p.title, p.fields, p.assets) for p in loaded.case.patients.patients
    ] == [(p.title, p.fields, p.assets) for p in expected.patients.patients]
    assert loaded.case.clinical == expected.clinical
    assert loaded.case.contacts == expected.contacts
    assert loaded.case.environment == expected.environment
    assert loaded.case.ses == expected.ses
    assert loaded.case.final == expected.final


def test_save_packs_scheme_asset_bytes(qtbot: QtBot, tmp_path: Path) -> None:
    """Сквозная цепочка ассета: выбор файла → стабильный id в Case → реальные байты в .epicase."""
    contacts_scheme = tmp_path / "scheme_contacts.png"
    contacts_scheme.write_bytes(b"\x89PNG-contacts")
    env_scheme = tmp_path / "scheme_env.jpg"
    env_scheme.write_bytes(b"JPG-env")

    window = MainWindow()
    qtbot.addWidget(window)
    editor = window.editor

    editor.contacts_editor.scheme_picker.set_file(str(contacts_scheme))
    editor.environment_editor.scheme_picker.set_file(str(env_scheme))

    # Запоминаем сгенерированные id ДО сохранения — пикер фиксирует их при выборе файла.
    contacts_ref = editor.contacts_editor.scheme_picker.value()
    env_ref = editor.environment_editor.scheme_picker.value()
    assert contacts_ref is not None and env_ref is not None

    dst = tmp_path / "case.epicase"
    assert window.save_case_to_path(dst) is True

    loaded = load_case(dst)
    # Case ссылается на схему по стабильному asset_id (фон корневого вида SchemeDocument)…
    contacts_doc = loaded.case.contacts.scheme
    env_doc = loaded.case.environment.scheme
    assert contacts_doc is not None and env_doc is not None
    assert contacts_doc.root.background == contacts_ref.asset_id
    assert env_doc.root.background == env_ref.asset_id
    # …а реальные байты файлов лежат в архиве под этими id.
    assert loaded.assets[contacts_ref.asset_id] == b"\x89PNG-contacts"
    assert loaded.assets[env_ref.asset_id] == b"JPG-env"


def test_save_packs_multi_location_asset_bytes(qtbot: QtBot, tmp_path: Path) -> None:
    """Сквозная цепочка мульти-ассетов: пациент + фото среды + изображение точки поиска."""
    patient_img = tmp_path / "patient.png"
    patient_img.write_bytes(b"PATIENT-bytes")
    env_photo = tmp_path / "photo.jpg"
    env_photo.write_bytes(b"PHOTO-bytes")
    reveal_img = tmp_path / "reveal.png"
    reveal_img.write_bytes(b"REVEAL-bytes")

    window = MainWindow()
    qtbot.addWidget(window)
    editor = window.editor

    # Пациент с изображением карточки.
    editor.add_patient_button.click()
    patient = editor.patient_editors[0]
    patient.assets_picker.add_file(str(patient_img))

    # Фото объекта внешней среды.
    editor.environment_editor.photos_picker.add_file(str(env_photo))

    # Изображение вскрытия точки поиска клинического этапа.
    search = editor.clinical_editor.search_editor
    search.add_entry_button.click()
    entry = search.entry_editors[0]
    entry.triggers.canonical_edit.setText("температура")
    entry.reveal_assets_picker.add_file(str(reveal_img))

    # Запоминаем id ДО сохранения — пикеры фиксируют их при выборе файла.
    patient_ref = patient.assets_picker.value()[0]
    photo_ref = editor.environment_editor.photos_picker.value()[0]
    reveal_ref = entry.reveal_assets_picker.value()[0]

    dst = tmp_path / "case.epicase"
    assert window.save_case_to_path(dst) is True

    loaded = load_case(dst)
    # Поля Case ссылаются на ассеты по стабильным id…
    assert loaded.case.patients.patients[0].assets == (patient_ref.asset_id,)
    assert loaded.case.environment.photos == (photo_ref.asset_id,)
    assert loaded.case.clinical.search is not None
    assert loaded.case.clinical.search.entries[0].reveal_assets == (reveal_ref.asset_id,)
    # …а реальные байты файлов лежат в архиве под этими id.
    assert loaded.assets[patient_ref.asset_id] == b"PATIENT-bytes"
    assert loaded.assets[photo_ref.asset_id] == b"PHOTO-bytes"
    assert loaded.assets[reveal_ref.asset_id] == b"REVEAL-bytes"


def test_save_invalid_template_number_warns_and_skips(
    qtbot: QtBot, tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Некорректное число в поле → предупреждение, save → False, файла нет (не падение)."""
    monkeypatch.setattr(
        QMessageBox, "warning", lambda *args, **kwargs: QMessageBox.StandardButton.Ok
    )

    window = MainWindow()
    qtbot.addWidget(window)
    editor = window.editor

    editor.ses_editor.include_level_checkbox.setChecked(True)
    level = editor.ses_editor.level_field_editor
    level.label_edit.setText("Доза")
    _select_type(level, "number")
    level.number_value_edit.setText("abc")

    dst = tmp_path / "case.epicase"
    assert window.save_case_to_path(dst) is False
    assert not dst.exists()


def test_report_dialog_for_valid_pair_returns_dialog(
    qtbot: QtBot, tmp_path: Path
) -> None:
    """Шов отчёта на валидной паре .epiresult/.epicase → ``ReportDialog`` (не None)."""
    case_path = save_case(Case(meta=CaseMeta(id="case-x")), tmp_path / "case")
    result_path = record_attempt(
        Attempt(meta=AttemptMeta(case_id="case-x", trainee_label="Петров")),
        tmp_path / "result",
    )

    window = MainWindow()
    qtbot.addWidget(window)

    dialog = window.report_dialog_for(result_path, case_path)
    assert dialog is not None
    assert isinstance(dialog, ReportDialog)
    qtbot.addWidget(dialog)


def test_report_dialog_for_broken_archive_returns_none(
    qtbot: QtBot, tmp_path: Path
) -> None:
    """Шов отчёта на чужом типе архива (.epicase как результат) → ``None`` (не падение)."""
    case_path = save_case(Case(meta=CaseMeta(id="case-x")), tmp_path / "case")

    window = MainWindow()
    qtbot.addWidget(window)

    assert window.report_dialog_for(case_path, case_path) is None


def test_report_dialog_for_carries_attachments_and_assets(
    qtbot: QtBot, tmp_path: Path
) -> None:
    """Вложения курсанта и байты архива доносятся через ``report_dialog_for`` в диалог."""
    case_path = save_case(Case(meta=CaseMeta(id="case-att")), tmp_path / "case")
    attempt = Attempt(
        meta=AttemptMeta(case_id="case-att", trainee_label="Петров"),
        clinical=AttemptClinical(
            documents=(
                DocumentResponse(
                    task_id="d1", attachments=(("att-1", "донесение.pdf"),)
                ),
            ),
        ),
    )
    result_path = record_attempt(
        attempt, tmp_path / "result", assets={"att-1": b"PDF-BYTES"}
    )

    window = MainWindow()
    qtbot.addWidget(window)

    dialog = window.report_dialog_for(result_path, case_path)
    assert dialog is not None
    qtbot.addWidget(dialog)
    assert dialog._assets.get("att-1") == b"PDF-BYTES"


# --- Тесты экрана сохранения ---


def test_show_case_saved_switches_stack(qtbot: QtBot) -> None:
    """После load в редактор + _show_case_saved стек переключается на страницу saved."""
    window = MainWindow()
    qtbot.addWidget(window)

    # Сначала переходим на редактор (имитируем открытый кейс)
    window._stack.setCurrentIndex(_PAGE_EDITOR)
    assert window._stack.currentIndex() == _PAGE_EDITOR

    window._show_case_saved("C:/cases/my.epicase")

    assert window._stack.currentIndex() == _PAGE_SAVED
    assert isinstance(window._stack.currentWidget(), CaseSavedView)
    assert window._saved_view._path_label.text() == "C:/cases/my.epicase"


def test_continue_requested_returns_to_editor(qtbot: QtBot) -> None:
    """continue_requested от CaseSavedView возвращает стек на страницу редактора."""
    window = MainWindow()
    qtbot.addWidget(window)

    window._show_case_saved("/path/case.epicase")
    assert window._stack.currentIndex() == _PAGE_SAVED

    window._saved_view.continue_requested.emit()

    assert window._stack.currentIndex() == _PAGE_EDITOR
    window._stack.setCurrentIndex(_PAGE_START)


def test_home_requested_returns_to_start(qtbot: QtBot) -> None:
    """home_requested от CaseSavedView возвращает стек на стартовый экран."""
    window = MainWindow()
    qtbot.addWidget(window)

    window._show_case_saved("/path/case.epicase")
    assert window._stack.currentIndex() == _PAGE_SAVED

    window._saved_view.home_requested.emit()

    assert window._stack.currentIndex() == _PAGE_START


def test_start_intro_finishes_on_page_leave_without_replaying(
    qtbot: QtBot,
) -> None:
    """Переходы реального стека завершают intro один раз на том же start widget."""
    window = MainWindow()
    qtbot.addWidget(window)
    application = QGuiApplication.instance()
    assert isinstance(application, QGuiApplication)
    application.applicationStateChanged.emit(Qt.ApplicationState.ApplicationActive)
    window.show()

    start_page = window._stack.widget(_PAGE_START)
    assert start_page is not None
    animated = start_page.findChild(AnimatedStartWidget)
    assert animated is not None
    background = animated.background
    completions: list[bool] = []
    background.intro_finished.connect(lambda: completions.append(True))
    qtbot.waitUntil(lambda: background.timer_active, timeout=250)
    assert background.intro_complete is False

    window._stack.setCurrentIndex(_PAGE_EDITOR)

    assert background.intro_complete is True
    assert background.intro_progress == 1.0
    assert background.timer_active is False
    assert completions == [True]

    window._show_case_saved("/path/case.epicase")
    window._saved_view.home_requested.emit()

    assert window._stack.currentIndex() == _PAGE_START
    assert window._stack.widget(_PAGE_START) is start_page
    qtbot.waitUntil(lambda: background.timer_active, timeout=250)
    qtbot.wait(25)
    assert background.intro_complete is True
    assert completions == [True]


# --- Тесты подтверждения перед потерей несохранённого кейса ---


def test_close_event_editor_no_ignores(qtbot: QtBot, monkeypatch: MonkeyPatch) -> None:
    """closeEvent на странице редактора при ответе No → событие проигнорировано."""
    window = MainWindow()
    qtbot.addWidget(window)
    window._stack.setCurrentIndex(_PAGE_EDITOR)
    monkeypatch.setattr(window, "_confirm_discard", lambda *a, **kw: False)

    event = QCloseEvent()
    window.closeEvent(event)
    assert not event.isAccepted()


def test_close_event_editor_yes_accepts(qtbot: QtBot, monkeypatch: MonkeyPatch) -> None:
    """closeEvent на странице редактора при ответе Yes → событие принято."""
    window = MainWindow()
    qtbot.addWidget(window)
    window._stack.setCurrentIndex(_PAGE_EDITOR)
    monkeypatch.setattr(window, "_confirm_discard", lambda *a, **kw: True)

    event = QCloseEvent()
    window.closeEvent(event)
    assert event.isAccepted()


def test_close_event_start_no_question(qtbot: QtBot, monkeypatch: MonkeyPatch) -> None:
    """closeEvent на стартовой странице принимается без вызова _confirm_discard."""
    called: list[bool] = []

    def _fake_confirm(*a: object, **kw: object) -> bool:
        called.append(True)
        return False

    window = MainWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(window, "_confirm_discard", _fake_confirm)
    # _PAGE_START по умолчанию

    event = QCloseEvent()
    window.closeEvent(event)
    assert event.isAccepted()
    assert not called


def test_open_case_dialog_editor_no_skips_load(
    qtbot: QtBot, monkeypatch: MonkeyPatch
) -> None:
    """open_case_dialog на странице редактора при ответе No не открывает файл."""
    monkeypatch.setattr(
        QFileDialog, "getOpenFileName", lambda *a, **kw: ("dummy.epicase", "")
    )
    window = MainWindow()
    qtbot.addWidget(window)
    window._stack.setCurrentIndex(_PAGE_EDITOR)
    monkeypatch.setattr(window, "_confirm_discard", lambda *a, **kw: False)

    load_called: list[Path] = []

    def _load(p: Path) -> bool:
        load_called.append(p)
        return True

    monkeypatch.setattr(window, "load_case_from_path", _load)

    window.open_case_dialog()
    assert load_called == []
