# PKG-1: автономные PyInstaller-сборки

## Цель

Собирать для Windows два независимых `one-file` GUI-приложения:

- `dist/EpiCase Constructor.exe`;
- `dist/EpiCase Player.exe`.

Рядом с EXE не требуются дополнительные файлы.

## Конфигурация

Два существующих spec-файла остаются единственным источником конфигурации:

- `packaging/constructor.spec`;
- `packaging/player.spec`.

Все пути вычисляются от каталога spec-файла и не зависят от текущего рабочего
каталога. Обе сборки используют `console=False` и `upx=False`.

Constructor включает только `epicase_constructor`, `epicase_core` и `epicase_ui`,
исключая `epicase_player`. Player включает только `epicase_player`,
`epicase_core` и `epicase_ui`, исключая `epicase_constructor`.

## Ресурсы и иконки

Обе сборки включают:

- `epicase_core/theme/theme.qss`;
- `epicase_ui/resources`, включая фирменные ICO, брендовые и hotspot-иконки.

Constructor дополнительно включает `epicase_constructor/resources/icons`.

Параметр `icon` у каждого EXE указывает на соответствующий подготовленный ICO:

- `epicase_constructor.ico`;
- `epicase_player.ico`.

Эти же ICO загружаются приложениями во время работы через `importlib.resources`.

## Проверка

Автоматическая проверка фиксирует контракт обоих spec-файлов: entrypoint,
one-file GUI-режим, имя, EXE-иконку, datas и исключение второго приложения.

После неё выполняются реальные PyInstaller-сборки. Для каждого EXE проверяются:

- наличие единственного автономного файла;
- успешный запуск без отсутствующих модулей и ресурсов;
- применение темы и непустая фирменная иконка.

Затем выполняется полный quality gate проекта. После успешной проверки PKG-1
отмечается выполненной в `TASKS.md`.

## Вне scope

Установщик, подпись кода, автообновление, сетевые функции и объединённый выбор
роли не добавляются.
