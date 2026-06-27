# VRChat Quick-Clip Tool - Research & Proposal

> A one-button way to record short (2–10s) VRChat clips on the spur of the moment:
> press a wrist button, get a countdown in-headset, and OBS auto-records the clip.

**Date:** 2026-06-27
**Status:** Idea / research complete - ready to build
**Verdict:** Very doable. ~80% already exists in an open-source repo; you build the countdown + timing glue.

---

## The goal

Make a short custom clip (waving at someone, pointing cutely, a happy-birthday message)
without the manual dance of opening the camera, enabling Spout, switching OBS, and hitting
record. Target flow:

1. Tap a button on the OVR Toolkit wrist watch.
2. The tool makes sure OBS is running and on the right scene.
3. A 5-second countdown appears in front of you in-game (via OSC).
4. At "1", OBS starts recording.
5. Recording runs for the configured clip length, then stops after a 1-second buffer.
   (e.g. a 5s clip = ~7s total: 1s intro + 5s clip + 1s tail.)

Clips are then ready to grab for social media.

---

## The one hard constraint (read this first)

**VRChat's Spout2 camera "Stream mode" cannot be automated.** There is no OSC address, no
config flag, no hotkey, and no API to enable Stream mode or the Spout toggle. It is a manual
step, confirmed against VRChat's official docs, wiki, and feedback boards.

**The mitigation:** once you enable it, it **persists for the whole VRChat session** and keeps
streaming even when the camera UI is closed. So it becomes a **one-time setup at launch**, not
a per-clip action. OBS keeps a Spout2 source bound to the sender name `VRCSender1` and
auto-reconnects whenever VRChat broadcasts.

- OBS needs the third-party **Off-World-Live `obs-spout2-plugin`** (a.k.a. win-spout). OBS has
  **no native Spout** support on Windows.
- Spout sender names are `VRCSender1` (main), `VRCSender2/3/4` (dolly multi-stream).
- Spout **resolution** is saved in `config.json` (`camera_spout_res_width`/`height`); the
  **enable toggle is not** saved and resets each launch.

**Alternative if camera angle doesn't matter:** OBS **Game Capture** needs zero setup but only
captures the jittery HMD desktop-mirror (your POV), not a clean placed camera angle. For
cute "wave at the camera" clips, the Spout camera is worth the one-time setup.

---

## Recommended architecture

```
Wrist button (OVR Toolkit)
      │  trigger
      ▼
Python clip controller   ◄── the only thing you build
      │
      ├─► OSC  /chatbox/input  → "5 .. 4 .. 3 .. 2 .. 1" shown above your head
      │
      └─► OBS WebSocket (v5)   → ensure scene + StartRecord/StopRecord
                                  start at "1", stop after timeout + 1s buffer
                                  → returns outputPath of the finished clip
```

### 1. Trigger - OVR Toolkit wrist watch (3 options)

OVR Toolkit (Steam App 1068820) has three real integration mechanisms:

| Option | Effort | How it works |
|---|---|---|
| **Macro → hotkey** (easiest) | Zero custom OVRT code | Wrist Macro fires a unique key combo (e.g. `Ctrl+Alt+F12`); Python `keyboard` lib (or AutoHotkey) catches it and runs the controller. |
| **Custom App** (cleanest UI) | Tiny HTML/JS | An HTML button in `LocalCustomApps/` does `fetch('http://127.0.0.1:8765/clip')` to your Python HTTP server. Gives visual feedback in VR (button can show "Recording…"). |
| **VRChat avatar menu** (no overlay) | Avatar setup | A toggle in VRChat's own action menu sends an OSC param; Python `python-osc` listens. The de-facto community pattern. |
| Module Plugin (.NET DLL) | Most work, fragile | Native wrist button calls `Process.Start()`. Overkill; breaks across OVRT updates. |

OVR Toolkit also exposes a WebSocket API (`ws://127.0.0.1:11450/api`) but it is **inbound only**
(send notifications to OVRT), so it can't trigger an outbound script on its own.

### 2. Countdown - VRChat OSC chatbox

Send to UDP port **9000** (VRChat receives on 9000, sends on 9001):

```
/chatbox/input  ["5", True, False]   # then "4", "3", "2", "1", one per second
```

- Arg 2 `True` = bypass the keyboard and display immediately.
- Arg 3 `False` = suppress the per-tick notification "ding".
- No avatar edits needed; works on any avatar; the bubble shows above your head (visible to
  you and to nearby people - could be a feature).
- Requires **OSC enabled** in VRChat (Action Menu → OSC → Enabled - one-time).
- Rate limit is ~1 message/sec (community-observed) - a 1-second countdown sits right at that
  ceiling, so don't go faster.
