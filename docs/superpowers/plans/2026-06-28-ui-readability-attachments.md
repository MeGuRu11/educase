# UI Readability and Attachment Cards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Сделать подписи хотспотов читаемыми на любом фоне и заменить списки вложений компактными карточками в Player и отчёте Constructor.

**Architecture:** Геометрия схемы, домен и архивы не меняются. Хотспот получает графическую
плашку средствами `QGraphicsItem`; Player и Constructor строят собственные карточки вложений,
но используют общие чистые функции форматирования из `epicase_core.theme.file_labels` и единый
набор `objectName`/QSS.

**Tech Stack:** Python 3.12, PySide6 Widgets/Graphics View, QSS, pytest-qt, ruff, mypy strict.

---

### Task 1: Контрастная подпись хотспота

**Files:**
- Modify: `tests/player/test_scheme_viewer.py`
- Modify: `src/epicase_player/ui/scheme_viewer.py:35-45`
- Modify: `src/epicase_player/ui/scheme_viewer.py:273-289`

- [ ] **Step 1: Добавить падающий тест графической плашки**

В `tests/player/test_scheme_viewer.py` импортировать `QColor`, `QGraphicsPathItem`,
`QGraphicsRectItem`, `QGraphicsTextItem`, `QGraphicsView`, затем добавить:

```python
def test_viewer_hotspot_label_has_contrast_background_and_wraps(
    qtbot: QtBot, png_bytes: Callable[..., bytes]
) -> None:
    label = "Водонапорная башня с длинным названием"
    scheme = SchemeDocument(
        root=SchemeView(
            background="bg",
            hotspots=(
                Hotspot(
                    id="water",
                    label=label,
                    shape=HotspotShape(x=0.1, y=0.1, w=0.35, h=0.4),
                ),
            ),
        ),
    )
    viewer = SchemeViewerWidget(scheme, {"bg": png_bytes(300, 200)})
    qtbot.addWidget(viewer)

    graphics_view = viewer.findChild(QGraphicsView)
    assert graphics_view is not None
    scene = graphics_view.scene()
    assert scene is not None
    labels = [item for item in scene.items() if isinstance(item, QGraphicsTextItem)]
    backgrounds = [
        item for item in scene.items() if isinstance(item, QGraphicsPathItem)
    ]
    zones = [
        item
        for item in scene.items()
        if isinstance(item, QGraphicsRectItem) and item.parentItem() is None
    ]

    assert len(labels) == 1
    assert labels[0].toPlainText() == label
    assert labels[0].defaultTextColor() == QColor("#FFFFFF")
    assert labels[0].font().bold() is True
    assert 0 < labels[0].textWidth() <= 105
    assert len(backgrounds) == 1
    assert backgrounds[0].brush().color().alpha() >= 230
    assert len(zones) == 1
    assert zones[0].toolTip() == label
```

- [ ] **Step 2: Запустить тест и подтвердить RED**

Run:

```powershell
.\.venv\Scripts\pytest.exe -q tests/player/test_scheme_viewer.py::test_viewer_hotspot_label_has_contrast_background_and_wraps -o addopts=""
```

Expected: FAIL — сцена содержит `QGraphicsSimpleTextItem`, но не содержит
`QGraphicsTextItem`/`QGraphicsPathItem`.

- [ ] **Step 3: Реализовать плашку минимальным изменением**

В `scheme_viewer.py` заменить обычную подпись на `QGraphicsTextItem` и фон:

