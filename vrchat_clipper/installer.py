"""Guided install and uninstall for the packaged executable.

``vrchat-clipper install`` sets the recorder up in one step:

* copies the executable into a folder you choose (default
  ``%LOCALAPPDATA%\\Programs\\VRChatClipper``);
* writes a default ``config.json`` next to it if none exists;
* copies the OVR Toolkit wrist-button app into OVR Toolkit's ``LocalCustomApps``
  folder, detected from your Steam libraries;
* registers with SteamVR for auto-launch;
* optionally adds a Start Menu shortcut.

``vrchat-clipper uninstall`` reverses the SteamVR registration and removes the OVR
Toolkit app folder, and with ``--purge`` also deletes the config and install folder.

The detection and copy logic lives in small, testable functions so a future GUI
installer (for example an Inno Setup wrapper) can call ``install --silent`` and
reuse all of it rather than re-implementing Steam/OVR Toolkit path discovery.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from . import config as config_module
from .paths import ovr_dir

LOGGER = logging.getLogger(__name__)

# Steam AppID for OVR Toolkit.
OVRT_APPID = "1068820"
# Folder name created inside OVR Toolkit's LocalCustomApps.
OVR_APP_FOLDER = "VRChatClipper"
INSTALLED_EXE_NAME = "vrchat-clipper.exe"
INSTALL_DIR_NAME = "VRChatClipper"


# --------------------------------------------------------------------------- #
# Pure helpers (no side effects) - unit-testable on any platform.
# --------------------------------------------------------------------------- #


def default_install_dir() -> Path:
    """The recommended per-user install folder.

    Windows: ``%LOCALAPPDATA%\\Programs\\VRChatClipper`` - a per-user location that
    needs no administrator rights. Elsewhere (dev machines): under the user data
    directory so the command still works for testing.
    """

    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local) / "Programs" / INSTALL_DIR_NAME
    return Path.home() / ".local" / "share" / "vrchat-clipper"


def parse_library_folders(vdf_text: str) -> list[Path]:
    """Extract every Steam library path from a ``libraryfolders.vdf`` file."""

    paths: list[Path] = []
    for match in re.finditer(r'"path"\s+"([^"]+)"', vdf_text):
        raw = match.group(1).replace("\\\\", "\\")
        paths.append(Path(raw))
    return paths


def parse_appmanifest_installdir(acf_text: str) -> str | None:
    """Return the ``installdir`` recorded in a Steam ``appmanifest_*.acf`` file."""

    match = re.search(r'"installdir"\s+"([^"]+)"', acf_text)
    return match.group(1) if match else None


def localcustomapps_candidates(ovrt_dir: Path) -> list[Path]:
    """Possible LocalCustomApps locations inside an OVR Toolkit install.

    Different OVR Toolkit versions use one of these two layouts, so both are
    tried, most specific first.
    """

    return [
        ovrt_dir / "CustomApps" / "LocalCustomApps",
        ovrt_dir / "LocalCustomApps",
    ]


def pick_localcustomapps(ovrt_dir: Path) -> Path:
    """Choose the LocalCustomApps folder, preferring one that already exists."""

    candidates = localcustomapps_candidates(ovrt_dir)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    # Neither exists yet: fall back to the plain, historically documented layout.
    return candidates[-1]


def ovr_entry_url(cfg: dict[str, Any]) -> str:
    """The ``http://host:port/ovr`` URL OVR Toolkit should load."""

    server = cfg.get("server", {}) if isinstance(cfg, dict) else {}
    host = str(server.get("host", "127.0.0.1"))
    port = int(server.get("port", 8765))
    if host in {"0.0.0.0", "::"}:
        host = "127.0.0.1"
    return f"http://{host}:{port}/ovr"


# --------------------------------------------------------------------------- #
# Detection (reads the filesystem / registry).
# --------------------------------------------------------------------------- #


