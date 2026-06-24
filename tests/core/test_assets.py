"""Тесты ``read_asset_sources``: I/O-сбор байтов ассетов драфта (Qt-free)."""
from __future__ import annotations

from pathlib import Path

import pytest

from epicase_core.application.assets import read_asset_sources
from epicase_core.application.case_builder import (
    AssetRef,
    CaseDraft,
    ClinicalDraft,
    ContactsDraft,
    EnvironmentDraft,
    FinalDraft,
    HotspotDraft,
    PatientDraft,
    SchemeViewDraft,
    SearchDraft,
    SearchEntryDraft,
    SesDraft,
    SynonymSetDraft,
)


def test_reads_scheme_bytes(tmp_path: Path) -> None:
    """Заданная ``contacts.scheme`` → ``{asset_id: те же байты файла}``."""
    source = tmp_path / "scheme.png"
    source.write_bytes(b"\x89PNG-bytes")

    draft = CaseDraft(
        case_id="case-a",
        contacts=ContactsDraft(scheme=AssetRef("a1.png", str(source))),
    )
    assets = read_asset_sources(draft)

    assert assets == {"a1.png": b"\x89PNG-bytes"}


def test_reads_contacts_and_environment_schemes(tmp_path: Path) -> None:
    """Обе схемы (этапы 3 и 4) собираются в один словарь по своим id."""
    contacts_src = tmp_path / "contacts.png"
    contacts_src.write_bytes(b"CONTACTS")
    env_src = tmp_path / "env.jpg"
    env_src.write_bytes(b"ENV")

    draft = CaseDraft(
        case_id="case-b",
        contacts=ContactsDraft(scheme=AssetRef("c1.png", str(contacts_src))),
        environment=EnvironmentDraft(scheme=AssetRef("e1.jpg", str(env_src))),
    )
    assets = read_asset_sources(draft)

    assert assets == {"c1.png": b"CONTACTS", "e1.jpg": b"ENV"}


def test_empty_scheme_gives_empty_dict() -> None:
    """Драфт без ассетов → пустой словарь."""
    draft = CaseDraft(case_id="case-c", contacts=ContactsDraft())
    assert read_asset_sources(draft) == {}


def test_missing_source_raises_oserror(tmp_path: Path) -> None:
    """Несуществующий ``source_path`` → ``OSError`` пробрасывается наверх."""
    draft = CaseDraft(
        case_id="case-d",
        contacts=ContactsDraft(scheme=AssetRef("x1.png", str(tmp_path / "ghost.png"))),
    )
    with pytest.raises(OSError):
        read_asset_sources(draft)


def _reveal_search(asset_id: str, source: Path) -> SearchDraft:
    """Поиск с одной точкой (непустой канон) и одним изображением вскрытия — для тестов этапов."""
    return SearchDraft(
        entries=(
            SearchEntryDraft(
                triggers=SynonymSetDraft(canonical="триггер"),
                reveal_assets=(AssetRef(asset_id, str(source)),),
            ),
        ),
    )


def test_reads_assets_from_all_locations(tmp_path: Path) -> None:
    """Ассеты из всех мест драфта (включая reveal всех трёх этапов с поиском) — в один словарь."""
    patient_src = tmp_path / "patient.png"
    patient_src.write_bytes(b"PATIENT")
    scheme_src = tmp_path / "scheme.png"
    scheme_src.write_bytes(b"SCHEME")
    photo_src = tmp_path / "photo.jpg"
    photo_src.write_bytes(b"PHOTO")
    clinical_src = tmp_path / "clinical.png"
    clinical_src.write_bytes(b"CLINICAL")
    ses_src = tmp_path / "ses.png"
    ses_src.write_bytes(b"SES")
    final_src = tmp_path / "final.png"
    final_src.write_bytes(b"FINAL")

    draft = CaseDraft(
        case_id="case-all",
        patients=(
            PatientDraft(title="П1", assets=(AssetRef("pa.png", str(patient_src)),)),
        ),
        contacts=ContactsDraft(scheme=AssetRef("sc.png", str(scheme_src))),
        environment=EnvironmentDraft(photos=(AssetRef("ph.jpg", str(photo_src)),)),
        clinical=ClinicalDraft(search=_reveal_search("cl.png", clinical_src)),
        ses=SesDraft(search=_reveal_search("se.png", ses_src)),
        final=FinalDraft(search=_reveal_search("fi.png", final_src)),
    )
    assets = read_asset_sources(draft)

    # Точный словарь: пропадание любого из трёх reveal-этапов сломает сравнение.
    assert assets == {
        "pa.png": b"PATIENT",
        "sc.png": b"SCHEME",
        "ph.jpg": b"PHOTO",
        "cl.png": b"CLINICAL",
        "se.png": b"SES",
        "fi.png": b"FINAL",
    }


def test_reveal_assets_of_dropped_entry_not_packed(tmp_path: Path) -> None:
    """Точка поиска с пустым каноном отбрасывается билдером → её ассет в архив НЕ пакуется."""
    reveal_src = tmp_path / "orphan.png"
    reveal_src.write_bytes(b"ORPHAN")

    draft = CaseDraft(
        case_id="case-orphan",
        clinical=ClinicalDraft(
            search=SearchDraft(
                entries=(
                    SearchEntryDraft(
                        triggers=SynonymSetDraft(canonical="   "),  # пустой → точка отброшена
                        reveal_assets=(AssetRef("or.png", str(reveal_src)),),
                    ),
                ),
            ),
        ),
    )
    assert read_asset_sources(draft) == {}


