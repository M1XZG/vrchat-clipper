"""PyInstaller entry point for the packaged VRChat Clipper executable.

Kept as a thin wrapper so the spec has a concrete script to analyse. All logic
lives in the package so ``python -m vrchat_clipper`` and the frozen exe share the
exact same code path.
"""

from vrchat_clipper.__main__ import main

if __name__ == "__main__":
    main()
