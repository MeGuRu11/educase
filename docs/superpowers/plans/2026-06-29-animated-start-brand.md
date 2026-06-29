# Animated Start Screen Branding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the approved A2 EpiCase brand system and a non-blocking two-phase animated start screen to Constructor and Player.

**Architecture:** Introduce `epicase_ui` as a shared PySide6 presentation package. It owns packaged SVG brand resources, vector rendering, animation lifecycle and the common overlay shell; each application keeps its own `StartScreen`, button signals and product-specific text.

**Tech Stack:** Python 3.12, PySide6 Widgets/QtSvg, QPainter, pytest/pytest-qt, QSS, Hatchling, ruff, mypy strict.

---

### Task 1: Add the shared UI package and A2 SVG resources

**Files:**
- Create: `src/epicase_ui/__init__.py`
- Create: `src/epicase_ui/branding.py`
- Create: `src/epicase_ui/resources/brand/epicase.svg`
- Create: `src/epicase_ui/resources/brand/epicase_constructor.svg`
- Create: `src/epicase_ui/resources/brand/epicase_player.svg`
- Create: `tests/ui/__init__.py`
- Create: `tests/ui/test_branding.py`
- Modify: `pyproject.toml`
- Modify: `AGENTS.md`
- Modify: `.agents/skills/epicase-project/SKILL.md`

- [ ] **Step 1: Write failing package and SVG tests**

Create `tests/ui/test_branding.py`:

```python
"""Тесты общих SVG-ресурсов бренда EpiCase."""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
from PySide6.QtCore import QByteArray
from PySide6.QtSvg import QSvgRenderer

from epicase_ui.branding import BrandAsset, brand_svg_bytes


@pytest.mark.parametrize("asset", tuple(BrandAsset))
def test_brand_svg_is_valid(asset: BrandAsset) -> None:
    data = brand_svg_bytes(asset)

    assert data.startswith(b"<svg")
    assert QSvgRenderer(QByteArray(data)).isValid()


def test_product_brand_variants_are_distinct() -> None:
    constructor = brand_svg_bytes(BrandAsset.CONSTRUCTOR)
    player = brand_svg_bytes(BrandAsset.PLAYER)

    assert constructor != player
    assert b"#B49A56" in constructor
    assert b"#D9EEEB" in player


def test_epicase_ui_is_in_build_and_mypy_packages() -> None:
    config = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    wheel_packages = config["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"]
    mypy_packages = config["tool"]["mypy"]["packages"]
    assert "src/epicase_ui" in wheel_packages
    assert "epicase_ui" in mypy_packages
```

Create an empty `tests/ui/__init__.py`.

- [ ] **Step 2: Run the tests and confirm the import fails**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ui/test_branding.py -q
```

Expected: collection error because `epicase_ui` does not exist.

- [ ] **Step 3: Add the package metadata**

Append `src/epicase_ui` to the wheel package list and `epicase_ui` to the mypy
package list in `pyproject.toml`:

```toml
[tool.hatch.build.targets.wheel]
packages = [
    "src/epicase_core",
    "src/epicase_constructor",
    "src/epicase_player",
    "src/epicase_ui",
]

[tool.mypy]
python_version = "3.12"
strict = true
mypy_path = "src"
packages = ["epicase_core", "epicase_constructor", "epicase_player", "epicase_ui"]
```

- [ ] **Step 4: Document the shared presentation boundary**

Add `epicase_ui` to the source tree in `AGENTS.md`:

```text
  epicase_ui/            # общие PySide6 presentation-компоненты двух приложений
```

Add the same boundary to `.agents/skills/epicase-project/SKILL.md`:

```markdown
- `epicase_ui` — общие PySide6 presentation-компоненты; не импортирует приложения
  или Infrastructure.
```

Do not change the rule that `epicase_core.domain` has no external dependencies.

- [ ] **Step 5: Add the resource loader**

Create `src/epicase_ui/branding.py`:

```python
"""Общие SVG-ресурсы фирменной системы EpiCase."""
from __future__ import annotations

from enum import StrEnum
from importlib.resources import files


class BrandAsset(StrEnum):
    """Доступные варианты знака EpiCase."""

    COMMON = "epicase"
    CONSTRUCTOR = "epicase_constructor"
    PLAYER = "epicase_player"


def brand_svg_bytes(asset: BrandAsset) -> bytes:
    """Прочитать SVG-вариант бренда из package resources."""
    return (
        files("epicase_ui")
        .joinpath("resources", "brand", f"{asset.value}.svg")
        .read_bytes()
    )
```

Create `src/epicase_ui/__init__.py`:

```python
"""Общие presentation-компоненты Constructor и Player."""
from epicase_ui.branding import BrandAsset, brand_svg_bytes

__all__ = ["BrandAsset", "brand_svg_bytes"]
```

- [ ] **Step 6: Add the approved common A2 SVG**

Create `src/epicase_ui/resources/brand/epicase.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <path d="M50 8 83 27v46L50 92 17 73V27Z" fill="#FFFFFF"
        stroke="#0F766E" stroke-width="5" stroke-linejoin="round"/>
  <circle cx="50" cy="22" r="5" fill="#B49A56"/>
  <circle cx="27" cy="66" r="5" fill="#0F766E"/>
  <circle cx="73" cy="66" r="5" fill="#0F766E"/>
  <path d="M50 27v10M32 62l10-8M68 62l-10-8" fill="none"
        stroke="#0F766E" stroke-width="3.5" stroke-linecap="round"/>
  <circle cx="50" cy="50" r="16" fill="#D9EEEB"
          stroke="#17393A" stroke-width="3"/>
  <path d="M46 39h8v7h7v8h-7v7h-8v-7h-7v-8h7Z" fill="#17393A"/>
