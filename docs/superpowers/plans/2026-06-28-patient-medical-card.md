# Patient Medical Card Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the plain patient tiles and detail dialog with a keyboard-accessible clinical-card UI while preserving the existing `PatientCard` data model and stage behavior.

**Architecture:** Keep `PatientsStageView` and the domain unchanged. `PatientCardWidget` becomes a styled interactive `QFrame`; `PatientDetailDialog` renders the same ordered field pairs as semantic label/value rows and keeps using `AssetImageWidget` for case assets. All visual properties remain in the shared QSS.

**Tech Stack:** Python 3.12, PySide6 Widgets, pytest/pytest-qt, QSS, ruff, mypy strict.

---

### Task 1: Redesign the patient tile and keyboard activation

**Files:**
- Modify: `tests/player/test_patient_card_widget.py`
- Modify: `src/epicase_player/ui/patient_card_widget.py`

- [ ] **Step 1: Replace the old tile tests with failing structural and keyboard tests**

Use object names rather than widget order so the tests describe the public UI contract:

```python
"""Тесты кликабельной медицинской карточки пациента."""
from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel
from pytestqt.qtbot import QtBot

from epicase_core.domain.stages import PatientCard
from epicase_player.ui.patient_card_widget import PatientCardWidget


def _card() -> PatientCard:
    return PatientCard(
        id="internal-p1",
        title="Рядовой А. — 1-я рота",
        fields=(("Диагноз", "сальмонеллёз"), ("Возраст", "25 лет")),
    )


def test_card_face_shows_only_patient_identity(qtbot: QtBot) -> None:
    widget = PatientCardWidget(_card())
    qtbot.addWidget(widget)

    title = widget.findChild(QLabel, "patientCardTitle")
    card_type = widget.findChild(QLabel, "patientCardType")
    action = widget.findChild(QLabel, "patientCardAction")
    assert title is not None
    assert title.text() == "Рядовой А. — 1-я рота"
    assert card_type is not None
    assert card_type.text() == "Медицинская карта пациента"
    assert action is not None
    assert action.text() == "Открыть карту →"

    texts = [label.text() for label in widget.findChildren(QLabel)]
    assert "сальмонеллёз" not in texts
    assert "25 лет" not in texts
    assert "internal-p1" not in texts


def test_card_has_medical_marker(qtbot: QtBot) -> None:
    widget = PatientCardWidget(_card())
    qtbot.addWidget(widget)

    symbol = widget.findChild(QLabel, "patientCardMarkerSymbol")
    marker_text = widget.findChild(QLabel, "patientCardMarkerText")
    assert symbol is not None
    assert symbol.text() == "+"
    assert marker_text is not None
    assert marker_text.text() == "КАРТА"


def test_clicked_signal_emitted_on_left_mouse_press(qtbot: QtBot) -> None:
    widget = PatientCardWidget(_card())
    qtbot.addWidget(widget)
    widget.show()

    with qtbot.waitSignal(widget.clicked, timeout=1000):
        qtbot.mouseClick(widget, Qt.MouseButton.LeftButton)  # type: ignore[no-untyped-call]  # pytest-qt lacks stubs


@pytest.mark.parametrize(
    "key",
    (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space),
)
def test_clicked_signal_emitted_from_keyboard(qtbot: QtBot, key: Qt.Key) -> None:
    widget = PatientCardWidget(_card())
    qtbot.addWidget(widget)
    widget.show()
    widget.setFocus()

    with qtbot.waitSignal(widget.clicked, timeout=1000):
        qtbot.keyClick(widget, key)  # type: ignore[no-untyped-call]  # pytest-qt lacks stubs
```

