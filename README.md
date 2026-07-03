# vrchat-clipper

A small open-source tool for recording short VRChat clips on demand from a VR wrist button.

vrchat-clipper is built for quick 2 to 10 second social media clips: wave at a friend, deliver a birthday message, capture a small joke, then get a neat recording from OBS without taking off the headset or reaching for the keyboard.

## Features

- VR wrist-button trigger through an OVR Toolkit Custom App.
- Three wrist buttons: **RECORD CLIP** (timed clip with countdown), plus **START** /
  **STOP** for free-form recording of any length.
- Local FastAPI server with a configuration Web UI at <http://127.0.0.1:8765/>.
- `POST /api/clip` (timed clip) and `POST /api/record/start` · `POST /api/record/stop`
  (free recording) endpoints for simple local integrations.
- In-game countdown through VRChat OSC chatbox messages (timed clips only; free
  recording sends no OSC).
- OBS Studio recording control through obs-websocket v5.
- Optional OBS auto-launch and scene switching.
- Configurable clip length, intro buffer, tail buffer, countdown text, OBS settings, OSC settings, and output copy folder.
- Sensible defaults: a 5 second clip records about 7 seconds total, with 1 second before and after the main clip.

## Architecture

```text
OVR Toolkit wrist buttons ─► Python FastAPI server (python -m vrchat_clipper)

  RECORD CLIP   POST /api/clip          ─► timed clip
                                            ├─ VRChat OSC /chatbox/input: 5, 4, 3, 2, 1, REC
                                            └─ OBS WebSocket v5: record (intro+clip+tail), stop

  START / STOP  POST /api/record/start  ─► free recording (any length, no OSC)
                POST /api/record/stop       └─ OBS WebSocket v5: start … stop on demand

  Both paths optionally switch the OBS scene and copy the finished clip to an output folder.
```

For the full research and design background, see [docs/DESIGN.md](docs/DESIGN.md).

## Requirements

These are needed no matter how you install the clipper, because they are the
apps it drives:

