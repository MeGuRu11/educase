"""Тесты DocumentWidget: выбор документа из списка с обманками и заполнение полей."""
from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
)
from pytestqt.qtbot import QtBot

from epicase_core.domain.documents import (
    ChoiceMatch,
    DocumentField,
    DocumentOption,
    DocumentTask,
    DocumentTemplate,
    FieldType,
    FillMode,
    TextMatch,
)
from epicase_core.domain.search import SynonymSet
from epicase_player.ui.asset_image_widget import AssetImageWidget
from epicase_player.ui.document_widget import DocumentWidget
from epicase_player.ui.stage_views import _doc_resp


def _make_task() -> DocumentTask:
    """DocumentTask с правильным документом (TEXT + CHOICE поля) и обманкой (template=None)."""
    text_field = DocumentField(
        id="fld_diag",
        type=FieldType.TEXT,
        rule=TextMatch(keywords=SynonymSet(canonical="сальмонеллёз")),
        label="Диагноз",
    )
    choice_field = DocumentField(
        id="fld_level",
        type=FieldType.CHOICE,
        rule=ChoiceMatch(correct=("Неблагополучное",)),
        label="Уровень СЭС",
        options=("Благополучное", "Неустойчивое", "Неблагополучное", "Чрезвычайное"),
    )
    correct_opt = DocumentOption(
        id="opt_correct",
        title="Донесение ДМ4",
        is_correct=True,
        template=DocumentTemplate(
            id="tpl_dm4",
            title="ДМ4",
            fields=(text_field, choice_field),
        ),
    )
    decoy_opt = DocumentOption(
        id="opt_decoy",
        title="Форма Ф23",
        is_correct=False,
        template=None,
    )
    return DocumentTask(
        id="task1",
        prompt="Выберите нужный документ и заполните его поля.",
        options=(correct_opt, decoy_opt),
    )


def test_initial_state_no_fields_result_none(qtbot: QtBot) -> None:
    """При старте form_area пустой (нет виджетов полей) и result is None."""
    w = DocumentWidget(_make_task())
    qtbot.addWidget(w)
    assert w.result is None
    assert w.current_field_widgets() == []


def test_select_correct_option_builds_field_widgets(qtbot: QtBot) -> None:
    """Выбор документа с template → строятся DocumentFieldWidget по числу полей шаблона."""
    w = DocumentWidget(_make_task())
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(0)  # "Донесение ДМ4" (correct) — первая реальная опция
    assert len(w.current_field_widgets()) == 2


def test_select_decoy_option_no_fields_message(qtbot: QtBot) -> None:
    """Выбор обманки (template=None) → полей нет, сообщение об отсутствии полей."""
    w = DocumentWidget(_make_task())
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(1)  # "Форма Ф23" (decoy) — вторая реальная опция
    assert w.current_field_widgets() == []
    labels: list[QLabel] = w.form_area.findChildren(QLabel)
    texts = [lbl.text() for lbl in labels]
    assert any("Для этого документа" in t for t in texts)


def test_submit_correct_option_correct_answers(qtbot: QtBot) -> None:
    """on_submit с правильным документом и верными полями.

    Ожидается: option_correct True, все элементы fields_ok True.
    """
    w = DocumentWidget(_make_task())
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(0)  # correct option — первая реальная опция

    field_widgets = w.current_field_widgets()
    assert len(field_widgets) == 2

    text_fw = next(fw for fw in field_widgets if fw.field.type == FieldType.TEXT)
    assert isinstance(text_fw.input, QLineEdit)
    text_fw.input.setText("сальмонеллёз")

    # combo без фиктивного пункта: 0=Благополучное, 1=Неустойчивое, 2=Неблагополучное
    choice_fw = next(fw for fw in field_widgets if fw.field.type == FieldType.CHOICE)
    assert isinstance(choice_fw.input, QComboBox)
    choice_fw.input.setCurrentIndex(2)  # "Неблагополучное"

    w.btn_submit.click()

    result = w.result
    assert result is not None
    assert result.option_correct is True
    assert result.option_id == "opt_correct"
    assert all(ok for _, ok in result.fields_ok)


def test_submit_decoy_option(qtbot: QtBot) -> None:
    """on_submit с обманкой → option_correct False, fields_ok пустой."""
    w = DocumentWidget(_make_task())
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(1)  # decoy — вторая реальная опция
    w.btn_submit.click()

    result = w.result
    assert result is not None
    assert result.option_correct is False
    assert result.option_id == "opt_decoy"
    assert result.fields_ok == ()


