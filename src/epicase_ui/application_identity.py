"""Distinct runtime identities for the two EpiCase applications."""

from __future__ import annotations

import ctypes
import sys
from dataclasses import dataclass
from enum import StrEnum
from importlib.resources import files
from typing import Protocol, cast

from loguru import logger
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication


class ApplicationVariant(StrEnum):
    """A separately launched and packaged EpiCase application."""

    CONSTRUCTOR = "constructor"
    PLAYER = "player"


@dataclass(frozen=True)
class ApplicationIdentity:
    """Stable runtime identity used by Qt, Windows, and future packaging."""

    application_name: str
    display_name: str
    app_user_model_id: str
    icon_filename: str


_APPLICATION_IDENTITIES = {
    ApplicationVariant.CONSTRUCTOR: ApplicationIdentity(
        application_name="EpiCase Constructor",
        display_name="EpiCase Constructor",
        app_user_model_id="VMedA.EpiCase.Constructor",
        icon_filename="epicase_constructor.ico",
    ),
    ApplicationVariant.PLAYER: ApplicationIdentity(
        application_name="EpiCase Player",
        display_name="EpiCase Player",
        app_user_model_id="VMedA.EpiCase.Player",
        icon_filename="epicase_player.ico",
    ),
}


class _AppUserModelIdSetter(Protocol):
    """Typed surface of the shell32 function used by this module."""

    argtypes: list[type[ctypes.c_wchar_p]]
    restype: type[ctypes.c_long]

    def __call__(self, app_user_model_id: str) -> int: ...


class _Shell32(Protocol):
    """Typed subset of shell32 used by this module."""

    SetCurrentProcessExplicitAppUserModelID: _AppUserModelIdSetter


class _WinDllFactory(Protocol):
    """Platform-provided ctypes Windows library loader."""

    def __call__(self, name: str, *, use_last_error: bool) -> _Shell32: ...


def application_identity(variant: ApplicationVariant) -> ApplicationIdentity:
    """Return the fixed identity for an EpiCase application variant."""
    return _APPLICATION_IDENTITIES[variant]


def application_icon(variant: ApplicationVariant) -> QIcon:
    """Load the allowlisted packaged ICO for an EpiCase application variant."""
    identity = application_identity(variant)
    resource = files("epicase_ui").joinpath(
        "resources",
        "app_icons",
        identity.icon_filename,
    )
    try:
        icon = QIcon(str(resource))
    except OSError as exc:
        logger.warning(
            "Не удалось загрузить иконку приложения {}: {}",
            identity.icon_filename,
            exc,
        )
        return QIcon()
    if icon.isNull():
        logger.warning(
            "Иконка приложения отсутствует или повреждена: {}",
            identity.icon_filename,
        )
    return icon


def configure_application(
    app: QApplication,
    variant: ApplicationVariant,
) -> QIcon:
    """Apply one variant identity to Qt and the current Windows process."""
    identity = application_identity(variant)
    app.setApplicationName(identity.application_name)
    app.setApplicationDisplayName(identity.display_name)
    icon = application_icon(variant)
    app.setWindowIcon(icon)
    _set_windows_app_user_model_id(identity.app_user_model_id)
    return icon


def _call_windows_app_user_model_id(app_user_model_id: str) -> int:
    """Call the Windows API that assigns the current process taskbar identity."""
    factory = cast(_WinDllFactory, ctypes.WinDLL)
    shell32 = factory("shell32", use_last_error=True)
    setter = shell32.SetCurrentProcessExplicitAppUserModelID
    setter.argtypes = [ctypes.c_wchar_p]
    setter.restype = ctypes.c_long
    return setter(app_user_model_id)


def _set_windows_app_user_model_id(app_user_model_id: str) -> None:
    """Set the taskbar identity on Windows and remain a no-op elsewhere."""
    if sys.platform != "win32":
        return
    try:
        result = _call_windows_app_user_model_id(app_user_model_id)
    except (AttributeError, OSError) as exc:
        logger.warning(
            "Не удалось назначить Windows AppUserModelID {}: {}",
            app_user_model_id,
            exc,
        )
        return
    if result != 0:
        logger.warning(
            "Windows отклонила AppUserModelID {} с HRESULT {}",
            app_user_model_id,
            result,
        )
