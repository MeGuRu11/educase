"""Дымовые тесты: пакеты импортируются, версия доступна."""
from __future__ import annotations

import epicase_core
from epicase_core.infrastructure.archive import EDUCASE_EXT, EDURESULT_EXT


def test_core_version_present() -> None:
    assert epicase_core.__version__


def test_archive_extensions() -> None:
    assert EDUCASE_EXT == ".epicase"
    assert EDURESULT_EXT == ".epiresult"
