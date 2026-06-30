# Windows Application Icons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Добавить адаптивные SVG-исходники и воспроизводимые многокадровые Windows ICO для Constructor и Player.

**Architecture:** Четыре SVG лежат как package resources: full-варианты для размеров от 32 px и упрощённые small-варианты для 16–24 px. Типизированный офлайн-генератор на PySide6 рендерит SVG в PNG и упаковывает кадры в ICO средствами `struct`; checked-in ICO сверяются с повторной генерацией по структуре, DPI и RGBA-пикселям.

**Tech Stack:** Python 3.12, PySide6 `QSvgRenderer`/`QImage`, стандартные `dataclasses`, `pathlib`, `struct`, pytest.

---

## File map

- Create `src/epicase_ui/resources/app_icons/epicase_constructor.svg` — полный знак Constructor.
- Create `src/epicase_ui/resources/app_icons/epicase_constructor_small.svg` — оптически упрощённый знак Constructor.
- Create `src/epicase_ui/resources/app_icons/epicase_player.svg` — полный знак Player.
- Create `src/epicase_ui/resources/app_icons/epicase_player_small.svg` — оптически упрощённый знак Player.
- Create `src/epicase_ui/resources/app_icons/epicase_constructor.ico` — девять PNG-кадров Constructor.
- Create `src/epicase_ui/resources/app_icons/epicase_player.ico` — девять PNG-кадров Player.
- Create `tools/__init__.py` — делает генератор импортируемым в тестах.
- Create `tools/generate_app_icons.py` — валидирует SVG, рендерит PNG и собирает ICO.
- Create `tests/ui/test_app_icon_sources.py` — визуальные контракты SVG.
- Create `tests/ui/test_app_icon_generation.py` — структура ICO, прозрачность и воспроизводимость.
- Modify `pyproject.toml` — явно включает ICO в wheel artifacts.
- Modify `TASKS.md` — закрывает только `ICON-1B`.

### Task 1: Adaptive SVG sources

**Files:**
- Create: `src/epicase_ui/resources/app_icons/epicase_constructor.svg`
- Create: `src/epicase_ui/resources/app_icons/epicase_constructor_small.svg`
- Create: `src/epicase_ui/resources/app_icons/epicase_player.svg`
- Create: `src/epicase_ui/resources/app_icons/epicase_player_small.svg`
- Create: `tests/ui/test_app_icon_sources.py`

- [ ] **Step 1: Write failing SVG resource tests**

```python
"""Контракты адаптивных исходников Windows-иконок."""
from __future__ import annotations

from importlib.resources import files

import pytest
from PySide6.QtCore import QByteArray
from PySide6.QtSvg import QSvgRenderer

_NAMES = (
    "epicase_constructor.svg",
    "epicase_constructor_small.svg",
    "epicase_player.svg",
    "epicase_player_small.svg",
)


def _icon_bytes(name: str) -> bytes:
    return files("epicase_ui").joinpath("resources", "app_icons", name).read_bytes()


@pytest.mark.parametrize("name", _NAMES)
def test_app_icon_svg_is_valid_square_artwork(name: str) -> None:
    data = _icon_bytes(name)
    renderer = QSvgRenderer(QByteArray(data))

    assert renderer.isValid()
    assert renderer.viewBoxF().width() == renderer.viewBoxF().height()
    assert b"#17393A" in data


def test_constructor_and_player_use_distinct_role_signs() -> None:
    constructor = _icon_bytes("epicase_constructor.svg")
    player = _icon_bytes("epicase_player.svg")

    assert constructor != player
    assert b"#B49A56" in constructor
    assert b"#0F766E" in player
    assert b'data-role="blueprint"' in constructor
    assert b'data-role="route"' in player


def test_small_sources_drop_fine_detail_and_keep_role_signs() -> None:
    constructor = _icon_bytes("epicase_constructor_small.svg")
    player = _icon_bytes("epicase_player_small.svg")

    assert b'data-detail="grid"' not in constructor
    assert b'data-role="blueprint"' in constructor
    assert b'data-role="route"' in player
```

