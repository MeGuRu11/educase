"""Pure helpers for user-facing file metadata labels."""
from __future__ import annotations

from pathlib import Path

_KIBIBYTE = 1024
_MEBIBYTE = 1024 * 1024
_MAX_TYPE_LABEL_LENGTH = 10


def file_type_label(filename: str | Path) -> str:
    """Return a bounded uppercase file extension or a generic Russian label."""
    suffix = Path(filename).suffix.lstrip(".")
    if not suffix:
        return "ФАЙЛ"
    label = suffix.upper()
    if len(label) > _MAX_TYPE_LABEL_LENGTH:
        return f"{label[:_MAX_TYPE_LABEL_LENGTH]}…"
    return label


def file_size_label(size_bytes: int) -> str:
    """Format a byte count with compact binary B, KB, or MB units."""
    size = max(size_bytes, 0)
    if size < _KIBIBYTE:
        return f"{size} Б"
    if size < _MEBIBYTE:
        return f"{_compact_decimal(size / _KIBIBYTE)} КБ"
    return f"{_compact_decimal(size / _MEBIBYTE)} МБ"


def _compact_decimal(value: float) -> str:
    return f"{value:.1f}".rstrip("0").rstrip(".").replace(".", ",")
