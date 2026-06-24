"""Дымовые тесты: пакеты импортируются, версия доступна."""
from __future__ import annotations

import epicase_core
from epicase_core.infrastructure.archive import EPICASE_EXT, EPIRESULT_EXT


def test_core_version_present() -> None:
    assert epicase_core.__version__


def test_archive_extensions() -> None:
    assert EPICASE_EXT == ".epicase"
    assert EPIRESULT_EXT == ".epiresult"
