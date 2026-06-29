# Investigation Map Animation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the simple start-screen graph with the approved balanced investigation-map animation for Constructor and Player.

**Architecture:** Add an internal `InvestigationMapRenderer` to the shared `epicase_ui` package. It owns deterministic route data, perspective-grid rendering and elapsed-time animation; `AnimatedStartBackground` keeps lifecycle and delegates painting to the renderer.

**Tech Stack:** Python 3.12, PySide6 Widgets, QPainter, pytest/pytest-qt, ruff, mypy strict.

---

### Task 1: Add deterministic investigation-map geometry

**Files:**
- Create: `src/epicase_ui/investigation_map.py`
- Create: `tests/ui/test_investigation_map.py`

- [ ] **Step 1: Write failing geometry tests**

Create tests for:

```python
def test_cubic_point_returns_route_endpoints() -> None:
    route = _CubicRoute(
        points=((0.0, 0.2), (0.2, 0.0), (0.8, 1.0), (1.0, 0.8)),
        accent=False,
        signal_period_ms=5_000,
        signal_phase=0.0,
    )

    assert _cubic_point(route, 0.0) == pytest.approx((0.0, 0.2))
    assert _cubic_point(route, 1.0) == pytest.approx((1.0, 0.8))
```

and:

```python
def test_variants_define_distinct_balanced_maps() -> None:
    constructor = _VARIANT_SPECS[StartVariant.CONSTRUCTOR]
    player = _VARIANT_SPECS[StartVariant.PLAYER]

    assert len(constructor.routes) == 4
    assert len(player.routes) == 4
    assert constructor.routes != player.routes
    assert constructor.primary.name() == "#17393a"
    assert constructor.accent.name() == "#b49a56"
    assert player.primary.name() == "#0f766e"
    assert player.accent.name() == "#d9eeeb"
```

- [ ] **Step 2: Run tests and verify RED**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ui/test_investigation_map.py -q
```

Expected: collection fails because `epicase_ui.investigation_map` does not exist.

- [ ] **Step 3: Add the model and pure curve evaluator**

Create:

```python
class StartVariant(StrEnum):
    CONSTRUCTOR = "constructor"
    PLAYER = "player"


@dataclass(frozen=True)
class _CubicRoute:
    points: tuple[tuple[float, float], ...]
    accent: bool
    signal_period_ms: int
    signal_phase: float


@dataclass(frozen=True)
class _MapSpec:
    routes: tuple[_CubicRoute, ...]
    hotspots: tuple[tuple[float, float], ...]
    primary: QColor
    accent: QColor
    grid_opacity: float


def _cubic_point(route: _CubicRoute, progress: float) -> tuple[float, float]:
    clamped = min(1.0, max(0.0, progress))
    inverse = 1.0 - clamped
    weights = (
        inverse**3,
        3.0 * inverse**2 * clamped,
        3.0 * inverse * clamped**2,
        clamped**3,
    )
    return (
        sum(point[0] * weight for point, weight in zip(route.points, weights, strict=True)),
        sum(point[1] * weight for point, weight in zip(route.points, weights, strict=True)),
    )
```

Add four balanced routes and three hotspots per variant. Constructor data is
more regular; Player data uses freer curves. Keep coordinates normalized.

- [ ] **Step 4: Run focused checks**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ui/test_investigation_map.py -q
.\.venv\Scripts\ruff.exe check src/epicase_ui/investigation_map.py tests/ui/test_investigation_map.py
.\.venv\Scripts\mypy.exe src/epicase_ui/investigation_map.py tests/ui/test_investigation_map.py
```

Expected: all commands exit with code 0.

### Task 2: Render the four animated map layers

**Files:**
- Modify: `src/epicase_ui/investigation_map.py`
- Modify: `tests/ui/test_investigation_map.py`

- [ ] **Step 1: Write failing raster and motion tests**

Render each variant to a real `QImage` through `QPainter` and assert:

```python
assert QColor("#EDF0F3").name() in colors
assert spec.primary.name() in colors
assert spec.accent.name() in colors
assert completed_image != early_intro_image
assert completed_image != later_motion_image
```

The test uses `intro_progress=0.15`, `1.0`, and elapsed times `2_000` and
`3_000` ms. It also checks `renderer.layer_names`:

```python
assert renderer.layer_names == ("grid", "routes", "hotspots", "signals")
```

- [ ] **Step 2: Run tests and verify RED**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ui/test_investigation_map.py -q
```

Expected: failures because `InvestigationMapRenderer` is absent.

- [ ] **Step 3: Implement the renderer**

Add:

```python
class InvestigationMapRenderer:
    layer_names = ("grid", "routes", "hotspots", "signals")

    def __init__(self, variant: StartVariant) -> None:
        self.variant = StartVariant(variant)
        self._spec = _VARIANT_SPECS[self.variant]

    def paint(
        self,
        painter: QPainter,
        rect: QRect,
        *,
        elapsed_ms: int,
        intro_progress: float,
    ) -> None:
        grid_progress = _segment_progress(intro_progress, 0.0, 0.32)
        route_progress = _segment_progress(intro_progress, 0.18, 0.79)
        activity_progress = _segment_progress(intro_progress, 0.46, 1.0)
        self._paint_grid(painter, rect, elapsed_ms, grid_progress)
        self._paint_routes(painter, rect, elapsed_ms, route_progress)
        self._paint_hotspots(painter, rect, elapsed_ms, activity_progress)
        self._paint_signals(painter, rect, elapsed_ms, activity_progress)
