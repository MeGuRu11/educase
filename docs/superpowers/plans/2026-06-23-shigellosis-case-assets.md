# Shigellosis Case Assets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Создать и проверить единый комплект из 11 PNG-ассетов для учебного кейса о вспышке шигеллёза.

**Architecture:** Каждый кадр генерируется отдельно встроенным генератором изображений по общей стилевой спецификации и сценическому дополнению. Полученные файлы копируются в один проектный каталог, затем центрированно кадрируются в 4:3, масштабируются до точных размеров и переводятся в непрозрачный sRGB PNG.

**Tech Stack:** built-in image generation, Python, Pillow, PowerShell.

---

### Task 1: Подготовить каталог и общую спецификацию

**Files:**
- Create: `assets/case_shigellosis/`

- [ ] **Step 1: Создать каталог**

Run:

```powershell
New-Item -ItemType Directory -Force assets/case_shigellosis
```

Expected: каталог существует, существующие файлы не удалены.

- [ ] **Step 2: Зафиксировать общий prompt**

Использовать во всех 11 вызовах:

```text
Use case: stylized-concept
Asset type: EduCase inspection scene background with clickable hotspots added later by the application
Style/medium: semi-realistic 3D architectural visualization, consistent institutional training-series render
Lighting/mood: soft even overcast daylight, no hard shadows, calm instructional presentation
Color palette: muted gray-green, beige, white tile, gray concrete, subdued low-saturation colors
Composition: landscape 4:3 frame; clearly separated inspection objects with open space around them
Constraints: no visible text, letters, numbers, signage, logos, watermarks, borders or vignette; no flags, heraldry, real military insignia, weapons or combat; empty scene or only distant anonymous rear-facing silhouettes; opaque background
```

### Task 2: Сгенерировать территорию

**Files:**
- Create: `assets/case_shigellosis/scheme-territory.png`

- [ ] **Step 1: Сгенерировать эталон серии**

Добавить к общему prompt:

```text
Scene: bird's-eye view with gentle isometric perspective of a fenced military compound.
Required separated objects: checkpoint and gates, internal roads, parade ground, two barracks, a larger visually prominent canteen, medical station, water tower, boiler house with chimney, food warehouse, utility block with outdoor latrines.
Ground: lawns and restrained deciduous trees between buildings.
Layout: every building has a distinct footprint and generous gaps for independent clickable zones; nothing touches or overlaps.
```

- [ ] **Step 2: Сохранить выбранный результат под требуемым именем**

Expected: исходное изображение имеет ландшафтный кадр без текста и перечисленные объекты.

### Task 3: Сгенерировать интерьеры пищевого объекта

**Files:**
- Create: `assets/case_shigellosis/interior-canteen-kitchen.png`
- Create: `assets/case_shigellosis/interior-cold-room.png`
- Create: `assets/case_shigellosis/interior-canteen-hall.png`
- Create: `assets/case_shigellosis/interior-dishwashing.png`
- Create: `assets/case_shigellosis/detail-fridge-shelf.png`
- Create: `assets/case_shigellosis/interior-food-storage.png`

- [ ] **Step 1: Сгенерировать пищеблок**

Scene delta: eye-level wide kitchen with cooking range or kettles, preparation table, sink,
equipment rack and cold-room door; shared cutting boards, raw and ready food mixed, mildly
unclean surfaces.

- [ ] **Step 2: Сгенерировать холодильную камеру**

Scene delta: walk-in cold room with metal shelves, wall thermometer without legible markings,
trays and crates; raw meat and ready food stored together, disordered shelves.

- [ ] **Step 3: Сгенерировать обеденный зал**

Scene delta: rows of tables and benches, serving line with bain-marie in the background,
separate dishwashing pass-through window.

- [ ] **Step 4: Сгенерировать моечную**

Scene delta: dishwashing tubs, drying rack and dishes; cramped arrangement and no distinct
disinfection area.

- [ ] **Step 5: Сгенерировать крупный план холодильной полки**

Scene delta: close-up shelf with raw meat immediately beside an uncovered prepared meal;
clinical instructional framing without gore.

- [ ] **Step 6: Сгенерировать продовольственный склад**

Scene delta: shelving, sacks, boxes, cans and pallets; some food directly on the floor and
incompatible goods stored together.

Expected for every step: 4:3 landscape, eye-level unless stated otherwise, 3–5 separated
inspection targets, no text.

### Task 4: Сгенерировать казарменные и санитарные помещения

**Files:**
- Create: `assets/case_shigellosis/interior-barracks.png`
- Create: `assets/case_shigellosis/interior-washroom.png`
- Create: `assets/case_shigellosis/interior-latrine.png`

- [ ] **Step 1: Сгенерировать спальное помещение**

Scene delta: rows of bunk beds, bedside cabinets, central aisle and windows; crowded spacing,
closed or poorly ventilated appearance.

- [ ] **Step 2: Сгенерировать умывальную**

Scene delta: long row of sinks and taps, mirrors and tile; a few visibly broken or dry taps,
too few usable washing points.

- [ ] **Step 3: Сгенерировать санузел**

Scene delta: restrained institutional toilet with cubicles and handwashing basin; worn,
unsatisfactory but non-graphic condition.

Expected: no people in the foreground, no bodily waste or graphic contamination.

### Task 5: Сгенерировать водонапорную башню

**Files:**
- Create: `assets/case_shigellosis/exterior-water-tower.png`

- [ ] **Step 1: Сгенерировать внешний вид**

Scene delta: eye-level three-quarter view of an old utilitarian water tower, nearby water-main
service hatch or inspection well, aging valves and pipework, damp concrete and visible leak
traces; no text or signs.

### Task 6: Нормализовать изображения

**Files:**
- Modify: all files in `assets/case_shigellosis/`

- [ ] **Step 1: Привести файлы к точным размерам**

Use Pillow with `ImageOps.fit(..., method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))`.
Set `scheme-territory.png` to `2048×1536`; set the other ten files to `1600×1200`.
Convert every image to `RGB` and save as optimized PNG with an embedded sRGB-compatible
profile when available.

- [ ] **Step 2: Проверить технические свойства**

Run a Pillow inspection that asserts:

```python
image.format == "PNG"
image.size == expected_size
image.mode == "RGB"
```

Expected: 11 files checked, zero failures.

### Task 7: Проверить комплект и зафиксировать результат

**Files:**
- Verify: `assets/case_shigellosis/*.png`

- [ ] **Step 1: Создать контактный лист для визуальной проверки**

Create a temporary JPEG/PNG preview with labeled filenames outside the deliverable images.
Review consistency, accidental text, missing objects, obvious people, weapons, insignia,
watermarks and unusable hotspot crowding.

- [ ] **Step 2: Проверить состав каталога**

Expected exact filenames:

```text
scheme-territory.png
interior-canteen-kitchen.png
interior-cold-room.png
interior-canteen-hall.png
interior-dishwashing.png
interior-barracks.png
interior-washroom.png
exterior-water-tower.png
interior-food-storage.png
detail-fridge-shelf.png
interior-latrine.png
```

- [ ] **Step 3: Запустить quality gate проекта**

Run:

```powershell
ruff check src tests
mypy src tests
pytest -q
python -m compileall -q src tests
```

Expected: все команды завершаются с кодом 0.

- [ ] **Step 4: Commit**

```powershell
git add assets/case_shigellosis docs/superpowers/plans/2026-06-23-shigellosis-case-assets.md
git commit -m "feat: add shigellosis case image assets"
```
