# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the single-file VRChat Clipper executable.

Build:

    pyinstaller vrchat-clipper.spec

Produces ``dist/vrchat-clipper`` (Linux/macOS) or ``dist/vrchat-clipper.exe``
(Windows). The same spec is used on the GitHub Actions Windows runner to produce
the shippable ``.exe``.

The web UI in ``web/`` is embedded as data and resolved at runtime through
``vrchat_clipper.paths.resource_dir`` (which reads ``sys._MEIPASS``). The user's
``config.json`` is intentionally NOT bundled; it lives next to the executable.
"""

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
)

block_cipher = None

# uvicorn imports its loop/protocol implementations lazily, so PyInstaller's
# static analysis misses them. Pull the whole package in explicitly.
hidden_imports = (
    collect_submodules("uvicorn")
    + [
        "websockets",
        "websockets.legacy",
        "httptools",
        "anyio",
        "anyio._backends._asyncio",
    ]
)

# Bundle the web UI and the OVR Toolkit wrist-button app (both now inside the
# package). Paths are relative to this spec file at build time; they are placed
# at <bundle>/web and <bundle>/ovr-custom-app to match paths.web_dir() and
# paths.ovr_dir().
datas = [
    ("vrchat_clipper/web", "web"),
    ("vrchat_clipper/ovr-custom-app", "ovr-custom-app"),
]

# openvr ships a native library (openvr_api.dll / .so / .dylib) plus data files
# that PyInstaller does not pick up automatically. Collect them so SteamVR
# registration works from the frozen build. Best-effort: if openvr is not
# installed at build time, skip it rather than failing the build.
binaries = []
try:
    binaries += collect_dynamic_libs("openvr")
    datas += collect_data_files("openvr")
except Exception:
    pass

a = Analysis(
    ["app_main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="vrchat-clipper",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="vrchat_clipper/web/icon.png",
)
