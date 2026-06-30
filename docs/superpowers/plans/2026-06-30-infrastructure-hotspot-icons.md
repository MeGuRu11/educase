# Infrastructure Hotspot Icons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Constructor сохраняет выбранный тип инфраструктуры, а Player показывает утверждённые картографические пины вместо постоянно видимых прямоугольников.

**Architecture:** `Hotspot.icon` уже существует в domain и архиве. Ключ проводится через application draft; allowlist SVG и общий `HotspotMarkerItem` живут в `epicase_ui`; прямоугольник остаётся областью редактирования в Constructor и невидимым hit-area в Player.

**Tech Stack:** Python 3.12, PySide6 Widgets/Graphics View/QtSvg, pytest, pytest-qt, ruff, mypy strict.

---

## Правила выполнения

В PowerShell сначала привязать общую `.venv` к текущему worktree:

```powershell
$env:PYTHONPATH = (Resolve-Path 'src').Path
```

Цикл каждого кодового task:

1. добавить целевой тест;
2. запустить его и подтвердить ожидаемый RED;
3. добавить минимальную реализацию;
4. запустить целевой тест;
5. выполнить полный gate;
6. сделать один Conventional Commit.

Полный gate:

```powershell
ruff check src tests
mypy src tests
pytest -q
python -m compileall -q src tests
```

Push, merge и новый PR не выполнять.

## Файлы и ответственность

Создать:

- `src/epicase_ui/hotspot_icons.py` — allowlist, fallback, SVG bytes и `QIcon`;
- `src/epicase_ui/hotspot_marker.py` — общий `HotspotMarkerItem`;
- `src/epicase_ui/resources/hotspots/*.svg` — 10 локальных пиктограмм;
- `tests/ui/test_hotspot_icons.py`;
- `tests/ui/test_hotspot_marker.py`.

Изменить:

- `src/epicase_core/application/case_builder.py`;
- `src/epicase_core/application/case_loader.py`;
- `src/epicase_ui/__init__.py`;
- `src/epicase_constructor/ui/scheme_zone_editor.py`;
- `src/epicase_constructor/ui/scheme_zone_canvas.py`;
- `src/epicase_player/ui/scheme_viewer.py`;
- профильные tests и `TASKS.md`.

### Task 1: Application pipeline для `Hotspot.icon`

**Files:**

- Modify: `src/epicase_core/application/case_builder.py:191-210,534-557`
- Modify: `src/epicase_core/application/case_loader.py:255-279`
- Test: `tests/core/test_case_builder.py`
- Test: `tests/core/test_case_loader.py`

- [ ] **Step 1: Add failing round-trip tests**

```python
def test_build_contacts_preserves_hotspot_icon() -> None:
    draft = ContactsDraft(
        scheme=AssetRef("scheme", "", data=b"PNG"),
        hotspots=(
            HotspotDraft(
                0.1, 0.2, 0.3, 0.4, label="Медпункт", icon="medical"
            ),
        ),
    )
    stage = build_case(
        CaseDraft(case_id="case", title="Case", contacts=draft)
    ).contacts
    assert stage.scheme is not None
    assert stage.scheme.root.hotspots[0].icon == "medical"
```

В loader-тесте собрать `LoadedCase` с корневым `icon="barracks"` и вложенным
`icon="cold_storage"`, вызвать `case_to_draft` и проверить оба ключа.

- [ ] **Step 2: Verify RED**

```powershell
pytest tests/core/test_case_builder.py::test_build_contacts_preserves_hotspot_icon tests/core/test_case_loader.py::test_case_to_draft_preserves_nested_hotspot_icon -q
```

Expected: `HotspotDraft` не принимает `icon`.

- [ ] **Step 3: Implement symmetric mapping**

```python
@dataclass(frozen=True)
class HotspotDraft:
    x: float
    y: float
    w: float
    h: float
    label: str = ""
    icon: str = ""
    reveal_text: str = ""
    reveal_assets: tuple[AssetRef, ...] = ()
    child: SchemeViewDraft | None = None
```

