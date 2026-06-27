"""Standalone VRChat OSC chatbox test.

Sends a few chatbox messages straight to VRChat over OSC, independently of the
clipper flow, so you can confirm OSC -> VRChat chatbox actually works.

Run it WHILE you are in VRChat (with OSC enabled):

    .venv\\Scripts\\python.exe tools\\osc_test.py

It reads host/port from config.json (default 127.0.0.1:9000). Watch the chatbox
bubble above your avatar. If nothing appears, the problem is VRChat-side OSC
reception (port, OSC not really enabled, an OSC router stealing 9000, firewall),
not the clipper code.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from pythonosc.udp_client import SimpleUDPClient

CONFIG = Path(__file__).resolve().parents[1] / "config.json"


def osc_settings() -> tuple[str, int]:
    host, port = "127.0.0.1", 9000
    if CONFIG.exists():
        try:
            osc = json.loads(CONFIG.read_text(encoding="utf-8")).get("osc", {})
            host = str(osc.get("host", host))
            port = int(osc.get("port", port))
        except Exception as exc:  # noqa: BLE001
            print(f"(could not read config.json, using defaults: {exc})")
    return host, port


def send(client: SimpleUDPClient, text: str) -> None:
    # /chatbox/input: [text, post-immediately=True, play-SFX=True]
    # SFX=True makes VRChat play the chatbox notification blip, so you can
    # confirm the message was received even if you can't see your own bubble.
    client.send_message("/chatbox/input", [text, True, True])
    print(f"  sent: {text!r}")


def main() -> None:
    host, port = osc_settings()
    print(f"Sending OSC chatbox messages to {host}:{port}")
    print("Make sure VRChat is focused with OSC enabled. Watch your chatbox bubble.\n")
    client = SimpleUDPClient(host, port)

    send(client, "VRChat Clipper OSC test")
    time.sleep(2)
    for n in range(5, 0, -1):
        send(client, str(n))
        time.sleep(1)
    send(client, "REC")
    time.sleep(2)
    send(client, "")  # clear
    print("\nDone. If you saw the countdown in VRChat, OSC works.")


if __name__ == "__main__":
    main()