- [ ] **Step 2: Verify RED**

Run:

```powershell
$env:PYTHONPATH = (Resolve-Path 'src').Path
& 'C:\Users\user\Desktop\Program\educase\.venv\Scripts\pytest.exe' tests/ui/test_app_icon_sources.py -q
```

Expected: four `FileNotFoundError` failures because `resources/app_icons` does not exist.

- [ ] **Step 3: Add full and small SVG artwork**

Use `viewBox="0 0 64 64"` and a transparent canvas.

Constructor full:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <path d="M32 3 57 17v30L32 61 7 47V17Z"
        fill="#FFFFFF" stroke="#17393A" stroke-width="3.5"/>
  <g data-detail="grid" fill="none" stroke="#D9EEEB" stroke-width="2">
    <path d="M18 19h28M18 32h28M18 45h28"/>
    <path d="M20 16v32M32 10v44M44 16v32"/>
  </g>
  <g data-role="blueprint">
    <path d="m20 43 12-22 12 22Z" fill="none" stroke="#17393A"
          stroke-linejoin="round" stroke-width="3"/>
    <g fill="#B49A56" stroke="#17393A" stroke-width="2">
      <circle cx="32" cy="21" r="4.5"/>
      <circle cx="20" cy="43" r="4.5"/>
      <circle cx="44" cy="43" r="4.5"/>
    </g>
  </g>
</svg>
```

Constructor small uses no grid, `stroke-width="5.5"` for the outline and
triangle, and `r="6.5"` brass nodes.

Player full:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <path d="M32 3 57 17v30L32 61 7 47V17Z"
        fill="#0F766E" stroke="#17393A" stroke-width="3.5"/>
  <g data-role="route">
    <path d="M19 42c7-1 7-20 17-20 6 0 7 7 7 12"
          fill="none" stroke="#FFFFFF" stroke-linecap="round" stroke-width="5"/>
    <circle cx="19" cy="42" r="5" fill="#D9EEEB"
            stroke="#17393A" stroke-width="2"/>
    <path d="m37 32 6 7 6-7" fill="none" stroke="#FFFFFF"
          stroke-linecap="round" stroke-linejoin="round" stroke-width="4"/>
  </g>
</svg>
```

Player small uses `stroke-width="7"` for the route and arrow and `r="6.5"`
for the start point.

- [ ] **Step 4: Run target tests**

Run the Task 1 pytest command again.

Expected: `6 passed`.

- [ ] **Step 5: Run full gate**

```powershell
$env:PYTHONPATH = (Resolve-Path 'src').Path
& 'C:\Users\user\Desktop\Program\educase\.venv\Scripts\ruff.exe' check src tests
& 'C:\Users\user\Desktop\Program\educase\.venv\Scripts\mypy.exe' src tests
& 'C:\Users\user\Desktop\Program\educase\.venv\Scripts\pytest.exe' -q
& 'C:\Users\user\Desktop\Program\educase\.venv\Scripts\python.exe' -m compileall -q src tests
```

Expected: all commands exit 0.

- [ ] **Step 6: Commit**

```powershell
git add src/epicase_ui/resources/app_icons tests/ui/test_app_icon_sources.py
git commit -m "feat(ui): add adaptive application icon sources"
```

### Task 2: Deterministic ICO generator

**Files:**
- Create: `tools/__init__.py`
- Create: `tools/generate_app_icons.py`
- Create: `tests/ui/test_app_icon_generation.py`
- Create: `src/epicase_ui/resources/app_icons/epicase_constructor.ico`
- Create: `src/epicase_ui/resources/app_icons/epicase_player.ico`

- [ ] **Step 1: Write failing generator tests**

