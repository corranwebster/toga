from __future__ import annotations

import os
import sys
from functools import cache
from importlib.metadata import entry_points

from .factory import Factory

# Map python sys.platform with toga platforms names
_TOGA_PLATFORMS = {
    "android": "android",
    "darwin": "macOS",
    "ios": "iOS",
    "linux": "linux",
    "freebsd": "freeBSD",
    "tvos": "tvOS",
    "watchos": "watchOS",
    "wearos": "wearOS",
    "emscripten": "web",
    "win32": "windows",
}


def get_current_platform() -> str | None:
    # Rely on `sys.getandroidapilevel`, which only exists on Android; see
    # https://github.com/beeware/Python-Android-support/issues/8
    if hasattr(sys, "getandroidapilevel"):
        return "android"
    elif sys.platform.startswith("freebsd"):
        return "freeBSD"
    else:
        return _TOGA_PLATFORMS.get(sys.platform)


current_platform = get_current_platform()


def find_backends():
    # As of Setuptools 65.5, entry points are returned duplicated if the
    # package is installed editable. Use a set to ensure that each entry point
    # is only returned once.
    # See https://github.com/pypa/setuptools/issues/3649
    return sorted(set(entry_points(group="toga.backends")))


@cache
def get_backend() -> str:
    toga_backends = find_backends()
    if len(toga_backends) == 1:
        backend_name = toga_backends[0].name
    else:
        backend_name = os.environ.get("TOGA_BACKEND")
        if backend_name is not None:
            toga_backends = [
                entry_point
                for entry_point in toga_backends
                if entry_point.name == backend_name
            ]
        if len(toga_backends) == 0:
            raise RuntimeError("No Toga backend could be loaded.")
        elif len(toga_backends) == 1:
            backend_name = toga_backends[0].name
        else:
            toga_backends_string = ", ".join(
                [
                    f"{entry_point.value!r} ({entry_point.name})"
                    for entry_point in toga_backends
                ]
            )
            raise RuntimeError(
                f"Multiple candidate toga backends found: "
                f"({toga_backends_string}). "
                f"Uninstall the backends you don't require, or use "
                f"TOGA_BACKEND to specify a backend."
            )
    return backend_name


factory = Factory("core")


def __getattr__(name):
    if name == "backend":
        globals()["backend"] = get_backend()
        return globals()["backend"]
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'") from None
