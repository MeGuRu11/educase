"""Кодеки файлов обмена EduCase.

Формат: ZIP-контейнер с внутренним JSON + ассеты (фото, документы).
JSON НИКОГДА не показывается пользователю — это внутреннее представление.
Перенос архивов — только вручную через Проводник. Сети нет (ADR-003).

Расширения:
  .educase   — кейс (преподаватель → курсант)
  .eduresult — результат прохождения (курсант → преподаватель)

TODO(сверить с DATA_MODEL.md / educase-archive-format):
  - точная схема manifest.json (версия формата, id кейса, контрольная сумма)
  - перечень и структура ассетов
  - валидация при импорте
"""
from __future__ import annotations

EDUCASE_EXT = ".educase"
EDURESULT_EXT = ".eduresult"
MANIFEST_NAME = "manifest.json"
DATA_NAME = "data.json"
ASSETS_DIR = "assets"
FORMAT_VERSION = 1