</svg>
```

- [ ] **Step 7: Add the Constructor SVG variant**

Create `src/epicase_ui/resources/brand/epicase_constructor.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <path d="M50 8 83 27v46L50 92 17 73V27Z" fill="#FFFFFF"
        stroke="#17393A" stroke-width="5" stroke-linejoin="round"/>
  <path d="M24 35h52M24 50h52M24 65h52M35 18v64M50 10v80M65 18v64"
        fill="none" stroke="#D9EEEB" stroke-width="1.5"/>
  <circle cx="50" cy="22" r="5" fill="#B49A56"/>
  <circle cx="27" cy="66" r="5" fill="#B49A56"/>
  <circle cx="73" cy="66" r="5" fill="#B49A56"/>
  <path d="M50 27v10M32 62l10-8M68 62l-10-8" fill="none"
        stroke="#17393A" stroke-width="3.5" stroke-linecap="round"/>
  <circle cx="50" cy="50" r="16" fill="#F2EAD7"
          stroke="#17393A" stroke-width="3"/>
  <path d="M46 39h8v7h7v8h-7v7h-8v-7h-7v-8h7Z" fill="#17393A"/>
</svg>
```

- [ ] **Step 8: Add the Player SVG variant**

Create `src/epicase_ui/resources/brand/epicase_player.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <path d="M50 8 83 27v46L50 92 17 73V27Z" fill="#FFFFFF"
        stroke="#0F766E" stroke-width="5" stroke-linejoin="round"/>
  <circle cx="50" cy="22" r="5" fill="#D9EEEB"
          stroke="#0F766E" stroke-width="2"/>
  <circle cx="27" cy="66" r="5" fill="#0F766E"/>
  <circle cx="73" cy="66" r="5" fill="#D9EEEB"
          stroke="#0F766E" stroke-width="2"/>
  <path d="M50 27v10M32 62l10-8M68 62l-10-8" fill="none"
        stroke="#0F766E" stroke-width="3.5" stroke-linecap="round"/>
  <circle cx="50" cy="50" r="16" fill="#D9EEEB"
          stroke="#17393A" stroke-width="3"/>
  <path d="M46 39h8v7h7v8h-7v7h-8v-7h-7v-8h7Z" fill="#17393A"/>
</svg>
```

- [ ] **Step 9: Run focused tests and static checks**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ui/test_branding.py -q
.\.venv\Scripts\ruff.exe check src/epicase_ui tests/ui/test_branding.py
.\.venv\Scripts\mypy.exe src/epicase_ui tests/ui/test_branding.py
```

Expected: all commands exit with code 0.

- [ ] **Step 10: Commit the brand resources**

```powershell
git add -- pyproject.toml AGENTS.md .agents/skills/epicase-project/SKILL.md src/epicase_ui tests/ui
git commit -m "feat(ui): add EpiCase brand resources"
```

### Task 2: Implement the scalable brand mark widget

**Files:**
- Create: `src/epicase_ui/brand_mark.py`
- Create: `tests/ui/test_brand_mark.py`
- Modify: `src/epicase_ui/__init__.py`

- [ ] **Step 1: Write failing widget tests**

Create `tests/ui/test_brand_mark.py`:

```python
"""Тесты масштабируемого знака EpiCase."""
from __future__ import annotations

from PySide6.QtGui import QPixmap
from pytest import MonkeyPatch
from pytestqt.qtbot import QtBot

import epicase_ui.brand_mark as brand_mark_module
from epicase_ui.brand_mark import BrandMarkWidget
from epicase_ui.branding import BrandAsset


def test_brand_mark_loads_requested_asset(qtbot: QtBot) -> None:
    widget = BrandMarkWidget(BrandAsset.PLAYER)
    qtbot.addWidget(widget)

    assert widget.asset is BrandAsset.PLAYER
    assert widget.has_valid_svg
    assert widget.accessibleName() == "Логотип EpiCase Player"


def test_brand_mark_clamps_intro_progress(qtbot: QtBot) -> None:
    widget = BrandMarkWidget(BrandAsset.COMMON)
    qtbot.addWidget(widget)

    widget.set_intro_progress(-1.0)
    assert widget.intro_progress == 0.0
    widget.set_intro_progress(2.0)
    assert widget.intro_progress == 1.0


def test_brand_mark_renders_at_different_sizes(qtbot: QtBot) -> None:
    widget = BrandMarkWidget(BrandAsset.CONSTRUCTOR)
    qtbot.addWidget(widget)
    for size in (32, 72, 144):
        widget.resize(size, size)
        pixmap = QPixmap(widget.size())
        pixmap.fill()
        widget.render(pixmap)  # type: ignore[no-untyped-call]  # PySide6 render overload lacks stubs
        assert not pixmap.isNull()


def test_brand_mark_uses_text_fallback_for_invalid_svg(
    qtbot: QtBot,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(brand_mark_module, "brand_svg_bytes", lambda _asset: b"broken")
    widget = BrandMarkWidget(BrandAsset.COMMON)
    qtbot.addWidget(widget)
    widget.resize(96, 96)

    pixmap = QPixmap(widget.size())
    pixmap.fill()
    widget.render(pixmap)  # type: ignore[no-untyped-call]  # PySide6 render overload lacks stubs

    assert not widget.has_valid_svg
    assert widget.fallback_text == "EpiCase"
```

