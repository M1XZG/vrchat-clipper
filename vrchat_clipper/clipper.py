"""Clip orchestration for countdown, OBS recording and optional copy."""

from __future__ import annotations

import asyncio
import logging
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from . import obs, osc

LOGGER = logging.getLogger(__name__)


@dataclass
class ClipperState:
    """Current clipper state exposed by the status API."""

    state: str = "idle"
    message: str = "Idle"
    countdown: int | None = None
    last_clip: str | None = None
    busy: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "message": self.message,
            "countdown": self.countdown,
            "last_clip": self.last_clip,
            "busy": self.busy,
        }


class Clipper:
    """Run one VRChat clip capture at a time."""

    def __init__(self, config_getter: Callable[[], dict[str, Any]] | None = None) -> None:
        self.config_getter = config_getter
        self.state = ClipperState()
        self._lock = asyncio.Lock()

    @property
    def busy(self) -> bool:
        return self.state.busy or self._lock.locked()

    async def _sleep_recording(self, seconds: float) -> None:
        end_time = time.monotonic() + max(0.0, seconds)
        while True:
            remaining = end_time - time.monotonic()
            if remaining <= 0:
                return
            self.state.message = f"Recording: {remaining:.1f}s remaining"
            await asyncio.sleep(min(1.0, remaining))

    def _copy_output(self, source_path: str | None, folder: str) -> str | None:
        if not source_path or not folder:
            return source_path
        source = Path(source_path)
        if not source.exists():
            LOGGER.warning("OBS output path does not exist: %s", source)
            return source_path
        try:
            destination_dir = Path(folder)
            destination_dir.mkdir(parents=True, exist_ok=True)
            destination = destination_dir / source.name
            shutil.copy2(source, destination)
            return str(destination)
        except Exception as exc:
            LOGGER.warning("Could not copy clip to %s: %s", folder, exc)
            return source_path

    async def run_clip(self, cfg: dict[str, Any]) -> None:
        """Run a full clip workflow safely as a fire and forget task."""

        if self._lock.locked():
            self.state.message = "already running"
            self.state.busy = False
            return

        async with self._lock:
            self.state.busy = True
            self.state.countdown = None
            client = None
            try:
                osc_cfg = cfg.get("osc", {})
                obs_cfg = cfg.get("obs", {})
                output_cfg = cfg.get("output", {})

                self.state.state = "counting"
                self.state.message = "Counting"
                countdown_s = int(cfg.get("countdown_s", 0))
                if osc_cfg.get("countdown_enabled") and countdown_s > 0:
                    await osc.run_countdown(
                        osc_cfg.get("host", "127.0.0.1"),
                        int(osc_cfg.get("port", 9000)),
                        countdown_s,
                        str(osc_cfg.get("countdown_template", "{n}")),
                        str(osc_cfg.get("go_text", "REC")),
                        self._on_countdown_tick,
                    )
                else:
                    self.state.message = "Countdown skipped"

                self.state.countdown = None
                self.state.state = "connecting"
                self.state.message = "Connecting to OBS"
                if obs_cfg.get("auto_launch") and not obs.is_obs_running():
                    obs.launch_obs(str(obs_cfg.get("obs_path", "")))
                    client = await asyncio.to_thread(
                        obs.wait_until_connectable,
                        obs_cfg.get("host", "127.0.0.1"),
                        int(obs_cfg.get("port", 4455)),
                        str(obs_cfg.get("password", "")),
                    )
                else:
                    client = await asyncio.to_thread(
                        obs.wait_until_connectable,
                        obs_cfg.get("host", "127.0.0.1"),
                        int(obs_cfg.get("port", 4455)),
                        str(obs_cfg.get("password", "")),
                        4,
                        0.5,
                    )

                if obs_cfg.get("switch_scene"):
                    await asyncio.to_thread(
                        obs.ensure_scene, client, str(obs_cfg.get("scene", ""))
                    )

                self.state.state = "recording"
                self.state.message = "Starting recording"
                await asyncio.to_thread(obs.start_record, client)
                record_seconds = (
                    float(cfg.get("intro_buffer_s", 0.0))
                    + float(cfg.get("clip_length_s", 0.0))
                    + float(cfg.get("tail_buffer_s", 0.0))
                )
                await self._sleep_recording(record_seconds)

                self.state.state = "saving"
                self.state.message = "Saving recording"
                output_path = await asyncio.to_thread(obs.stop_record, client)
                self.state.last_clip = output_path

                copied_path = await asyncio.to_thread(
                    self._copy_output,
                    output_path,
                    str(output_cfg.get("copy_to_folder", "")),
                )
                self.state.last_clip = copied_path
                self.state.message = "Clip saved" if copied_path else "Recording stopped"
                self.state.state = "idle"
            except Exception as exc:
                LOGGER.exception("Clip failed")
                self.state.state = "error"
                self.state.message = str(exc)
                await asyncio.sleep(1)
                self.state.state = "idle"
            finally:
                if client is not None:
                    try:
                        await asyncio.to_thread(client.disconnect)
                    except Exception as exc:
                        LOGGER.warning("Could not disconnect from OBS: %s", exc)
                try:
                    osc_cfg = cfg.get("osc", {})
                    osc.clear_chatbox(
                        osc_cfg.get("host", "127.0.0.1"),
                        int(osc_cfg.get("port", 9000)),
                        str(osc_cfg.get("done_text", "")),
                    )
                except Exception as exc:
                    LOGGER.warning("Could not send final OSC text: %s", exc)
                self.state.countdown = None
                self.state.busy = False

    def _on_countdown_tick(self, n: int) -> None:
        self.state.countdown = n
        self.state.message = f"Counting: {n}"
