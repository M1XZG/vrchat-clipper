"""Command line entry point for python -m vrchat_clipper."""

from __future__ import annotations

import argparse

from .config import load_config
from .server import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the VRChat Clipper backend")
    parser.parse_args()
    cfg = load_config()
    server_cfg = cfg["server"]
    print(f"Serving VRChat Clipper at http://{server_cfg['host']}:{server_cfg['port']}")
    run()


if __name__ == "__main__":
    main()
