"""Tests for the distinct Constructor and Player application identities."""

from __future__ import annotations

import sys
from dataclasses import replace
from importlib import import_module

import pytest
from loguru import logger
from PySide6.QtWidgets import QApplication
from pytest import MonkeyPatch
from pytestqt.qtbot import QtBot

from epicase_ui.application_identity import (
    _APPLICATION_IDENTITIES,
    ApplicationIdentity,
    ApplicationVariant,
    application_icon,
    application_identity,
    configure_application,
)

application_identity_module = import_module("epicase_ui.application_identity")


def test_application_identities_are_fixed_and_distinct() -> None:
    """Each executable-facing variant has a stable identity contract."""
    constructor = application_identity(ApplicationVariant.CONSTRUCTOR)
    player = application_identity(ApplicationVariant.PLAYER)

    assert constructor == ApplicationIdentity(
        application_name="EpiCase Constructor",
        display_name="EpiCase Constructor",
        app_user_model_id="VMedA.EpiCase.Constructor",
        icon_filename="epicase_constructor.ico",
    )
    assert player == ApplicationIdentity(
        application_name="EpiCase Player",
        display_name="EpiCase Player",
        app_user_model_id="VMedA.EpiCase.Player",
        icon_filename="epicase_player.ico",
    )
    assert constructor != player


def test_application_icons_are_packaged_and_distinct(qtbot: QtBot) -> None:
    """Both allowlisted ICO resources load and remain visually distinct."""
    del qtbot
    constructor = application_icon(ApplicationVariant.CONSTRUCTOR)
    player = application_icon(ApplicationVariant.PLAYER)

    assert not constructor.isNull()
    assert not player.isNull()
    assert constructor.pixmap(64, 64).cacheKey() != player.pixmap(64, 64).cacheKey()


def test_application_icon_warns_and_returns_empty_icon_when_resource_is_missing(
    qtbot: QtBot,
    monkeypatch: MonkeyPatch,
) -> None:
    """A damaged installation does not prevent either application from starting."""
    del qtbot
    variant = ApplicationVariant.CONSTRUCTOR
    identity = application_identity(variant)
    monkeypatch.setitem(
        _APPLICATION_IDENTITIES,
        variant,
        replace(identity, icon_filename="missing.ico"),
    )
    messages: list[str] = []
    sink_id = logger.add(messages.append, level="WARNING", format="{message}")

    try:
        icon = application_icon(variant)
    finally:
        logger.remove(sink_id)

    assert icon.isNull()
    assert any("missing.ico" in message for message in messages)


def test_configure_application_sets_qt_identity(
    qapp: QApplication,
    monkeypatch: MonkeyPatch,
) -> None:
    """The application-level name and icon match the selected identity."""
    monkeypatch.setattr(sys, "platform", "linux")

    icon = configure_application(
        qapp,
        ApplicationVariant.CONSTRUCTOR,
    )

    assert qapp.applicationName() == "EpiCase Constructor"
    assert qapp.applicationDisplayName() == "EpiCase Constructor"
    assert qapp.windowIcon().cacheKey() == icon.cacheKey()


def test_configure_application_sets_windows_app_user_model_id(
    qapp: QApplication,
    monkeypatch: MonkeyPatch,
) -> None:
    """Windows receives the stable ID that separates taskbar groups."""
    calls: list[str] = []

    def record_app_user_model_id(value: str) -> int:
        calls.append(value)
        return 0

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(
        application_identity_module,
        "_call_windows_app_user_model_id",
        record_app_user_model_id,
    )

    configure_application(
        qapp,
        ApplicationVariant.PLAYER,
    )

    assert calls == ["VMedA.EpiCase.Player"]


def test_configure_application_skips_windows_api_on_other_platforms(
    qapp: QApplication,
    monkeypatch: MonkeyPatch,
) -> None:
    """Non-Windows environments do not attempt to load shell32."""
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(
        application_identity_module,
        "_call_windows_app_user_model_id",
        lambda value: pytest.fail(f"unexpected Windows call: {value}"),
    )

    configure_application(
        qapp,
        ApplicationVariant.PLAYER,
    )


def test_configure_application_continues_when_windows_api_is_unavailable(
    qapp: QApplication,
    monkeypatch: MonkeyPatch,
) -> None:
    """A missing shell32 API is logged without blocking application startup."""

    def raise_os_error(app_user_model_id: str) -> int:
        raise OSError(app_user_model_id)

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(
        application_identity_module,
        "_call_windows_app_user_model_id",
        raise_os_error,
    )
    messages: list[str] = []
    sink_id = logger.add(messages.append, level="WARNING", format="{message}")

    try:
        icon = configure_application(
            qapp,
            ApplicationVariant.PLAYER,
        )
    finally:
        logger.remove(sink_id)

    assert not icon.isNull()
    assert any("VMedA.EpiCase.Player" in message for message in messages)