- [ ] **Step 2: Run the tests and confirm the module is missing**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ui/test_brand_mark.py -q
```

Expected: collection error for `epicase_ui.brand_mark`.

- [ ] **Step 3: Implement `BrandMarkWidget`**

Create `src/epicase_ui/brand_mark.py`:

```python
"""Векторный знак EpiCase с безопасным текстовым fallback."""
from __future__ import annotations

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPaintEvent, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QWidget

from epicase_ui.branding import BrandAsset, brand_svg_bytes

_ACCESSIBLE_NAMES = {
    BrandAsset.COMMON: "Логотип EpiCase",
    BrandAsset.CONSTRUCTOR: "Логотип EpiCase Constructor",
    BrandAsset.PLAYER: "Логотип EpiCase Player",
}


class BrandMarkWidget(QWidget):
    """Масштабируемый SVG-знак; прогресс используется вступительной анимацией."""

    def __init__(
        self,
        asset: BrandAsset,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.asset = asset
        self.fallback_text = "EpiCase"
        self._intro_progress = 1.0
        self._renderer = QSvgRenderer(self)
        try:
            self._valid_svg = self._renderer.load(QByteArray(brand_svg_bytes(asset)))
        except OSError:
            self._valid_svg = False
        self.setObjectName("brandMark")
        self.setAccessibleName(_ACCESSIBLE_NAMES[asset])
        self.setMinimumSize(48, 48)

    @property
    def has_valid_svg(self) -> bool:
        """Загружен ли валидный SVG."""
        return self._valid_svg

    @property
    def intro_progress(self) -> float:
        """Текущий прогресс появления в диапазоне 0..1."""
        return self._intro_progress

    def set_intro_progress(self, progress: float) -> None:
        """Обновить прогресс появления и перерисовать знак."""
        self._intro_progress = max(0.0, min(1.0, progress))
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self._valid_svg:
            painter.setPen(QColor("#1F2A33"))
            font = QFont(self.font())
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.fallback_text)
            return

        eased = 1.0 - (1.0 - self._intro_progress) ** 3
        scale = 0.72 + 0.28 * eased
        side = min(self.width(), self.height()) * scale
        target = QRectF(
            (self.width() - side) / 2.0,
            (self.height() - side) / 2.0,
            side,
            side,
        )
        painter.setOpacity(0.25 + 0.75 * eased)
        self._renderer.render(painter, target)
```

- [ ] **Step 4: Export the widget**

Update `src/epicase_ui/__init__.py`:

```python
"""Общие presentation-компоненты Constructor и Player."""
from epicase_ui.brand_mark import BrandMarkWidget
from epicase_ui.branding import BrandAsset, brand_svg_bytes

__all__ = ["BrandAsset", "BrandMarkWidget", "brand_svg_bytes"]
```

- [ ] **Step 5: Run focused tests and static checks**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ui/test_brand_mark.py tests/ui/test_branding.py -q
.\.venv\Scripts\ruff.exe check src/epicase_ui tests/ui
.\.venv\Scripts\mypy.exe src/epicase_ui tests/ui
```

Expected: all commands exit with code 0.

- [ ] **Step 6: Commit the brand widget**

```powershell
git add -- src/epicase_ui tests/ui/test_brand_mark.py
git commit -m "feat(ui): add scalable EpiCase brand mark"
```

### Task 3: Implement the shared animated start shell

**Files:**
- Create: `src/epicase_ui/animated_start.py`
- Create: `tests/ui/test_animated_start.py`
- Modify: `src/epicase_ui/__init__.py`

- [ ] **Step 1: Write failing lifecycle, interaction and render tests**

Create `tests/ui/test_animated_start.py`:

