"""Round-trip L1: ``case_to_draft`` (домен → драфт) и источники байтов ассетов (Qt-free)."""
from __future__ import annotations

from pathlib import Path

from educase_core.application.assets import read_asset_sources
from educase_core.application.case_builder import (
    AssetRef,
    CaseDraft,
    PatientDraft,
    build_case,
)
from educase_core.application.case_loader import case_to_draft
from educase_core.application.cases import LoadedCase, load_case, save_case
from educase_core.domain import Case, CaseMeta
from educase_core.domain.stages import PatientCard, StagePatients


def test_case_to_draft_round_trip(tmp_path: Path) -> None:
    """CaseDraft → .educase → load_case → case_to_draft: мета, пациенты и ассеты сохранены."""
    draft = CaseDraft(
        case_id="case-l1",
        title="Вспышка ОКИ",
        author="Иванов",
        nosology="Сальмонеллёз",
        unit_personnel=150,
        patients=(
            PatientDraft(
                title="Пациент 1",
                fields=(("Возраст", "25 лет"), ("Жалобы", "температура")),
                assets=(
                    AssetRef("p1-a.png", "", data=b"IMG-A"),
                    AssetRef("p1-b.png", "", data=b"IMG-B"),
                ),
            ),
            PatientDraft(title="Пациент 2", fields=(("Возраст", "30 лет"),)),
        ),
    )

    case = build_case(draft)
    assets = read_asset_sources(draft)
    dst = tmp_path / "c.educase"
    save_case(case, dst, assets=assets)

    reloaded = case_to_draft(load_case(dst))

    # Мета.
    assert reloaded.case_id == "case-l1"
    assert reloaded.title == "Вспышка ОКИ"
    assert reloaded.author == "Иванов"
    assert reloaded.nosology == "Сальмонеллёз"
    assert reloaded.unit_personnel == 150

    # Этапы 2–6 в этом срезе не обращаются — остаются пустыми.
    assert reloaded.clinical is None
    assert reloaded.contacts is None
    assert reloaded.environment is None
    assert reloaded.ses is None
    assert reloaded.final is None

    # Пациенты: заголовки и поля.
    assert [p.title for p in reloaded.patients] == ["Пациент 1", "Пациент 2"]
    assert reloaded.patients[0].fields == (
        ("Возраст", "25 лет"),
        ("Жалобы", "температура"),
    )
    assert reloaded.patients[1].fields == (("Возраст", "30 лет"),)
    assert reloaded.patients[1].assets == ()

    # Ассеты восстановлены из памяти: множество id и совпадение байтов.
    refs = reloaded.patients[0].assets
    assert {r.asset_id for r in refs} == {"p1-a.png", "p1-b.png"}
    by_id = {r.asset_id: r.data for r in refs}
    assert by_id["p1-a.png"] == b"IMG-A"
    assert by_id["p1-b.png"] == b"IMG-B"
    # Имя файла утрачено → display_name = asset_id; путь к файлу пуст.
    assert all(r.display_name == r.asset_id and r.source_path == "" for r in refs)


def test_case_to_draft_drops_assets_without_bytes() -> None:
    """Ссылка карточки без байтов в архиве (битая) отбрасывается при обращении."""
    case = Case(
        meta=CaseMeta(id="case-orphan"),
        patients=StagePatients(
            patients=(
                PatientCard(id="p1", title="П", assets=("present.png", "missing.png")),
            )
        ),
    )
    loaded = LoadedCase(case=case, assets={"present.png": b"OK"})

    reloaded = case_to_draft(loaded)
    refs = reloaded.patients[0].assets
    assert {r.asset_id for r in refs} == {"present.png"}
    assert refs[0].data == b"OK"


def test_read_asset_sources_uses_data_then_file(tmp_path: Path) -> None:
    """read_asset_sources: ``AssetRef`` с ``data`` берёт байты из памяти; без ``data`` — файл."""
    src = tmp_path / "real.png"
    src.write_bytes(b"FROM-FILE")

    draft = CaseDraft(
        case_id="case-src",
        patients=(
            PatientDraft(
                title="П",
                assets=(
                    AssetRef("mem.png", "", data=b"FROM-MEMORY"),
                    AssetRef("file.png", str(src)),
                ),
            ),
        ),
    )
    assert read_asset_sources(draft) == {
        "mem.png": b"FROM-MEMORY",
        "file.png": b"FROM-FILE",
    }
