"""Тесты фабрики build_stage_view — состав виджетов для каждого типа этапа."""
from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QLabel, QWidget
from pytestqt.qtbot import QtBot

from educase_core.domain.documents import DocumentOption, DocumentTask
from educase_core.domain.scheme import SchemeDocument, SchemeView
from educase_core.domain.search import InspectionCheck, KeywordSearch, SearchEntry, SynonymSet
from educase_core.domain.stages import (
    BranchOption,
    BranchPoint,
    PatientCard,
    StageClinical,
    StageContacts,
    StageEnvironment,
    StageFinal,
    StagePatients,
    StageSes,
    Timeline,
)
from educase_player.ui.asset_image_widget import AssetImageWidget
from educase_player.ui.branch_widget import BranchWidget
from educase_player.ui.document_widget import DocumentWidget
from educase_player.ui.inspection_widget import InspectionWidget
from educase_player.ui.patient_card_widget import PatientCardWidget
from educase_player.ui.scheme_viewer import SchemeViewerWidget
from educase_player.ui.search_widget import SearchWidget
from educase_player.ui.stage_views import build_stage_view
from educase_player.ui.timeline_widget import TimelineWidget


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


def test_stage_final_with_timelines_contains_timeline_widget(qtbot: QtBot) -> None:
    """StageFinal с timelines → TimelineWidget для каждого."""
    tl = Timeline(id="tl1", title="Сроки", events=(("01.01.2024", "Начало"),))
    stage = StageFinal(timelines=(tl,))
    view = build_stage_view(stage)
    qtbot.addWidget(view)

    widgets: list[TimelineWidget] = view.findChildren(TimelineWidget)
    assert len(widgets) == 1


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
