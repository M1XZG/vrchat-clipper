# OBS setup

vrchat-clipper does two things with OBS: it captures VRChat's camera feed through a
Spout2 source, and it starts and stops recording over the OBS WebSocket. This page
covers both. You do it once, then the clipper drives OBS on its own.

You only need to read this after you've installed the clipper itself — see the
[Windows executable guide](install-windows-exe.md) or the
[Python install guide](install-python.md).

## Prerequisite: VRChat is broadcasting its camera

OBS can only capture VRChat's camera once VRChat is sending it out over Spout. Turn
on the VRChat camera's Stream mode and Spout2 output first — that's a VRChat-side
setting covered in
[One-time VRChat and OBS setup, step 1](one-time-setup.md#1-enable-vrchat-camera-stream-mode-and-spout2).
It has to be re-enabled once per VRChat session; everything below you set up only
once.

## 1. Install the Spout2 plugin

OBS has no built-in Spout support on Windows, so install the
[Off-World-Live obs-spout2-plugin](https://github.com/Off-World-Live/obs-spout2-plugin)
(also known as win-spout). Download the installer from its releases, run it while OBS
is closed, then reopen OBS. You should now see **Spout2 Capture** in the list of
sources.

## 2. Add the Spout2 Capture source

1. In OBS, create or open a scene named `VRChat`. This name is the default the
   clipper switches to; if you use a different name, set `obs.scene` in `config.json`
   to match.
2. In that scene, add a **Spout2 Capture** source.
3. Set the source's **Spout Sender** to `VRCSender1`. VRChat's main camera always
   broadcasts under this name (the dolly multi-stream cameras use `VRCSender2`
   through `VRCSender4`).
4. With VRChat running and its camera in Stream mode, confirm the VRChat camera view
   now appears in the OBS preview.

If the source stays black, VRChat isn't broadcasting — re-check the
[VRChat camera step](one-time-setup.md#1-enable-vrchat-camera-stream-mode-and-spout2) and that the sender
name is exactly `VRCSender1`.

## 3. Enable the OBS WebSocket

The clipper controls recording through obs-websocket v5, which ships inside OBS 28
and newer, so there's nothing extra to install.

1. In OBS, open **Tools → WebSocket Server Settings**.
2. Tick **Enable WebSocket server**.
3. Leave the port at `4455`. If you change it, set `obs.port` in `config.json` to
   the same value.
4. Set a **password**, then click **Apply**.
5. Copy that password into your local `config.json` under `obs.password`.

Keep `config.json` out of version control — it holds your OBS password, and the repo
already gitignores it. The matching settings are documented in the
[Configuration reference](configuration.md).

## Check it works

With VRChat running (camera in Stream mode) and OBS open:

- The `VRChat` scene shows the live camera feed.
- The clipper can reach OBS. Fire a test clip from the tray icon or the Web UI, or
  from the same PC run:

  ```powershell
  curl -X POST http://127.0.0.1:8765/api/clip
  ```

  OBS should switch to the `VRChat` scene and record a short file.

If OBS won't connect or records a blank source, see
[Troubleshooting](troubleshooting.md).