- A **Windows PC** running **SteamVR**.
- **VRChat**, with OSC enabled.
- **OBS Studio 28 or newer** (includes obs-websocket v5).
- **OVR Toolkit** (for the wrist button).
- The [Off-World-Live obs-spout2-plugin](https://github.com/Off-World-Live/obs-spout2-plugin),
  required because OBS has no native Spout support on Windows.

The **Windows executable** needs nothing else. The **Python package** additionally
needs **Python 3.10 or newer**. Linux and macOS are fine for development, but the
intended runtime target is Windows with SteamVR.

## Installation

There are two ways to install, and they behave identically once running. Pick one:

- **[Option A — Windows executable](#option-a--windows-executable-easiest)** —
  no Python required, one file plus a config. Best for most users.
- **[Option B — Python package](#option-b--python-package)** — install with `pip`,
  or run from a source checkout. Best if you already use Python or want to modify
  the code.

After installing, open <http://127.0.0.1:8765/> to configure clip timing, OBS,
OSC, and an optional output folder, then do the shared
[One-time VRChat and OBS setup](#one-time-vrchat-and-obs-setup).

### Option A — Windows executable (easiest)

1. Download `vrchat-clipper.exe` from the project's
   [GitHub Releases](https://github.com/M1XZG/vrchat-clipper/releases), or build it
   yourself (see [Building the releases](#building-the-releases)).
2. Put it in a folder of your choice. Optionally copy `config.example.json` next
   to it as `config.json` (the app also creates one when you save settings).
3. Double-click `vrchat-clipper.exe`.

It starts the local server, shows a **system-tray icon**, and — on first run, if
SteamVR is present — registers itself with SteamVR for auto-launch. From the tray
icon you can open the Web UI, trigger a clip, or quit.

`config.json` lives **next to the executable** and stays plain, editable JSON.
You can point the app at a different file with the `VRCHAT_CLIPPER_CONFIG`
environment variable.

### Option B — Python package

Install the wheel from a release (or from a checkout) into any Python 3.10+
environment:

```powershell
py -3 -m venv .venv
.venv\Scripts\python -m pip install vrchat_clipper-<version>-py3-none-any.whl
# Optional: tray icon + SteamVR auto-launch support
.venv\Scripts\python -m pip install "vrchat-clipper[desktop] @ ."
```

This installs a `vrchat-clipper` command. Run it from the folder where you want
`config.json` to live:

```powershell
copy config.example.json config.json
vrchat-clipper
```

You can also run straight from a source checkout without installing:

```powershell
git clone https://github.com/M1XZG/vrchat-clipper.git
cd vrchat-clipper
py -3 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy config.example.json config.json
.venv\Scripts\python -m vrchat_clipper
```

On Windows you can double-click `run.bat`; on Linux or macOS dev machines, run
`./run.sh`.

Useful command-line flags (both the exe and the `vrchat-clipper` command accept
them):

| Flag | Effect |
|---|---|
| `--no-tray` | Run a plain foreground server with no tray icon. |
| `--tray` | Force the system-tray icon (default when running as the exe). |
| `--register-vr` | Register with SteamVR for auto-launch, then exit. |
| `--unregister-vr` | Remove the SteamVR auto-launch registration, then exit. |
| `--no-vr-register` | Start normally but do not touch SteamVR registration. |

> The tray icon and SteamVR registration need the optional `desktop` extras
> (`pystray`, `Pillow`, `openvr`). The Windows executable already bundles them; for
> the Python package install `vrchat-clipper[desktop]`. Without them the server
> still runs headless.

### What still needs separate setup

Neither install format can contain these, so they are installed once (see
[One-time VRChat and OBS setup](#one-time-vrchat-and-obs-setup)):

- The **OVR Toolkit wrist button** (`vrchat_clipper/ovr-custom-app/`) runs inside OVR Toolkit, so
  it is copied into OVR Toolkit's `LocalCustomApps` folder separately. See
  [vrchat_clipper/ovr-custom-app/README.md](vrchat_clipper/ovr-custom-app/README.md).
- **OBS Studio**, the **Off-World-Live obs-spout2-plugin**, and **VRChat's** camera
  Stream mode / Spout toggle.

### Launch with SteamVR

Once registered (automatically on first run of the exe, or with `--register-vr`),
the recorder appears under **SteamVR → Settings → Startup / Shutdown → Manage
Add-Ons** and starts whenever SteamVR starts. Toggle it there, or run
`--unregister-vr` to remove it.

## Building the releases

Both formats are built automatically by GitHub Actions when a version tag such as
`v0.2.0` is pushed (`.github/workflows/release.yml`), and attached to a GitHub
Release. To build them yourself:

**Windows executable** — [PyInstaller](https://pyinstaller.org/) produces a binary
for the platform it runs on, so a Windows `.exe` must be built on Windows:

```powershell
py -3 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt -r requirements-exe.txt
.venv\Scripts\pyinstaller --clean --noconfirm vrchat-clipper.spec
# -> dist\vrchat-clipper.exe
```

**Python wheel + sdist** — build on any platform:

```sh
python -m pip install --upgrade build
python -m build            # -> dist/*.whl and dist/*.tar.gz
```


## One-time VRChat and OBS setup

### 1. Enable VRChat camera Stream mode and Spout2

VRChat's in-game camera Stream mode plus Spout2 output cannot be automated. VRChat does not provide an API, OSC address, or hotkey for this setting.

Enable it once per VRChat session. After that, OBS can keep using a Spout2 source bound to sender name `VRCSender1`, and clipping is fully automated for the rest of the session.

In short:

1. Start VRChat.
2. Open the VRChat camera.
3. Enable Stream mode and Spout2 output.
4. Leave VRChat running. The Spout sender should remain available even if the camera UI is closed.

### 2. Install and configure OBS Spout2 capture

1. Install the Off-World-Live obs-spout2-plugin.
2. In OBS, create or open a scene named `VRChat`.
3. Add a Spout2 Capture source.
4. Set the source sender to `VRCSender1`.
5. Confirm that the VRChat camera feed appears in OBS.

### 3. Enable OBS WebSocket

OBS 28 and newer includes obs-websocket v5, no separate install is needed.

1. In OBS, open **Tools > WebSocket Server Settings**.
2. Enable the WebSocket server.
3. Keep the default port `4455`, unless you also change `obs.port` in `config.json`.
4. Set a password.
5. Put that password in your local `config.json`. Do not commit `config.json`.

### 4. Enable VRChat OSC

In VRChat, open **Action Menu > OSC > Enabled**.

vrchat-clipper sends countdown messages to UDP port `9000` at OSC address `/chatbox/input` with arguments: message text, bypass keyboard, suppress sound effect.

### 5. Install the OVR Toolkit Custom App

The wrist button lives in `vrchat_clipper/ovr-custom-app/`. Copy that folder into
`%OVRToolkitInstallDir%/LocalCustomApps/VRChatClipper/` and follow
[vrchat_clipper/ovr-custom-app/README.md](vrchat_clipper/ovr-custom-app/README.md).

OVR Toolkit custom apps only load `http(s)://` URLs (not local `file://` paths), so the
button UI is served by the clipper server itself. The custom app's `entry.txt` points at:

```text
http://127.0.0.1:8765/ovr
```

Start the clipper server first, then restart OVR Toolkit so it loads the tile.

## Configuration reference

Copy `config.example.json` to `config.json`, then edit `config.json`. The live file is ignored by Git because it may contain your OBS password.

| Field | Default | Meaning |
|---|---:|---|
| `clip_length_s` | `5.0` | Main action length in seconds. |
| `intro_buffer_s` | `1.0` | Extra recording time before the main clip window. |
| `tail_buffer_s` | `1.0` | Extra recording time after the main clip window. |
| `countdown_s` | `5` | Number of countdown seconds shown before recording starts. |
| `obs.host` | `127.0.0.1` | OBS WebSocket host. |
| `obs.port` | `4455` | OBS WebSocket port. |
| `obs.password` | empty | OBS WebSocket password. Store the real value only in `config.json`. |
| `obs.scene` | `VRChat` | OBS scene used for recording. |
| `obs.switch_scene` | `true` | Switch OBS to `obs.scene` before recording. |
| `obs.auto_launch` | `true` | Launch OBS if `obs64.exe` is not already running. |
| `obs.obs_path` | `C:\Program Files\obs-studio\bin\64bit\obs64.exe` | Path to the OBS executable used for auto-launch. |
| `osc.host` | `127.0.0.1` | VRChat OSC receive host. |
| `osc.port` | `9000` | VRChat OSC receive port. |
| `osc.countdown_enabled` | `true` | Send countdown and status messages to the VRChat chatbox. |
| `osc.countdown_template` | `{n}` | Countdown text template. `{n}` is replaced with the current number. |
| `osc.go_text` | `REC` | Text sent when recording starts. |
| `osc.done_text` | empty | Text sent after recording finishes. Leave empty to send nothing. |
| `server.host` | `127.0.0.1` | Local FastAPI bind host. Keep this loopback-only unless you know you need LAN access. |
| `server.port` | `8765` | Local FastAPI port for the Web UI and API. |
| `output.copy_to_folder` | empty | Optional folder to copy the finished clip into. Leave empty to keep OBS output only. |

## Timing model

The countdown happens before recording starts. With the default settings, you see a 5 second countdown, then OBS records:

```text
intro buffer       clip length             tail buffer
1 second      +    5 seconds       +       1 second     = about 7 seconds recorded
```

This gives you a small margin at both ends, which is useful when trimming for social media. Increase `clip_length_s` for longer actions, or adjust the buffers if you want tighter files.

Free recording (START / STOP) ignores these settings entirely — it records from the
moment you press START until you press STOP, with no countdown or buffers.

## How it works

### Timed clip — RECORD CLIP

1. The OVR Toolkit Custom App sends `POST /api/clip` to the local FastAPI server.
2. The server loads `config.json` and prevents overlapping clip jobs.
3. If enabled, the server makes sure OBS is running and switches to the configured scene.
4. The server sends the countdown to VRChat over OSC.
5. OBS starts recording at the end of the countdown.
6. The server waits for `intro_buffer_s + clip_length_s + tail_buffer_s`.
7. OBS stops recording and returns the output path.
8. If configured, the server copies the finished clip to `output.copy_to_folder`.

### Free recording — START / STOP

1. The Custom App sends `POST /api/record/start`. The server makes sure OBS is running,
   switches scene if configured, and starts recording **immediately — no countdown and
   no OSC output**.
2. Recording continues for **any length** until you press STOP.
3. `POST /api/record/stop` stops OBS, returns the output path, and copies the clip to
   `output.copy_to_folder` if configured.

Only one mode runs at a time; the server's busy guard blocks overlaps, and the wrist
buttons disable themselves while a job is running.

## Troubleshooting

### The Web UI is unreachable

- Confirm the server is running with `python -m vrchat_clipper`.
- Open <http://127.0.0.1:8765/> on the same PC.
- If you changed `server.port`, use the new port.
- Check whether another app is already using the port.

### The OVR Toolkit tile shows "file cannot be accessed" / "file not found"

- OVR Toolkit only loads `http(s)://` URLs. `entry.txt` must contain
  `http://127.0.0.1:8765/ovr`, **not** a local file name or `file://` path.
- The clipper server must be running so that URL is live — open
  <http://127.0.0.1:8765/ovr> in a browser to confirm you see the button.
- Restart OVR Toolkit after editing `entry.txt` (it is read once at startup).

### The OVR Toolkit button does nothing

- Confirm the Custom App page loads at <http://127.0.0.1:8765/ovr>.
- Test the endpoints from the same PC:

```powershell
curl -X POST http://127.0.0.1:8765/api/clip            # timed clip
curl -X POST http://127.0.0.1:8765/api/record/start    # begin free recording
curl -X POST http://127.0.0.1:8765/api/record/stop     # end free recording
```

### OBS does not connect

- Use OBS Studio 28 or newer.
- Enable **Tools > WebSocket Server Settings**.
- Check `obs.host`, `obs.port`, and `obs.password` in `config.json`.
- If `obs.auto_launch` is enabled, check `obs.obs_path` points to `obs64.exe`.
- Start OBS manually once to confirm the scene and WebSocket settings.

### OBS records the wrong view or a blank source

- Install the Off-World-Live obs-spout2-plugin.
- In VRChat, enable camera Stream mode and Spout2 output once for the session.
- In OBS, set the Spout2 Capture source to `VRCSender1`.
- Confirm your OBS scene name matches `obs.scene`.

### The countdown does not appear in VRChat

- Enable VRChat OSC in **Action Menu > OSC > Enabled**.
- Keep `osc.host` as `127.0.0.1` and `osc.port` as `9000` for a local VRChat client.
- Do not set countdown messages faster than once per second.
- Check that `osc.countdown_enabled` is `true`.

### Clips are longer than expected

This is normal if buffers are enabled. Total recorded time is approximately:

```text
intro_buffer_s + clip_length_s + tail_buffer_s
```

The countdown is not part of the recorded duration.

## Acknowledgements and prior art

- [MissingNO123/OBS-Scripts-for-VRChat](https://github.com/MissingNO123/OBS-Scripts-for-VRChat), prior art for VRChat OSC and OBS control.
- [python-osc](https://github.com/attwad/python-osc), used for OSC messages.
- [obsws-python](https://github.com/aatikturk/obsws-python), used for OBS WebSocket v5 control.
- [Off-World-Live obs-spout2-plugin](https://github.com/Off-World-Live/obs-spout2-plugin), used to capture VRChat Spout2 output in OBS.

## Licence

MIT, see [LICENSE](LICENSE).

## Disclaimer

vrchat-clipper is a community tool. It is not affiliated with, endorsed by, or sponsored by VRChat Inc., OBS Studio, OVR Toolkit, or Off-World-Live.
