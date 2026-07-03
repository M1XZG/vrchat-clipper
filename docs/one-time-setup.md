# One-time VRChat and OBS setup

After [installing the clipper](install-windows-exe.md), configure VRChat, OBS, and
the OVR Toolkit wrist button once. With these in place the clipper handles the rest
each session. The only step you repeat is re-enabling the VRChat camera Spout feed,
which VRChat forgets between sessions.

## 1. Enable VRChat camera Stream mode and Spout2

VRChat's in-game camera Stream mode plus Spout2 output cannot be automated. VRChat
does not provide an API, OSC address, or hotkey for this setting.

Enable it once per VRChat session. After that, OBS can keep using a Spout2 source
bound to sender name `VRCSender1`, and clipping is fully automated for the rest of
the session.

In short:

1. Start VRChat.
2. Open the VRChat camera.
3. Enable Stream mode and Spout2 output.
4. Leave VRChat running. The Spout sender should remain available even if the camera
   UI is closed.

## 2. Set up OBS

The clipper captures VRChat's camera through an OBS Spout2 source and controls
recording over the OBS WebSocket. Both are configured once, in the
**[OBS setup guide](obs-setup.md)**: install the Off-World-Live Spout2 plugin, add a
`Spout2 Capture` source bound to `VRCSender1`, and enable the OBS WebSocket server
with a password you put in `config.json`.

## 3. Enable VRChat OSC

In VRChat, open **Action Menu > OSC > Enabled**.

vrchat-clipper sends countdown messages to UDP port `9000` at OSC address
`/chatbox/input` with arguments: message text, bypass keyboard, suppress sound
effect.

## 4. Install the OVR Toolkit Custom App

The wrist button lives in `vrchat_clipper/ovr-custom-app/`. Copy that folder into
`%OVRToolkitInstallDir%/LocalCustomApps/VRChatClipper/` and follow
[vrchat_clipper/ovr-custom-app/README.md](../vrchat_clipper/ovr-custom-app/README.md).

OVR Toolkit custom apps only load `http(s)://` URLs (not local `file://` paths), so
the button UI is served by the clipper server itself. The custom app's `entry.txt`
points at:

```text
http://127.0.0.1:8765/ovr
```

Start the clipper server first, then restart OVR Toolkit so it loads the tile.

## Next steps

- Tune clip length, buffers, OBS, and OSC in the
  [Configuration reference](configuration.md).
- Hitting a snag? See [Troubleshooting](troubleshooting.md).
