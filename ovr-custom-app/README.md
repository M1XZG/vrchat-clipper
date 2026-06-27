# VRChat Clipper OVR Toolkit app

This is the in-headset wrist button. OVR Toolkit's custom-app browser only loads
**`http(s)://` URLs** (local `file://` paths are not supported), so the button UI is
served by the clipper server itself at `http://127.0.0.1:8765/ovr`. `entry.txt` points
there.

## Install

1. Copy this whole folder into `%OVRToolkitInstallDir%/LocalCustomApps/VRChatClipper/`.
2. Start the clipper server first (`run.bat`, or `python -m vrchat_clipper`) so
   `http://127.0.0.1:8765/ovr` is live.
3. Restart OVR Toolkit (it reads `entry.txt` at startup).
4. Open Edit Mode, find the VRChat Clipper tile, pin it to your wrist.

The button calls `http://127.0.0.1:8765/api/clip`; the page polls `/api/status` for
live feedback. Both match the default server config.

## Buttons

- **RECORD CLIP** — fixed-length clip with the OSC countdown (the timed workflow).
- **START** / **STOP** — free-form recording: START begins recording immediately (no
  countdown, no OSC) and it keeps going until you press STOP, for clips of any length.

Only one mode runs at a time; buttons disable themselves while busy.

## Pin it to your wrist

Once the tile loads (the red **RECORD CLIP** button):

1. Open OVR Toolkit's dashboard and spawn the **VRChat Clipper** window.
2. Enter **Edit Mode** on that window (grab it, or use its Edit/pencil icon).
3. Set **Attach To** → **Left** or **Right Controller** (the wrist you want — usually
   your non-dominant hand, so you press it with the other hand).
4. Use the **position / rotation / scale** controls to seat it on the inner wrist,
   shrunk down like a watch face.
5. If available, enable **"Show on look" / "Watch"** so it only appears when you glance
   at your wrist. Then **lock / pin** it and exit Edit Mode.

Tips: keep it big enough to press reliably; if it lands on the wrong hand, flip the
Attach To controller; the server must be running each session or the button shows
"Offline". Exact labels vary slightly by OVR Toolkit version.

## Files

- `entry.txt` — the URL OVR Toolkit loads: `http://127.0.0.1:8765/ovr`. If you change
  the server host/port, update this to match.
- `icon.png` — the tile icon.
- `index.html` — the button UI. The server serves this file from the repo at `/ovr`.
- `permissions.json` — OVR Toolkit permissions. Not required for an `http://` entry,
  but harmless to leave in place.

## Troubleshooting

- **"File could not be accessed / file not found"** — `entry.txt` is pointing at a
  local file. It must be the `http://127.0.0.1:8765/ovr` URL; `file://` will not work.
- **"Offline / cannot reach 127.0.0.1:8765"** — the clipper server isn't running, or is
  on a different port. Start it, then reload the tile.
- Always **restart OVR Toolkit** after editing `entry.txt` (read once at startup).