```python
"""Тесты общей анимированной оболочки стартового экрана."""
from __future__ import annotations

from unittest.mock import MagicMock

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QPushButton, QVBoxLayout
from pytestqt.qtbot import QtBot

from epicase_ui.animated_start import (
    AnimatedStartBackground,
    AnimatedStartWidget,
    StartVariant,
)
from epicase_ui.brand_mark import BrandMarkWidget
from epicase_ui.branding import BrandAsset


def _content() -> tuple[QFrame, BrandMarkWidget, QPushButton]:
    card = QFrame()
    layout = QVBoxLayout(card)
    mark = BrandMarkWidget(BrandAsset.COMMON)
    button = QPushButton("Действие")
    layout.addWidget(mark)
    layout.addWidget(button)
    return card, mark, button


def test_variants_have_distinct_backgrounds(qtbot: QtBot) -> None:
    constructor = AnimatedStartBackground(StartVariant.CONSTRUCTOR)
    player = AnimatedStartBackground(StartVariant.PLAYER)
    qtbot.addWidget(constructor)
    qtbot.addWidget(player)

    assert constructor.objectName() == "constructorStartBackground"
    assert player.objectName() == "playerStartBackground"
    assert constructor.variant is not player.variant


def test_intro_finishes_once_and_does_not_replay(qtbot: QtBot) -> None:
    background = AnimatedStartBackground(
        StartVariant.PLAYER,
        intro_duration_ms=10,
        frame_interval_ms=5,
    )
    qtbot.addWidget(background)
    finished = MagicMock()
    background.intro_finished.connect(finished)
    background.resize(400, 240)
    background.show()

    qtbot.waitUntil(lambda: background.intro_complete, timeout=500)
    assert finished.call_count == 1

    background.hide()
    background.show()
    qtbot.wait(30)
    assert finished.call_count == 1


def test_timer_stops_while_hidden_and_resumes_without_intro(
    qtbot: QtBot,
) -> None:
    background = AnimatedStartBackground(
        StartVariant.CONSTRUCTOR,
        intro_duration_ms=5,
        frame_interval_ms=5,
    )
    qtbot.addWidget(background)
    background.show()
    qtbot.waitUntil(lambda: background.intro_complete, timeout=500)
    assert background.timer_active

    background.hide()
    assert not background.timer_active
    background.show()
    qtbot.waitUntil(lambda: background.timer_active, timeout=500)
    assert background.intro_complete


def test_action_is_available_during_intro(qtbot: QtBot) -> None:
    card, mark, button = _content()
    shell = AnimatedStartWidget(
        StartVariant.PLAYER,
        card,
        mark,
        intro_duration_ms=500,
        frame_interval_ms=20,
    )
    qtbot.addWidget(shell)
    shell.show()
    handler = MagicMock()
    button.clicked.connect(handler)

    button.click()

    assert button.isEnabled()
    handler.assert_called_once()


def test_shell_render_smoke(qtbot: QtBot) -> None:
    card, mark, _button = _content()
    shell = AnimatedStartWidget(StartVariant.PLAYER, card, mark)
    qtbot.addWidget(shell)
    shell.resize(800, 500)
    shell.show()

    pixmap = QPixmap(shell.size())
    pixmap.fill()
    shell.render(pixmap)  # type: ignore[no-untyped-call]  # PySide6 render overload lacks stubs

    assert not pixmap.isNull()
    assert shell.background.variant is StartVariant.PLAYER
```

- [ ] **Step 2: Run the tests and confirm the module is missing**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ui/test_animated_start.py -q
```

Expected: collection error for `epicase_ui.animated_start`.

- [ ] **Step 3: Implement the animation state and background painter**

Create `src/epicase_ui/animated_start.py`:

```python
"""Общая анимированная оболочка стартовых экранов EpiCase."""
from __future__ import annotations

import math
from enum import StrEnum

from PySide6.QtCore import (
    QElapsedTimer,
    QEvent,
    QLineF,
    QPointF,
    QTimer,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QGuiApplication,
    QHideEvent,
    QPaintEvent,
    QPainter,
    QPen,
    QShowEvent,
)
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QWidget,
)

from epicase_ui.brand_mark import BrandMarkWidget

_BACKGROUND = QColor("#EDF0F3")
_TEAL = QColor("#0F766E")
_DEEP_TEAL = QColor("#17393A")
_PALE_TEAL = QColor("#D9EEEB")
_BRASS = QColor("#B49A56")
_INTRO_DURATION_MS = 1400
_FRAME_INTERVAL_MS = 50

_PLAYER_NODES = (
    (0.10, 0.22, 0.0, False),
    (0.28, 0.72, 1.1, False),
    (0.46, 0.28, 2.0, True),
    (0.63, 0.66, 2.8, False),
    (0.78, 0.20, 3.6, False),
    (0.88, 0.76, 4.3, True),
    (0.51, 0.84, 5.0, False),
)
_CONSTRUCTOR_NODES = (
    (0.12, 0.20, 0.0, True),
    (0.30, 0.20, 0.9, False),
    (0.48, 0.42, 1.8, True),
    (0.68, 0.24, 2.7, False),
    (0.86, 0.24, 3.6, True),
    (0.68, 0.72, 4.5, False),
    (0.30, 0.72, 5.4, True),
)
_EDGES = ((0, 2), (1, 2), (2, 3), (2, 4), (3, 5), (3, 6))
_ASSEMBLY_TARGETS = ((-0.04, -0.12), (-0.10, 0.08), (0.10, 0.08))


class StartVariant(StrEnum):
    """Визуальный характер фоновой сети."""

    CONSTRUCTOR = "constructor"
    PLAYER = "player"


