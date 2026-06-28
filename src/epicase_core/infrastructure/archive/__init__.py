"""Кодеки файлов обмена EpiCase.

Формат: ZIP-контейнер с внутренним JSON + ассеты (фото, документы).
JSON НИКОГДА не показывается пользователю — это внутреннее представление.
Перенос архивов — только вручную через Проводник. Сети нет (ADR-003).

Расширения:
  .epicase   — кейс (преподаватель → курсант)
  .epiresult — результат прохождения (курсант → преподаватель)
"""
from __future__ import annotations

EPICASE_EXT = ".epicase"
EPIRESULT_EXT = ".epiresult"
MANIFEST_NAME = "manifest.json"
DATA_NAME = "data.json"
ASSETS_DIR = "assets"
FORMAT_VERSION = 1
