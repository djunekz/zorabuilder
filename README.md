# ZORA Builder

Bundles a single Python script (plus the local and third-party modules it uses) into one standalone ELF binary for Termux/Android.

## Structure

```
zorabuilder.py          thin entrypoint
pyproject.toml          package metadata (pip install -e . gives the zora / zorabuilder commands)
core/
  cli.py                argparse + orchestration
  config.py             BuildConfig
  scanner.py            import detection (ast) and module discovery
  bundler.py            deterministic ZIP, zlib, base64
  codegen.py            C loader source generator
  compiler.py           compilation via clang/cc/gcc, UPX
  report.py             build report (text + JSON)
  ui.py                 colors, banner, logger
```

## Usage

```
zorabuilder script output [options]
```

```bash
pkg install python clang zlib
python zorabuilder.py myapp.py myapp
./myapp
```

More examples:

```bash
zorabuilder myapp.py myapp --isolated --upx
zorabuilder tool.py bin/tool --extra yaml,requests
zorabuilder tool.py tool --no-bundle --json-report build.json
```

Running `zorabuilder` with no arguments prints the help.

## Options

| Option | Description |
|---|---|
| `--no-bundle` | bundle only the script, no dependency modules |
| `--extra MODULES` | force-include modules (comma-separated), including stdlib modules |
| `--isolated` | ignore site-packages and PYTHON* env vars at runtime |
| `--no-optimize` | faster build: `-O1` instead of `-O3 -flto` |
| `--compress-level 0-9` | zlib level (default 9) |
| `--cc COMPILER` | choose the compiler (default auto: clang, cc, gcc) |
| `--static` | try a static link, fall back to dynamic (experimental) |
| `--upx` | compress the final binary with UPX |
| `--keep-c` | keep the generated C source as `<output>.c` |
| `--json-report FILE` | write a JSON build report |
| `--verbose` | show modules the scanner could not find |
| `--version` | show the version |

## Limitations

The binary still uses `libpythonX.Y.so` and the stdlib from the Python installation on the same device (`$PREFIX`), so it is not portable to other systems. The stdlib is not bundled unless forced with `--extra`. Packages with C extensions (`.so`) are not bundled. Dynamic imports (`__import__`, `importlib`) are not detected; use `--extra`.

## Audit: bugs fixed

**Display / CLI**

1. Usage was shown as `zorabuilder [options] script output`; it is now `zorabuilder script output [options]`.
2. Options are grouped (arguments, build, output), usage examples were added, and metavars are clear (`MODULES`, `FILE`, `0-9` instead of `{0,1,2,...}`).
3. The banner was also shown on errors and always printed `Mode: Full Bundle` even with `--no-bundle`; the banner is now shown only for help and builds, with the correct mode.
4. Argument errors now include an example and a `--help` hint; running with no arguments shows the help.
5. ANSI colors leaked into pipes/logs; they are now disabled automatically when output is not a terminal or `NO_COLOR` is set. Warnings and errors go to stderr.

**Built binary**

6. Binary arguments were parsed as Python interpreter options: `sys.argv` was corrupted (the first argument was treated as a file name), and `-h`/`--version`/`-c` printed Python's help/version or failed to initialize. Now `parse_argv = 0`.
7. `sys.exit(n)` always exited with 0 or 1 and `sys.exit("message")` printed nothing; both are now handled by `PyErr_Print`, so exit codes and messages are correct.
8. zlib decompression guessed the output size and doubled the buffer up to ~2 GB on corrupt data; the real size is now embedded at build time.
9. Overly long temp paths were silently truncated; they are now checked. An unwritable `TMPDIR` falls back to `/tmp`.
10. C API calls had no NULL checks; all are now checked and init errors show the cause.

**Build**

11. `zorabuilder app.py app.py` overwrote the source script with an ELF; it is now rejected. Also rejected: output that is a directory, a missing output folder, and scripts with syntax errors.
12. `--keep-c` used `with_suffix(".c")` (a name like `app.c` overwrote the binary, `my.app` became `my.c`); it is now `<output>.c`, and is kept even if compilation fails.
13. `--cc wrong` silently used another compiler; it is now an error.
14. The temp work folder leaked on exceptions; output is now written to a temp location first and then moved, so no half-built files are left behind.
15. The UPX result was never checked; a UPX failure now produces a warning.
16. Header/library paths were hardcoded to `$PREFIX/include/pythonX.Y`; they now come from `sysconfig` (including `abiflags`), and the prefix comes from `sys.base_prefix`.

**Scanner / bundler**

17. The entire stdlib was bundled (a 211-byte script produced a 2.3 MB bundle) even though the stdlib is loaded from `$PREFIX`; frozen modules were counted as bundled but never entered the ZIP. The stdlib is now skipped (unless forced with `--extra`, or shadowed by a local module of the same name).
18. The `test`/`tests` folder filter was checked against the absolute path: a project inside a folder named `test` was not bundled at all. It is now relative to the package root.
19. The scanner and bundler used different filter rules; they now share one function.
20. `except OSError: pass` swallowed files that failed to read; errors are now visible.
21. Namespace packages were not found; they are now supported. Packages with C extensions produce a warning.
22. Bundles were non-deterministic (timestamps); they are now fixed. The ZIP was compressed twice (deflate, then zlib); it is now stored, then zlib once.
23. The scanner's `sys.path.insert` was never cleaned up; it is now restored.

**Packaging**

24. `pyproject.toml` pointed to `zora_builder.cli:main` while the folder is named `core`; it now points to `core.cli:main`. The scanner also prefers local modules in the script's folder, so a script that has its own module named `core` does not pick up the builder's package by mistake.
25. `pyproject` version was 3.1.0 vs 2.0.0 in the code; there is now a single source (`VERSION` in `core/cli.py`, currently 2.1.0).
26. Setuptools auto-discovery failed (both `zorabuilder.py` and a package present); `packages` is now explicit.