class AnimatedStartBackground(QWidget):
    """Векторная сеть с одноразовым вступлением и управляемым таймером."""

    intro_finished = Signal()
    intro_progress_changed = Signal(float)

    def __init__(
        self,
        variant: StartVariant,
        parent: QWidget | None = None,
        *,
        intro_duration_ms: int = _INTRO_DURATION_MS,
        frame_interval_ms: int = _FRAME_INTERVAL_MS,
    ) -> None:
        super().__init__(parent)
        self.variant = variant
        self.setObjectName(f"{variant.value}StartBackground")
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self._intro_duration_ms = max(1, intro_duration_ms)
        self._intro_progress = 0.0
        self._intro_complete = False
        self._intro_accumulated_ms = 0
        self._motion_accumulated_ms = 0
        self._active_clock = QElapsedTimer()
        self._intro_clock = QElapsedTimer()
        self._timer = QTimer(self)
        self._timer.setInterval(max(1, frame_interval_ms))
        self._timer.timeout.connect(self._tick)
        app = QGuiApplication.instance()
        if isinstance(app, QGuiApplication):
            app.applicationStateChanged.connect(self._on_application_state_changed)

    @property
    def intro_complete(self) -> bool:
        """Завершено ли одноразовое вступление."""
        return self._intro_complete

    @property
    def intro_progress(self) -> float:
        """Прогресс вступления 0..1."""
        return self._intro_progress

    @property
    def timer_active(self) -> bool:
        """Работает ли кадровый таймер."""
        return self._timer.isActive()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._sync_timer()

    def hideEvent(self, event: QHideEvent) -> None:
        self._stop_timer()
        super().hideEvent(event)

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            self._sync_timer()

    def _on_application_state_changed(self, _state: Qt.ApplicationState) -> None:
        self._sync_timer()

    def _should_run(self) -> bool:
        return (
            self.isVisible()
            and not self.window().isMinimized()
            and QGuiApplication.applicationState()
            == Qt.ApplicationState.ApplicationActive
        )

    def _sync_timer(self) -> None:
        if self._should_run():
            self._start_timer()
        else:
            self._stop_timer()

    def _start_timer(self) -> None:
        if self._timer.isActive():
            return
        self._active_clock.restart()
        if not self._intro_complete:
            self._intro_clock.restart()
        self._timer.start()
        self._tick()

    def _stop_timer(self) -> None:
        if not self._timer.isActive():
            return
        self._motion_accumulated_ms += self._active_clock.elapsed()
        if not self._intro_complete:
            self._intro_accumulated_ms += self._intro_clock.elapsed()
        self._timer.stop()

    def _motion_ms(self) -> int:
        if self._timer.isActive():
            return self._motion_accumulated_ms + self._active_clock.elapsed()
        return self._motion_accumulated_ms

    def _intro_ms(self) -> int:
        if self._timer.isActive() and not self._intro_complete:
            return self._intro_accumulated_ms + self._intro_clock.elapsed()
        return self._intro_accumulated_ms

    def _tick(self) -> None:
        if not self._intro_complete:
            progress = min(1.0, self._intro_ms() / self._intro_duration_ms)
            if progress != self._intro_progress:
                self._intro_progress = progress
                self.intro_progress_changed.emit(progress)
            if progress >= 1.0:
                self._intro_complete = True
                self._intro_accumulated_ms = self._intro_duration_ms
                self.intro_finished.emit()
        self.update()

    def _nodes(self) -> tuple[tuple[float, float, float, bool], ...]:
        if self.variant is StartVariant.CONSTRUCTOR:
            return _CONSTRUCTOR_NODES
        return _PLAYER_NODES

    def _node_positions(self) -> tuple[QPointF, ...]:
        seconds = self._motion_ms() / 1000.0
        width = float(self.width())
        height = float(self.height())
        points: list[QPointF] = []
        for x, y, phase, _accent in self._nodes():
            speed = 0.11 if self.variant is StartVariant.PLAYER else 0.07
            dx = math.sin(seconds * speed + phase) * 0.012
            dy = math.cos(seconds * speed * 0.8 + phase) * 0.010
            points.append(QPointF((x + dx) * width, (y + dy) * height))
        return tuple(points)

    def paintEvent(self, event: QPaintEvent) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), _BACKGROUND)
        if self.variant is StartVariant.CONSTRUCTOR:
            self._draw_grid(painter)
        points = self._node_positions()
        self._draw_network(painter, points)
        if self._intro_progress < 1.0:
            self._draw_intro_particles(painter, points)

    def _draw_grid(self, painter: QPainter) -> None:
        color = QColor(_DEEP_TEAL)
        color.setAlpha(18)
        painter.setPen(QPen(color, 1.0))
        step = 48
        for x in range(0, self.width(), step):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), step):
            painter.drawLine(0, y, self.width(), y)

    def _draw_network(self, painter: QPainter, points: tuple[QPointF, ...]) -> None:
        edge_color = QColor(_DEEP_TEAL if self.variant is StartVariant.CONSTRUCTOR else _TEAL)
        edge_color.setAlpha(int(24 + 40 * self._intro_progress))
        painter.setPen(QPen(edge_color, 1.2))
        for start, end in _EDGES:
            painter.drawLine(QLineF(points[start], points[end]))

        for point, (_x, _y, _phase, accent) in zip(points, self._nodes(), strict=True):
            color = (
                _BRASS
                if accent and self.variant is StartVariant.CONSTRUCTOR
                else _PALE_TEAL
                if accent
                else _TEAL
            )
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(point, 3.5 if accent else 2.8, 3.5 if accent else 2.8)

    def _draw_intro_particles(
        self,
        painter: QPainter,
        points: tuple[QPointF, ...],
    ) -> None:
        eased = 1.0 - (1.0 - self._intro_progress) ** 3
        center = QPointF(self.width() / 2.0, self.height() / 2.0)
        color = QColor(_TEAL)
        color.setAlpha(int(220 * (1.0 - self._intro_progress)))
        painter.setPen(QPen(color, 2.0))
        painter.setBrush(color)
        targets: list[QPointF] = []
        for dx, dy in _ASSEMBLY_TARGETS:
            targets.append(
                QPointF(
                    center.x() + dx * self.width(),
                    center.y() + dy * self.height(),
                )
            )
        for source, target in zip(points[:3], targets, strict=True):
            point = QPointF(
                source.x() + (target.x() - source.x()) * eased,
                source.y() + (target.y() - source.y()) * eased,
            )
            painter.drawLine(QLineF(point, target))
            painter.drawEllipse(point, 4.0, 4.0)