```python
_HOTSPOT_LABEL_BACKGROUND = QColor(20, 49, 48, 240)
_HOTSPOT_LABEL_TEXT = QColor("#FFFFFF")
_HOTSPOT_LABEL_PAD_X = 6.0
_HOTSPOT_LABEL_PAD_Y = 3.0

def _add_hotspot_label(
    rect_item: QGraphicsRectItem, label: str, rect: QRectF
) -> None:
    text_item = QGraphicsTextItem(label, rect_item)
    font = text_item.font()
    font.setBold(True)
    font.setPointSize(10)
    text_item.setFont(font)
    text_item.setDefaultTextColor(_HOTSPOT_LABEL_TEXT)
    text_item.setTextWidth(max(1.0, rect.width() - 2 * _HOTSPOT_LABEL_PAD_X))
    text_item.setPos(
        rect.left() + _HOTSPOT_LABEL_PAD_X,
        rect.top() + _HOTSPOT_LABEL_PAD_Y,
    )

    height = min(
        rect.height(),
        text_item.boundingRect().height() + 2 * _HOTSPOT_LABEL_PAD_Y,
    )
    path = QPainterPath()
    path.addRoundedRect(
        QRectF(rect.left(), rect.top(), rect.width(), height),
        3.0,
        3.0,
    )
    background = QGraphicsPathItem(path, rect_item)
    background.setPen(QPen(Qt.PenStyle.NoPen))
    background.setBrush(QBrush(_HOTSPOT_LABEL_BACKGROUND))
    background.setZValue(1.0)
    text_item.setZValue(2.0)
```

В `_add_hotspot` вычислить `rect` один раз, сохранить полный label в tooltip и вызвать
`_add_hotspot_label(rect_item, hotspot.label, rect)`. Удалить `_HOTSPOT_TEXT` и
`QGraphicsSimpleTextItem`.

- [ ] **Step 4: Проверить GREEN и существующую механику схемы**

Run:

```powershell
.\.venv\Scripts\pytest.exe -q tests/player/test_scheme_viewer.py tests/player/test_scheme_viewer_zoom.py -o addopts=""
```

Expected: все тесты PASS.

- [ ] **Step 5: Создать первый коммит**

```powershell
git add -- tests/player/test_scheme_viewer.py src/epicase_player/ui/scheme_viewer.py
git commit -m "feat(player): improve hotspot label contrast"
```

---

### Task 2: Общие подписи типа и размера файла

**Files:**
- Create: `src/epicase_core/theme/file_labels.py`
- Create: `tests/core/test_file_labels.py`

- [ ] **Step 1: Добавить падающие тесты форматирования**

```python
from epicase_core.theme.file_labels import file_size_label, file_type_label


def test_file_type_label_uses_extension_or_fallback() -> None:
    assert file_type_label("акт.pdf") == "PDF"
    assert file_type_label("план.docx") == "DOCX"
    assert file_type_label("README") == "ФАЙЛ"


def test_file_size_label_uses_compact_binary_units() -> None:
    assert file_size_label(248) == "248 Б"
    assert file_size_label(1024) == "1 КБ"
    assert file_size_label(1536) == "1,5 КБ"
    assert file_size_label(1024 * 1024) == "1 МБ"
```

- [ ] **Step 2: Запустить тест и подтвердить RED**

Run:

```powershell
.\.venv\Scripts\pytest.exe -q tests/core/test_file_labels.py -o addopts=""
```

Expected: collection ERROR `ModuleNotFoundError: epicase_core.theme.file_labels`.

- [ ] **Step 3: Реализовать чистые функции**

```python
"""Подписи типа и размера файла для UI Player и Constructor."""
from __future__ import annotations

from pathlib import Path


def file_type_label(filename: str) -> str:
    """Вернуть короткую верхнерегистровую подпись расширения."""
    suffix = Path(filename).suffix.removeprefix(".").upper()
    return suffix[:5] if suffix else "ФАЙЛ"


def file_size_label(byte_count: int) -> str:
    """Вернуть размер в Б/КБ/МБ с двоичными единицами и десятичной запятой."""
    size = max(0, byte_count)
    if size < 1024:
        return f"{size} Б"
    if size < 1024 * 1024:
        return f"{_number(size / 1024)} КБ"
    return f"{_number(size / (1024 * 1024))} МБ"


def _number(value: float) -> str:
    rounded = round(value, 1)
    if rounded.is_integer():
        return str(int(rounded))
    return f"{rounded:.1f}".replace(".", ",")
```

