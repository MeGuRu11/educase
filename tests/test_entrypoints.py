"""Tests for Constructor and Player process entry points."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from typing import Protocol, cast

import pytest
from pytest import MonkeyPatch

from epicase_ui import ApplicationVariant


class _Entrypoint(Protocol):
    """Callable surface required from an application entry-point module."""

    main: Callable[[], int]


@pytest.mark.parametrize(
    ("module_name", "expected_variant"),
    (
        ("epicase_constructor.__main__", ApplicationVariant.CONSTRUCTOR),
        ("epicase_player.__main__", ApplicationVariant.PLAYER),
    ),
)
def test_main_configures_identity_and_launches_window_maximized(
    monkeypatch: MonkeyPatch,
    module_name: str,
    expected_variant: ApplicationVariant,
) -> None:
    """Each entry point applies its icon before maximizing the main window."""
    module = import_module(module_name)
    entrypoint = cast(_Entrypoint, module)
    events: list[str] = []
    applications: list[object] = []
    configured: list[tuple[object, ApplicationVariant]] = []
    sentinel_icon = object()

    class FakeApplication:
        def __init__(self, argv: list[str]) -> None:
            del argv
            applications.append(self)
            events.append("application-created")

        def setStyleSheet(self, qss: str) -> None:
            del qss

        def exec(self) -> int:
            events.append("exec")
            return 17

    class FakeMainWindow:
        def __init__(self) -> None:
            events.append("window-created")

        def setWindowIcon(self, icon: object) -> None:
            assert icon is sentinel_icon
            events.append("window-icon")

        def showMaximized(self) -> None:
            events.append("maximized")

        def show(self) -> None:
            pytest.fail("Entry point used normal-size show()")

        def showFullScreen(self) -> None:
            pytest.fail("Entry point used borderless showFullScreen()")

    def fake_setup_logging(application_name: str) -> None:
        del application_name

    def fake_load_qss() -> str:
        return ""

    def fake_configure_application(
        app: object,
        variant: ApplicationVariant,
    ) -> object:
        configured.append((app, variant))
        events.append("configure")
        return sentinel_icon

    monkeypatch.setattr(module, "QApplication", FakeApplication)
    monkeypatch.setattr(module, "MainWindow", FakeMainWindow)
    monkeypatch.setattr(module, "setup_logging", fake_setup_logging)
    monkeypatch.setattr(module, "load_qss", fake_load_qss)
    monkeypatch.setattr(
        module,
        "configure_application",
        fake_configure_application,
        raising=False,
    )

    assert entrypoint.main() == 17
    assert configured == [(applications[0], expected_variant)]
    assert events == [
        "application-created",
        "configure",
        "window-created",
        "window-icon",
        "maximized",
        "exec",
    ]
