"""Сбор байтов ассетов кейса из исходных файлов (слой приложения).

Единственное место чтения файлов в цепочке сборки кейса: ``build_case`` и ``build_*`` —
чистые функции без I/O, поэтому чтение байтов ассетов вынесено сюда. Обход охватывает ВЕСЬ
драфт: ассеты карточек пациентов, схему/зоны/фото этапа «Среда», схему и зоны этапа
«Контакты» и изображения вскрытия всех точек поиска (клинический, СЭС, финал).
"""
from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from educase_core.application.case_builder import AssetRef, CaseDraft, HotspotDraft


def _iter_hotspot_assets(spots: tuple[HotspotDraft, ...]) -> Iterator[AssetRef]:
    """Рекурсивно выдать ассеты зон: фото вскрытия + фон/фото вложенных видов.

    Для каждой зоны выдаёт её ``reveal_assets``; если у зоны есть вложенный вид с заданным
    фоном — выдаёт фон вложенного вида и рекурсивно ассеты его зон. Вложенный вид без фона
    билдер отбрасывает (``_build_scheme_view``), поэтому его ассеты в архив не пакуются (та же
    orphan-логика на КАЖДОМ уровне вложенности).
    """
    for spot in spots:
        yield from spot.reveal_assets
        if spot.child is not None and spot.child.background is not None:
            yield spot.child.background
            yield from _iter_hotspot_assets(spot.child.hotspots)


def _iter_asset_refs(draft: CaseDraft) -> Iterator[AssetRef]:
    """Выдать все ``AssetRef`` драфта по всем местам ассетов кейса.

    Источники: ассеты карточек пациентов; схема и фото зон этапа «Контакты»; схема, фото зон и
    фото этапа «Среда»; изображения вскрытия точек поиска этапов с поиском (клинический, СЭС,
    финал). Этапы и схемы со значением ``None`` пропускаются. Фото зон выдаются только при
    заданном фоне схемы: без фона билдер отбрасывает зоны, поэтому их фото в архив не пакуются
    (иначе вышли бы недостижимые orphan-блобы). Зоны обходятся рекурсивно
    (``_iter_hotspot_assets``): фон и фото вложенных интерьерных видов зон выдаются тоже, но
    только при заданном фоне СООТВЕТСТВУЮЩЕГО уровня (orphan-логика сохраняется на каждом
    уровне — согласованно с ``_build_scheme_view``, который роняет вид без фона). Точки поиска с
    пустым каноническим триггером пропускаются ТОЧНО как в ``_build_search`` (case_builder): их
    домен-запись не создаётся, поэтому и байты их ассетов в архив не пакуются (та же orphan-логика).
    """
    for patient in draft.patients:
        yield from patient.assets
    if draft.contacts is not None and draft.contacts.scheme is not None:
        yield draft.contacts.scheme
        yield from _iter_hotspot_assets(draft.contacts.hotspots)
    if draft.environment is not None:
        if draft.environment.scheme is not None:
            yield draft.environment.scheme
            yield from _iter_hotspot_assets(draft.environment.hotspots)
        yield from draft.environment.photos
    for stage in (draft.clinical, draft.ses, draft.final):
        if stage is None:
            continue
        for entry in stage.search.entries:
            if not entry.triggers.canonical.strip():
                continue
            yield from entry.reveal_assets


def _asset_bytes(ref: AssetRef) -> bytes:
    """Байты ассета: из памяти (``ref.data`` загруженного кейса) либо из файла-источника.

    При открытии кейса на правку байты приходят прямо из архива (``ref.data``) — путь к
    исходному файлу утрачен. У нового/заменённого выбора в пикере ``data`` пуст, поэтому байты
    читаются ``Path(ref.source_path).read_bytes()``.
    """
    if ref.data is not None:
        return ref.data
    return Path(ref.source_path).read_bytes()


def read_asset_sources(draft: CaseDraft) -> dict[str, bytes]:
    """Прочитать байты всех ассетов драфта в ``{asset_id: bytes}``.

    Обходит весь драфт (``_iter_asset_refs``), для каждого ``AssetRef`` берёт байты через
    ``_asset_bytes`` (из памяти или из файла). Словарь по ``asset_id`` естественно
    дедуплицирует повторные ссылки. ``OSError`` (нет файла/нет доступа) пробрасывается
    наверх — обработает окно. Если ассетов нет — пустой словарь.
    """
    return {ref.asset_id: _asset_bytes(ref) for ref in _iter_asset_refs(draft)}


__all__ = ["read_asset_sources"]