def test_submit_wrong_answers_no_crash(qtbot: QtBot) -> None:
    """Неверное заполнение полей → fields_ok содержит False, виджет не падает (ADR-008)."""
    w = DocumentWidget(_make_task())
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(0)  # correct option

    field_widgets = w.current_field_widgets()
    text_fw = next(fw for fw in field_widgets if fw.field.type == FieldType.TEXT)
    assert isinstance(text_fw.input, QLineEdit)
    text_fw.input.setText("неверный диагноз")

    w.btn_submit.click()

    result = w.result
    assert result is not None
    assert any(not ok for _, ok in result.fields_ok)


def test_submit_neutral_message_no_verdict(qtbot: QtBot) -> None:
    """После on_submit отображается нейтральное «Ответ сохранён», вердикт не показан (ADR-005)."""
    w = DocumentWidget(_make_task())
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(0)
    w.btn_submit.click()

    all_labels: list[QLabel] = w.findChildren(QLabel)
    texts = [lbl.text() for lbl in all_labels]
    assert "Ответ сохранён" in texts
    assert not any("верн" in t.lower() or "неверн" in t.lower() for t in texts)


def test_result_none_before_submit(qtbot: QtBot) -> None:
    """result is None до первого нажатия «Готово»."""
    w = DocumentWidget(_make_task())
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(0)
    assert w.result is None


def test_selected_option_none_for_placeholder(qtbot: QtBot) -> None:
    """selected_option() → None при плейсхолдере (currentIndex == -1)."""
    w = DocumentWidget(_make_task())
    qtbot.addWidget(w)
    assert w.options_combo.currentIndex() == -1
    assert w.selected_option() is None


def test_switch_from_correct_to_decoy_clears_fields(qtbot: QtBot) -> None:
    """Переключение с шаблонного документа на обманку очищает виджеты полей."""
    w = DocumentWidget(_make_task())
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(0)  # correct — строятся поля
    assert len(w.current_field_widgets()) == 2
    w.options_combo.setCurrentIndex(1)  # decoy — поля должны пропасть
    assert w.current_field_widgets() == []


def test_field_widget_ids_match_template(qtbot: QtBot) -> None:
    """id полей виджетов совпадают с id полей шаблона."""
    w = DocumentWidget(_make_task())
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(0)
    field_widgets = w.current_field_widgets()
    ids = {fw.field.id for fw in field_widgets}
    assert ids == {"fld_diag", "fld_level"}


def test_submit_without_selection_sets_invalid_property(qtbot: QtBot) -> None:
    """Нажатие «Готово» без выбора — мягкая подсветка (invalid=True), не блокирует (ADR-008)."""
    w = DocumentWidget(_make_task())
    qtbot.addWidget(w)
    assert w.options_combo.currentIndex() == -1

    w.btn_submit.click()

    # result всё равно записан (ADR-008: не блокирует)
    assert w.result is not None
    assert w.result.option_id is None
    # комбобокс помечен как invalid
    assert w.options_combo.property("invalid") is True


def test_selection_after_invalid_clears_property(qtbot: QtBot) -> None:
    """Выбор варианта после подсветки ошибки сбрасывает свойство invalid."""
    w = DocumentWidget(_make_task())
    qtbot.addWidget(w)
    w.btn_submit.click()  # invalid=True
    assert w.options_combo.property("invalid") is True

    w.options_combo.setCurrentIndex(0)  # любой выбор → invalid сбрасывается
    assert w.options_combo.property("invalid") is False


# --- ADR-014: FREE_TEXT и reference_assets ---


def _make_free_text_task() -> DocumentTask:
    """DocumentTask с верным документом FREE_TEXT и обманкой (template=None)."""
    correct_opt = DocumentOption(
        id="opt_free",
        title="Объяснительная",
        is_correct=True,
        template=DocumentTemplate(
            id="tpl_free",
            title="Объяснительная",
            fill_mode=FillMode.FREE_TEXT,
        ),
    )
    decoy_opt = DocumentOption(
        id="opt_decoy2",
        title="Рапорт",
        is_correct=False,
        template=None,
    )
    return DocumentTask(
        id="task_free",
        prompt="Заполните объяснительную",
        options=(correct_opt, decoy_opt),
    )