class AnimatedStartWidget(QWidget):
    """Фон и карточка действий с синхронизированным появлением знака."""

    def __init__(
        self,
        variant: StartVariant,
        content: QFrame,
        brand_mark: BrandMarkWidget,
        parent: QWidget | None = None,
        *,
        intro_duration_ms: int = _INTRO_DURATION_MS,
        frame_interval_ms: int = _FRAME_INTERVAL_MS,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("animatedStart")
        self.background = AnimatedStartBackground(
            variant,
            self,
            intro_duration_ms=intro_duration_ms,
            frame_interval_ms=frame_interval_ms,
        )
        content.setObjectName("startActionCard")
        self._effect = QGraphicsOpacityEffect(content)
        content.setGraphicsEffect(self._effect)
        self._brand_mark = brand_mark

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.background, 0, 0)
        layout.addWidget(
            content,
            0,
            0,
            Qt.AlignmentFlag.AlignCenter,
        )

        self.background.intro_progress_changed.connect(self._apply_intro_progress)
        self._apply_intro_progress(0.0)

    def _apply_intro_progress(self, progress: float) -> None:
        self._brand_mark.set_intro_progress(progress)
        self._effect.setOpacity(0.72 + 0.28 * progress)
```

- [ ] **Step 4: Export the shared components**

Update `src/epicase_ui/__init__.py`:

```python
"""Общие presentation-компоненты Constructor и Player."""
from epicase_ui.animated_start import (
    AnimatedStartBackground,
    AnimatedStartWidget,
    StartVariant,
)
from epicase_ui.brand_mark import BrandMarkWidget
from epicase_ui.branding import BrandAsset, brand_svg_bytes

__all__ = [
    "AnimatedStartBackground",
    "AnimatedStartWidget",
    "BrandAsset",
    "BrandMarkWidget",
    "StartVariant",
    "brand_svg_bytes",
]
```

- [ ] **Step 5: Run focused tests and static checks**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ui -q
.\.venv\Scripts\ruff.exe check src/epicase_ui tests/ui
.\.venv\Scripts\mypy.exe src/epicase_ui tests/ui
```

Expected: all commands exit with code 0. Application state plus show/hide events
are the lifecycle contract; no polling is added.

- [ ] **Step 6: Commit the shared animation**

```powershell
git add -- src/epicase_ui tests/ui
git commit -m "feat(ui): add animated start screen shell"
```

### Task 4: Integrate the animated start screen into Player

**Files:**
- Modify: `src/epicase_player/ui/start_screen.py`
- Modify: `tests/player/test_start_screen.py`
- Modify: `src/epicase_core/theme/theme.qss`
- Modify: `tests/core/test_theme.py`

- [ ] **Step 1: Add failing Player structure and interaction tests**

Append to `tests/player/test_start_screen.py`:

```python
from PySide6.QtWidgets import QFrame, QLabel

from epicase_ui import (
    AnimatedStartBackground,
    AnimatedStartWidget,
    BrandAsset,
    BrandMarkWidget,
    StartVariant,
)


def test_player_start_uses_animated_brand_shell(qtbot: QtBot) -> None:
    screen = StartScreen()
    qtbot.addWidget(screen)

    shell = screen.findChild(AnimatedStartWidget)
    background = screen.findChild(AnimatedStartBackground)
    mark = screen.findChild(BrandMarkWidget)
    card = screen.findChild(QFrame, "startActionCard")
    product = screen.findChild(QLabel, "startProduct")
    assert screen.objectName() == "playerStartScreen"
    assert shell is not None
    assert background is not None
    assert background.variant is StartVariant.PLAYER
    assert mark is not None
    assert mark.asset is BrandAsset.PLAYER
    assert card is not None
    assert product is not None
    assert product.text() == "PLAYER"


def test_player_open_action_is_enabled_during_intro(qtbot: QtBot) -> None:
    screen = StartScreen()
    qtbot.addWidget(screen)
    button = next(
        button
        for button in screen.findChildren(QPushButton)
        if "Открыть кейс" in button.text()
    )

    assert button.isEnabled()
```

Append to `tests/core/test_theme.py`:

```python
def test_load_qss_contains_animated_start_selectors() -> None:
    qss = load_qss()
    required = (
        "QFrame#startActionCard",
        "QLabel#startProduct",
        "QLabel#startRole",
        "QWidget#playerStartScreen",
    )
    for selector in required:
        pattern = rf"{re.escape(selector)}\s*\{{"
        assert re.search(pattern, qss) is not None
```

