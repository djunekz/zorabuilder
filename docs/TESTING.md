# Testing

The test suite uses the standard library's `unittest`. There is nothing to install.

```bash
python3 -m unittest discover -s tests -t . -v
```

Run it from the repository root. `-t .` makes `core` and `tests` importable.

## What is tested

| File | Level | Covers |
| ---- | ----- | ------ |
| `tests/test_scanner.py` | unit | Import extraction, stdlib skipping, local modules, shadowing, `--extra`, namespace packages, folder filtering, `sys.path` restoration |
| `tests/test_bundler.py` | unit | ZIP contents, determinism, fixed timestamps, compression round trip |
| `tests/test_codegen.py` | unit + compile | Placeholder substitution, escaping, chunking, and that the generated C compiles with `-Wall -Wextra` and **no warnings** |
| `tests/test_cli.py` | unit + subprocess | Argument parsing, usage text, error output, validation, `--version`, banner and color switches |
| `tests/test_e2e.py` | end-to-end | Real builds and runs: argument pass-through, exit codes, temp file cleanup, signals, `--isolated`, `--no-bundle`, `--keep-c`, `--json-report`, `--cc`, `--static`, and the programs in `examples/` |
| `tests/helpers.py` | support | `TempDirTestCase`, `run_zora`, toolchain detection |

## Environment-dependent tests

Tests that compile C are skipped automatically, with a message, when a compiler or the Python/zlib headers are missing. A skipped run is **not** a full run: check the summary for `skipped=` and make sure the end-to-end tests ran at least once before you open a PR.

## Writing tests

- Subclass `TempDirTestCase`. It gives you `self.tmp` (a fresh directory removed afterwards), `self.write(path, content)`, and silences log output.
- Test behavior through public functions (`collect_all_modules`, `build_bundle_zip`, `main`) and through the real command line (`run_zora([...])`).
- For anything that touches the loader, build and run a binary; reading the C source is not enough.
- Redirect the loader's temp directory in end-to-end tests with `TMPDIR` so you can assert no `zora_*` file is left behind.
- Keep each test independent and fast. Prefer small scripts.
- A bug fix needs a test that fails before the fix.
- Follow the conventions: no comments or docstrings; name tests after the behavior (`test_output_same_as_input`).

Example:

```python
from core.scanner import collect_all_modules
from tests.helpers import TempDirTestCase


class ExampleTests(TempDirTestCase):
    def test_local_module_is_collected(self):
        entry = self.write("main.py", "import helper\n")
        self.write("helper.py", "X = 1\n")
        self.assertEqual(set(collect_all_modules(entry)), {"helper"})
```

## Continuous integration

`.github/workflows/ci.yml` runs on every push to `main` and every pull request:

| Job | What it does |
| --- | ------------ |
| Lint | `ruff check .` and byte-compilation |
| Shell scripts | `bash -n` and ShellCheck on all scripts, and an install, reinstall and uninstall smoke test |
| Tests | The full suite on Python 3.10, 3.11, 3.12 and 3.13, then the device check (`scripts/termux-check.sh`) |
| Package install | Builds the wheel, installs it into a clean virtualenv and runs `zorabuilder --version` |

Other workflows: CodeQL analysis, dependency review on pull requests, label automation, stale issue handling and the release pipeline. See [RELEASING.md](RELEASING.md).

## Device check (Termux and Linux)

CI runs on Linux x86-64. To verify a real device, run the device check from a checkout. It was written for Termux and works on any Linux:

```bash
pkg install python clang zlib git
git clone https://github.com/djunekz/zorabuilder.git
cd zorabuilder
./scripts/termux-check.sh
```

It runs, in order:

| Check | What it proves |
| ----- | -------------- |
| Environment | Python 3.10+, a compiler and `Python.h` are present |
| Unit and end-to-end tests | The whole suite passes on this device (skip with `--skip-tests`) |
| Install, installed version | `install.sh` works into a temporary prefix |
| Single-file and multi-module builds | Real binaries build and run |
| Argument pass-through | `-h` reaches the program, not Python |
| `--isolated` build | Isolated binaries run |
| Exit code | `sys.exit(3)` gives exit status 3 |
| Ctrl+C | `SIGINT` becomes `KeyboardInterrupt` and the program can handle it |
| Temp files | No `zora_*` files are left in the temp directory |
| Reinstall and uninstall | Installer is idempotent; uninstall keeps built binaries |

It also reports, without failing, whether binaries can run from shared storage (`/sdcard`). On Android they normally cannot, which is expected.

Exit status is 0 only when every check passes. Add `--keep` to keep the temporary work directory. When you report a device-specific problem, attach the full output of this script.

Still manual before a release: rebuild a binary after `pkg upgrade python` and confirm the old binary fails with a clear error while the rebuilt one works.

## Reporting test failures

Include the full unittest output, your platform, `python3 --version` and the compiler version in a [bug report](https://github.com/djunekz/zorabuilder/issues/new?template=bug_report.yml).