- [ ] **Step 4: Проверить GREEN**

Run:

```powershell
.\.venv\Scripts\pytest.exe -q tests/core/test_file_labels.py -o addopts=""
```

Expected: `2 passed`.

---

### Task 3: Компактные карточки вложений в Player

**Files:**
- Modify: `tests/player/test_document_widget.py:274-441`
- Modify: `src/epicase_player/ui/document_widget.py:8-22`
- Modify: `src/epicase_player/ui/document_widget.py:45-194`

- [ ] **Step 1: Заменить старый тест списка падающими тестами карточек**

Удалить импорт `QListWidget`, импортировать `QFrame` и добавить:

```python
def test_attachment_pick_renders_compact_file_card(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "report.pdf"
    source.write_bytes(b"x" * 1536)
    widget = DocumentWidget(_make_attachment_task())
    qtbot.addWidget(widget)
    widget.options_combo.setCurrentIndex(0)
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileNames",
        lambda *args, **kwargs: ([str(source)], ""),
    )

    widget._pick_files(allow_multiple=True)

    cards = widget.form_area.findChildren(QFrame, "attachmentCard")
    assert len(cards) == 1
    texts = [label.text() for label in cards[0].findChildren(QLabel)]
    assert "PDF" in texts
    assert "report.pdf" in texts
    assert "1,5 КБ" in texts
    assert widget.form_area.findChild(QLabel, "attachmentEmpty").isHidden()
    title = widget.form_area.findChild(QLabel, "attachmentSectionTitle")
    assert title is not None
    assert title.text() == "Прикреплённые файлы · 1"
```

```python
def test_attachment_remove_button_removes_only_its_file(
    qtbot: QtBot, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = tmp_path / "first.pdf"
    second = tmp_path / "second.docx"
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    widget = DocumentWidget(_make_attachment_task())
    qtbot.addWidget(widget)
    widget.options_combo.setCurrentIndex(0)
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileNames",
        lambda *args, **kwargs: ([str(first), str(second)], ""),
    )
    widget._pick_files(allow_multiple=True)

    remove_buttons = widget.form_area.findChildren(
        QPushButton, "attachmentRemoveButton"
    )
    assert len(remove_buttons) == 2
    remove_buttons[0].click()

    assert len(widget.attachments()) == 1
    assert widget.attachments()[0][1] == "second.docx"
```

- [ ] **Step 2: Запустить тесты и подтвердить RED**

Run:

```powershell
.\.venv\Scripts\pytest.exe -q tests/player/test_document_widget.py -o addopts=""
```

Expected: новые тесты FAIL — `attachmentCard` и `attachmentRemoveButton` отсутствуют.

- [ ] **Step 3: Построить карточки и пустое состояние**

Импортировать `file_size_label`/`file_type_label` из
`epicase_core.theme.file_labels`. В `DocumentWidget` хранить:

```python
self._attach_cards_layout: QVBoxLayout | None = None
self._attach_header: QLabel | None = None
self._attach_empty: QLabel | None = None
self._clear_button: QPushButton | None = None
```

Добавить:

```python
def _remove_attachment(self, asset_id: str) -> None:
    self._attachments = [
        pair for pair in self._attachments if pair[0] != asset_id
    ]
    self._attach_bytes.pop(asset_id, None)
    self._refresh_attach_list()

def _attachment_card(self, asset_id: str, filename: str) -> QFrame:
    card = QFrame()
    card.setObjectName("attachmentCard")
    row = QHBoxLayout(card)

    badge = QLabel(file_type_label(filename))
    badge.setObjectName("attachmentTypeBadge")
    row.addWidget(badge)

    text = QVBoxLayout()
    name = QLabel(filename)
    name.setObjectName("attachmentName")
    meta = QLabel(file_size_label(len(self._attach_bytes[asset_id])))
    meta.setObjectName("attachmentMeta")
    text.addWidget(name)
    text.addWidget(meta)
    row.addLayout(text, 1)

    remove = QPushButton("Удалить")
    remove.setObjectName("attachmentRemoveButton")
    remove.clicked.connect(lambda: self._remove_attachment(asset_id))
    row.addWidget(remove)
    return card
```

