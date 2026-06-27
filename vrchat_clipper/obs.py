"""Defensive OBS WebSocket v5 helpers."""

from __future__ import annotations

import logging
import os
import platform
import subprocess
import time
from typing import Any

try:
    from obsws_python import ReqClient
except ImportError:  # pragma: no cover
    ReqClient = None  # type: ignore[assignment]

LOGGER = logging.getLogger(__name__)


class ObsConnectionError(Exception):
    """Raised when OBS WebSocket cannot be reached."""


def _is_windows() -> bool:
    return platform.system().lower() == "windows"


def is_obs_running() -> bool:
    """Best effort detection for a running obs64.exe process on Windows."""

    if not _is_windows():
        return False

    try:
        import psutil  # type: ignore

        for process in psutil.process_iter(["name"]):
            try:
                if (process.info.get("name") or "").lower() == "obs64.exe":
                    return True
            except Exception:
                continue
        return False
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq obs64.exe"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        return "obs64.exe" in result.stdout.lower()
    except Exception as exc:
        LOGGER.debug("Could not query tasklist for OBS: %s", exc)
        return False


def launch_obs(obs_path: str) -> None:
    """Launch OBS minimised on Windows, logging failures without raising."""

    if not _is_windows():
        LOGGER.warning("OBS auto launch is only supported on Windows")
        return
    try:
        cwd = os.path.dirname(obs_path) or None
        subprocess.Popen([obs_path, "--minimize-to-tray"], cwd=cwd)
    except Exception as exc:
        LOGGER.warning("Could not launch OBS from %s: %s", obs_path, exc)


def connect(host: str, port: int, password: str, timeout: float = 5) -> Any:
    """Connect to OBS WebSocket and return a request client."""

    if ReqClient is None:
        raise ObsConnectionError("obsws-python is not installed")
    try:
        return ReqClient(host=host, port=port, password=password, timeout=timeout)
    except Exception as exc:
        raise ObsConnectionError(f"Could not connect to OBS: {exc}") from exc


def wait_until_connectable(
    host: str,
    port: int,
    password: str,
    attempts: int = 20,
    delay: float = 0.5,
) -> Any:
    """Retry OBS connection until it succeeds or attempts are exhausted."""

    last_error: ObsConnectionError | None = None
    for attempt in range(max(1, attempts)):
        try:
            return connect(host, port, password)
        except ObsConnectionError as exc:
            last_error = exc
            if attempt < attempts - 1:
                time.sleep(delay)
    raise ObsConnectionError(str(last_error) if last_error else "Could not connect to OBS")


def _call(client: Any, snake_name: str, pascal_name: str, *args: Any, **kwargs: Any) -> Any:
    method = getattr(client, snake_name, None) or getattr(client, pascal_name, None)
    if method is None:
        raise AttributeError(f"OBS client has no method {snake_name}")
    return method(*args, **kwargs)


def ensure_scene(client: Any, scene_name: str) -> None:
    """Switch the current programme scene if OBS exposes the requested scene."""

    if not scene_name:
        return
    try:
        response = _call(client, "get_current_program_scene", "GetCurrentProgramScene")
        current = (
            getattr(response, "current_program_scene_name", None)
            or getattr(response, "currentProgramSceneName", None)
            or getattr(response, "scene_name", None)
            or getattr(response, "sceneName", None)
        )
        if current == scene_name:
            return
        set_method = getattr(client, "set_current_program_scene", None) or getattr(
            client, "SetCurrentProgramScene", None
        )
        if set_method is None:
            LOGGER.warning("OBS client cannot switch scenes")
            return
        for kwargs in ({"sceneName": scene_name}, {"scene_name": scene_name}):
            try:
                set_method(**kwargs)
                return
            except TypeError:
                continue
        set_method(scene_name)
    except Exception as exc:
        LOGGER.warning("Could not switch OBS scene to %s: %s", scene_name, exc)


def start_record(client: Any) -> None:
    """Start OBS recording."""

    _call(client, "start_record", "StartRecord")


def stop_record(client: Any) -> str | None:
    """Stop OBS recording and return the output path when OBS provides it."""

    response = _call(client, "stop_record", "StopRecord")
    output_path = (
        getattr(response, "output_path", None)
        or getattr(response, "outputPath", None)
        or getattr(response, "output", None)
    )
    return str(output_path) if output_path else None
