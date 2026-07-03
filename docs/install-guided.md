# Guided install (`install` command)

The Windows executable can set itself up in one step. Instead of placing the exe by
hand, creating a config, and copying the wrist-button files into OVR Toolkit, run the
built-in installer and it does all of that for you.

This is the quickest path if you just want everything wired up. If you would rather
place files yourself, the [manual Windows executable guide](install-windows-exe.md)
and the [Python guide](install-python.md) still work exactly as before.

## What it does

Running `install`:

1. Copies `vrchat-clipper.exe` into an install folder — by default
   `%LOCALAPPDATA%\Programs\VRChatClipper`, which needs no administrator rights.
2. Writes a default `config.json` next to it (only if one isn't there already).
3. Finds OVR Toolkit through your Steam libraries and copies the wrist-button app
   into its `LocalCustomApps` folder, with `entry.txt` pointed at your server.
4. Registers the recorder with SteamVR for auto-launch.
5. Offers to add a Start Menu shortcut.

## Run it

Download `vrchat-clipper.exe` from the
[Releases page](https://github.com/M1XZG/vrchat-clipper/releases), open a terminal in
the download folder, and run:

```powershell
.\vrchat-clipper.exe install
```

It walks you through the install folder, confirms the detected OVR Toolkit location,
and asks about the shortcut. Accept the defaults and you're done. Then finish the
[one-time VRChat and OBS setup](one-time-setup.md), which the installer can't do for
you (they're settings inside VRChat and OBS).

### Unattended install

To install without prompts — handy for scripts or a future GUI wrapper — use
`--silent`, which takes the defaults for everything:

```powershell
.\vrchat-clipper.exe install --silent
```

### Options

| Flag | Effect |
|---|---|
| `--dir <path>` | Install folder (default `%LOCALAPPDATA%\Programs\VRChatClipper`). |
| `--ovrt-dir <path>` | OVR Toolkit `LocalCustomApps` folder, skipping auto-detection. |
| `--skip-ovr` | Don't install the OVR Toolkit wrist button. |
| `--no-vr` | Don't register with SteamVR. |
| `--no-shortcut` | Don't create a Start Menu shortcut. |
| `--silent` | Run without prompts, using defaults. |

## If OVR Toolkit isn't found

The installer locates OVR Toolkit by reading your Steam library folders and the app's
Steam manifest (AppID `1068820`). If Steam is in an unusual place, or OVR Toolkit
uses a `LocalCustomApps` layout it doesn't recognise, it prints the folder you need
and lets you paste the correct path — or pass `--ovrt-dir` directly. As a last resort
it tells you which bundled folder to copy into `LocalCustomApps` yourself.

## Uninstall

```powershell
.\vrchat-clipper.exe uninstall
```

This removes the SteamVR auto-launch registration and deletes the wrist-button folder
from OVR Toolkit. Add `--purge` to also delete `config.json` and the install folder:

```powershell
.\vrchat-clipper.exe uninstall --purge
```

If the executable is running from the install folder it can't delete itself; the
command tells you to remove that folder manually after it exits.

## Next steps

- [One-time VRChat and OBS setup](one-time-setup.md) — the VRChat camera, OBS, and OSC
  settings the installer can't automate.
- [Configuration reference](configuration.md) — every `config.json` field.
- [Troubleshooting](troubleshooting.md) — if something doesn't work.