В `_rebuild_form` создать `QFrame#attachmentListPanel`, заголовок
`QLabel#attachmentSectionTitle`, `QLabel#attachmentEmpty` и кнопку
`QPushButton#attachClear`. В `_refresh_attach_list` удалить старые карточки через
`setParent(None)/deleteLater()`, обновить заголовок `Прикреплённые файлы · N`,
пустое состояние и видимость «Очистить всё».

- [ ] **Step 4: Проверить все тесты DocumentWidget**

Run:

```powershell
.\.venv\Scripts\pytest.exe -q tests/player/test_document_widget.py tests/player/test_stage_views.py -o addopts=""
```

Expected: все тесты PASS, включая запись байтов и single/multiple semantics.

---

### Task 4: Карточки вложений в отчёте и единый QSS

**Files:**
- Modify: `tests/constructor/test_report_view.py:216-297`
- Modify: `src/epicase_constructor/ui/report_view.py:116-158`
- Modify: `src/epicase_core/theme/theme.qss:203-262`
- Modify: `TASKS.md`

- [ ] **Step 1: Добавить падающий тест карточки отчёта**

```python
def test_report_view_renders_attachment_card_metadata(qtbot: QtBot) -> None:
    view = ReportView(_attachment_report(), {"att-1": b"x" * 1536})
    qtbot.addWidget(view)

    cards = view.findChildren(QFrame, "attachmentCard")
    assert len(cards) == 1
    texts = [label.text() for label in cards[0].findChildren(QLabel)]
    assert "PDF" in texts
    assert "донесение.pdf" in texts
    assert "1,5 КБ" in texts
    title = view.findChild(QLabel, "attachmentSectionTitle")
    assert title is not None
    assert title.text() == "Вложенные документы · 1"
```

Импортировать `QFrame` в `tests/constructor/test_report_view.py`. В тесте missing asset
дополнительно проверить наличие
`QLabel#attachmentWarning`.

- [ ] **Step 2: Запустить тест и подтвердить RED**

Run:

```powershell
.\.venv\Scripts\pytest.exe -q tests/constructor/test_report_view.py -o addopts=""
```

Expected: FAIL — `attachmentCard`, metadata и новый заголовок отсутствуют.

- [ ] **Step 3: Перестроить строку отчёта в карточку**

В `_attachments_section` установить заголовок:

```python
header = QLabel(f"{_ATTACHMENTS_HEADER} · {len(attachments)}")
header.setObjectName("attachmentSectionTitle")
```

Импортировать `file_size_label`/`file_type_label` из
`epicase_core.theme.file_labels`. В `_attachment_row` использовать `QFrame#attachmentCard`, badge
`QLabel#attachmentTypeBadge`, `QLabel#attachmentName` и metadata:

```python
if present:
    meta = QLabel(file_size_label(len(self._assets[asset_id])))
    meta.setObjectName("attachmentMeta")
else:
    meta = QLabel(_MISSING_ASSET)
    meta.setObjectName("attachmentWarning")
```

Существующие `attachmentOpenButton`/`attachmentSaveButton`, их callbacks и поведение
missing asset сохранить.

- [ ] **Step 4: Добавить QSS карточек**

Добавить в `theme.qss`:

```css
QFrame#attachmentListPanel {
    background: #F6F8FA;
    border: 1px solid #D4DAE0;
    border-radius: 8px;
}
QFrame#attachmentCard {
    background: #FFFFFF;
    border: 1px solid #D4DAE0;
    border-radius: 8px;
}
QLabel#attachmentSectionTitle,
QLabel#attachmentName {
    color: #1F2A33;
    font-weight: bold;
}
QLabel#attachmentTypeBadge {
    color: #0F766E;
    background: #D9EEEB;
    border-radius: 6px;
    padding: 7px;
    font-weight: bold;
}
QLabel#attachmentMeta,
QLabel#attachmentEmpty {
    color: #66727E;
}
QLabel#attachmentWarning {
    color: #B45454;
}
QPushButton#attachButton,
QPushButton#attachmentOpenButton {
    background: #0F766E;
    color: #FFFFFF;
    border-color: #0F766E;
}
QPushButton#attachClear,
QPushButton#attachmentRemoveButton,
QPushButton#attachmentSaveButton {
    background: #FFFFFF;
    color: #40515F;
}
```

Добавить состояния акцентных кнопок:

```css
QPushButton#attachButton:hover,
QPushButton#attachmentOpenButton:hover {
    background: #0B5E57;
    border-color: #0B5E57;
}
QPushButton#attachButton:pressed,
QPushButton#attachmentOpenButton:pressed {
    background: #0A524C;
    border-color: #0A524C;
}
```

- [ ] **Step 5: Обновить TASKS.md**

В раздел готового добавить без volatile HEAD:

```markdown
- [x] UI: контрастные подписи хотспотов на фотографиях
- [x] UI: компактные карточки вложений в Player и отчёте Constructor
```

- [ ] **Step 6: Проверить связанные тесты**

Run:

```powershell
.\.venv\Scripts\pytest.exe -q tests/core/test_file_labels.py tests/player/test_document_widget.py tests/player/test_stage_views.py tests/constructor/test_report_view.py -o addopts=""
```

Expected: все тесты PASS.

- [ ] **Step 7: Создать второй коммит**

```powershell
git add -- src/epicase_core/theme/file_labels.py src/epicase_core/theme/theme.qss src/epicase_player/ui/document_widget.py src/epicase_constructor/ui/report_view.py tests/core/test_file_labels.py tests/player/test_document_widget.py tests/constructor/test_report_view.py TASKS.md
git commit -m "feat(attachments): present files as compact cards"
```

---

### Task 5: Полная проверка и живая приёмка

**Files:**
- Verify: all modified files
- Fixture: `C:\Users\user\Desktop\Program\educase_testdata\shigellosis.epicase`
- Fixture: `C:\Users\user\Desktop\Program\educase_testdata\shigellosis_mixed.epiresult`

- [ ] **Step 1: Запустить обязательный quality gate по порядку**

```powershell
.\.venv\Scripts\ruff.exe check src tests
.\.venv\Scripts\mypy.exe src tests
.\.venv\Scripts\pytest.exe -q
.\.venv\Scripts\python.exe -m compileall -q src tests
```

Expected: четыре команды завершаются с exit code 0.

- [ ] **Step 2: Проверить состав и чистоту изменений**

```powershell
git diff --check
git status --short
git log --oneline -5
```

Expected: `git diff --check` без ошибок; после коммитов рабочее дерево чистое.

- [ ] **Step 3: Проверить вживую Player**

1. Открыть `shigellosis.epicase`.
2. На этапах 3–4 проверить читаемость каждой подписи на светлых и тёмных участках.
3. Проверить «Водонапорная башня», вложенные виды, зум, панорамирование и клики.
4. Прикрепить один файл, затем два файла; проверить карточки, размеры, удаление одного
   и «Очистить всё».

- [ ] **Step 4: Проверить вживую Constructor**

1. Открыть `shigellosis_mixed.epiresult` и исходный кейс.
2. Проверить число вложений, badges, имена и размеры.
3. Проверить «Открыть» и «Сохранить как…».
4. Убедиться, что статусы `верно/неверно/не отвечено`, таймлайны и отсутствие баллов
   не изменились.