- [ ] **Step 2: Run focused tests and confirm they fail**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/player/test_start_screen.py tests/core/test_theme.py -q
```

Expected: failures because Player still uses the static centered layout and the
new selectors are absent.

- [ ] **Step 3: Replace Player `StartScreen`**

Replace `src/epicase_player/ui/start_screen.py` with:

```python
"""Анимированный стартовый экран Player."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from epicase_ui import (
    AnimatedStartWidget,
    BrandAsset,
    BrandMarkWidget,
    StartVariant,
)


class StartScreen(QWidget):
    """Первый экран курсанта; анимация декоративна и не блокирует действия."""

    open_requested: Signal = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("playerStartScreen")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setMaximumWidth(460)
        col = QVBoxLayout(card)
        col.setContentsMargins(28, 24, 28, 24)
        col.setSpacing(9)
        col.setAlignment(Qt.AlignmentFlag.AlignCenter)

        mark = BrandMarkWidget(BrandAsset.PLAYER)
        mark.setFixedSize(76, 76)
        col.addWidget(mark, alignment=Qt.AlignmentFlag.AlignCenter)

        title = QLabel("EpiCase")
        title.setObjectName("startTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(title)

        product = QLabel("PLAYER")
        product.setObjectName("startProduct")
        product.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(product)

        role = QLabel("Учебный тренажёр военного эпидемиолога")
        role.setObjectName("startRole")
        role.setAlignment(Qt.AlignmentFlag.AlignCenter)
        role.setWordWrap(True)
        col.addWidget(role)
        col.addSpacing(16)

        open_button = QPushButton("Открыть кейс…")
        open_button.setObjectName("startAccentButton")
        open_button.clicked.connect(self.open_requested)
        col.addWidget(open_button)

        hint = QLabel("Откройте файл .epicase, полученный от преподавателя")
        hint.setObjectName("startHint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setWordWrap(True)
        col.addWidget(hint)

        root.addWidget(AnimatedStartWidget(StartVariant.PLAYER, card, mark))
```

- [ ] **Step 4: Add the shared card and Player selectors**

Replace the old C7/C8 start-screen title/subtitle block in `theme.qss` with:

```qss
/* --- N2: анимированные стартовые экраны --- */
QFrame#startActionCard {
    background: #FFFFFF;
    border: 1px solid #D4DAE0;
    border-radius: 14px;
}
QLabel#startTitle {
    font-size: 28px;
    font-weight: bold;
    color: #1F2A33;
}
QLabel#startProduct {
    font-size: 11px;
    font-weight: bold;
}
QLabel#startRole {
    font-size: 14px;
    color: #66727E;
}
QLabel#startHint {
    font-size: 12px;
    color: #9AA5AF;
}
QWidget#playerStartScreen QLabel#startProduct {
    color: #0F766E;
}
```

Keep the existing `startAccentButton` and `startSecondaryButton` rules.

- [ ] **Step 5: Run Player, shared UI and theme tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ui tests/player/test_start_screen.py tests/player/test_main_window.py tests/core/test_theme.py -q
.\.venv\Scripts\ruff.exe check src/epicase_player/ui/start_screen.py tests/player/test_start_screen.py tests/core/test_theme.py
.\.venv\Scripts\mypy.exe src/epicase_player/ui/start_screen.py tests/player/test_start_screen.py tests/core/test_theme.py
```

Expected: all commands exit with code 0.

- [ ] **Step 6: Commit Player integration**

```powershell
git add -- src/epicase_player/ui/start_screen.py tests/player/test_start_screen.py src/epicase_core/theme/theme.qss tests/core/test_theme.py
git commit -m "feat(player): animate the branded start screen"
```

### Task 5: Integrate the animated start screen into Constructor

**Files:**
- Modify: `src/epicase_constructor/ui/start_screen.py`
- Modify: `tests/constructor/test_start_screen.py`
- Test: `tests/constructor/test_case_load.py`
- Modify: `src/epicase_core/theme/theme.qss`
- Modify: `tests/core/test_theme.py`

- [ ] **Step 1: Add failing Constructor structure tests**

Append to `tests/constructor/test_start_screen.py`:

```python
from PySide6.QtWidgets import QFrame, QLabel

from epicase_ui import (
    AnimatedStartBackground,
    AnimatedStartWidget,
    BrandAsset,
    BrandMarkWidget,
    StartVariant,
)


def test_constructor_start_uses_animated_brand_shell(qtbot: QtBot) -> None:
    screen = StartScreen()
    qtbot.addWidget(screen)

    shell = screen.findChild(AnimatedStartWidget)
    background = screen.findChild(AnimatedStartBackground)
    mark = screen.findChild(BrandMarkWidget)
    card = screen.findChild(QFrame, "startActionCard")
    product = screen.findChild(QLabel, "startProduct")
    assert screen.objectName() == "constructorStartScreen"
    assert shell is not None
    assert background is not None
    assert background.variant is StartVariant.CONSTRUCTOR
    assert mark is not None
    assert mark.asset is BrandAsset.CONSTRUCTOR
    assert card is not None
    assert product is not None
    assert product.text() == "КОНСТРУКТОР"


def test_constructor_actions_are_enabled_during_intro(qtbot: QtBot) -> None:
    screen = StartScreen()
    qtbot.addWidget(screen)

    assert all(button.isEnabled() for button in screen.findChildren(QPushButton))
```

Extend `test_load_qss_contains_animated_start_selectors` in
`tests/core/test_theme.py` with:

```python
"QWidget#constructorStartScreen",
```

- [ ] **Step 2: Run focused tests and confirm they fail**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/constructor/test_start_screen.py tests/constructor/test_case_load.py tests/core/test_theme.py -q
```

Expected: failures because Constructor still uses the static layout.

- [ ] **Step 3: Replace Constructor `StartScreen`**

Replace `src/epicase_constructor/ui/start_screen.py` with:

```python
"""Анимированный стартовый экран Constructor."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from epicase_ui import (
    AnimatedStartWidget,
    BrandAsset,
    BrandMarkWidget,
    StartVariant,
)


