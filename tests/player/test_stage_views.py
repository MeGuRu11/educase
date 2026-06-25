"""Тесты фабрики build_stage_view — состав виджетов для каждого типа этапа."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from PySide6.QtWidgets import QFileDialog, QLabel, QWidget
from pytestqt.qtbot import QtBot

from epicase_core.domain.documents import DocumentOption, DocumentTask, DocumentTemplate, FillMode
from epicase_core.domain.scheme import SchemeDocument, SchemeView
from epicase_core.domain.search import InspectionCheck, KeywordSearch, SearchEntry, SynonymSet
from epicase_core.domain.stages import (
    BranchOption,
    BranchPoint,
    PatientCard,
    StageClinical,
    StageContacts,
    StageEnvironment,
    StageFinal,
    StagePatients,
    StageSes,
)
from epicase_player.ui.asset_image_widget import AssetImageWidget
from epicase_player.ui.branch_widget import BranchWidget
from epicase_player.ui.document_widget import DocumentWidget
from epicase_player.ui.inspection_widget import InspectionWidget
from epicase_player.ui.patient_card_widget import PatientCardWidget
from epicase_player.ui.scheme_viewer import SchemeViewerWidget
from epicase_player.ui.search_widget import SearchWidget
from epicase_player.ui.stage_views import _doc_resp, build_stage_view


def _find_search_widget(widget: QWidget) -> SearchWidget | None:
    children: list[SearchWidget] = widget.findChildren(SearchWidget)
    return children[0] if children else None


def _one_entry_search() -> KeywordSearch:
    return KeywordSearch(
        entries=(
            SearchEntry(
                id="e1",
                triggers=SynonymSet(canonical="тест"),
                reveal_text="Результат поиска.",
            ),
        )
    )


def test_stage_with_search_contains_search_widget(qtbot: QtBot) -> None:
    """Этап с непустым search → SearchWidget присутствует."""
    stage = StageClinical(search=_one_entry_search())
    view = build_stage_view(stage)
    qtbot.addWidget(view)

    assert _find_search_widget(view) is not None


def test_stage_without_search_field_no_widget(qtbot: QtBot) -> None:
    """Этап без атрибута search (StageContacts) → SearchWidget отсутствует."""
    stage = StageContacts()
    view = build_stage_view(stage)
    qtbot.addWidget(view)

    assert _find_search_widget(view) is None


def test_stage_with_none_search_no_widget(qtbot: QtBot) -> None:
    """Этап с search=None → SearchWidget не добавляется."""
    stage = StageClinical(search=None)
    view = build_stage_view(stage)
    qtbot.addWidget(view)

    assert _find_search_widget(view) is None


def test_stage_with_empty_entries_no_widget(qtbot: QtBot) -> None:
    """Этап с search.entries=() → SearchWidget не добавляется."""
    stage = StageClinical(search=KeywordSearch(entries=()))
    view = build_stage_view(stage)
    qtbot.addWidget(view)

    assert _find_search_widget(view) is None


def test_stage_with_documents_contains_document_widget(qtbot: QtBot) -> None:
    """Этап с непустым documents → DocumentWidget присутствует для каждого DocumentTask."""
    task = DocumentTask(
        id="t1",
        prompt="Выберите документ",
        options=(DocumentOption(id="opt1", title="Документ А"),),
    )
    stage = StageClinical(documents=(task,))
    view = build_stage_view(stage)
    qtbot.addWidget(view)

    widgets: list[DocumentWidget] = view.findChildren(DocumentWidget)
    assert len(widgets) == 1


def test_stage_without_documents_no_document_widget(qtbot: QtBot) -> None:
    """Этап без documents → DocumentWidget отсутствует."""
    stage = StageClinical(documents=())
    view = build_stage_view(stage)
    qtbot.addWidget(view)

    widgets: list[DocumentWidget] = view.findChildren(DocumentWidget)
    assert len(widgets) == 0


# --- Новые тесты: индивидуальная сборка этапов ---


def test_stage_patients_with_cards_contains_patient_card_widget(qtbot: QtBot) -> None:
    """StagePatients с пациентами → PatientCardWidget для каждого."""
    card = PatientCard(id="p1", title="Пациент 1", fields=(("Диагноз", "ОРВИ"),))
    stage = StagePatients(patients=(card,))
    view = build_stage_view(stage)
    qtbot.addWidget(view)

    widgets: list[PatientCardWidget] = view.findChildren(PatientCardWidget)
    assert len(widgets) == 1


def test_stage_clinical_with_branch_contains_branch_widget(qtbot: QtBot) -> None:
    """StageClinical с branch → BranchWidget присутствует."""
    branch = BranchPoint(
        id="bp1",
        prompt="Выберите диагноз",
        options=(BranchOption(id="o1", label="Да", is_correct=True),),
    )
    stage = StageClinical(branch=branch)
    view = build_stage_view(stage)
    qtbot.addWidget(view)

    widgets: list[BranchWidget] = view.findChildren(BranchWidget)
    assert len(widgets) == 1


def test_stage_clinical_without_branch_no_branch_widget(qtbot: QtBot) -> None:
    """StageClinical без branch → BranchWidget отсутствует."""
    stage = StageClinical(branch=None)
    view = build_stage_view(stage)
    qtbot.addWidget(view)

    widgets: list[BranchWidget] = view.findChildren(BranchWidget)
    assert len(widgets) == 0


def test_stage_final_does_not_render_timeline_widget(qtbot: QtBot) -> None:
    """StageFinal с timelines НЕ рендерит TimelineWidget курсанту (эталон скрыт)."""
    from epicase_core.domain.stages import Timeline
    from epicase_player.ui.timeline_widget import TimelineWidget

    tl = Timeline(id="tl1", title="Сроки", events=(("01.01.2024", "Начало"),))
    stage = StageFinal(timelines=(tl,))
    view = build_stage_view(stage)
    qtbot.addWidget(view)

    widgets: list[TimelineWidget] = view.findChildren(TimelineWidget)
    assert len(widgets) == 0


def test_stage_contacts_with_inspection_contains_inspection_widget(qtbot: QtBot) -> None:
    """StageContacts с inspection → InspectionWidget присутствует."""
    inspection = InspectionCheck(expected=(SynonymSet(canonical="вода"),))
    stage = StageContacts(inspection=inspection)
    view = build_stage_view(stage)
    qtbot.addWidget(view)

    widgets: list[InspectionWidget] = view.findChildren(InspectionWidget)
    assert len(widgets) == 1


def test_stage_environment_with_inspection_contains_inspection_widget(qtbot: QtBot) -> None:
    """StageEnvironment с inspection → InspectionWidget присутствует."""
    inspection = InspectionCheck(expected=(SynonymSet(canonical="туалет"),))
    stage = StageEnvironment(inspection=inspection)
    view = build_stage_view(stage)
    qtbot.addWidget(view)

    widgets: list[InspectionWidget] = view.findChildren(InspectionWidget)
    assert len(widgets) == 1


def test_empty_stage_shows_no_tasks_label(qtbot: QtBot) -> None:
    """Пустой StagePatients (нет search, нет patients) → строка «Нет заданий на этом этапе»."""
    stage = StagePatients()
    view = build_stage_view(stage)
    qtbot.addWidget(view)

    labels: list[QLabel] = view.findChildren(QLabel)
    texts = [lbl.text() for lbl in labels]
    assert any("Нет заданий" in t for t in texts)


def test_stage_ses_with_documents_contains_document_widget(qtbot: QtBot) -> None:
    """StageSes с documents → DocumentWidget присутствует."""
    task = DocumentTask(
        id="t1",
        prompt="Выберите документ",
        options=(DocumentOption(id="opt1", title="Приказ"),),
    )
    stage = StageSes(documents=(task,))
    view = build_stage_view(stage)
    qtbot.addWidget(view)

    widgets: list[DocumentWidget] = view.findChildren(DocumentWidget)
    assert len(widgets) == 1


# --- Рендер изображений ассетов (схема/фото), заход 3 ---


def test_contacts_scheme_present_renders_image(
    qtbot: QtBot, png_bytes: Callable[..., bytes]
) -> None:
    """StageContacts со scheme, чей фон присутствует в assets → SchemeViewerWidget с фоном."""
    stage = StageContacts(scheme=SchemeDocument(root=SchemeView(background="scheme-1")))
    view = build_stage_view(stage, {"scheme-1": png_bytes()})
    qtbot.addWidget(view)

    viewers: list[SchemeViewerWidget] = view.findChildren(SchemeViewerWidget)
    assert len(viewers) == 1
    assert viewers[0].has_background() is True


def test_contacts_scheme_missing_shows_placeholder(qtbot: QtBot) -> None:
    """StageContacts со scheme без байт фона → SchemeViewerWidget-плейсхолдер, без падения."""
    stage = StageContacts(scheme=SchemeDocument(root=SchemeView(background="ghost")))
    view = build_stage_view(stage, {})  # байт нет
    qtbot.addWidget(view)

    viewers: list[SchemeViewerWidget] = view.findChildren(SchemeViewerWidget)
    assert len(viewers) == 1
    assert viewers[0].has_background() is False


def test_environment_two_photos_render_images(
    qtbot: QtBot, png_bytes: Callable[..., bytes]
) -> None:
    """StageEnvironment с двумя photos в assets → два AssetImageWidget с изображениями."""
    stage = StageEnvironment(photos=("ph-1", "ph-2"))
    view = build_stage_view(stage, {"ph-1": png_bytes(), "ph-2": png_bytes()})
    qtbot.addWidget(view)

    images: list[AssetImageWidget] = view.findChildren(AssetImageWidget)
    assert len(images) == 2
    assert all(img.has_image() for img in images)


def test_environment_scheme_present_renders_image(
    qtbot: QtBot, png_bytes: Callable[..., bytes]
) -> None:
    """StageEnvironment со scheme, чей фон в assets → SchemeViewerWidget с фоном."""
    stage = StageEnvironment(scheme=SchemeDocument(root=SchemeView(background="env-scheme")))
    view = build_stage_view(stage, {"env-scheme": png_bytes()})
    qtbot.addWidget(view)

    viewers: list[SchemeViewerWidget] = view.findChildren(SchemeViewerWidget)
    assert len(viewers) == 1
    assert viewers[0].has_background() is True


def test_environment_scheme_missing_shows_placeholder(qtbot: QtBot) -> None:
    """StageEnvironment со scheme без байт фона → SchemeViewerWidget-плейсхолдер, без падения."""
    stage = StageEnvironment(scheme=SchemeDocument(root=SchemeView(background="ghost")))
    view = build_stage_view(stage, {})
    qtbot.addWidget(view)

    viewers: list[SchemeViewerWidget] = view.findChildren(SchemeViewerWidget)
    assert len(viewers) == 1
    assert viewers[0].has_background() is False


def test_environment_photos_dangling_refs_show_placeholders(qtbot: QtBot) -> None:
    """Инвариант висячей ссылки через цикл фото: нет байт / мусор → плейсхолдеры, без исключения."""
    stage = StageEnvironment(photos=("missing", "garbage"))
    # "missing" — нет байт вовсе; "garbage" — байты есть, но не изображение.
    view = build_stage_view(stage, {"garbage": b"not an image"})
    qtbot.addWidget(view)

    images: list[AssetImageWidget] = view.findChildren(AssetImageWidget)
    assert len(images) == 2
    assert all(img.has_image() is False for img in images)


# --- ADR-015: ATTACHMENT и collect_assets ---


def _make_attachment_option() -> DocumentOption:
    return DocumentOption(
        id="opt_att",
        title="Акт",
        is_correct=True,
        template=DocumentTemplate(
            id="tpl_att",
            title="Акт",
            fill_mode=FillMode.ATTACHMENT,
            allow_multiple=True,
        ),
    )


def test_doc_resp_includes_attachments(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """_doc_resp кладёт attachments в DocumentResponse."""
    f = tmp_path / "file.txt"
    f.write_bytes(b"x")
    task = DocumentTask(id="t1", prompt="", options=(_make_attachment_option(),))
    widget = DocumentWidget(task)
    qtbot.addWidget(widget)
    widget.options_combo.setCurrentIndex(0)

    monkeypatch.setattr(QFileDialog, "getOpenFileNames", lambda *a, **kw: ([str(f)], ""))
    widget._pick_files(allow_multiple=True)

    resp = _doc_resp(task, widget)
    assert len(resp.attachments) == 1
    asset_id, name = resp.attachments[0]
    assert name == "file.txt"
    assert asset_id in widget.attachment_bytes()


def test_collect_assets_clinical_with_attachment(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ClinicalStageView.collect_assets() возвращает байты ATTACHMENT-вложений."""
    f = tmp_path / "act.pdf"
    f.write_bytes(b"pdf data")
    task = DocumentTask(id="t1", prompt="", options=(_make_attachment_option(),))
    stage = StageClinical(documents=(task,))
    view = build_stage_view(stage)
    qtbot.addWidget(view)

    doc_widgets: list[DocumentWidget] = view.findChildren(DocumentWidget)
    assert len(doc_widgets) == 1
    dw = doc_widgets[0]
    dw.options_combo.setCurrentIndex(0)

    monkeypatch.setattr(QFileDialog, "getOpenFileNames", lambda *a, **kw: ([str(f)], ""))
    dw._pick_files(allow_multiple=True)

    assets = view.collect_assets()
    assert len(assets) == 1
    assert list(assets.values()) == [b"pdf data"]


def test_collect_assets_empty_without_attachments(qtbot: QtBot) -> None:
    """collect_assets() пуст, если нет ATTACHMENT-вложений."""
    stage = StageClinical()
    view = build_stage_view(stage)
    qtbot.addWidget(view)
    assert view.collect_assets() == {}