```python
"""Структура и воспроизводимость Windows ICO."""
from __future__ import annotations

import struct
from importlib.resources import files

import pytest
from PySide6.QtGui import QImage

from tools.generate_app_icons import ICON_SIZES, IconSource, build_ico


def _resource(name: str) -> bytes:
    return files("epicase_ui").joinpath("resources", "app_icons", name).read_bytes()


def _frames(data: bytes) -> list[tuple[int, bytes]]:
    reserved, kind, count = struct.unpack_from("<HHH", data)
    assert (reserved, kind, count) == (0, 1, len(ICON_SIZES))
    frames: list[tuple[int, bytes]] = []
    for index in range(count):
        width, height, _, _, planes, bpp, length, offset = struct.unpack_from(
            "<BBBBHHII", data, 6 + index * 16
        )
        assert planes == 1
        assert bpp == 32
        size = width or 256
        assert (height or 256) == size
        frames.append((size, data[offset : offset + length]))
    return frames


@pytest.mark.parametrize("app", ("constructor", "player"))
def test_checked_in_ico_has_exact_png_frames(app: str) -> None:
    frames = _frames(_resource(f"epicase_{app}.ico"))

    assert tuple(size for size, _ in frames) == ICON_SIZES
    for size, payload in frames:
        assert payload.startswith(b"\x89PNG\r\n\x1a\n")
        image = QImage.fromData(payload, "PNG")
        assert not image.isNull()
        assert (image.width(), image.height()) == (size, size)
        assert image.hasAlphaChannel()


@pytest.mark.parametrize("app", ("constructor", "player"))
def test_checked_in_ico_is_visually_reproducible(app: str) -> None:
    source = IconSource(
        full_svg=_resource(f"epicase_{app}.svg"),
        small_svg=_resource(f"epicase_{app}_small.svg"),
    )

    generated_frames = _frames(build_ico(source))
    checked_frames = _frames(_resource(f"epicase_{app}.ico"))
    assert tuple(size for size, _ in generated_frames) == tuple(
        size for size, _ in checked_frames
    )
    for (size, generated_payload), (_, checked_payload) in zip(
        generated_frames, checked_frames, strict=True
    ):
        generated_image = QImage.fromData(generated_payload)
        checked_image = QImage.fromData(checked_payload)
        assert (generated_image.width(), generated_image.height()) == (size, size)
        assert generated_image.dotsPerMeterX() == checked_image.dotsPerMeterX()
        assert _rgba_pixels(generated_image) == _rgba_pixels(checked_image)


def test_build_ico_rejects_invalid_svg() -> None:
    with pytest.raises(ValueError, match="Некорректный SVG"):
        build_ico(IconSource(full_svg=b"broken", small_svg=b"broken"))
```

- [ ] **Step 2: Verify RED**

Run:

```powershell
$env:PYTHONPATH = (Resolve-Path 'src').Path
& 'C:\Users\user\Desktop\Program\educase\.venv\Scripts\pytest.exe' tests/ui/test_app_icon_generation.py -q
```

Expected: collection error because `tools.generate_app_icons` does not exist.

- [ ] **Step 3: Implement the generator**

Define:

```python
ICON_SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)
_SMALL_MAX_SIZE = 24


@dataclass(frozen=True)
class IconSource:
    full_svg: bytes
    small_svg: bytes
```

`_render_png(svg: bytes, size: int) -> bytes` must:

1. construct `QSvgRenderer(QByteArray(svg))` and raise
   `ValueError("Некорректный SVG исходника иконки")` when invalid;
2. render with antialiasing into transparent
   `QImage(size, size, QImage.Format.Format_ARGB32)`;
3. encode through `QBuffer` as PNG and return immutable bytes.

`build_ico(source: IconSource) -> bytes` renders small SVG through 24 px and
full SVG at larger sizes. Build the directory with:

```python
header = struct.pack("<HHH", 0, 1, len(frames))
entry = struct.pack(
    "<BBBBHHII",
    size if size < 256 else 0,
    size if size < 256 else 0,
    0,
    0,
    1,
    32,
    len(payload),
    offset,
)
```