class StartScreen(QWidget):
    """Первый экран преподавателя с тремя существующими действиями."""

    create_requested: Signal = Signal()
    open_requested: Signal = Signal()
    check_result_requested: Signal = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("constructorStartScreen")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setMaximumWidth(520)
        col = QVBoxLayout(card)
        col.setContentsMargins(30, 24, 30, 24)
        col.setSpacing(8)
        col.setAlignment(Qt.AlignmentFlag.AlignCenter)

        mark = BrandMarkWidget(BrandAsset.CONSTRUCTOR)
        mark.setFixedSize(76, 76)
        col.addWidget(mark, alignment=Qt.AlignmentFlag.AlignCenter)

        title = QLabel("EpiCase")
        title.setObjectName("startTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(title)

        product = QLabel("КОНСТРУКТОР")
        product.setObjectName("startProduct")
        product.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(product)

        role = QLabel("Рабочее место преподавателя")
        role.setObjectName("startRole")
        role.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(role)
        col.addSpacing(14)

        create_button = QPushButton("Создать новый кейс")
        create_button.setObjectName("startAccentButton")
        create_button.clicked.connect(self.create_requested)
        col.addWidget(create_button)

        open_button = QPushButton("Открыть кейс для правки")
        open_button.setObjectName("startSecondaryButton")
        open_button.clicked.connect(self.open_requested)
        col.addWidget(open_button)

        check_button = QPushButton("Проверить результат курсанта")
        check_button.setObjectName("startSecondaryButton")
        check_button.clicked.connect(self.check_result_requested)
        col.addWidget(check_button)

        root.addWidget(AnimatedStartWidget(StartVariant.CONSTRUCTOR, card, mark))
```

- [ ] **Step 4: Add the Constructor product selector**

Append to the N2 QSS block:

```qss
QWidget#constructorStartScreen QLabel#startProduct {
    color: #17393A;
}
```

No gradient or inline Python style is allowed.

- [ ] **Step 5: Run Constructor, shared UI and theme tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ui tests/constructor/test_start_screen.py tests/constructor/test_case_load.py tests/constructor/test_main_window.py tests/core/test_theme.py -q
.\.venv\Scripts\ruff.exe check src/epicase_constructor/ui/start_screen.py tests/constructor/test_start_screen.py tests/core/test_theme.py
.\.venv\Scripts\mypy.exe src/epicase_constructor/ui/start_screen.py tests/constructor/test_start_screen.py tests/core/test_theme.py
```

Expected: all commands exit with code 0. Existing create/open/check signals remain
unchanged.

- [ ] **Step 6: Commit Constructor integration**

```powershell
git add -- src/epicase_constructor/ui/start_screen.py tests/constructor/test_start_screen.py src/epicase_core/theme/theme.qss tests/core/test_theme.py
git commit -m "feat(constructor): animate the branded start screen"
```

### Task 6: Complete N2 and run the full quality gate

**Files:**
- Modify: `TASKS.md`

- [ ] **Step 1: Mark N2 and ICON-1A complete**

Change only:

```markdown
- [ ] N2 — стартовый экран с анимированным фоном (S-M)
```

to:

```markdown
- [x] N2 — стартовый экран с анимированным фоном (S-M)
```

and:

```markdown
  - [ ] ICON-1A — утвердить общую визуальную систему и два различимых образа приложений
```

to:

```markdown
  - [x] ICON-1A — утвердить общую визуальную систему и два различимых образа приложений
```

Keep N5, ICON-1B, ICON-1C and all later tasks open.

- [ ] **Step 2: Run the full gate in order**

```powershell
.\.venv\Scripts\ruff.exe check src tests
.\.venv\Scripts\mypy.exe src tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q src tests
```

Expected: all four commands exit with code 0. Record the final collected test
count.

- [ ] **Step 3: Verify scope and repository cleanliness**

```powershell
git diff --check
git status --short
git diff --stat
```

Expected: only `TASKS.md` remains after Tasks 1–5 commits and there are no
whitespace errors.

- [ ] **Step 4: Commit the tracker**

```powershell
git add -- TASKS.md
git commit -m "docs: complete animated start screen task"
```

- [ ] **Step 5: Prepare the live verification handoff**

Report all implementation commit hashes, the pytest count and these live checks:

1. launch Constructor and Player separately;
2. confirm one main window and no splash/taskbar flicker;
3. confirm the 1.2–1.5 second A2 intro;
4. click an action before the intro finishes;
5. compare Constructor grid/brass motion with Player free teal network;
6. resize, maximize, minimize and restore;
7. open a case/editor and confirm the background stops;
8. return Constructor home and confirm the intro does not replay.

### Task 7: Increase background animation smoothness

**Files:**
- Modify: `src/epicase_ui/animated_start.py`
- Modify: `tests/ui/test_animated_start.py`

- [ ] **Step 1: Write the failing timer cadence test**

Add a test that creates `AnimatedStartBackground` with default arguments and
asserts that its child `QTimer` has a 33 ms interval and uses
`Qt.TimerType.PreciseTimer`.

- [ ] **Step 2: Run the focused test and verify it fails**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ui/test_animated_start.py::test_start_animation_uses_smooth_default_frame_cadence -q
```

Expected: FAIL because the current default interval is 50 ms.

- [ ] **Step 3: Implement the shared 30 FPS cadence**

Use one `_FRAME_INTERVAL_MS = 33` constant as the default for
`AnimatedStartBackground` and `AnimatedStartWidget`. Configure the internal
timer with `Qt.TimerType.PreciseTimer`. Keep all motion calculations based on
elapsed time.

- [ ] **Step 4: Run the full quality gate**

Run `ruff check src tests`, `mypy src tests`, `pytest -q`, and
`python -m compileall -q src tests` in that order.

- [ ] **Step 5: Commit**

```powershell
git add -- docs/superpowers/specs/2026-06-29-animated-start-brand-design.md docs/superpowers/plans/2026-06-29-animated-start-brand.md src/epicase_ui/animated_start.py tests/ui/test_animated_start.py
git commit -m "perf(ui): smooth start screen animation"
```