```

Split painting into `_paint_grid`, `_paint_routes`, `_paint_hotspots` and
`_paint_signals`. Use these timing functions:

```python
grid_progress = _segment_progress(intro_progress, 0.0, 0.32)
route_progress = _segment_progress(intro_progress, 0.18, 0.79)
activity_progress = _segment_progress(intro_progress, 0.46, 1.0)
```

Requirements:

- perspective grid movement period is at least 12 seconds;
- route pens use deterministic dash offsets from elapsed time;
- route particles use `_cubic_point`;
- three hotspot rings use staggered 2.5–4 second phases;
- the scan wedge rotates no faster than once per 10 seconds;
- painter state is balanced with `save()`/`restore()`;
- no random values, images or I/O.

- [ ] **Step 4: Run focused checks**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ui/test_investigation_map.py -q
.\.venv\Scripts\ruff.exe check src/epicase_ui/investigation_map.py tests/ui/test_investigation_map.py
.\.venv\Scripts\mypy.exe src/epicase_ui/investigation_map.py tests/ui/test_investigation_map.py
```

Expected: all commands exit with code 0.

- [ ] **Step 5: Commit the renderer**

```powershell
git add -- src/epicase_ui/investigation_map.py tests/ui/test_investigation_map.py
git commit -m "feat(ui): add investigation map renderer"
```

### Task 3: Integrate the map into the shared start background

**Files:**
- Modify: `src/epicase_ui/animated_start.py`
- Modify: `tests/ui/test_animated_start.py`

- [ ] **Step 1: Write the failing integration test**

Add:

```python
def test_background_uses_investigation_map_renderer(qtbot: QtBot) -> None:
    constructor = AnimatedStartBackground(StartVariant.CONSTRUCTOR)
    player = AnimatedStartBackground(StartVariant.PLAYER)
    qtbot.addWidget(constructor)
    qtbot.addWidget(player)

    assert constructor.map_layers == ("grid", "routes", "hotspots", "signals")
    assert player.map_layers == ("grid", "routes", "hotspots", "signals")
```

- [ ] **Step 2: Run the integration test and verify RED**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ui/test_animated_start.py::test_background_uses_investigation_map_renderer -q
```

Expected: failure because `map_layers` does not exist.

- [ ] **Step 3: Delegate background painting**

Import `InvestigationMapRenderer` and `StartVariant` from
`epicase_ui.investigation_map`. In `AnimatedStartBackground.__init__` create:

```python
self._map_renderer = InvestigationMapRenderer(self._variant)
```

Expose read-only diagnostics:

```python
@property
def map_layers(self) -> tuple[str, ...]:
    return self._map_renderer.layer_names
```

Replace the old grid/network/intro-particle painting with:

```python
painter.fillRect(self.rect(), _FIELD_COLOR)
self._map_renderer.paint(
    painter,
    self.rect(),
    elapsed_ms=self._active_milliseconds(),
    intro_progress=self._intro_progress,
)
```

Remove the obsolete node, edge and particle constants and their painting
methods. Keep all timer, lifecycle and foreground-card code unchanged.

- [ ] **Step 4: Run shared and application UI tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ui tests/player/test_start_screen.py tests/constructor/test_start_screen.py tests/constructor/test_main_window.py -q
.\.venv\Scripts\ruff.exe check src/epicase_ui tests/ui
.\.venv\Scripts\mypy.exe src/epicase_ui tests/ui
```

Expected: all commands exit with code 0.

- [ ] **Step 5: Commit the integration**

```powershell
git add -- src/epicase_ui/animated_start.py tests/ui/test_animated_start.py
git commit -m "feat(ui): animate start screens as investigation maps"
```

### Task 4: Verify and document completion

**Files:**
- Modify: `docs/superpowers/plans/2026-06-29-investigation-map-animation.md`

- [ ] **Step 1: Run the full quality gate**

```powershell
.\.venv\Scripts\ruff.exe check src tests
.\.venv\Scripts\mypy.exe src tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q src tests
```

Expected: all four commands exit with code 0. Record the collected test count.

- [ ] **Step 2: Verify repository scope**

```powershell
git diff --check
git status --short
git diff --stat
```

Expected: only this plan remains modified after implementation commits.

- [ ] **Step 3: Mark plan tasks complete and commit**

Change this plan's task checkboxes from `[ ]` to `[x]`, then run:

```powershell
git add -- docs/superpowers/plans/2026-06-29-investigation-map-animation.md
git commit -m "docs: complete investigation map animation"
```

- [ ] **Step 4: Prepare live verification**

Report the commit hashes, test count and these checks:

1. Constructor uses a structured deep-teal map with brass signals;
2. Player uses freer teal routes with pale accents;
3. routes reveal during the 1.4-second intro;
4. signals move, hotspot rings expand and the scan wave remains subtle;
5. buttons work before the intro ends;
6. resize, maximize, minimize and restore remain correct;
7. leaving the start page stops animation;
8. returning to Constructor home does not replay the intro.
