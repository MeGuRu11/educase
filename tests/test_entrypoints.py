"""Tests for Constructor and Player process entry points."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from typing import Protocol, cast

import pytest
from pytest import MonkeyPatch


class _Entrypoint(Protocol):
    """Callable surface required from an application entry-point module."""

    main: Callable[[], int]


@pytest.mark.parametrize(
    "module_name",
    ("epicase_constructor.__main__", "epicase_player.__main__"),
)
def test_main_launches_window_maximized(
    monkeypatch: MonkeyPatch,
    module_name: str,
) -> None:
    """Normal process startup keeps system chrome and maximizes the main window."""
    module = import_module(module_name)
    entrypoint = cast(_Entrypoint, module)
    show_calls: list[str] = []

    class FakeApplication:
        def __init__(self, argv: list[str]) -> None:
            del argv

        def setStyleSheet(self, qss: str) -> None:
            del qss

        def exec(self) -> int:
            return 17

    class FakeMainWindow:
        def showMaximized(self) -> None:
            show_calls.append("maximized")

        def show(self) -> None:
            pytest.fail("Entry point used normal-size show()")

        def showFullScreen(self) -> None:
            pytest.fail("Entry point used borderless showFullScreen()")

    def fake_setup_logging(application_name: str) -> None:
        del application_name

    def fake_load_qss() -> str:
        return ""

    monkeypatch.setattr(module, "QApplication", FakeApplication)
    monkeypatch.setattr(module, "MainWindow", FakeMainWindow)
    monkeypatch.setattr(module, "setup_logging", fake_setup_logging)
    monkeypatch.setattr(module, "load_qss", fake_load_qss)

    assert entrypoint.main() == 17
    assert show_calls == ["maximized"]
