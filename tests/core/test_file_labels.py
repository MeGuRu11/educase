"""Tests for user-facing file metadata labels."""
from __future__ import annotations

import pytest

from epicase_core.theme.file_labels import file_size_label, file_type_label


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("акт.pdf", "PDF"),
        ("план.docx", "DOCX"),
        ("кейс.epicase", "EPICASE"),
        ("результат.epiresult", "EPIRESULT"),
        ("README", "ФАЙЛ"),
    ],
)
def test_file_type_label_uses_uppercase_extension_or_generic_label(
    filename: str,
    expected: str,
) -> None:
    """File type labels expose an uppercase extension or a generic fallback."""
    assert file_type_label(filename) == expected


def test_file_type_label_truncates_arbitrarily_long_extensions() -> None:
    """Untrusted extensions cannot make the compact type badge unbounded."""
    assert file_type_label("артефакт.abcdefghijklmnop") == "ABCDEFGHIJ…"


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        (248, "248 Б"),
        (1024, "1 КБ"),
        (1536, "1,5 КБ"),
        (1024 * 1024, "1 МБ"),
    ],
)
def test_file_size_label_uses_compact_binary_units(size: int, expected: str) -> None:
    """File sizes use binary units with at most one decimal place."""
    assert file_size_label(size) == expected
