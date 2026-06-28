---
name: epicase-archive-format
description: >-
  Формат `.epicase` и `.epiresult`: ZIP, manifest, data.json и ассеты.
  Используй для импорта, экспорта и упаковки файлов.
---

# Формат архивов EpiCase

## Контейнер

```text
manifest.json
data.json
assets/<asset_id>
```

JSON не показывается пользователю. Обмен выполняется только локальными файлами.

## Расширения и функции

- `.epicase`: `write_epicase` / `read_epicase`;
- `.epiresult`: `write_epiresult` / `read_epiresult`.

Код находится в `epicase_core/infrastructure/archive`. UI вызывает его только через
`epicase_core.application.cases` и `epicase_core.application.results`.

## Manifest

- `format_version` — текущая версия `1`;
- `kind` — `epicase` или `epiresult`;
- `created_at`;
- `checksum` — SHA-256 байтов `data.json`;
- `meta` — id, название и другие служебные метаданные.

## Валидация

Кодек проверяет ZIP, наличие обязательных записей, тип архива, поддерживаемую версию,
JSON-объект и контрольную сумму. Ошибки представлены `ArchiveError`,
`CorruptedArchiveError`, `IncompatibleVersionError`.

Кейс и результат сериализуются доменными `to_dict/from_dict`; байты фото и документов
хранятся отдельно в `assets/`.
