"""Исключения кодеков архивов обмена."""
from __future__ import annotations


class ArchiveError(Exception):
    """Базовая ошибка работы с архивом обмена."""


class CorruptedArchiveError(ArchiveError):
    """Архив повреждён или имеет неверную структуру."""


class IncompatibleVersionError(ArchiveError):
    """Версия формата архива несовместима с текущей."""