def steam_root() -> Path | None:
    """Locate the Steam installation folder, or ``None`` if not found."""

    # Preferred on Windows: the registry value Steam writes for the current user.
    if os.name == "nt":
        try:
            import winreg  # type: ignore

            for hive, key in (
                (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam"),
            ):
                try:
                    with winreg.OpenKey(hive, key) as handle:
                        value, _ = winreg.QueryValueEx(
                            handle, "SteamPath" if hive == winreg.HKEY_CURRENT_USER else "InstallPath"
                        )
                        candidate = Path(value)
                        if candidate.exists():
                            return candidate
                except OSError:
                    continue
        except Exception:  # pragma: no cover - winreg quirks
            pass

    for candidate in (
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Steam",
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Steam",
        Path.home() / ".steam" / "steam",
        Path.home() / ".local" / "share" / "Steam",
    ):
        if candidate.exists():
            return candidate
    return None


def steam_library_paths(steam: Path) -> list[Path]:
    """All Steam library roots, including the main install."""

    libraries = [steam]
    vdf = steam / "steamapps" / "libraryfolders.vdf"
    if vdf.exists():
        try:
            libraries.extend(parse_library_folders(vdf.read_text(encoding="utf-8")))
        except OSError:
            pass
    # De-duplicate while preserving order.
    seen: set[str] = set()
    unique: list[Path] = []
    for library in libraries:
        key = str(library).lower()
        if key not in seen:
            seen.add(key)
            unique.append(library)
    return unique


def find_ovrt_dir() -> Path | None:
    """Find the OVR Toolkit install directory via Steam, or ``None``."""

    steam = steam_root()
    if steam is None:
        return None
    for library in steam_library_paths(steam):
        manifest = library / "steamapps" / f"appmanifest_{OVRT_APPID}.acf"
        if not manifest.exists():
            continue
        installdir = "OVR Toolkit"
        try:
            parsed = parse_appmanifest_installdir(manifest.read_text(encoding="utf-8"))
            if parsed:
                installdir = parsed
        except OSError:
            pass
        candidate = library / "steamapps" / "common" / installdir
        if candidate.exists():
            return candidate
    return None


def find_ovrt_localcustomapps() -> Path | None:
    """Find OVR Toolkit's LocalCustomApps folder via Steam, or ``None``."""

    ovrt = find_ovrt_dir()
    if ovrt is None:
        return None
    return pick_localcustomapps(ovrt)


# --------------------------------------------------------------------------- #
# Actions (side effects).
# --------------------------------------------------------------------------- #


def _running_executable() -> Path | None:
    """The frozen executable currently running, or ``None`` when from source."""

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    return None


def copy_executable(dest_dir: Path) -> Path | None:
    """Copy the running exe into ``dest_dir``. Returns the installed path.

    Returns ``None`` when not running as a frozen exe (nothing to copy - the
    ``vrchat-clipper`` command is already on PATH from the pip install).
    """

    source = _running_executable()
    if source is None:
        return None
    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / INSTALLED_EXE_NAME
    if target.resolve() == source.resolve():
        return target
    shutil.copy2(source, target)
    return target


def write_default_config(dest_dir: Path, *, overwrite: bool = False) -> Path:
    """Write a default ``config.json`` into ``dest_dir`` if absent."""

    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / "config.json"
    if target.exists() and not overwrite:
        return target
    target.write_text(
        json.dumps(config_module.default_config(), indent=2) + "\n", encoding="utf-8"
    )
    return target


def install_ovr_app(localcustomapps: Path, entry_url: str) -> Path:
    """Copy the wrist-button app into ``localcustomapps`` and set its entry URL."""

    source = ovr_dir()
    target = localcustomapps / OVR_APP_FOLDER
    target.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        if item.name.lower() == "readme.md" or item.is_dir():
            continue
        shutil.copy2(item, target / item.name)
    # entry.txt tells OVR Toolkit which URL to load; keep it matched to the server.
    (target / "entry.txt").write_text(entry_url, encoding="utf-8")
    return target


def create_start_menu_shortcut(exe: Path) -> Path | None:
    """Create a Start Menu shortcut on Windows. Best-effort; returns the path."""

    if os.name != "nt":
        return None
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None
    shortcut = (
        Path(appdata)
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
        / "VRChat Clipper.lnk"
    )
    shortcut.parent.mkdir(parents=True, exist_ok=True)
    ps = (
        "$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{lnk}'); "
        "$s.TargetPath = '{exe}'; "
        "$s.WorkingDirectory = '{cwd}'; "
        "$s.Save()"
    ).format(lnk=str(shortcut), exe=str(exe), cwd=str(exe.parent))
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
            check=True,
            capture_output=True,
        )
        return shortcut
    except Exception as exc:  # pragma: no cover - Windows only
        LOGGER.warning("Could not create Start Menu shortcut: %s", exc)
        return None


