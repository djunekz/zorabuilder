# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to semantic versioning.

## [Unreleased]

---

## [v2.1.0] - 2026-11-21

### Added
- `core/cli.py` - new `--version` option
- `core/cli.py` - usage examples section at the bottom of `--help`
- `core/cli.py` - running `zorabuilder` with no arguments now prints the help (exit 0)
- `core/cli.py` - input validation: script not found, syntax error in the script, output is a directory, output folder does not exist, output is the same file as the input script
- `core/cli.py` - `--extra` combined with `--no-bundle` now warns that `--extra` is ignored
- `core/cli.py` - clean handling of `Ctrl+C` during a build (exit 130)
- `core/scanner.py` - namespace packages are now discovered and bundled
- `core/scanner.py` - warning when a package contains C extensions (`.so`) that cannot be bundled
- `core/scanner.py` - `iter_package_files()` shared by the scanner and the bundler, so both use the same filter rules
- `core/ui.py` - colors are disabled automatically when output is not a terminal or `NO_COLOR` is set
- `core/report.py` - JSON report now includes `version`, and its target folder is created automatically
- `pyproject.toml` - new `zorabuilder` console command in addition to `zora`
- `core/cli.py` - new `--no-banner` option, and `ZORA_NO_BANNER` environment variable, to print a one-line title instead of the ASCII banner
- `install.sh` - installer for Termux and Debian/Ubuntu: installs system packages, copies ZORA Builder and creates the `zorabuilder` and `zora` launchers; supports `--prefix`, `--no-deps`, `--with-upx`, `--ref`, `--force`, runs from a checkout or via `curl | bash`
- `uninstall.sh` - removes only what the installer created, asks for confirmation unless `--yes` is given, never touches built binaries or system packages
- `requirements.txt`, `requirements-dev.txt` - dependency files (the builder itself has no runtime dependencies)
- `tests/` - unittest suite covering the scanner, bundler, code generator, CLI and real end-to-end builds, including signal handling
- `examples/` - `app.py` and `multi_module/` demo programs used by the docs and the tests
- `.github/ISSUE_TEMPLATE/` - issue forms for bug reports, build failures, feature requests and documentation problems, plus `config.yml` with contact links
- `.github/PULL_REQUEST_TEMPLATE.md`, `.github/CODEOWNERS`, `.github/dependabot.yml`, `.github/labeler.yml`, `.github/labels.yml`, `.github/release.yml` - repository automation and templates
- `.github/workflows/ci.yml` - lint, shell script checks with an install/uninstall smoke test, tests on Python 3.10 to 3.13, and a packaging check
- `.github/workflows/codeql.yml`, `dependency-review.yml`, `labeler.yml`, `labels-sync.yml`, `stale.yml` - code scanning, dependency review, PR labeling, label sync and stale issue handling
- `.github/workflows/release.yml` - verifies the tag against `VERSION`, runs the tests, builds distributions with `SHA256SUMS`, and publishes a GitHub Release using the matching CHANGELOG section
- `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CONTRIBUTING.md`, `SUPPORT.md`, `ACCESSIBILITY.md`, `GOVERNANCE.md`, `PRIVACY.md` - community and policy documents
- `docs/` - `USAGE.md`, `TROUBLESHOOTING.md`, `FAQ.md`, `ARCHITECTURE.md`, `DEVELOPMENT.md`, `TESTING.md`, `RELEASING.md`, `ROADMAP.md`
- `.gitignore`, `.gitattributes`, `.editorconfig` - repository hygiene
- `pyproject.toml` - project metadata (authors, keywords, classifiers, URLs), `dev` extra and ruff configuration
- `LICENSE` - MIT license (Copyright (c) 2026 djunekz)
- `scripts/termux-check.sh` - device check that runs the release checklist on Termux or any Linux: environment, test suite, install, builds, argument pass-through, exit codes, Ctrl+C handling, temp file cleanup, reinstall and uninstall, with a PASS/FAIL summary and exit status
- `CODE_OF_CONDUCT.md`, `SECURITY.md`, `SUPPORT.md`, `GOVERNANCE.md` - private contact by email for security reports and conduct concerns
- `CHANGELOG.md` - this file

