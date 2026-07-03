# Troubleshooting

## The Web UI is unreachable

- Confirm the server is running (from source, `python -m vrchat_clipper`; the exe
  runs it automatically).
- Open <http://127.0.0.1:8765/> on the same PC.
- If you changed `server.port`, use the new port.
- Check whether another app is already using the port.

## The OVR Toolkit tile shows "file cannot be accessed" / "file not found"

- OVR Toolkit only loads `http(s)://` URLs. `entry.txt` must contain
  `http://127.0.0.1:8765/ovr`, **not** a local file name or `file://` path.
- The clipper server must be running so that URL is live — open
  <http://127.0.0.1:8765/ovr> in a browser to confirm you see the button.
- Restart OVR Toolkit after editing `entry.txt` (it is read once at startup).

## The OVR Toolkit button does nothing

- Confirm the Custom App page loads at <http://127.0.0.1:8765/ovr>.
- Test the endpoints from the same PC:

```powershell
curl -X POST http://127.0.0.1:8765/api/clip            # timed clip
curl -X POST http://127.0.0.1:8765/api/record/start    # begin free recording
curl -X POST http://127.0.0.1:8765/api/record/stop     # end free recording
```

## OBS does not connect

- Use OBS Studio 28 or newer.
- Enable **Tools > WebSocket Server Settings**.
- Check `obs.host`, `obs.port`, and `obs.password` in `config.json`.
- If `obs.auto_launch` is enabled, check `obs.obs_path` points to `obs64.exe`.
- Start OBS manually once to confirm the scene and WebSocket settings.

See the [OBS setup guide](obs-setup.md) for the full configuration.

## OBS records the wrong view or a blank source

- Install the Off-World-Live obs-spout2-plugin.
- In VRChat, enable camera Stream mode and Spout2 output once for the session.
- In OBS, set the Spout2 Capture source to `VRCSender1`.
- Confirm your OBS scene name matches `obs.scene`.

## The countdown does not appear in VRChat

- Enable VRChat OSC in **Action Menu > OSC > Enabled**.
- Keep `osc.host` as `127.0.0.1` and `osc.port` as `9000` for a local VRChat client.
- Do not set countdown messages faster than once per second.
- Check that `osc.countdown_enabled` is `true`.

## Clips are longer than expected

This is normal if buffers are enabled. Total recorded time is approximately:

```text
intro_buffer_s + clip_length_s + tail_buffer_s
```

The countdown is not part of the recorded duration. See the
[timing model](how-it-works.md#timing-model).

## The recorder doesn't close when SteamVR exits

The exe watches SteamVR and quits when it shuts down. If it lingers, it was probably
started manually rather than launched by SteamVR (the watcher only attaches when it
can reach the running runtime at startup). Let SteamVR launch it, or quit it from the
tray icon.

## The guided installer can't find OVR Toolkit

Pass the folder directly, for example:

```powershell
.\vrchat-clipper.exe install --ovrt-dir "D:\SteamLibrary\steamapps\common\OVR Toolkit\LocalCustomApps"
```

See the [guided install guide](install-guided.md) for details.
