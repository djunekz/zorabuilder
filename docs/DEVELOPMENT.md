# Development Guide

How to set up, run, debug and extend ZORA Builder.

## Prerequisites

- Python 3.10 or newer
- A C compiler (clang, cc or gcc) with the Python headers and zlib headers
- Git
- Optional: `ruff` and `shellcheck` for the same checks CI runs

```bash
git clone https://github.com/djunekz/zorabuilder.git
cd zorabuilder
python3 -m pip install -r requirements-dev.txt
```

The builder has **no runtime dependencies**. `requirements.txt` lists only `setuptools`, needed to install the package with pip; `requirements-dev.txt` adds `ruff`.

## Run from source

```bash
python3 zorabuilder.py --help
python3 zorabuilder.py examples/app.py /tmp/app && /tmp/app Ana --shout
python3 -m core --version
```

For an editable install with the `zorabuilder` and `zora` commands:

```bash
python3 -m pip install -e .
```

## Repository layout

```text
zorabuilder.py            entrypoint
core/                     the builder (see docs/ARCHITECTURE.md)
tests/                    unittest suite
examples/                 small programs used in docs and tests
install.sh, uninstall.sh  installer scripts
scripts/                  maintenance scripts (device check)
docs/                     documentation
.github/                  issue forms, PR template, workflows
pyproject.toml            packaging, ruff configuration
requirements*.txt         dependency files
```

## Everyday commands

| Task | Command |
| ---- | ------- |
| Run all tests | `python3 -m unittest discover -s tests -t . -v` |
| Run one test module | `python3 -m unittest tests.test_scanner -v` |
| Run one test | `python3 -m unittest tests.test_cli.MainTests.test_version -v` |
| Lint | `ruff check .` |
| Check shell scripts | `bash -n install.sh uninstall.sh scripts/termux-check.sh && shellcheck --severity=warning install.sh uninstall.sh scripts/termux-check.sh` |
| Check a real device | `./scripts/termux-check.sh` |
| Build a wheel | `python3 -m pip install build && python3 -m build` |

## Debugging

### Look at the generated C

```bash
python3 zorabuilder.py app.py app --keep-c
less app.c
```

Compile it by hand to see compiler output directly:

```bash
INC=$(python3 -c "import sysconfig; print(sysconfig.get_paths()['include'])")
LIB=$(python3 -c "import sysconfig; print(sysconfig.get_config_var('LIBDIR'))")
LD=$(python3 -c "import sysconfig; print(sysconfig.get_config_var('LDVERSION'))")
cc app.c -O1 -I"$INC" -L"$LIB" -Wl,-rpath,"$LIB" -lpython"$LD" -lz -o app_manual
```

### Inspect the payload

The payload is `base64(zlib(ZIP))`. To look inside a bundle from Python:

```python
import base64, io, zlib, zipfile
from core.scanner import collect_all_modules
from core.bundler import build_bundle_zip
from pathlib import Path

entry = Path("app.py")
data = build_bundle_zip(entry, collect_all_modules(entry))
print(zipfile.ZipFile(io.BytesIO(data)).namelist())
```

### Watch the loader at runtime

```bash
strace -f -e trace=openat,unlink ./app 2>&1 | grep zora_
ltrace ./app
```

Both are optional tools. You should see `zora_XXXXXX.zip` created and then unlinked.

### Scanner problems

`--verbose` prints modules that could not be resolved. To see what was found, call the scanner directly:

```python
from pathlib import Path
from core.scanner import collect_all_modules
print(collect_all_modules(Path("app.py"), verbose=True))
```

## Making changes

### Add a CLI option

1. `core/cli.py`: declare it in `build_arg_parser` (pick the right group), map it in `config_from_args`.
2. `core/config.py`: add the `BuildConfig` field with a default.
3. Use it in `run` or pass it to the module that needs it.
4. Tests: a parser test in `tests/test_cli.py`, plus an end-to-end test if it changes the binary.
5. Docs: `README.md` options table, `docs/USAGE.md`, `CHANGELOG.md`.

### Change the C loader

1. Edit `C_TEMPLATE` in `core/codegen.py`. Placeholders look like `__NAME__` and are replaced in `generate_c_stub`.
2. Keep it warning-free: `tests/test_codegen.py` compiles it with `-Wall -Wextra` and fails on any output.
3. Check every path that returns early: the temp file must still be removed.
4. Run the end-to-end tests, especially `SignalTests`.
5. Update `docs/ARCHITECTURE.md` if behavior changes.

### Change scanning or bundling

Keep `iter_package_files` as the single source of truth for which files of a package are bundled, so the scanner and the bundler never disagree.

## Conventions

- No comments and no docstrings; clear names, small functions, tests and `docs/` carry the explanations
- Standard library only
- Python 3.10 compatible syntax and APIs
- 120-column lines, four-space indents, LF endings
- User errors: `ui.die(...)`. Warnings: `ui.log(..., "warn")`.
- Never print to stdout from code that is not user-facing output
- Output text is English, one idea per line, starts with the fix when possible

## Environment quirks

- **Termux:** `sys.base_prefix` is `/data/data/com.termux/files/usr`; the loader uses it as Python's home and as the fallback for the temp directory.
- **Debian/Ubuntu:** headers need `python3-dev`; the shared library comes from `libpython3-dev`.
- **Virtualenvs:** the builder uses the interpreter that runs it for scanning, but the *base* prefix for the runtime home. Run the builder with the virtualenv's Python to make its packages visible.
- **CI:** GitHub's `setup-python` builds provide a shared `libpython`, which the end-to-end tests rely on.

## Getting help

Open an issue, or see [SUPPORT.md](../SUPPORT.md).
