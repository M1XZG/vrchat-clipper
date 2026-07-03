# Install with the Windows executable

This guide sets the single `.exe` up by hand — you place the file, create the config,
and copy the wrist button into OVR Toolkit yourself. It's the most transparent path
if you like to know where everything goes.

> Want it done for you? The [guided install](install-guided.md) runs
> `vrchat-clipper.exe install` and handles all of that in one step. Prefer `pip` or a
> source checkout? See the [Python install guide](install-python.md). Every route
> gives you the same app.

## Before you start

The clipper drives other apps, so you still need these installed regardless of how
you install the clipper itself:

- A Windows PC running **SteamVR**.
- **VRChat**, with OSC enabled.
- **OBS Studio 28 or newer** (this version bundles obs-websocket v5).
- **OVR Toolkit**, which draws the wrist button in VR.
- The [Off-World-Live obs-spout2-plugin](https://github.com/Off-World-Live/obs-spout2-plugin),
  because OBS has no built-in Spout support on Windows.

You configure those once after installing — see
[One-time VRChat and OBS setup](one-time-setup.md).

## Step 1 — Download the executable

1. Open the [GitHub Releases page](https://github.com/M1XZG/vrchat-clipper/releases).
2. Download `vrchat-clipper.exe` from the latest release.
3. Move it into a folder you'll keep, for example `Documents\VRChatClipper\`.

The app writes its settings file, `config.json`, into that same folder, so give it a
home rather than leaving it in `Downloads`.

## Step 2 — First run

Double-click `vrchat-clipper.exe`. On the first launch it:

- starts the local server on <http://127.0.0.1:8765/>,
- adds a **system-tray icon** (bottom-right of the taskbar), and
- registers itself with SteamVR for auto-launch, if SteamVR is installed.

Right-click the tray icon to open the Web UI, fire a test clip, or quit.

Windows SmartScreen may warn about an unsigned app the first time. Choose
**More info → Run anyway** to continue.

## Step 3 — Configure it

Open <http://127.0.0.1:8765/> in any browser on the same PC. Set your clip length,
OBS connection details, OSC options, and an optional folder to copy finished clips
into. Saving writes `config.json` next to the executable, in plain readable JSON you
can also hand-edit later.

Every setting is explained in the
[Configuration reference](configuration.md).

## Step 4 — Let SteamVR launch it

Because the exe registered itself on first run, SteamVR starts the clipper for you
from then on. You can see and toggle it under **SteamVR → Settings → Startup /
Shutdown → Manage Add-Ons**, where it appears as **VRChat Clipper**:

![VRChat Clipper listed under SteamVR startup add-ons, toggled On](images/steamvr-startup-addons.png)

Leave it **On** and the server is running any time you're in VR. It also shuts down
automatically when you exit SteamVR, so it won't linger in the background. To stop it
launching at all, switch it **Off** here, or run the exe once with `--unregister-vr`.

## Step 5 — Add the wrist button in OVR Toolkit

The in-VR button is an OVR Toolkit custom app. Copy the
[`vrchat_clipper/ovr-custom-app/`](../vrchat_clipper/ovr-custom-app/) folder into
OVR Toolkit's `LocalCustomApps` folder and follow
[its README](../vrchat_clipper/ovr-custom-app/README.md). The full walk-through,
including pinning the tile to your wrist, is in
[Install the OVR Toolkit Custom App](one-time-setup.md#4-install-the-ovr-toolkit-custom-app).

Once it's pinned, glancing at your wrist in VRChat shows the panel:

![The VRChat Clipper wrist panel in-game, showing RECORD CLIP, START, STOP, and a Ready status](images/wrist-button-ingame.png)

- **RECORD CLIP** runs the timed clip with the in-headset countdown.
- **START** and **STOP** capture a free-form clip of any length.
- The status line underneath shows what the tool is doing (`Ready`, `Clip saved`,
  and so on).

## Step 6 — One-time VRChat and OBS setup

The last pieces live inside VRChat and OBS and can't be bundled into the exe. Do
these once and clipping is automatic after that:
[One-time VRChat and OBS setup](one-time-setup.md).

## Command-line flags

You rarely need these, but the exe accepts them if you want to change how it starts:

| Flag | Effect |
|---|---|
| `--no-tray` | Run a plain foreground server with no tray icon. |
| `--tray` | Force the system-tray icon (the default for the exe). |
| `--register-vr` | Register with SteamVR for auto-launch, then exit. |
| `--unregister-vr` | Remove the SteamVR auto-launch registration, then exit. |
| `--no-vr-register` | Start normally, but leave SteamVR registration untouched. |

Point the app at a different settings file with the `VRCHAT_CLIPPER_CONFIG`
environment variable if you don't want `config.json` beside the exe.

## If something isn't working

Common problems and fixes are in the
[Troubleshooting section](troubleshooting.md) — the Web UI being
unreachable, the wrist tile not loading, OBS not connecting, and the countdown not
showing up.