### Changed
- `core/cli.py` - usage is now `zorabuilder script output [options]` instead of `zorabuilder [options] script output`
- `core/cli.py` - options are grouped into `arguments`, `build options`, `output options` and `other`
- `core/cli.py` - clearer metavars: `MODULES`, `COMPILER`, `FILE`, `0-9` (replacing `{0,1,2,...,9}`) and clearer help texts
- `core/cli.py` - missing-argument errors now include an example and a `--help` hint
- `core/cli.py` - the banner is shown only for help and builds, no longer on error screens
- `core/cli.py` - the banner `Mode:` line is now correct (`Full Bundle` / `Script Only`)
- `core/ui.py` - warnings and errors are written to stderr
- `core/scanner.py` - the stdlib is no longer bundled (small script: bundle went from 2.3 MB to 880 bytes); use `--extra` to force it, and local modules named like a stdlib module are still bundled
- `core/scanner.py` - local modules in the script's folder take priority over installed ones, so a script with its own module named `core` no longer picks up the builder's package
- `core/bundler.py` - ZIP entries use fixed timestamps and sorted order, so the binary hash is reproducible for the same input
- `core/bundler.py` - ZIP is now `stored` and compressed once with zlib (previously deflate, then zlib again)
- `core/compiler.py` - header and library paths come from `sysconfig` (including `abiflags`) with a prefix fallback
- `core/compiler.py` - Python home/prefix now uses `sys.base_prefix`
- `core/compiler.py` - the binary is compiled in a temp folder and moved to the output only on success
- `core/codegen.py` - the real ZIP size is embedded in the C loader at build time
- `core/config.py` - `bundle_stdlib` renamed to `bundle_deps`
- `pyproject.toml` - declares the MIT license and includes the LICENSE file in distributions
- `pyproject.toml` - single version source: `core.cli.VERSION` (previously `pyproject` said 3.1.0 vs 2.0.0 in the code)
- `pyproject.toml` - explicit `packages = ["core"]`
- `README.md` - rewritten with installation options, usage, option reference, real output samples, architecture overview, limitations and a documentation index

### Fixed
- `core/codegen.py` - binary arguments were parsed as Python interpreter options: `sys.argv` was corrupted and `-h`, `--version`, `-c` printed Python's help/version or failed to initialize (now `parse_argv = 0`)
- `core/codegen.py` - `sys.exit(n)` always exited with 0 or 1 and `sys.exit("message")` printed nothing; exit codes and messages are now correct
- `core/codegen.py` - decompression guessed the output size and could double the buffer up to ~2 GB on corrupt data
- `core/codegen.py` - overly long temp paths were silently truncated; they are now checked
- `core/codegen.py` - an unwritable or missing `TMPDIR` now falls back to `/tmp`
- `core/codegen.py` - missing NULL checks on C API calls; all are checked now and init errors show the cause
- `core/codegen.py` - Ctrl+C could not be caught by the script: the loader installed its own `SIGINT` handler before Python started, which stopped Python from installing its handler, so `except KeyboardInterrupt`, `finally` blocks and `atexit` callbacks never ran. `SIGINT` is now handed to Python, an uncaught `KeyboardInterrupt` exits with 130, and signals inherited as ignored (for example in background jobs) stay ignored
- `core/cli.py` - `zorabuilder app.py app.py` overwrote the source script with an ELF
- `core/cli.py` - the banner always printed `Mode: Full Bundle` even with `--no-bundle`
- `core/compiler.py` - `--keep-c` used `with_suffix(".c")`, so `app.c` overwrote the binary and `my.app` became `my.c`; it now saves `<output>.c` and keeps it even if compilation fails
- `core/compiler.py` - `--cc` with a missing compiler silently used another compiler; it is now an error
- `core/compiler.py` - the temp work folder leaked on exceptions, and failed builds could leave partial output
- `core/compiler.py` - the UPX result was never checked; a UPX failure now produces a warning
- `core/compiler.py` - header/library paths were hardcoded to `$PREFIX/include/pythonX.Y`
- `core/report.py` - the `Run:` hint printed `././path` for outputs that already had a path
- `core/scanner.py` - frozen modules were counted as bundled but never entered the ZIP
- `core/scanner.py` - the `test`/`tests` folder filter was checked against the absolute path, so a project inside a folder named `test` was not bundled at all (now relative to the package root)
- `core/scanner.py` - the `sys.path` entry added during scanning was never removed
- `core/bundler.py` - `except OSError: pass` swallowed files that failed to read; errors are now visible
- `core/bundler.py` - scanner and bundler used different filter rules for package files
- `pyproject.toml` - entry point pointed to a non-existent package (`zora_builder.cli:main`); now `core.cli:main`
- `pyproject.toml` - setuptools auto-discovery failed because both `zorabuilder.py` and a package were present

### Removed
- `core/bundler.py` - removed the unused `compress_level` argument from `build_bundle_zip()` (the level now applies to the zlib step only)

---

## [v2.0.0] - 2026-11-18

### Added
- Initial modular release: `core` package split into `cli`, `config`, `scanner`, `bundler`, `codegen`, `compiler`, `report` and `ui`