- [ ] **Step 2: Run the tile tests and confirm they fail**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/player/test_patient_card_widget.py -q
```

Expected: failures because the new `patientCard*` labels do not exist and keyboard activation is not implemented.

- [ ] **Step 3: Implement the tile as an interactive `QFrame`**

Replace `patient_card_widget.py` with:

```python
"""Компактная кликабельная медицинская карточка пациента."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QMouseEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from epicase_core.domain.stages import PatientCard


class PatientCardWidget(QFrame):
    """Идентификация пациента и переход к полной медицинской карте."""

    clicked = Signal()

    def __init__(self, card: PatientCard, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.card = card
        self.setObjectName("patientCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(f"Открыть медицинскую карту: {card.title}")
        self.setMinimumHeight(124)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        marker = QFrame()
        marker.setObjectName("patientCardMarker")
        marker.setFixedWidth(64)
        marker_layout = QVBoxLayout(marker)
        marker_layout.setContentsMargins(8, 14, 8, 14)
        marker_layout.setSpacing(4)
        marker_layout.addStretch()

        symbol = QLabel("+")
        symbol.setObjectName("patientCardMarkerSymbol")
        symbol.setAlignment(Qt.AlignmentFlag.AlignCenter)
        marker_layout.addWidget(symbol)

        marker_text = QLabel("КАРТА")
        marker_text.setObjectName("patientCardMarkerText")
        marker_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        marker_layout.addWidget(marker_text)
        marker_layout.addStretch()
        layout.addWidget(marker)

        content = QWidget()
        content.setObjectName("patientCardContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(14, 12, 14, 12)
        content_layout.setSpacing(5)

        title = QLabel(card.title)
        title.setObjectName("patientCardTitle")
        title.setWordWrap(True)
        content_layout.addWidget(title)

        card_type = QLabel("Медицинская карта пациента")
        card_type.setObjectName("patientCardType")
        content_layout.addWidget(card_type)
        content_layout.addStretch()

        action = QLabel("Открыть карту →")
        action.setObjectName("patientCardAction")
        content_layout.addWidget(action)
        layout.addWidget(content, 1)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.clicked.emit()
            event.accept()
            return
        super().keyPressEvent(event)
```

- [ ] **Step 4: Run tile and flow-layout tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/player/test_patient_card_widget.py tests/player/test_flow_layout.py -q
```

Expected: all tests pass; `PatientsStageView` still builds one 300 px tile per patient.

- [ ] **Step 5: Commit the tile behavior**

```powershell
git add -- src/epicase_player/ui/patient_card_widget.py tests/player/test_patient_card_widget.py
git commit -m "feat(player): redesign patient card tiles"
```

### Task 2: Structure the primary medical data dialog

**Files:**
- Modify: `tests/player/test_patient_detail_dialog.py`
- Modify: `src/epicase_player/ui/patient_detail_dialog.py`

- [ ] **Step 1: Write failing tests for semantic rows, empty state and materials**

Replace `test_patient_detail_dialog.py` with:

```python
"""Тесты структурированной медицинской карты пациента."""
from __future__ import annotations

from PySide6.QtWidgets import QLabel
from pytestqt.qtbot import QtBot

from epicase_core.domain.stages import PatientCard
from epicase_player.ui.patient_detail_dialog import PatientDetailDialog


def _card(*fields: tuple[str, str], assets: tuple[str, ...] = ()) -> PatientCard:
    return PatientCard(id="p1", title="Иванов И.И.", fields=fields, assets=assets)


def test_dialog_shows_clinical_header(qtbot: QtBot) -> None:
    dialog = PatientDetailDialog(_card(("Жалобы", "Слабость")), assets={})
    qtbot.addWidget(dialog)

    eyebrow = dialog.findChild(QLabel, "patientDetailEyebrow")
    title = dialog.findChild(QLabel, "patientDetailTitle")
    assert dialog.objectName() == "patientDetailDialog"
    assert dialog.minimumWidth() == 600
    assert eyebrow is not None
    assert eyebrow.text() == "Медицинская карта пациента"
    assert title is not None
    assert title.text() == "Иванов И.И."


def test_fields_are_separate_label_value_rows(qtbot: QtBot) -> None:
    dialog = PatientDetailDialog(
        _card(("Диагноз", "сальмонеллёз"), ("Возраст", "30 лет")),
        assets={},
    )
    qtbot.addWidget(dialog)

    names = dialog.findChildren(QLabel, "patientFieldName")
    values = dialog.findChildren(QLabel, "patientFieldValue")
    assert [label.text() for label in names] == ["Диагноз", "Возраст"]
    assert [label.text() for label in values] == ["сальмонеллёз", "30 лет"]
    assert all(label.wordWrap() for label in values)


def test_empty_fields_show_neutral_state(qtbot: QtBot) -> None:
    dialog = PatientDetailDialog(_card(), assets={})
    qtbot.addWidget(dialog)

    empty = dialog.findChild(QLabel, "patientEmptyState")
    assert empty is not None
    assert empty.text() == "Первичные данные не заполнены"


def test_materials_heading_only_appears_with_assets(qtbot: QtBot) -> None:
    without_assets = PatientDetailDialog(_card(), assets={})
    with_assets = PatientDetailDialog(
        _card(assets=("photo_01",)),
        assets={},
    )
    qtbot.addWidget(without_assets)
    qtbot.addWidget(with_assets)

    assert without_assets.findChild(QLabel, "patientMaterialsTitle") is None
    heading = with_assets.findChild(QLabel, "patientMaterialsTitle")
    assert heading is not None
    assert heading.text() == "Материалы пациента"


def test_missing_asset_shows_placeholder(qtbot: QtBot) -> None:
    dialog = PatientDetailDialog(
        _card(assets=("photo_01",)),
        assets={},
    )
    qtbot.addWidget(dialog)

    texts = [label.text() for label in dialog.findChildren(QLabel)]
    assert any("недоступно" in text for text in texts)
```

- [ ] **Step 2: Run the dialog tests and confirm they fail**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/player/test_patient_detail_dialog.py -q
```

Expected: failures because the current dialog uses `schemeReveal*` names, concatenates field pairs into one label and has no empty/materials states.

- [ ] **Step 3: Implement the structured dialog**

Replace `patient_detail_dialog.py` with:

```python
"""Модальная read-only медицинская карта пациента (ADR-008)."""
from __future__ import annotations

from collections.abc import Mapping

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from epicase_core.domain.stages import PatientCard
from epicase_player.ui.asset_image_widget import AssetImageWidget


class PatientDetailDialog(QDialog):
    """Первичные данные и материалы пациента без редактирования."""

    def __init__(
        self,
        card: PatientCard,
        assets: Mapping[str, bytes],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("patientDetailDialog")
        self.setWindowTitle(card.title)
        self.setMinimumWidth(600)
        self.resize(720, 560)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QFrame()
        header.setObjectName("patientDetailHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(24, 18, 24, 18)
        header_layout.setSpacing(4)

        eyebrow = QLabel("Медицинская карта пациента")
        eyebrow.setObjectName("patientDetailEyebrow")
        header_layout.addWidget(eyebrow)

        title = QLabel(card.title)
        title.setObjectName("patientDetailTitle")
        title.setWordWrap(True)
        header_layout.addWidget(title)
        outer.addWidget(header)

        scroll = QScrollArea()
        scroll.setObjectName("patientDetailScroll")
        scroll.setWidgetResizable(True)

        body = QFrame()
        body.setObjectName("patientDetailBody")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(24, 20, 24, 20)
        body_layout.setSpacing(0)

        if card.fields:
            for key, value in card.fields:
                row = QFrame()
                row.setObjectName("patientFieldRow")
                row_layout = QVBoxLayout(row)
                row_layout.setContentsMargins(0, 10, 0, 12)
                row_layout.setSpacing(4)

                name = QLabel(key)
                name.setObjectName("patientFieldName")
                name.setWordWrap(True)
                row_layout.addWidget(name)

                field_value = QLabel(value)
                field_value.setObjectName("patientFieldValue")
                field_value.setWordWrap(True)
                field_value.setTextInteractionFlags(
                    Qt.TextInteractionFlag.TextSelectableByMouse
                )
                row_layout.addWidget(field_value)
                body_layout.addWidget(row)
        else:
            empty = QLabel("Первичные данные не заполнены")
            empty.setObjectName("patientEmptyState")
            body_layout.addWidget(empty)

        if card.assets:
            materials = QLabel("Материалы пациента")
            materials.setObjectName("patientMaterialsTitle")
            body_layout.addWidget(materials)
            for asset_id in card.assets:
                body_layout.addWidget(AssetImageWidget(asset_id, assets))

        body_layout.addStretch()
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

        footer = QFrame()
        footer.setObjectName("patientDetailFooter")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(16, 12, 16, 12)
        footer_layout.addStretch()

        close = QPushButton("Закрыть")
        close.setObjectName("patientDetailClose")
        close.clicked.connect(self.accept)
        footer_layout.addWidget(close)
        outer.addWidget(footer)
```

- [ ] **Step 4: Run focused dialog and stage tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/player/test_patient_detail_dialog.py tests/player/test_stage_views.py -q
```

Expected: all tests pass and stage dialog creation still receives the original card and assets.

- [ ] **Step 5: Commit the dialog structure**

```powershell
git add -- src/epicase_player/ui/patient_detail_dialog.py tests/player/test_patient_detail_dialog.py
git commit -m "feat(player): structure patient medical details"
```

### Task 3: Apply the approved clinical-card theme

**Files:**
- Modify: `tests/core/test_theme.py`
- Modify: `src/epicase_core/theme/theme.qss`

- [ ] **Step 1: Add a failing selector contract test**

Append:

```python
def test_load_qss_contains_patient_medical_card_selectors() -> None:
    qss = load_qss()
    required = (
        "QFrame#patientCard",
        "QFrame#patientCardMarker",
        "QLabel#patientCardTitle",
        "QFrame#patientDetailHeader",
        "QLabel#patientFieldName",
        "QPushButton#patientDetailClose",
    )
    assert all(selector in qss for selector in required)
```

- [ ] **Step 2: Run the selector test and confirm it fails**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/core/test_theme.py::test_load_qss_contains_patient_medical_card_selectors -q
```

Expected: failure because the approved selectors are not yet present.

- [ ] **Step 3: Replace the old patient hover rule with the complete QSS block**

Use only existing palette values:

```qss
/* --- N1: клинические карточки пациентов --- */
QFrame#patientCard {
    background: #FFFFFF;
    border: 1px solid #D4DAE0;
    border-radius: 10px;
}
QFrame#patientCard:hover {
    background: #F6F8FA;
    border-color: #0F766E;
}
QFrame#patientCard:focus {
    border: 2px solid #0F766E;
}
QFrame#patientCardMarker {
    background: #0F766E;
    border-top-left-radius: 9px;
    border-bottom-left-radius: 9px;
}
QLabel#patientCardMarkerSymbol {
    color: #FFFFFF;
    font-size: 26px;
    font-weight: bold;
}
QLabel#patientCardMarkerText {
    color: #D9EEEB;
    font-size: 10px;
    font-weight: bold;
}
QWidget#patientCardContent {
    background: transparent;
}
QLabel#patientCardTitle {
    color: #1F2A33;
    font-size: 15px;
    font-weight: bold;
}
QLabel#patientCardType {
    color: #66727E;
    font-size: 12px;
}
QLabel#patientCardAction {
    color: #0F766E;
    font-size: 12px;
    font-weight: bold;
}

QDialog#patientDetailDialog {
    background: #EDF0F3;
}
QFrame#patientDetailHeader {
    background: #0F766E;
}
QLabel#patientDetailEyebrow {
    color: #D9EEEB;
    font-size: 12px;
}
QLabel#patientDetailTitle {
    color: #FFFFFF;
    font-size: 20px;
    font-weight: bold;
}
QScrollArea#patientDetailScroll {
    background: #EDF0F3;
    border: none;
}
QFrame#patientDetailBody {
    background: #FFFFFF;
}
QFrame#patientFieldRow {
    border-bottom: 1px solid #E1E6EA;
}
QLabel#patientFieldName {
    color: #66727E;
    font-size: 12px;
    font-weight: bold;
}
QLabel#patientFieldValue {
    color: #1F2A33;
    font-size: 14px;
}
QLabel#patientEmptyState {
    color: #66727E;
    padding: 18px 0;
}
QLabel#patientMaterialsTitle {
    color: #1F2A33;
    font-size: 16px;
    font-weight: bold;
    padding-top: 18px;
}
QFrame#patientDetailFooter {
    background: #FFFFFF;
    border-top: 1px solid #D4DAE0;
}
QPushButton#patientDetailClose {
    background: #0F766E;
    color: #FFFFFF;
    border: 1px solid #0F766E;
    border-radius: 6px;
    padding: 7px 20px;
}
QPushButton#patientDetailClose:hover {
    background: #0B5E57;
    border-color: #0B5E57;
}
QPushButton#patientDetailClose:pressed {
    background: #0A524C;
}
```

- [ ] **Step 4: Run theme and complete patient UI tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/core/test_theme.py tests/player/test_patient_card_widget.py tests/player/test_patient_detail_dialog.py tests/player/test_flow_layout.py tests/player/test_stage_views.py -q
```

Expected: all focused tests pass.

- [ ] **Step 5: Commit the approved visual system**

```powershell
git add -- src/epicase_core/theme/theme.qss tests/core/test_theme.py
git commit -m "feat(player): style patient medical cards"
```

### Task 4: Complete N1 and run the project quality gate

**Files:**
- Modify: `TASKS.md`

- [ ] **Step 1: Mark only N1 complete**

Change:

```markdown
- [ ] N1 — мед-карточный вид карточек пациента (M)
```

to:

```markdown
- [x] N1 — мед-карточный вид карточек пациента (M)
```

Do not start or mark N2.

- [ ] **Step 2: Run the full gate in the required order**

```powershell
.\.venv\Scripts\ruff.exe check src tests
.\.venv\Scripts\mypy.exe src tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q src tests
```

Expected: all four commands exit with code 0. Record the final pytest test count for the report.

- [ ] **Step 3: Confirm the diff is limited to N1**

```powershell
git status --short
git diff --check
git diff --stat
```

Expected: only `TASKS.md` remains uncommitted after the three implementation commits; no whitespace errors.

- [ ] **Step 4: Commit the tracker update**

```powershell
git add -- TASKS.md
git commit -m "docs: complete patient medical card task"
```

- [ ] **Step 5: Prepare the live verification handoff**

Report the commit hashes, pytest count and these checks for
`C:\Users\user\Desktop\Program\educase_testdata\shigellosis.epicase`:

1. all eight tiles look consistent and keep medical details hidden;
2. long patient names wrap without overlap;
3. mouse, Enter and Space open the same card;
4. all four primary fields are readable without horizontal scrolling;
5. scrolling and closing the dialog preserve the current stage.
