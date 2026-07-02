"""Path resolution that works both from source and from a PyInstaller bundle.

Two distinct locations matter once the app is frozen into a single executable:

* Bundled, read-only resources (the ``web/`` UI) are unpacked by PyInstaller into
  a temporary directory exposed as ``sys._MEIPASS``. Use :func:`resource_dir`.
* User-editable state (``config.json``) must live next to the executable so it
  survives restarts and is easy to find. Use :func:`app_dir`.

When running from source both fall back to the repository root, so nothing about
the normal ``python -m vrchat_clipper`` workflow changes.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _frozen() -> bool:
    """True when running inside a PyInstaller (or similar) bundle."""

    return bool(getattr(sys, "frozen", False))


def resource_dir() -> Path:
    """Directory holding bundled read-only resources such as ``web/``."""

    if _frozen():
        # PyInstaller onefile extracts data files under sys._MEIPASS. onedir
        # builds set it to the executable's folder. Fall back to that folder.
        base = getattr(sys, "_MEIPASS", None)
        if base:
            return Path(base)
        return Path(sys.executable).resolve().parent
    # From source, resources live at the repository root (one level above this
    # package directory).
    return Path(__file__).resolve().parents[1]


def app_dir() -> Path:
    """Directory for user-editable state that persists next to the app.

    Frozen: the folder containing the executable. From source: the repository
    root, matching the historical ``./config.json`` location when launched via
    ``run.bat`` / ``run.sh``.
    """

    if _frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]