В `_build_hotspots`: `icon=d.icon`.
В `_hotspot_to_draft`: `icon=h.icon`.
Исправить docstrings, которые сейчас говорят, что ключ теряется.

- [ ] **Step 4: Target PASS, full gate, commit**

```powershell
pytest tests/core/test_case_builder.py::test_build_contacts_preserves_hotspot_icon tests/core/test_case_loader.py::test_case_to_draft_preserves_nested_hotspot_icon -q
ruff check src tests
mypy src tests
pytest -q
python -m compileall -q src tests
git add src/epicase_core/application/case_builder.py src/epicase_core/application/case_loader.py tests/core/test_case_builder.py tests/core/test_case_loader.py
git commit -m "feat(core): preserve hotspot icon keys"
```

### Task 2: Общий SVG-каталог и `HotspotMarkerItem`

**Files:**

- Create: `src/epicase_ui/hotspot_icons.py`
- Create: `src/epicase_ui/hotspot_marker.py`
- Create: `src/epicase_ui/resources/hotspots/{inspect,barracks,canteen,medical,water,sanitary,storage,cold_storage,waste,entrance}.svg`
- Modify: `src/epicase_ui/__init__.py`
- Test: `tests/ui/test_hotspot_icons.py`
- Test: `tests/ui/test_hotspot_marker.py`

- [ ] **Step 1: Add failing registry tests**

```python
def test_registry_contains_approved_icon_keys() -> None:
    assert tuple(spec.key for spec in hotspot_icon_specs()) == (
        "inspect", "barracks", "canteen", "medical", "water",
        "sanitary", "storage", "cold_storage", "waste", "entrance",
    )


def test_all_hotspot_svg_resources_are_valid() -> None:
    for spec in hotspot_icon_specs():
        renderer = QSvgRenderer(QByteArray(hotspot_icon_svg_bytes(spec.key)))
        assert renderer.isValid(), spec.key


def test_unknown_keys_fall_back_to_inspect() -> None:
    assert hotspot_icon_spec("").key == "inspect"
    assert hotspot_icon_spec("zoom").key == "inspect"
    assert hotspot_icon_spec("../../secret").key == "inspect"
```

- [ ] **Step 2: Verify RED**

```powershell
pytest tests/ui/test_hotspot_icons.py -q
```

- [ ] **Step 3: Implement allowlist**

`hotspot_icons.py` defines:

```python
@dataclass(frozen=True)
class HotspotIconSpec:
    key: str
    label: str


DEFAULT_HOTSPOT_ICON_KEY = "inspect"


def hotspot_icon_specs() -> tuple[HotspotIconSpec, ...]:
    return _SPECS


def hotspot_icon_spec(key: str) -> HotspotIconSpec:
    return _BY_KEY.get(key, _BY_KEY[DEFAULT_HOTSPOT_ICON_KEY])


def hotspot_icon_svg_bytes(key: str) -> bytes:
    spec = hotspot_icon_spec(key)
    try:
        data = files("epicase_ui").joinpath(
            "resources", "hotspots", f"{spec.key}.svg"
        ).read_bytes()
    except OSError:
        if spec.key == DEFAULT_HOTSPOT_ICON_KEY:
            raise
        return hotspot_icon_svg_bytes(DEFAULT_HOTSPOT_ICON_KEY)
    if not QSvgRenderer(QByteArray(data)).isValid():
        if spec.key == DEFAULT_HOTSPOT_ICON_KEY:
            raise ValueError("Invalid default hotspot SVG")
        return hotspot_icon_svg_bytes(DEFAULT_HOTSPOT_ICON_KEY)
    return data


def hotspot_icon_qicon(key: str) -> QIcon:
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setBrush(QColor("#0F766E"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(QRectF(0, 0, 32, 32), 7, 7)
    QSvgRenderer(QByteArray(hotspot_icon_svg_bytes(key))).render(
        painter, QRectF(6, 6, 20, 20)
    )
    painter.end()
    return QIcon(pixmap)
```

