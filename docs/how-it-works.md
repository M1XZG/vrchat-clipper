# How it works

vrchat-clipper is a small local server. The OVR Toolkit wrist buttons send it HTTP
requests, and it drives VRChat (over OSC) and OBS (over the WebSocket) in response.

```text
OVR Toolkit wrist buttons ─► Python FastAPI server (python -m vrchat_clipper)

  RECORD CLIP   POST /api/clip          ─► timed clip
                                            ├─ VRChat OSC /chatbox/input: 5, 4, 3, 2, 1, REC
                                            └─ OBS WebSocket v5: record (intro+clip+tail), stop

  START / STOP  POST /api/record/start  ─► free recording (any length, no OSC)
                POST /api/record/stop       └─ OBS WebSocket v5: start … stop on demand

  Both paths optionally switch the OBS scene and copy the finished clip to an output folder.
```

For the full research and design background, see [DESIGN.md](DESIGN.md).

## Timing model

The countdown happens before recording starts. With the default settings, you see a
5 second countdown, then OBS records:

```text
intro buffer       clip length             tail buffer
1 second      +    5 seconds       +       1 second     = about 7 seconds recorded
```

This gives you a small margin at both ends, which is useful when trimming for social
media. Increase `clip_length_s` for longer actions, or adjust the buffers if you want
tighter files. The countdown itself is not part of the recorded duration.

Free recording (START / STOP) ignores these settings entirely — it records from the
moment you press START until you press STOP, with no countdown or buffers.

## Timed clip — RECORD CLIP

1. The OVR Toolkit Custom App sends `POST /api/clip` to the local FastAPI server.
2. The server loads `config.json` and prevents overlapping clip jobs.
3. If enabled, the server makes sure OBS is running and switches to the configured
   scene.
4. The server sends the countdown to VRChat over OSC.
5. OBS starts recording at the end of the countdown.
6. The server waits for `intro_buffer_s + clip_length_s + tail_buffer_s`.
7. OBS stops recording and returns the output path.
8. If configured, the server copies the finished clip to `output.copy_to_folder`.

## Free recording — START / STOP

1. The Custom App sends `POST /api/record/start`. The server makes sure OBS is
   running, switches scene if configured, and starts recording **immediately — no
   countdown and no OSC output**.
2. Recording continues for **any length** until you press STOP.
3. `POST /api/record/stop` stops OBS, returns the output path, and copies the clip to
   `output.copy_to_folder` if configured.

Only one mode runs at a time; the server's busy guard blocks overlaps, and the wrist
buttons disable themselves while a job is running.

## Related

- [Configuration reference](configuration.md) — the settings referenced above.
- [Troubleshooting](troubleshooting.md) — when a step doesn't behave as expected.