def register_with_steamvr(exe: Path | None) -> bool:
    """Register the installed app with SteamVR for auto-launch."""

    if exe is not None and getattr(sys, "frozen", False):
        # Register the *installed* exe so the manifest points at the right path.
        try:
            result = subprocess.run(
                [str(exe), "--register-vr"], capture_output=True, timeout=60
            )
            return result.returncode == 0
        except Exception as exc:  # pragma: no cover - runtime dependent
            LOGGER.warning("SteamVR registration failed: %s", exc)
            return False
    # From source / pip: register the current interpreter entry point directly.
    from . import desktop

    return desktop.register_vrmanifest()


def unregister_from_steamvr(exe: Path | None) -> bool:
    """Remove the SteamVR auto-launch registration."""

    if exe is not None and exe.exists() and getattr(sys, "frozen", False):
        try:
            result = subprocess.run(
                [str(exe), "--unregister-vr"], capture_output=True, timeout=60
            )
            return result.returncode == 0
        except Exception as exc:  # pragma: no cover - runtime dependent
            LOGGER.warning("SteamVR unregistration failed: %s", exc)
            return False
    from . import desktop

    return desktop.unregister_vrmanifest()


# --------------------------------------------------------------------------- #
# Interactive helpers.
# --------------------------------------------------------------------------- #


def _prompt(question: str, default: str) -> str:
    try:
        answer = input(f"{question} [{default}]: ").strip()
    except EOFError:
        return default
    return answer or default


def _prompt_yes_no(question: str, default: bool) -> bool:
    suffix = "Y/n" if default else "y/N"
    try:
        answer = input(f"{question} ({suffix}): ").strip().lower()
    except EOFError:
        return default
    if not answer:
        return default
    return answer in {"y", "yes"}


# --------------------------------------------------------------------------- #
# Command entry points.
# --------------------------------------------------------------------------- #


def run_install(args: argparse.Namespace) -> int:
    silent = args.silent

    install_dir = Path(args.dir).expanduser() if args.dir else default_install_dir()
    if not silent and not args.dir:
        install_dir = Path(
            _prompt("Install folder", str(install_dir))
        ).expanduser()

    print(f"Installing VRChat Clipper into {install_dir}")
    installed_exe = copy_executable(install_dir)
    if installed_exe is not None:
        print(f"  copied executable -> {installed_exe}")
    else:
        print("  running from source/pip; skipping executable copy")

    cfg_path = write_default_config(install_dir)
    print(f"  config: {cfg_path}")
    cfg = config_module.merge_config(config_module.default_config(), {})

    # OVR Toolkit wrist-button app.
    if not args.skip_ovr:
        localcustomapps: Path | None
        if args.ovrt_dir:
            localcustomapps = Path(args.ovrt_dir).expanduser()
        else:
            localcustomapps = find_ovrt_localcustomapps()
            if localcustomapps is None and not silent:
                print("  could not auto-detect OVR Toolkit's LocalCustomApps folder.")
                typed = _prompt(
                    "  Enter its path, or leave blank to skip", ""
                ).strip()
                localcustomapps = Path(typed).expanduser() if typed else None
            elif localcustomapps is not None and not silent:
                if not _prompt_yes_no(
                    f"  Install wrist button into {localcustomapps}?", True
                ):
                    typed = _prompt("  Enter a different path, or blank to skip", "")
                    localcustomapps = Path(typed).expanduser() if typed.strip() else None

        if localcustomapps is not None:
            try:
                target = install_ovr_app(localcustomapps, ovr_entry_url(cfg))
                print(f"  wrist button -> {target}")
            except OSError as exc:
                print(f"  WARNING: could not install wrist button: {exc}")
        else:
            src = ovr_dir()
            print(
                "  skipped wrist button. Copy this folder into OVR Toolkit's "
                f"LocalCustomApps manually:\n    {src}"
            )

    # SteamVR auto-launch.
    if not args.no_vr:
        if register_with_steamvr(installed_exe):
            print("  registered with SteamVR for auto-launch")
        else:
            print("  WARNING: SteamVR registration did not complete (is SteamVR installed?)")

    # Start Menu shortcut.
    make_shortcut = not args.no_shortcut
    if make_shortcut and not silent and installed_exe is not None:
        make_shortcut = _prompt_yes_no("Create a Start Menu shortcut?", True)
    if make_shortcut and installed_exe is not None:
        shortcut = create_start_menu_shortcut(installed_exe)
        if shortcut is not None:
            print(f"  shortcut -> {shortcut}")

    print("\nDone. Start VRChat Clipper from the Start Menu or let SteamVR launch it.")
    if installed_exe is not None:
        print(f"Executable: {installed_exe}")
    return 0


