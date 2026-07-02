"""Command line entry point for ``python -m vrchat_clipper`` and the frozen exe.

Behaviour is intentionally different depending on how it is launched:

* From source (``python -m vrchat_clipper``): run a plain foreground server, the
  historical behaviour. No optional desktop dependencies are required.
* Frozen (the packaged ``.exe``): default to a system-tray app and make a
  best-effort attempt to register with SteamVR for auto-launch. Both can be
  toggled with flags.
"""

from __future__ import annotations

import argparse
import sys

from .config import load_config
from .server import run


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the VRChat Clipper backend")
    tray_group = parser.add_mutually_exclusive_group()
    tray_group.add_argument(
        "--tray",
        dest="tray",
        action="store_true",
        default=None,
        help="Run with a system-tray icon (default when running as a packaged exe).",
    )
    tray_group.add_argument(
        "--no-tray",
        dest="tray",
        action="store_false",
        help="Run a plain foreground server with no tray icon.",
    )
    parser.add_argument(
        "--register-vr",
        action="store_true",
        help="Register with SteamVR for auto-launch, then exit.",
    )
    parser.add_argument(
        "--unregister-vr",
        action="store_true",
        help="Remove the SteamVR auto-launch registration, then exit.",
    )
    parser.add_argument(
        "--no-vr-register",
        action="store_true",
        help="Do not auto-register with SteamVR on startup (frozen builds only).",
    )
    args = parser.parse_args()

    # One-shot SteamVR registration commands.
    if args.register_vr or args.unregister_vr:
        from . import desktop

        ok = (
            desktop.register_vrmanifest()
            if args.register_vr
            else desktop.unregister_vrmanifest()
        )
        raise SystemExit(0 if ok else 1)

    # Decide whether to show a tray: explicit flag wins, otherwise on when frozen.
    use_tray = args.tray if args.tray is not None else _is_frozen()

    cfg = load_config()
    server_cfg = cfg["server"]
    print(f"Serving VRChat Clipper at http://{server_cfg['host']}:{server_cfg['port']}")

    # Frozen builds try to register with SteamVR once on startup unless opted out.
    if _is_frozen() and not args.no_vr_register:
        try:
            from . import desktop

            desktop.register_vrmanifest()
        except Exception:
            pass

    if use_tray:
        from . import desktop

        desktop.run_with_tray()
    else:
        run()


if __name__ == "__main__":
    main()