Implement these bodies as follows:

- specs and Russian labels are copied exactly from the approved design;
- lookup uses only a fixed dict and never treats `key` as a path;
- empty/unknown keys resolve to `inspect`;
- `hotspot_icon_svg_bytes` reads
  `resources/hotspots/<allowlisted-key>.svg`;
- missing/invalid non-default SVG retries with `inspect`;
- `hotspot_icon_qicon` draws a 32×32 teal rounded square and renders the white
  SVG in a 20×20 inner rect;
- all public APIs have docstrings and are exported from `epicase_ui`.

Each SVG uses `viewBox="0 0 24 24"`, no fill, `#FFFFFF` stroke, round caps and
joins. Shapes: magnifier/crosshair, bed, fork/spoon, medical cross, water
tower, washbasin, warehouse, snowflake/refrigerator, waste bin and entrance
arrow respectively.

- [ ] **Step 4: Add failing marker tests**

```python
def test_marker_fallback_label_and_fixed_scale() -> None:
    marker = HotspotMarkerItem("../../unknown", "Длинная подпись объекта осмотра")
    assert marker.icon_key == "inspect"
    assert marker.toolTip() == "Длинная подпись объекта осмотра"
    assert len(marker.label_lines) <= 2
    assert marker.boundingRect().width() <= 160
    assert marker.flags() & QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations


def test_marker_can_place_label_above() -> None:
    marker = HotspotMarkerItem("water", "Водоснабжение", label_above=True)
    assert marker.label_above is True
```

Render-smoke paints `medical` into a 220×120 `QImage` and checks that the pin
center is `QColor("#0F766E")`.

- [ ] **Step 5: Verify RED**

```powershell
pytest tests/ui/test_hotspot_marker.py -q
```

- [ ] **Step 6: Implement marker**

`HotspotMarkerItem(QGraphicsItem)`:

```python
PIN_RADIUS = 22.0
PIN_TIP_Y = 28.0
LABEL_WIDTH = 160.0
```

Constructor args: `icon_key`, `label=""`, `label_above=False`, `parent=None`.
It resolves the key through the registry, caches a valid `QSvgRenderer`, sets
`ItemIgnoresTransformations`, tooltip and read-only properties
`icon_key`, `label`, `label_lines`, `label_above`.

`paint()` draws:

1. `#0F766E` circle with white 3 px border and triangular pointer;
2. 24×24 white SVG;
3. `#17393A` label card with white text, width ≤160 px and ≤2 lines;
4. card above the pin when `label_above=True`.

Add `set_icon_key()` for Constructor and recompute geometry with
`prepareGeometryChange()`.

- [ ] **Step 7: Target PASS, full gate, commit**

```powershell
pytest tests/ui/test_hotspot_icons.py tests/ui/test_hotspot_marker.py -q
ruff check src tests
mypy src tests
pytest -q
python -m compileall -q src tests
git add src/epicase_ui tests/ui/test_hotspot_icons.py tests/ui/test_hotspot_marker.py
git commit -m "feat(ui): add infrastructure hotspot markers"
```

### Task 3: Constructor authoring

**Files:**

- Modify: `src/epicase_constructor/ui/scheme_zone_editor.py`
- Modify: `src/epicase_constructor/ui/scheme_zone_canvas.py`
- Test: `tests/constructor/test_scheme_zone_editor.py`
- Test: `tests/constructor/test_scheme_zone_canvas.py`
- Test: `tests/constructor/test_case_load.py`

- [ ] **Step 1: Add failing editor/canvas tests**

