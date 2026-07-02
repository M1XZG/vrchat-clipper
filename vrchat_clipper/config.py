"""Configuration loading, merging, validation and saving."""

from __future__ import annotations

import copy
import json
import logging
import os
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)

DEFAULT: dict[str, Any] = {
    "clip_length_s": 5.0,
    "intro_buffer_s": 1.0,
    "tail_buffer_s": 1.0,
    "countdown_s": 5,
    "obs": {
        "host": "127.0.0.1",
        "port": 4455,
        "password": "",
        "scene": "VRChat",
        "switch_scene": True,
        "auto_launch": True,
        "obs_path": "C:\\Program Files\\obs-studio\\bin\\64bit\\obs64.exe",
    },
    "osc": {
        "host": "127.0.0.1",
        "port": 9000,
        "countdown_enabled": True,
        "countdown_template": "{n}",
        "go_text": "REC",
        "done_text": "",
    },
    "server": {"host": "127.0.0.1", "port": 8765},
    "output": {"copy_to_folder": ""},
}


def _config_path() -> Path:
    override = os.environ.get("VRCHAT_CLIPPER_CONFIG")
    if override:
        return Path(override)
    from .paths import app_dir

    return app_dir() / "config.json"


def default_config() -> dict[str, Any]:
    """Return a deep copy of the default configuration."""

    return copy.deepcopy(DEFAULT)


def _as_float(value: Any, default: float, minimum: float, maximum: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return min(max(number, minimum), maximum)


def _as_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return min(max(number, minimum), maximum)


def _as_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def _as_str(value: Any, default: str) -> str:
    if value is None:
        return default
    return str(value)


def _deep_merge(base: dict[str, Any], partial: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in partial.items():
        if key not in merged:
            continue
        if isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _validate(cfg: dict[str, Any]) -> dict[str, Any]:
    defaults = default_config()
    validated = default_config()

    validated["clip_length_s"] = _as_float(
        cfg.get("clip_length_s"), defaults["clip_length_s"], 0.1, 120.0
    )
    validated["intro_buffer_s"] = _as_float(
        cfg.get("intro_buffer_s"), defaults["intro_buffer_s"], 0.0, 30.0
    )
    validated["tail_buffer_s"] = _as_float(
        cfg.get("tail_buffer_s"), defaults["tail_buffer_s"], 0.0, 30.0
    )
    validated["countdown_s"] = _as_int(
        cfg.get("countdown_s"), defaults["countdown_s"], 0, 30
    )

    obs = cfg.get("obs") if isinstance(cfg.get("obs"), dict) else {}
    default_obs = defaults["obs"]
    validated["obs"] = {
        "host": _as_str(obs.get("host"), default_obs["host"]),
        "port": _as_int(obs.get("port"), default_obs["port"], 1, 65535),
        "password": _as_str(obs.get("password"), default_obs["password"]),
        "scene": _as_str(obs.get("scene"), default_obs["scene"]),
        "switch_scene": _as_bool(obs.get("switch_scene"), default_obs["switch_scene"]),
        "auto_launch": _as_bool(obs.get("auto_launch"), default_obs["auto_launch"]),
        "obs_path": _as_str(obs.get("obs_path"), default_obs["obs_path"]),
    }

    osc = cfg.get("osc") if isinstance(cfg.get("osc"), dict) else {}
    default_osc = defaults["osc"]
    validated["osc"] = {
        "host": _as_str(osc.get("host"), default_osc["host"]),
        "port": _as_int(osc.get("port"), default_osc["port"], 1, 65535),
        "countdown_enabled": _as_bool(
            osc.get("countdown_enabled"), default_osc["countdown_enabled"]
        ),
        "countdown_template": _as_str(
            osc.get("countdown_template"), default_osc["countdown_template"]
        ),
        "go_text": _as_str(osc.get("go_text"), default_osc["go_text"]),
        "done_text": _as_str(osc.get("done_text"), default_osc["done_text"]),
    }

    server = cfg.get("server") if isinstance(cfg.get("server"), dict) else {}
    default_server = defaults["server"]
    validated["server"] = {
        "host": _as_str(server.get("host"), default_server["host"]),
        "port": _as_int(server.get("port"), default_server["port"], 1, 65535),
    }

    output = cfg.get("output") if isinstance(cfg.get("output"), dict) else {}
    default_output = defaults["output"]
    validated["output"] = {
        "copy_to_folder": _as_str(
            output.get("copy_to_folder"), default_output["copy_to_folder"]
        )
    }

    return validated


def merge_config(base: dict[str, Any], partial: dict[str, Any]) -> dict[str, Any]:
    """Deep merge a partial update into a base config and clamp values."""

    if not isinstance(base, dict):
        base = default_config()
    if not isinstance(partial, dict):
        partial = {}
    schema_base = _deep_merge(default_config(), base)
    return _validate(_deep_merge(schema_base, partial))


def load_config() -> dict[str, Any]:
    """Load config from disk or return defaults when the file is absent."""

    path = _config_path()
    if not path.exists():
        return default_config()
    try:
        with path.open("r", encoding="utf-8") as config_file:
            loaded = json.load(config_file)
    except (OSError, json.JSONDecodeError) as exc:
        LOGGER.warning("Could not load config from %s: %s", path, exc)
        return default_config()
    if not isinstance(loaded, dict):
        LOGGER.warning("Config file %s does not contain a JSON object", path)
        return default_config()
    return merge_config(default_config(), loaded)


def save_config(cfg: dict[str, Any]) -> dict[str, Any]:
    """Validate and save config, returning the saved value."""

    validated = merge_config(default_config(), cfg)
    path = _config_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as config_file:
            json.dump(validated, config_file, indent=2)
            config_file.write("\n")
    except OSError as exc:
        LOGGER.error("Could not save config to %s: %s", path, exc)
        raise
    return validated