def test_reads_contacts_hotspot_photo_packed(tmp_path: Path) -> None:
    """Фото зоны (``hotspot.reveal_assets``) при заданном фоне → попадает в архив."""
    bg_src = tmp_path / "bg.png"
    bg_src.write_bytes(b"BG")
    zone_src = tmp_path / "zone.png"
    zone_src.write_bytes(b"ZONE-BYTES")

    draft = CaseDraft(
        case_id="case-hz",
        contacts=ContactsDraft(
            scheme=AssetRef("bg-1", str(bg_src)),
            hotspots=(
                HotspotDraft(
                    0.1,
                    0.2,
                    0.3,
                    0.4,
                    label="Спальное",
                    reveal_text="скученность",
                    reveal_assets=(AssetRef("z1", str(zone_src)),),
                ),
            ),
        ),
    )
    assets = read_asset_sources(draft)

    assert assets["z1"] == b"ZONE-BYTES"
    assert assets["bg-1"] == b"BG"


def test_environment_hotspot_photo_packed(tmp_path: Path) -> None:
    """Фото зоны этапа «Среда» при заданном фоне → попадает в архив."""
    bg_src = tmp_path / "bg.png"
    bg_src.write_bytes(b"BG")
    zone_src = tmp_path / "zone.png"
    zone_src.write_bytes(b"ZONE")

    draft = CaseDraft(
        case_id="case-ehz",
        environment=EnvironmentDraft(
            scheme=AssetRef("bg-2", str(bg_src)),
            hotspots=(
                HotspotDraft(0.0, 0.0, 0.5, 0.5, reveal_assets=(AssetRef("z2", str(zone_src)),)),
            ),
        ),
    )
    assets = read_asset_sources(draft)

    assert assets["z2"] == b"ZONE"


def test_hotspot_photo_without_scheme_not_packed(tmp_path: Path) -> None:
    """Зона без фона отбрасывается билдером → её фото в архив НЕ пакуется (orphan-логика)."""
    zone_src = tmp_path / "zone.png"
    zone_src.write_bytes(b"ORPHAN-ZONE")

    draft = CaseDraft(
        case_id="case-hz0",
        contacts=ContactsDraft(
            scheme=None,
            hotspots=(
                HotspotDraft(0.0, 0.0, 0.1, 0.1, reveal_assets=(AssetRef("z1", str(zone_src)),)),
            ),
        ),
    )
    assert read_asset_sources(draft) == {}


def test_nested_scheme_view_assets_packed(tmp_path: Path) -> None:
    """Фон вложенного вида и фото вложенной зоны пакуются, когда у вложенного вида задан фон."""
    bg_src = tmp_path / "bg.png"
    bg_src.write_bytes(b"BG")
    zone_src = tmp_path / "zone.png"
    zone_src.write_bytes(b"ZONE")
    child_bg_src = tmp_path / "child_bg.png"
    child_bg_src.write_bytes(b"CHILD-BG")
    child_zone_src = tmp_path / "child_zone.png"
    child_zone_src.write_bytes(b"CHILD-ZONE")

    draft = CaseDraft(
        case_id="case-nested",
        contacts=ContactsDraft(
            scheme=AssetRef("bg-1", str(bg_src)),
            hotspots=(
                HotspotDraft(
                    0.1,
                    0.2,
                    0.3,
                    0.4,
                    reveal_assets=(AssetRef("z1", str(zone_src)),),
                    child=SchemeViewDraft(
                        background=AssetRef("child-bg", str(child_bg_src)),
                        hotspots=(
                            HotspotDraft(
                                0.5,
                                0.5,
                                0.2,
                                0.2,
                                reveal_assets=(AssetRef("cz1", str(child_zone_src)),),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )
    assets = read_asset_sources(draft)

    assert assets["bg-1"] == b"BG"
    assert assets["z1"] == b"ZONE"
    assert assets["child-bg"] == b"CHILD-BG"
    assert assets["cz1"] == b"CHILD-ZONE"


def test_nested_scheme_view_without_background_not_packed(tmp_path: Path) -> None:
    """Вложенный вид без фона отброшен билдером → его фон/фото в архив НЕ пакуются (orphan)."""
    bg_src = tmp_path / "bg.png"
    bg_src.write_bytes(b"BG")
    child_zone_src = tmp_path / "child_zone.png"
    child_zone_src.write_bytes(b"ORPHAN-CHILD-ZONE")

    draft = CaseDraft(
        case_id="case-nested-orphan",
        contacts=ContactsDraft(
            scheme=AssetRef("bg-1", str(bg_src)),
            hotspots=(
                HotspotDraft(
                    0.1,
                    0.2,
                    0.3,
                    0.4,
                    child=SchemeViewDraft(
                        background=None,
                        hotspots=(
                            HotspotDraft(
                                0.5,
                                0.5,
                                0.2,
                                0.2,
                                reveal_assets=(AssetRef("cz1", str(child_zone_src)),),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )
    assert read_asset_sources(draft) == {"bg-1": b"BG"}


def test_duplicate_asset_id_deduplicated(tmp_path: Path) -> None:
    """Повтор одного ``asset_id`` в разных местах → один ключ (естественный дедуп словаря)."""
    source = tmp_path / "shared.png"
    source.write_bytes(b"SHARED")
    ref = AssetRef("dup.png", str(source))

    draft = CaseDraft(
        case_id="case-dup",
        patients=(PatientDraft(title="П1", assets=(ref,)),),
        environment=EnvironmentDraft(photos=(ref,)),
    )
    assets = read_asset_sources(draft)

    assert assets == {"dup.png": b"SHARED"}
