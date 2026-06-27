"""OSC chatbox helpers for VRChat countdown messages."""

from __future__ import annotations

import asyncio
import inspect
import logging
from typing import Any, Callable

try:
    from pythonosc.udp_client import SimpleUDPClient
except ImportError:  # pragma: no cover
    SimpleUDPClient = None  # type: ignore[assignment]

LOGGER = logging.getLogger(__name__)


def _client(host: str, port: int) -> Any:
    if SimpleUDPClient is None:
        raise RuntimeError("python-osc is not installed")
    return SimpleUDPClient(host, port)


def send_chatbox(client: Any, text: str) -> None:
    """Send text to the VRChat chatbox input endpoint."""

    client.send_message("/chatbox/input", [text, True, False])


async def _call_tick(on_tick: Callable[[int], Any] | None, n: int) -> None:
    if on_tick is None:
        return
    try:
        result = on_tick(n)
        if inspect.isawaitable(result):
            await result
    except Exception as exc:  # pragma: no cover
        LOGGER.warning("Countdown tick callback failed: %s", exc)


async def run_countdown(
    host: str,
    port: int,
    countdown_s: int,
    template: str,
    go_text: str,
    on_tick: Callable[[int], Any] | None = None,
) -> None:
    """Run a VRChat OSC countdown, ignoring UDP send failures."""

    try:
        client = _client(host, port)
    except Exception as exc:
        LOGGER.warning("Could not create OSC client: %s", exc)
        return

    for n in range(int(countdown_s), 0, -1):
        await _call_tick(on_tick, n)
        try:
            text = template.format(n=n)
        except Exception:
            text = str(n)
        try:
            send_chatbox(client, text)
        except Exception as exc:
            LOGGER.warning("Could not send OSC countdown tick: %s", exc)
        await asyncio.sleep(1)

    if go_text:
        try:
            send_chatbox(client, go_text)
        except Exception as exc:
            LOGGER.warning("Could not send OSC go text: %s", exc)


def clear_chatbox(host: str, port: int, text: str) -> None:
    """Send the final chatbox value, which may be an empty string."""

    try:
        client = _client(host, port)
        send_chatbox(client, text)
    except Exception as exc:
        LOGGER.warning("Could not clear OSC chatbox: %s", exc)


class OscCountdown:
    """Small object wrapper for OSC countdown settings."""

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

    async def run(
        self,
        countdown_s: int,
        template: str,
        go_text: str,
        on_tick: Callable[[int], Any] | None = None,
    ) -> None:
        await run_countdown(
            self.host, self.port, countdown_s, template, go_text, on_tick
        )

    def clear(self, text: str) -> None:
        clear_chatbox(self.host, self.port, text)