def test_free_text_mode_shows_plain_text_edit(qtbot: QtBot) -> None:
    """FREE_TEXT-режим → QPlainTextEdit в форме, поля пусты; ввод → free_text()."""
    w = DocumentWidget(_make_free_text_task())
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(0)
    assert w.current_field_widgets() == []
    te_list: list[QPlainTextEdit] = w.form_area.findChildren(QPlainTextEdit)
    assert len(te_list) == 1
    te_list[0].setPlainText("Объяснительная записка")
    assert w.free_text() == "Объяснительная записка"


def test_reference_assets_widgets_present(qtbot: QtBot) -> None:
    """Задание с reference_assets → >=2 AssetImageWidget; без вложений → 0."""
    task_with_refs = DocumentTask(
        id="task_refs",
        prompt="",
        options=(),
        reference_assets=("a1", "a2"),
    )
    w_with = DocumentWidget(task_with_refs)
    qtbot.addWidget(w_with)
    assert len(w_with.findChildren(AssetImageWidget)) >= 2

    task_no_refs = DocumentTask(id="task_norefs", prompt="", options=())
    w_without = DocumentWidget(task_no_refs)
    qtbot.addWidget(w_without)
    assert len(w_without.findChildren(AssetImageWidget)) == 0


def test_doc_resp_free_text_and_field_mode(qtbot: QtBot) -> None:
    """_doc_resp: FREE_TEXT-режим → free_text == введённый текст, field_answers пуст;
    FIELDS-режим → free_text == ''."""
    free_task = _make_free_text_task()
    free_widget = DocumentWidget(free_task)
    qtbot.addWidget(free_widget)
    free_widget.options_combo.setCurrentIndex(0)
    te_list: list[QPlainTextEdit] = free_widget.form_area.findChildren(QPlainTextEdit)
    te_list[0].setPlainText("Мой текст")
    resp = _doc_resp(free_task, free_widget)
    assert resp.free_text == "Мой текст"
    assert resp.field_answers == ()

    fields_task = _make_task()
    fields_widget = DocumentWidget(fields_task)
    qtbot.addWidget(fields_widget)
    fields_widget.options_combo.setCurrentIndex(0)
    resp2 = _doc_resp(fields_task, fields_widget)
    assert resp2.free_text == ""


# --- ADR-015: ATTACHMENT mode ---


def _make_attachment_task(allow_multiple: bool = True) -> DocumentTask:
    """DocumentTask с одной ATTACHMENT-опцией."""
    opt = DocumentOption(
        id="opt_att",
        title="Акт расследования",
        is_correct=True,
        template=DocumentTemplate(
            id="tpl_att",
            title="Акт",
            fill_mode=FillMode.ATTACHMENT,
            allow_multiple=allow_multiple,
        ),
    )
    return DocumentTask(id="task_att", prompt="Прикрепите акт.", options=(opt,))


def test_attachment_mode_shows_button_multiple(qtbot: QtBot) -> None:
    """ATTACHMENT allow_multiple=True → кнопка «Прикрепить файлы»."""
    w = DocumentWidget(_make_attachment_task(allow_multiple=True))
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(0)
    buttons: list[QPushButton] = [
        b for b in w.form_area.findChildren(QPushButton) if b.objectName() == "attachButton"
    ]
    assert buttons and buttons[0].text() == "Прикрепить файлы"


def test_attachment_mode_shows_button_single(qtbot: QtBot) -> None:
    """ATTACHMENT allow_multiple=False → кнопка «Прикрепить файл»."""
    w = DocumentWidget(_make_attachment_task(allow_multiple=False))
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(0)
    buttons: list[QPushButton] = [
        b for b in w.form_area.findChildren(QPushButton) if b.objectName() == "attachButton"
    ]
    assert buttons and buttons[0].text() == "Прикрепить файл"


def test_attachment_getters_empty_before_pick(qtbot: QtBot) -> None:
    """До прикрепления файлов оба геттера возвращают пустые значения."""
    w = DocumentWidget(_make_attachment_task())
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(0)
    assert w.attachments() == ()
    assert w.attachment_bytes() == {}


