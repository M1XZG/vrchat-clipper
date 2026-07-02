"""Path resolution that works from source, from a pip install, and when frozen.

Three situations must all work:

* **From source** (``python -m vrchat_clipper`` in a checkout).
* **Pip-installed** (the package lives under ``site-packages``).
* **Frozen** into a single PyInstaller executable.

The web UI ships inside the package (``vrchat_clipper/web``) so it is found in
all three cases. User-editable state (``config.json``) lives next to the
executable when frozen, otherwise in the current working directory.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _frozen() -> bool:
    """True when running inside a PyInstaller (or similar) bundle."""

    return bool(getattr(sys, "frozen", False))


def _bundle_root() -> Path:
    """Root of the unpacked bundle when frozen."""

    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base)
    return Path(sys.executable).resolve().parent


def web_dir() -> Path:
    """Directory holding the bundled web UI.

    Frozen builds place it at ``<bundle>/web`` (see the PyInstaller spec). From
    source or a pip install it lives inside the package.
    """

    if _frozen():
        return _bundle_root() / "web"
    return Path(__file__).resolve().parent / "web"


def app_dir() -> Path:
    """Directory for user-editable state that persists between runs.

    Frozen: the folder containing the executable, so ``config.json`` sits right
    next to it. Otherwise: the current working directory, preserving the
    historical ``./config.json`` location and behaving sensibly for a
    pip-installed console script.
    """

    if _frozen():
        return Path(sys.executable).resolve().parent
    return Path.cwd()
