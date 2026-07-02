"""Desktop integration for the frozen executable.

Everything here is best-effort and optional. The imports for the tray icon
(``pystray`` / ``Pillow``) and SteamVR bindings (``openvr``) are done lazily and
wrapped in broad ``try/except`` blocks, so:

* running from source (``python -m vrchat_clipper``) never needs these packages;
* a headless or Linux environment silently falls back to a plain server;
* a broken SteamVR install does not stop the recorder from working.

The two capabilities provided are:

* :func:`register_vrmanifest` / :func:`unregister_vrmanifest` — write an
  ``app.vrmanifest`` next to the executable and (un)register it with SteamVR so
  the recorder auto-launches when SteamVR starts.
* :func:`run_with_tray` — start the uvicorn server in a background thread and
  show a small system-tray icon. Falls back to :func:`vrchat_clipper.server.run`
  when a tray cannot be created.
"""

from __future__ import annotations

import json
import logging
import sys
import threading
import webbrowser
from pathlib import Path
from typing import Any

from .config import load_config
from .paths import app_dir, web_dir

LOGGER = logging.getLogger(__name__)

APP_KEY = "m1xzg.vrchatclipper"
APP_NAME = "VRChat Clipper"
APP_DESCRIPTION = "One-button VRChat short-clip recorder"


def _executable_path() -> Path:
    """Absolute path to the running executable (frozen) or this script."""

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    # From source there is no single binary; use the Python interpreter so the
    # generated manifest is still syntactically valid for inspection/testing.
    return Path(sys.executable).resolve()


def _manifest_path() -> Path:
    return app_dir() / "app.vrmanifest"


def write_vrmanifest() -> Path:
    """Write ``app.vrmanifest`` next to the executable and return its path."""

    manifest: dict[str, Any] = {
        "source": "builtin",
        "applications": [
            {
                "app_key": APP_KEY,
                "launch_type": "binary",
                "binary_path_windows": str(_executable_path()),
                "is_dashboard_overlay": True,
                "auto_launch": True,
                "strings": {
                    "en_us": {
                        "name": APP_NAME,
                        "description": APP_DESCRIPTION,
                    }
                },
            }
        ],
    }
    path = _manifest_path()
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def register_vrmanifest() -> bool:
    """Register the manifest with SteamVR and enable auto-launch.

    Returns ``True`` on success. Any failure (SteamVR not installed, no runtime,
    ``openvr`` missing) is logged and returns ``False`` without raising.
    """

    try:
        import openvr  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on optional dep
        LOGGER.warning("openvr not available, cannot register with SteamVR: %s", exc)
        return False

    manifest = write_vrmanifest()
    try:
        openvr.init(openvr.VRApplication_Utility)
    except Exception as exc:  # pragma: no cover - depends on SteamVR runtime
        LOGGER.warning("Could not init SteamVR runtime to register: %s", exc)
        return False
    try:
        apps = openvr.VRApplications()
        apps.addApplicationManifest(str(manifest), False)
        apps.setApplicationAutoLaunch(APP_KEY, True)
        LOGGER.info("Registered %s with SteamVR (auto-launch on).", APP_KEY)
        return True
    except Exception as exc:  # pragma: no cover - depends on SteamVR runtime
        LOGGER.warning("SteamVR manifest registration failed: %s", exc)
        return False
    finally:
        try:
            openvr.shutdown()
        except Exception:
            pass


def unregister_vrmanifest() -> bool:
    """Remove the manifest registration from SteamVR. Best-effort."""

    try:
        import openvr  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dep
        LOGGER.warning("openvr not available, cannot unregister: %s", exc)
        return False

    manifest = _manifest_path()
    try:
        openvr.init(openvr.VRApplication_Utility)
    except Exception as exc:  # pragma: no cover - runtime
        LOGGER.warning("Could not init SteamVR runtime to unregister: %s", exc)
        return False
    try:
        apps = openvr.VRApplications()
        apps.setApplicationAutoLaunch(APP_KEY, False)
        if manifest.exists():
            apps.removeApplicationManifest(str(manifest))
        LOGGER.info("Unregistered %s from SteamVR.", APP_KEY)
        return True
    except Exception as exc:  # pragma: no cover - runtime
        LOGGER.warning("SteamVR manifest removal failed: %s", exc)
        return False
    finally:
        try:
            openvr.shutdown()
        except Exception:
            pass


def _server_url() -> str:
    cfg = load_config()
    server = cfg.get("server", {})
    host = server.get("host", "127.0.0.1")
    port = int(server.get("port", 8765))
    # Present loopback binds as localhost for the browser.
    if host in {"0.0.0.0", "::"}:
        host = "127.0.0.1"
    return f"http://{host}:{port}/"


def _start_server_thread() -> threading.Thread:
    from .server import run

    thread = threading.Thread(target=run, name="vrchat-clipper-server", daemon=True)
    thread.start()
    return thread


def _tray_icon():  # pragma: no cover - requires a desktop session
    """Build a pystray Icon, or return ``None`` if unavailable."""

    try:
        import pystray  # type: ignore
        from PIL import Image  # type: ignore
    except Exception as exc:
        LOGGER.info("Tray unavailable (pystray/Pillow missing): %s", exc)
        return None

    icon_path = web_dir() / "icon.png"
    try:
        image = Image.open(icon_path)
    except Exception:
        # Fall back to a solid colour square so the tray still appears.
        from PIL import Image as _Image  # type: ignore

        image = _Image.new("RGBA", (64, 64), (239, 68, 68, 255))

    def _open_ui(icon, item):
        webbrowser.open(_server_url())

    def _record(icon, item):
        try:
            import urllib.request

            urllib.request.urlopen(_server_url().rstrip("/") + "/api/clip", data=b"", timeout=5)
        except Exception as exc:
            LOGGER.warning("Tray record request failed: %s", exc)

    def _quit(icon, item):
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("Open UI", _open_ui, default=True),
        pystray.MenuItem("Record now", _record),
        pystray.MenuItem("Quit", _quit),
    )
    return pystray.Icon("vrchat-clipper", image, APP_NAME, menu)


def run_with_tray() -> None:
    """Run the server with a tray icon, falling back to a plain server run."""

    _start_server_thread()
    icon = _tray_icon()
    if icon is None:
        LOGGER.info("No tray available; running server in the foreground.")
        # Keep the process alive on the server thread.
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass
        return
    icon.run()
