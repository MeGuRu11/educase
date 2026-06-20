"""Обращение доменного ``Case`` в ``CaseDraft`` для правки (этот срез: мета + пациенты).

Зеркало ``case_builder`` (драфт → домен): здесь домен раскладывается обратно в «сырые»
``*Draft``-структуры UI, чтобы редактор мог открыть сохранённый кейс. Ассеты восстанавливаются
ИЗ ПАМЯТИ (байты из архива ``LoadedCase.assets``): путь к исходному файлу и его имя при
загрузке утрачены, поэтому ``AssetRef`` собирается с ``data=<байты>``, пустым ``source_path`` и
``display_name=asset_id`` (для показа в пикере этого достаточно). Этапы 2–6 пока не обращаются
(остаются ``None``) — их добьют следующие срезы. Чистые функции без I/O.
"""
from __future__ import annotations

from collections.abc import Mapping

from educase_core.application.case_builder import AssetRef, CaseDraft, PatientDraft
from educase_core.application.cases import LoadedCase
from educase_core.domain.stages import PatientCard


def _asset_ref(asset_id: str, assets: Mapping[str, bytes]) -> AssetRef:
    """Собрать ``AssetRef`` загруженного ассета: байты из памяти, имя файла = ``asset_id``.

    Имя исходного файла при загрузке утрачено — для показа в пикере подставляется ``asset_id``.
    Вызывается только для известных ``asset_id`` (наличие в ``assets`` проверяет вызывающий).
    """
    return AssetRef(
        asset_id=asset_id,
        source_path="",
        display_name=asset_id,
        data=assets[asset_id],
    )


def _patient_to_draft(card: PatientCard, assets: Mapping[str, bytes]) -> PatientDraft:
    """Обратить ``PatientCard`` в ``PatientDraft``: заголовок, поля, ссылки на ассеты по id.

    Ссылки на ассеты без байтов в архиве (битые) отбрасываются: восстановить их в пикере
    нечем, а пере-сохранение всё равно не нашло бы файл.
    """
    return PatientDraft(
        title=card.title,
        fields=card.fields,
        assets=tuple(_asset_ref(a, assets) for a in card.assets if a in assets),
    )


def case_to_draft(loaded: LoadedCase) -> CaseDraft:
    """Обратить загруженный ``Case`` в ``CaseDraft`` для правки (этот срез: мета + пациенты).

    ``case_id`` берётся из меты — правка сохраняет идентичность кейса. Этапы 2–6 в этом срезе
    остаются ``None`` (их обращение — следующие срезы). Ассеты карточек пациентов
    восстанавливаются из памяти (``loaded.assets``).
    """
    case = loaded.case
    return CaseDraft(
        case_id=case.meta.id,
        title=case.meta.title,
        author=case.meta.author,
        nosology=case.meta.nosology,
        unit_personnel=case.meta.unit_personnel,
        patients=tuple(
            _patient_to_draft(p, loaded.assets) for p in case.patients.patients
        ),
        clinical=None,
        contacts=None,
        environment=None,
        ses=None,
        final=None,
    )


__all__ = ["case_to_draft"]