`generate_all(resource_dir: Path = _RESOURCE_DIR) -> None` uses only the
fixed names `constructor` and `player`, builds both byte strings before any
write, writes sibling `.tmp` files, then replaces the two ICO resources.

`main() -> int` calls `generate_all()` and returns 0. No CLI path or
application-name arguments are accepted.

- [ ] **Step 4: Generate checked-in ICO**

```powershell
$env:PYTHONPATH = (Resolve-Path 'src').Path
& 'C:\Users\user\Desktop\Program\educase\.venv\Scripts\python.exe' tools/generate_app_icons.py
```

Expected: two ICO files appear in `resources/app_icons/`.

- [ ] **Step 5: Run target tests**

Run the Task 2 pytest command again.

Expected: `5 passed`.

- [ ] **Step 6: Run full gate**

Run the four gate commands from Task 1.

Expected: all commands exit 0.

- [ ] **Step 7: Commit**

```powershell
git add tools src/epicase_ui/resources/app_icons tests/ui/test_app_icon_generation.py
git commit -m "build(ui): generate Windows application icons"
```

### Task 3: Package contract and task completion

**Files:**
- Modify: `pyproject.toml`
- Modify: `TASKS.md`
- Modify: `tests/ui/test_app_icon_generation.py`

- [ ] **Step 1: Add failing package-data test**

```python
def test_wheel_config_explicitly_includes_ico_resources() -> None:
    pyproject_path = Path(__file__).parents[2] / "pyproject.toml"
    config = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    artifacts = config["tool"]["hatch"]["build"]["targets"]["wheel"]["artifacts"]

    assert "src/epicase_ui/resources/**/*.ico" in artifacts
```

- [ ] **Step 2: Verify RED**

Run:

```powershell
$env:PYTHONPATH = (Resolve-Path 'src').Path
& 'C:\Users\user\Desktop\Program\educase\.venv\Scripts\pytest.exe' tests/ui/test_app_icon_generation.py::test_wheel_config_explicitly_includes_ico_resources -q
```

Expected: failure because `artifacts` is absent.

- [ ] **Step 3: Add the wheel artifact**

Under `[tool.hatch.build.targets.wheel]` add:

```toml
artifacts = [
    "src/epicase_ui/resources/**/*.ico",
]
```

- [ ] **Step 4: Mark only ICON-1B complete**

Change:

```markdown
  - [ ] ICON-1B — подготовить исходники и Windows ICO в необходимых размерах
```

to:

```markdown
  - [x] ICON-1B — подготовить исходники и Windows ICO в необходимых размерах
```

Keep `ICON-1`, `ICON-1C`, `DEMO-1` and `PKG-1` open.

- [ ] **Step 5: Run target test and full gate**

Run the Task 3 target test, then the four gate commands from Task 1.

Expected: all commands exit 0; total test count increases from 604 to 616.

- [ ] **Step 6: Inspect generated resources**

```powershell
git diff --check
git status --short
Get-ChildItem src/epicase_ui/resources/app_icons |
    Select-Object Name, Length
```

Expected: four SVG and two non-empty ICO files; no temporary files.

- [ ] **Step 7: Commit**

```powershell
git add pyproject.toml TASKS.md tests/ui/test_app_icon_generation.py
git commit -m "docs: complete Windows application icon sources"
```

### Task 4: Final verification and live handoff

**Files:** none.

- [ ] **Step 1: Repeat final gate from a clean worktree**

Run all four gate commands and `git status --short --branch`.

Expected: all commands exit 0 and worktree is clean.

- [ ] **Step 2: Report live checks**

Ask the user to open both ICO files in Windows Explorer and verify:

1. Constructor and Player are distinguishable in small and large icon views;
2. both remain readable on light and dark backgrounds;
3. the area outside the hexagon is transparent;
4. 16, 24, 32, 48 and 256 px frames remain sharp.

Do not start `ICON-1C`, push, merge or create a PR without separate approval.