def test_attachment_multiple_appends_files(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """allow_multiple=True: повторный вызов добавляет файлы, не заменяет."""
    f1 = tmp_path / "doc1.txt"
    f1.write_bytes(b"content1")
    f2 = tmp_path / "doc2.txt"
    f2.write_bytes(b"content2")

    w = DocumentWidget(_make_attachment_task(allow_multiple=True))
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(0)

    monkeypatch.setattr(QFileDialog, "getOpenFileNames", lambda *a, **kw: ([str(f1)], ""))
    w._pick_files(allow_multiple=True)

    monkeypatch.setattr(QFileDialog, "getOpenFileNames", lambda *a, **kw: ([str(f2)], ""))
    w._pick_files(allow_multiple=True)

    atts = w.attachments()
    assert len(atts) == 2
    assert {name for _, name in atts} == {"doc1.txt", "doc2.txt"}
    assert set(w.attachment_bytes().values()) == {b"content1", b"content2"}


def test_attachment_single_replaces_on_repeat(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """allow_multiple=False: повторное прикрепление заменяет предыдущее вложение."""
    f1 = tmp_path / "first.pdf"
    f1.write_bytes(b"first")
    f2 = tmp_path / "second.pdf"
    f2.write_bytes(b"second")

    w = DocumentWidget(_make_attachment_task(allow_multiple=False))
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(0)

    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **kw: (str(f1), ""))
    w._pick_files(allow_multiple=False)

    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **kw: (str(f2), ""))
    w._pick_files(allow_multiple=False)

    atts = w.attachments()
    assert len(atts) == 1
    assert atts[0][1] == "second.pdf"
    assert list(w.attachment_bytes().values()) == [b"second"]


def test_attachment_clear_empties_getters(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """_clear_attachments() обнуляет оба геттера."""
    f = tmp_path / "doc.txt"
    f.write_bytes(b"data")

    w = DocumentWidget(_make_attachment_task(allow_multiple=True))
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(0)

    monkeypatch.setattr(QFileDialog, "getOpenFileNames", lambda *a, **kw: ([str(f)], ""))
    w._pick_files(allow_multiple=True)
    assert len(w.attachments()) == 1

    w._clear_attachments()
    assert w.attachments() == ()
    assert w.attachment_bytes() == {}


def test_attachment_asset_ids_unique_and_match_bytes(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Каждое вложение получает уникальный asset_id; ключи attachment_bytes() совпадают."""
    f1 = tmp_path / "a.txt"
    f1.write_bytes(b"aaa")
    f2 = tmp_path / "b.txt"
    f2.write_bytes(b"bbb")

    w = DocumentWidget(_make_attachment_task(allow_multiple=True))
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(0)

    monkeypatch.setattr(
        QFileDialog, "getOpenFileNames", lambda *a, **kw: ([str(f1), str(f2)], "")
    )
    w._pick_files(allow_multiple=True)

    atts = w.attachments()
    ab = w.attachment_bytes()
    ids = [aid for aid, _ in atts]
    assert len(ids) == len(set(ids))
    assert set(ids) == set(ab.keys())


def test_attachment_list_widget_updated_on_pick(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """После pick QListWidget отображает имена прикреплённых файлов."""
    f = tmp_path / "report.docx"
    f.write_bytes(b"doc")

    w = DocumentWidget(_make_attachment_task(allow_multiple=True))
    qtbot.addWidget(w)
    w.options_combo.setCurrentIndex(0)

    monkeypatch.setattr(QFileDialog, "getOpenFileNames", lambda *a, **kw: ([str(f)], ""))
    w._pick_files(allow_multiple=True)

    lists: list[QListWidget] = w.form_area.findChildren(QListWidget)
    assert lists and lists[0].count() == 1
    assert lists[0].item(0).text() == "report.docx"


def test_attachment_getters_empty_in_other_modes(qtbot: QtBot) -> None:
    """FREE_TEXT и FIELDS-режимы не возвращают вложений."""
    w_free = DocumentWidget(_make_free_text_task())
    qtbot.addWidget(w_free)
    w_free.options_combo.setCurrentIndex(0)
    assert w_free.attachments() == ()
    assert w_free.attachment_bytes() == {}

    w_fields = DocumentWidget(_make_task())
    qtbot.addWidget(w_fields)
    w_fields.options_combo.setCurrentIndex(0)
    assert w_fields.attachments() == ()
    assert w_fields.attachment_bytes() == {}