def run_uninstall(args: argparse.Namespace) -> int:
    install_dir = Path(args.dir).expanduser() if args.dir else default_install_dir()
    installed_exe = install_dir / INSTALLED_EXE_NAME

    print("Uninstalling VRChat Clipper")
    if unregister_from_steamvr(installed_exe if installed_exe.exists() else None):
        print("  removed SteamVR auto-launch registration")
    else:
        print("  SteamVR registration not removed (may not have been registered)")

    # Remove the OVR Toolkit wrist-button folder.
    localcustomapps = (
        Path(args.ovrt_dir).expanduser()
        if args.ovrt_dir
        else find_ovrt_localcustomapps()
    )
    if localcustomapps is not None:
        target = localcustomapps / OVR_APP_FOLDER
        if target.exists():
            try:
                shutil.rmtree(target)
                print(f"  removed wrist button folder {target}")
            except OSError as exc:
                print(f"  WARNING: could not remove {target}: {exc}")

    if args.purge:
        config_file = install_dir / "config.json"
        try:
            if config_file.exists():
                config_file.unlink()
                print(f"  removed {config_file}")
        except OSError as exc:
            print(f"  WARNING: could not remove {config_file}: {exc}")
        # The running exe cannot delete itself on Windows; remove what we can.
        running = _running_executable()
        if running is not None and running.parent == install_dir:
            print(
                "  the executable is running from the install folder; delete "
                f"{install_dir} manually after it exits."
            )
        else:
            try:
                if install_dir.exists():
                    shutil.rmtree(install_dir)
                    print(f"  removed {install_dir}")
            except OSError as exc:
                print(f"  WARNING: could not remove {install_dir}: {exc}")

    print("\nDone.")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="vrchat-clipper", description="Install or uninstall VRChat Clipper"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    install = sub.add_parser("install", help="Install VRChat Clipper on this PC.")
    install.add_argument("--dir", help="Install folder (default: LocalAppData\\Programs\\VRChatClipper).")
    install.add_argument("--ovrt-dir", help="OVR Toolkit LocalCustomApps folder (skip auto-detection).")
    install.add_argument("--skip-ovr", action="store_true", help="Do not install the OVR Toolkit wrist button.")
    install.add_argument("--no-vr", action="store_true", help="Do not register with SteamVR.")
    install.add_argument("--no-shortcut", action="store_true", help="Do not create a Start Menu shortcut.")
    install.add_argument("--silent", action="store_true", help="Run without prompts, using defaults.")
    install.set_defaults(func=run_install)

    uninstall = sub.add_parser("uninstall", help="Remove VRChat Clipper from this PC.")
    uninstall.add_argument("--dir", help="Install folder to clean up.")
    uninstall.add_argument("--ovrt-dir", help="OVR Toolkit LocalCustomApps folder (skip auto-detection).")
    uninstall.add_argument("--purge", action="store_true", help="Also delete config.json and the install folder.")
    uninstall.add_argument("--silent", action="store_true", help="Run without prompts.")
    uninstall.set_defaults(func=run_uninstall)

    args = parser.parse_args(argv)
    return int(args.func(args))