- Library: `attwad/python-osc` (`pip install python-osc`), recommended by VRChat itself.

If you want a guaranteed dead-centre, in-face countdown instead of the head bubble, an OVR
Toolkit / XSOverlay notification is plan B.

### 3. Record - OBS WebSocket v5 (port 4455)

obs-websocket v5 is **bundled with OBS 28+** (no install). Two designs:

| Design | Fit | Notes |
|---|---|---|
| **Start/Stop record** (recommended) | Matches your spec exactly | Countdown → `StartRecord` at "1" → wait `clip_length + 1s` → `StopRecord`. The stop response returns `outputPath` of the file. Full control of clip length. |
| **Replay Buffer** | Best for "save the last N seconds" | Buffer always running; button calls `SaveReplayBuffer` and grabs the past retroactively (zero latency, never miss the moment). But length is fixed in OBS settings, and a *pre-roll* countdown makes less sense. |

Because you specifically want a countdown **before** the action ("wave", "happy birthday"),
**start/stop record fits your described flow best.**

The controller can also:
- Detect OBS via the `obs64.exe` process; launch it if missing
  (`obs64.exe --minimize-to-tray`, set working dir to its `bin\64bit` folder).
- Wait for the websocket to become connectable (retry loop, ~2–5s after launch).
- `GetCurrentProgramScene` / `SetCurrentProgramScene` to switch to your VRChat scene first.

**Library:** `onyx-and-iris/obsws-python` (synchronous, simple - `cl.start_record()`,
`cl.stop_record()`, `resp.output_path`). Use `simpleobsws` only if you want a fully async daemon.

Key requests: `GetRecordStatus`, `StartRecord`, `StopRecord` (returns `outputPath`),
`GetCurrentProgramScene`, `SetCurrentProgramScene`. Default port **4455**.

---

## Prior art - build on this

**[`MissingNO123/OBS-Scripts-for-VRChat`](https://github.com/MissingNO123/OBS-Scripts-for-VRChat)**
(actively maintained) already does most of it:

- Maps VRChat avatar OSC params → OBS record / replay-buffer / scene-switch.
- Syncs OBS state **back** to the avatar (button can show recording state).
- Ships a **Modular Avatar wrist-panel prefab** - covers the in-VR input side.
- Runs *inside* OBS via `obspython`, so no external websocket needed for the basic version.

You reuse that and add ~30 lines for the chatbox countdown + the timed stop.

Other useful references:

| Project | Use |
|---|---|
| [`attwad/python-osc`](https://github.com/attwad/python-osc) | Send the OSC countdown |
| [`onyx-and-iris/obsws-python`](https://github.com/onyx-and-iris/obsws-python) | Drive OBS recording |
| [`VolcanicArts/VRCOSC`](https://github.com/VolcanicArts/VRCOSC) | Full VRChat OSC framework (chatbox module) |
| [`Off-World-Live/obs-spout2-plugin`](https://github.com/Off-World-Live/obs-spout2-plugin) | The OBS Spout2 source plugin |

---

## What you actually build

A small Python "clip controller" that:

1. Listens for the trigger (hotkey / HTTP / OSC).
2. Ensures OBS is running (launch if not) and on the right scene.
3. Runs the OSC countdown 5 → 1.
4. `StartRecord` at "1", waits `clip_length + 1s`, `StopRecord`.
5. Reads `outputPath`, optionally copies the clip to a "ready-to-post" folder.

Config: clip length, countdown length, scene name, output folder, OBS host/port/password.

---

## Honest gotchas

- **Spout enable is manual once per session** (unavoidable - no API exists).
- Chatbox rate limit ~1/sec; fine for a countdown, don't exceed it.
- The countdown bubble sits above your head - readable to you, not dead-centre.
- OBS needs the third-party Spout2 plugin installed once.
- OSC must be enabled in VRChat settings (one-time).

---

## Bottom line

Start/stop-record design + OVR Toolkit Macro→hotkey trigger (upgrade to a Custom App later) +
OSC chatbox countdown, built on `MissingNO123/OBS-Scripts-for-VRChat`. Realistically a weekend
project. The only step you can't automate is the one-time Spout camera enable at VRChat launch.

---

## Component reference (ports & names)

| Thing | Value |
|---|---|
| VRChat OSC receive port | 9000 (you send here) |
| VRChat OSC send port | 9001 (you listen here) |
| OBS WebSocket port | 4455 (v5, OBS 28+) |
| OVR Toolkit WebSocket | `ws://127.0.0.1:11450/api` (inbound only) |
| Spout sender name | `VRCSender1` |
| Chatbox OSC address | `/chatbox/input` (string, bool bypass, bool no-sfx) |
