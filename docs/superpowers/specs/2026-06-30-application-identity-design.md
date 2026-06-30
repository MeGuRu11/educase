# ICON-1C: идентичность приложений и Windows-иконки

## Цель

Подключить подготовленные ICO к двум раздельным приложениям EpiCase:

- Constructor получает собственные имя, иконку и Windows AppUserModelID;
- Player получает собственные имя, иконку и Windows AppUserModelID;
- главное окно и панель задач показывают один и тот же вариант;
- будущая упаковка сохраняет два независимых EXE без переключателя ролей.

## Граница задачи

`ICON-1C` включает runtime-настройку `QApplication` и главных окон, а также
контракт для будущих PyInstaller-сборок.

`ICON-1C` не создаёт `.spec`-файлы и не собирает EXE. Это задача `PKG-1`.

## Раздельные приложения

Будущая поставка состоит из двух файлов:

- `EpiCase Constructor.exe` — только для преподавателя;
- `EpiCase Player.exe` — только для курсанта.

Единого EXE, выбора роли и скрытого перехода из Player в Constructor нет.
В `PKG-1` Constructor-сборка должна исключать `epicase_player`, а
Player-сборка — `epicase_constructor`. Курсантам выдаётся только Player EXE.

Общими остаются только безопасные внутренние пакеты `epicase_core` и
`epicase_ui`.

## Общий identity-модуль

Новый `src/epicase_ui/application_identity.py` содержит:

```python
class ApplicationVariant(StrEnum):
    CONSTRUCTOR = "constructor"
    PLAYER = "player"


@dataclass(frozen=True)
class ApplicationIdentity:
    application_name: str
    display_name: str
    app_user_model_id: str
    icon_filename: str
```

Фиксированный allowlist:

| Вариант | Application name | AppUserModelID | ICO |
|---|---|---|---|
| Constructor | `EpiCase Constructor` | `VMedA.EpiCase.Constructor` | `epicase_constructor.ico` |
| Player | `EpiCase Player` | `VMedA.EpiCase.Player` | `epicase_player.ico` |

Публичные функции:

- `application_identity(variant) -> ApplicationIdentity`;
- `application_icon(variant) -> QIcon`;
- `configure_application(app, variant) -> QIcon`.

`configure_application`:

1. назначает application name и display name;
2. загружает ICO через `importlib.resources`;
3. назначает иконку `QApplication`;
4. задаёт Windows AppUserModelID;
5. возвращает тот же `QIcon` для явного назначения главному окну.

## Entry points

Оба `__main__.py` сохраняют отдельные entrypoint:

```python
app = QApplication(sys.argv)
icon = configure_application(app, ApplicationVariant.CONSTRUCTOR)
app.setStyleSheet(load_qss())
window = MainWindow()
window.setWindowIcon(icon)
window.showMaximized()
```

Player использует `ApplicationVariant.PLAYER`.

Identity настраивается после создания `QApplication`, но до создания первого
окна. Логика открытия файлов и основной интерфейс не меняются.

## Windows AppUserModelID

На `sys.platform == "win32"` вызывается
`SetCurrentProcessExplicitAppUserModelID` из `shell32`.

На других платформах функция является no-op. Ошибка или отсутствие Windows API
логируется как предупреждение и не блокирует запуск приложения.

Разные AppUserModelID не позволяют Windows объединять Constructor и Player в
одну группу панели задач.

## Иконка и fallback

ICO читается только из allowlist package resources
`epicase_ui/resources/app_icons/`.

Если ресурс отсутствует или `QIcon` оказывается пустым:

- записывается предупреждение;
- возвращается пустой `QIcon`;
- приложение продолжает запуск;
- окно сохраняет стандартную системную иконку.

Произвольные пути и имена файлов публичный API не принимает.

## Тестирование

Тесты на реальных Qt-объектах проверяют:

- два различных `ApplicationIdentity`;
- точные AppUserModelID и имена ICO;
- загрузку двух непустых и различимых `QIcon`;
- application name, display name и window icon после настройки;
- Windows-вызов с правильным AppUserModelID;
- no-op на не-Windows платформе;
- безопасный fallback при отсутствующем ICO;
- выбор правильного варианта обоими entrypoint;
- назначение иконки главному окну до `showMaximized`.

После каждого изменения кода выполняется полный gate:

1. `ruff check src tests`;
2. `mypy src tests`;
3. `pytest -q`;
4. `python -m compileall -q src tests`.

## Критерии завершения

`ICON-1C` завершена, когда:

- оба entrypoint используют общий identity-модуль;
- Constructor и Player получают разные иконки и AppUserModelID;
- отсутствие ресурса или Windows API не блокирует запуск;
- тесты и полный gate зелёные;
- в `TASKS.md` закрыты `ICON-1C` и родительская `ICON-1`;
- `PKG-1` и создание двух `.spec`-файлов остаются открытыми.

## Живая проверка

Запустить Constructor и Player одновременно и проверить:

1. разные значки в заголовках окон;
2. разные значки и отдельные группы на панели задач;
3. разные записи в Alt+Tab;
4. сохранение иконок после minimize/restore;
5. отсутствие изменений в запуске и поведении приложений.