```python
def test_icon_combo_defaults_and_round_trips(qtbot: QtBot, tmp_path: Path) -> None:
    editor = SchemeZoneEditor()
    qtbot.addWidget(editor)
    editor.set_background(_make_ref(tmp_path))
    editor._add_button.click()
    card = editor.cards[0]
    assert card.icon_key() == "inspect"
    card.icon_combo.setCurrentIndex(card.icon_combo.findData("water"))
    assert editor.to_hotspots()[0].icon == "water"
    assert editor.canvas.zone_icon_key(0) == "water"
```

Add tests that:

- loading `icon="legacy_custom"` preserves raw combo data and draft output,
  while canvas displays `inspect`;
- nested editor saves `cold_storage`;
- resizing a `ZoneItem` moves its child marker to `zone.rect().center()`;
- `test_case_load` restores `canteen` in card and canvas.

- [ ] **Step 2: Verify RED**

```powershell
pytest tests/constructor/test_scheme_zone_editor.py::test_icon_combo_defaults_and_round_trips tests/constructor/test_scheme_zone_editor.py::test_unknown_icon_is_preserved_until_explicit_change tests/constructor/test_scheme_zone_canvas.py::test_zone_marker_follows_resize -q
```

- [ ] **Step 3: Implement combo**

`ZonePropsCard` gets `icon_changed = Signal(str)` and `QComboBox`. Populate it
from `hotspot_icon_specs()` using `hotspot_icon_qicon()`.

```python
def icon_key(self) -> str:
    value = self.icon_combo.currentData()
    return value if isinstance(value, str) else DEFAULT_HOTSPOT_ICON_KEY


def set_icon_key(self, key: str) -> None:
    index = self.icon_combo.findData(key)
    if index < 0:
        self.icon_combo.addItem(
            hotspot_icon_qicon(key), "Неизвестная иконка", key
        )
        index = self.icon_combo.count() - 1
    self.icon_combo.setCurrentIndex(index)
```

Load `draft.icon`; emit changes; write `icon=card.icon_key()` in
`to_hotspots`.

- [ ] **Step 4: Implement canvas synchronization**

`ZoneItem` creates `HotspotMarkerItem("inspect", parent=self)`, keeps its
position at `rect().center()` after resize and exposes `set_icon_key`.

`SchemeZoneCanvas` adds:

```python
def set_zone_icon(self, index: int, key: str) -> None:
    if 0 <= index < len(self._zones):
        self._zones[index].set_icon_key(key)


def zone_icon_key(self, index: int) -> str:
    return self._zones[index].marker.icon_key
```

`SchemeZoneEditor` connects each card's `icon_changed` to the corresponding
zone and explicitly synchronizes after `card.load`.

- [ ] **Step 5: Target PASS, full gate, commit**

```powershell
pytest tests/constructor/test_scheme_zone_editor.py tests/constructor/test_scheme_zone_canvas.py tests/constructor/test_case_load.py -q
ruff check src tests
mypy src tests
pytest -q
python -m compileall -q src tests
git add src/epicase_constructor/ui/scheme_zone_editor.py src/epicase_constructor/ui/scheme_zone_canvas.py tests/constructor/test_scheme_zone_editor.py tests/constructor/test_scheme_zone_canvas.py tests/constructor/test_case_load.py
git commit -m "feat(constructor): author hotspot infrastructure icons"
```

### Task 4: Player pins and hover hit-area

**Files:**

- Modify: `src/epicase_player/ui/scheme_viewer.py`
- Test: `tests/player/test_scheme_viewer.py`
- Test: `tests/player/test_scheme_viewer_zoom.py`

- [ ] **Step 1: Add failing Player tests**

Replace the old permanent-label test with assertions that:

```python
markers = [item for item in scene.items() if isinstance(item, HotspotMarkerItem)]
hit_areas = [
    item
    for item in scene.items()
    if isinstance(item, QGraphicsRectItem) and item.parentItem() is None
]
assert len(markers) == 1
assert markers[0].icon_key == "water"
assert markers[0].toolTip() == label
assert hit_areas[0].pen().style() == Qt.PenStyle.NoPen
assert hit_areas[0].brush().style() == Qt.BrushStyle.NoBrush
```

