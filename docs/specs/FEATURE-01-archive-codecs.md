# FEATURE-01 — Кодеки `.epicase` / `.epiresult`

Спецификация для роли **senior-developer (Opus)**. Первая фича: фундамент обмена. Кафедра не
нужна — это инженерное решение. Документная модель (ADR-009): архив — единственная
персистентность. Версионирование — manifest (ADR-010).

## Что создать → где

Каталог: `src/epicase_core/infrastructure/archive/`

| Файл | Содержимое |
|---|---|
| `__init__.py` *(есть)* | константы; **добавить** `DATA_NAME = "data.json"`, `ASSETS_DIR = "assets"` |
| `errors.py` *(новый)* | `ArchiveError`, `CorruptedArchiveError(ArchiveError)`, `IncompatibleVersionError(ArchiveError)` |
| `manifest.py` *(новый)* | dataclass `Manifest` + (де)сериализация |
| `codec.py` *(есть, заглушки)* | реализовать чтение/запись |

## Раскладка ZIP

```
<имя>.epicase  (ZIP)
├── manifest.json     # конверт (метаданные + контрольная сумма data.json)
├── data.json         # полезная нагрузка (payload). НЕ показывается пользователю
└── assets/           # бинарные ассеты (фото, документы), плоско по именам
    ├── <name1>
    └── <name2>
```

## Схема `manifest.json`

```json
{
  "format_version": 1,
  "kind": "epicase",
  "created_at": "2026-06-08T12:00:00Z",
  "checksum": "sha256:<hex>",
  "meta": { "case_id": "...", "title": "..." }
}
```
- `checksum` — sha256 от **байтов** `data.json`.
- `kind` — `"epicase"` или `"epiresult"`.
- `meta` — произвольные метаданные (необязательные).

## Сигнатуры (`codec.py`)

```python
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class ArchiveBundle:
    manifest: Manifest
    payload: dict[str, object]
    assets: dict[str, bytes]

def write_epicase(payload: Mapping[str, object], dst: Path, *,
                  assets: Mapping[str, bytes] | None = None,
                  meta: Mapping[str, object] | None = None) -> Path: ...

def read_epicase(src: Path) -> ArchiveBundle: ...

def write_epiresult(payload: Mapping[str, object], dst: Path, *,
                    assets: Mapping[str, bytes] | None = None,
                    meta: Mapping[str, object] | None = None) -> Path: ...

def read_epiresult(src: Path) -> ArchiveBundle: ...
```
Внутри — общие `_write_archive(kind, ext, ...)` и `_read_archive(expected_kind, src)`.
`write_*` гарантирует правильное расширение `dst`.

## Валидация при чтении
- не ZIP / нет `manifest.json` / нет `data.json` → `CorruptedArchiveError`.
- `format_version > FORMAT_VERSION` → `IncompatibleVersionError`.
- sha256(`data.json`) ≠ `manifest.checksum` → `CorruptedArchiveError`.
- `kind` не совпадает с ожидаемым (`read_epicase` на `.epiresult`) → `ArchiveError`.

## Ограничения
- Только stdlib: `zipfile`, `json`, `hashlib`, `datetime`, `pathlib`. Никакой сети, никаких новых
  зависимостей.
- Типы на всё (mypy strict); docstrings на русском; логирование через loguru, не print.
- Никаких хардкод-путей (`dst` задаёт вызывающий).
- JSON — внутренний формат, пользователю не показывается.

## Тесты (`tests/core/test_archive_codec.py`, на `tmp_path`)
- round-trip `.epicase`: write → read, payload и assets совпадают, `manifest.kind == "epicase"`.
- round-trip `.epiresult` аналогично.
- подмена `data.json` в архиве → `CorruptedArchiveError` (проверка checksum).
- `format_version = 99` → `IncompatibleVersionError`.
- `read_epicase` на `.epiresult` → `ArchiveError`.
- битый/не-ZIP файл → `CorruptedArchiveError`.

## Критерии приёмки
- `ruff check src tests` · `mypy src tests` · `pytest -q` · `compileall` — всё зелёное.
- Коммит: `feat(archive): кодеки .epicase/.epiresult с manifest и валидацией`.
