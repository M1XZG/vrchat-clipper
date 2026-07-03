# Configuration reference

vrchat-clipper reads its settings from `config.json`. The guided installer and the
Web UI both create this file for you; you can also copy `config.example.json` to
`config.json` and edit it by hand. Keep the live file out of version control — it may
hold your OBS password, and the repo already gitignores it.

The easiest way to change settings is the Web UI at <http://127.0.0.1:8765/>, which
writes the same file.

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

## Where the file lives

- **Windows executable / guided install:** next to `vrchat-clipper.exe`.
- **Python package / source:** the folder you run the command from.
- Override the location with the `VRCHAT_CLIPPER_CONFIG` environment variable.

## Related

- [How it works](how-it-works.md) — how the timing values combine into a recording.
- [Troubleshooting](troubleshooting.md) — when a setting doesn't behave as expected.