Add tests for unknown `zoom` → `inspect` and hover:

```python
qtbot.mouseMove(view.viewport(), view.mapFromScene(QPointF(40, 30)))
item = view._highlight_items["center"]
assert item.pen().color() == QColor("#0F766E")
assert item.brush().color().alpha() > 0
```

- [ ] **Step 2: Verify RED**

```powershell
pytest tests/player/test_scheme_viewer.py::test_viewer_renders_marker_and_hides_default_hit_area tests/player/test_scheme_viewer.py::test_viewer_unknown_icon_uses_inspect_marker tests/player/test_scheme_viewer_zoom.py::test_hover_temporarily_highlights_real_hotspot_area -q
```

- [ ] **Step 3: Create invisible hit-area and marker**

`_add_hotspot` returns a default-invisible `QGraphicsRectItem`, then adds:

```python
marker = HotspotMarkerItem(
    hotspot.icon,
    hotspot.label,
    label_above=hotspot.shape.y + hotspot.shape.h / 2 > 0.78,
)
marker.setPos(rect.center())
marker.setCursor(Qt.CursorShape.PointingHandCursor)
marker.setZValue(3.0)
scene.addItem(marker)
```

`_build_page` passes `{hotspot.id: hit_area}` into `_SchemeGraphicsView`.

- [ ] **Step 4: Add shared click/hover hit-test**

`_SchemeGraphicsView` accepts optional
`Mapping[str, QGraphicsRectItem]`, enables mouse tracking, and uses:

```python
def _hotspot_at(self, position: QPoint) -> Hotspot | None:
    scene_pos = self.mapToScene(position)
    nx = scene_pos.x() / self._px_w if self._px_w else 0.0
    ny = scene_pos.y() / self._px_h if self._px_h else 0.0
    return next(
        (spot for spot in self._hotspots if spot.shape.contains(nx, ny)),
        None,
    )
```

Click and hover both call this helper. Hover resets all items to `NoPen` /
`NoBrush`, then applies existing `_HOTSPOT_PEN` and `_HOTSPOT_FILL` to the
matched item. `leaveEvent` clears hover. Panning and zoom remain unchanged.
Delete the old permanent label renderer and unused imports/constants.

- [ ] **Step 5: Target PASS, full gate, commit**

```powershell
pytest tests/player/test_scheme_viewer.py tests/player/test_scheme_viewer_zoom.py -q
ruff check src tests
mypy src tests
pytest -q
python -m compileall -q src tests
git add src/epicase_player/ui/scheme_viewer.py tests/player/test_scheme_viewer.py tests/player/test_scheme_viewer_zoom.py
git commit -m "feat(player): render infrastructure hotspot pins"
```

### Task 5: Завершение N5

**Files:**

- Modify: `TASKS.md`

- [ ] **Step 1: Close only N5**

```markdown
- [x] N5 — инфраструктурные пины вместо постоянных прямоугольников-хотспотов
```

ICON-1B, ICON-1C, DEMO-1 и последующие задачи остаются открытыми.

- [ ] **Step 2: Final gate and commit**

```powershell
ruff check src tests
mypy src tests
pytest -q
python -m compileall -q src tests
git diff --check
git add TASKS.md
git commit -m "docs: complete infrastructure hotspot icons"
git status --short --branch
```

- [ ] **Step 3: Live acceptance report**

Попросить пользователя проверить:

1. выбор всех десяти типов в этапах 3 и 4 Constructor;
2. мгновенное обновление пина у корневой и вложенной зоны;
3. сохранение иконки после move/resize и save/reopen;
4. отсутствие постоянных рамок в Player;
5. hover-подсветку прежнего прямоугольного hit-area;
6. клик по любой точке hit-area;
7. постоянный экранный размер при zoom/pan;
8. child/reveal/Back без регрессии;
9. универсальный `inspect` у старого кейса.

Не выполнять push, merge или создание нового PR без явного подтверждения.
