"""Скриншот-прогон шести этапов Player на синтетическом кейсе (offscreen-режим).

Загружает ``_scratch/sample.educase``, строит ``CaseNavigator`` и для каждого из шести
этапов переключает стек реальной кнопкой «Далее» (проверка свободной навигации, ADR-008),
снимает ``QWidget.grab()`` и пишет ``_scratch/stage_{N}_{kind}.png``. Любое исключение на
этапе ловится, попадает в отчёт, прогон продолжается. Предупреждения Qt перехватываются
обработчиком сообщений.

Запуск из .venv (Qt без дисплея)::

    python scripts/shoot_stages.py
"""
from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

# Qt без дисплея — обязательно до импорта QtWidgets и создания QApplication.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Колесо PySide6 не поставляет шрифты; offscreen-движок иначе рисует «тофу»-квадраты.
# Подсовываем системные шрифты Windows, чтобы пруфы были читаемыми (только если каталог есть).
if "QT_QPA_FONTDIR" not in os.environ:
    _win_fonts = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    if _win_fonts.is_dir():
        os.environ["QT_QPA_FONTDIR"] = str(_win_fonts)

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from PySide6.QtCore import (  # noqa: E402
    QMessageLogContext,
    QtMsgType,
    qInstallMessageHandler,
)
from PySide6.QtWidgets import QApplication  # noqa: E402

from epicase_core.application.cases import ArchiveError, load_case  # noqa: E402
from epicase_player.ui.case_navigator import CaseNavigator  # noqa: E402

_QT_MESSAGES: list[str] = []


def _qt_handler(mode: QtMsgType, context: QMessageLogContext, message: str) -> None:
    """Сложить сообщение Qt в буфер вместо вывода в stderr."""
    _QT_MESSAGES.append(f"{mode!r}: {message}")


def _scratch_dir() -> Path:
    """Каталог пруфов: ``EDUCASE_SCRATCH`` или ``_scratch`` в корне репозитория."""
    base = os.environ.get("EDUCASE_SCRATCH")
    return Path(base) if base else _REPO_ROOT / "_scratch"


def main() -> int:
    """Снять скриншоты всех этапов; вернуть 0, если каждый отрисовался."""
    qInstallMessageHandler(_qt_handler)
    scratch = _scratch_dir()
    case_path = scratch / "sample.educase"

    report: list[str] = []
    rendered: list[str] = []
    failed: list[str] = []

    if not case_path.exists():
        print(f"НЕ НАЙДЕН кейс: {case_path}")
        print("Сначала запустите scripts/make_sample_case.py")
        return 2

    # QApplication нужен до построения любых виджетов.
    app = QApplication.instance() or QApplication([])

    try:
        loaded = load_case(case_path)
        report.append(f"Round-trip: кейс прочитан, ассетов в архиве: {len(loaded.assets)}")
    except ArchiveError as exc:
        print(f"Round-trip ПРОВАЛЕН: {exc}")
        return 2

    case = loaded.case
    stages = case.ordered()

    try:
        nav = CaseNavigator(case)
    except Exception:  # диагностический прогон — ловим всё, чтобы отчитаться
        print("CaseNavigator не построился:")
        print(traceback.format_exc())
        return 1

    nav.resize(1100, 850)
    nav.show()
    app.processEvents()

    for i, stage in enumerate(stages):
        kind = stage.KIND.value
        label = f"этап {i + 1} ({kind})"
        try:
            if i > 0:
                # Реальная навигация вперёд — заодно проверяем, что «Далее» не заперт.
                nav.btn_next.click()
            app.processEvents()
            if nav.current_index != i:
                raise RuntimeError(
                    f"стек на индексе {nav.current_index}, ожидался {i}"
                )
            pixmap = nav.grab()
            out = scratch / f"stage_{i + 1}_{kind}.png"
            if not pixmap.save(str(out)):
                raise RuntimeError(f"QPixmap.save вернул False для {out}")
            size = out.stat().st_size
            report.append(f"OK  {label}: {out.name} ({pixmap.width()}x{pixmap.height()}, {size} Б)")
            rendered.append(label)
        except Exception:  # изолируем сбой этапа, продолжаем остальные
            report.append(f"FAIL {label}:\n{traceback.format_exc()}")
            failed.append(label)

    report_path = scratch / "shoot_report.txt"
    body = "\n".join(report)
    qt_block = (
        "\n--- Сообщения Qt ---\n" + "\n".join(_QT_MESSAGES)
        if _QT_MESSAGES
        else "\n--- Сообщений Qt нет ---"
    )
    report_path.write_text(body + qt_block, encoding="utf-8")

    print("=== Скриншот-прогон этапов ===")
    print(body)
    print(qt_block)
    print("\n--- Итог ---")
    print(f"Отрисовано: {len(rendered)}/{len(stages)} — {', '.join(rendered) or '—'}")
    print(f"Упало: {len(failed)} — {', '.join(failed) or '—'}")
    print(f"Отчёт: {report_path}")

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
