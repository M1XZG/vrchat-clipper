# Contributing to vrchat-clipper

Thanks for wanting to help. This is a small community VR tool, and contributions are
welcome — a bug fix, a new feature, better docs, or just a good bug report all count.

## Ways to help

- **Report a bug or suggest a feature** using the
  [issue templates](https://github.com/M1XZG/vrchat-clipper/issues/new/choose).
- **Improve the documentation** in `docs/` or the README.
- **Send a code change** as a pull request.

## Before you start

For anything more than a small fix, please open an issue first so we can agree on the
approach before you spend time on it. It saves everyone effort. Have a quick look
through existing issues and pull requests too, so we don't duplicate work.

## Development setup

You need Python 3.10 or newer. Work from a fork:

```sh
git clone https://github.com/<your-username>/vrchat-clipper.git
cd vrchat-clipper
python -m venv .venv
.venv/bin/pip install -r requirements.txt
python -m vrchat_clipper
```

On Windows you can double-click `run.bat`; on Linux or macOS use `./run.sh`. The
[Python install guide](docs/install-python.md) has more detail, including how to build
the executable.

## Making a change

`main` is protected, so changes land through reviewed pull requests rather than direct
pushes. The flow is the usual fork-and-PR:

1. Fork the repository and create a branch off `main`: `git checkout -b my-change`.
2. Make your change. Keep it focused — one topic per pull request is much easier to
   review than a grab-bag.
3. Match the surrounding style. The code uses type hints and small, documented
   functions; follow what's already there.
4. Check the app still starts with `python -m vrchat_clipper`. If you touched the
   packaging or the app itself and you're on Windows, building the exe is a good extra
   check (see the Python install guide).
5. Push to your fork and open a pull request against `main`, filling in the template.

## Commit messages

Write a short summary line in the imperative ("Fix /ovr 404 in the frozen exe"), and
use the body to explain the why when it isn't obvious from the change itself.

## Please don't commit

- `config.json` (it may hold your OBS password — it's gitignored for a reason).
- Build artefacts (`dist/`, `build/`, `*.egg-info/`) or virtual environments.
- Anything with secrets, tokens, or personal paths.

## Licence

By contributing, you agree that your work is licensed under the project's
[MIT licence](LICENSE).

## Code of conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). By taking part
you agree to abide by it.

That's it. Be kind, keep it reasonable, and thanks for pitching in.
