# Usage Guide

A practical guide from first build to advanced options.

## Requirements

- Python 3.10 or newer
- A C compiler: clang, cc or gcc
- Python headers and zlib headers
- Optional: [UPX](https://upx.github.io/) for `--upx`

Termux:

```bash
pkg install python clang zlib
```

Debian / Ubuntu:

```bash
sudo apt-get install python3 python3-dev gcc zlib1g-dev
```

The builder itself needs no Python packages. See [README](../README.md) for installation.

## Your first binary

Create a script:

```python
import sys

name = sys.argv[1] if len(sys.argv) > 1 else "world"
print(f"Hello, {name}!")
```

Build and run it:

```bash
zorabuilder hello.py hello
./hello Termux
```

```text
Hello, Termux!
```

The command is always:

```text
zorabuilder script output [options]
```

- `script` is your entry script
- `output` is the binary to create
- options come last

## Reading the build output

```text
ℹ Entry script: hello.py
⟳ Scanning imports...
ℹ Found 1 bundleable module(s)
⟳ Building ZIP bundle...
◈   + __main__.py (93 bytes)
◈   + mod: helper.py (42 bytes)
ℹ Bundle size: 349 bytes (1 modules)
⟳ Compressing + encoding bundle...
⟳ Generating C loader...
⟳ Compiler: cc
⟳ Running build (O3+LTO)...
✓ Build successful → hello
```

| Symbol | Meaning |
| ------ | ------- |
| `ℹ` | Information |
| `⟳` | A step is running |
| `◈` | A file was added to the bundle |
| `✓` | Success |
| `⚠` | Warning (goes to stderr) |
| `✗` | Error (goes to stderr) |

The final report shows sizes and the SHA-256 of the binary.

## Projects with several files

Imports next to your script are found and bundled automatically:

```text
project/
├── main.py          import helper, from textkit.fmt import banner
├── helper.py
└── textkit/
    ├── __init__.py
    └── fmt.py
```

```bash
zorabuilder project/main.py main
```

Try the ready-made [examples](../examples):

```bash
zorabuilder examples/app.py app && ./app Ana --shout --info
zorabuilder examples/multi_module/main.py multi && ./multi A B
```

What is bundled:

| Kind | Bundled? |
| ---- | -------- |
| Local modules and packages next to the script | Yes |
| Pure-Python third-party packages installed in the builder's Python | Yes |
| Standard library | No (loaded from the Python installation); use `--extra` to force |
| C extension modules (`.so`) | No |
| Data files (JSON, images, templates) | No |
| Tests folders inside packages (`test`, `tests`) | Skipped |

## Third-party packages

The scanner resolves imports using the Python that **runs the builder**. Install the packages into that environment first:

```bash
pip install requests
zorabuilder app.py app
```

Using a virtual environment? Run the builder with that interpreter so the scanner can see its packages:

```bash
./venv/bin/python zorabuilder.py app.py app
```

Packages that contain compiled extensions (for example NumPy) cannot be bundled. You will see a warning.

## Passing arguments

Your binary receives its arguments exactly as typed. `./app -h`, `./app --version` and `./app -c` all reach your script, and `sys.argv[0]` is the path used to start the binary.

## Options in depth

### `--no-bundle`

Bundle only the entry script. Use it when everything your script needs is already importable at runtime on the target device.

```bash
zorabuilder tool.py tool --no-bundle
```

### `--extra MODULES`

Force-include modules the scanner cannot see (dynamic imports, plugins), or standard library modules you want inside the bundle. Comma-separated.

```bash
zorabuilder app.py app --extra yaml,plugins_a,plugins_b
```

### `--isolated`

The binary ignores `site-packages` and `PYTHON*` environment variables. Recommended for binaries you give to other people, together with a complete bundle.

### `--no-optimize`

Compile with `-O1` instead of `-O3 -flto`. Much faster to build; use it while developing.

### `--compress-level 0-9`

zlib level for the payload. 9 (default) is smallest; 0 stores without compression.

### `--cc COMPILER`

Choose the compiler instead of auto-detection (`clang`, then `cc`, then `gcc`).

```bash
zorabuilder app.py app --cc gcc
```

### `--static`

Try a static link and fall back to a dynamic one if it fails. Experimental; most Termux setups will fall back.

### `--upx`

Compress the final binary with UPX. Needs `upx` installed (`pkg install upx`). If UPX fails you get a warning and an uncompressed binary. Some Android devices refuse to run UPX-packed binaries; if yours crashes, rebuild without it.

### `--keep-c`

Write the generated C source next to the output as `<output>.c`. Useful for debugging and for bug reports. The file is kept even if compilation fails.

### `--json-report FILE`

Write a machine-readable report:

```json
{
  "version": "2.1.0",
  "input": "hello.py",
  "output": "hello",
  "modules": ["helper"],
  "sizes": { "original": 93, "bundle": 349, "final": 18560 },
  "sha256": "5e46bbcd51d9d666bc87d76507d6e77fa36bbe2889064df5aa2adedc27c2e80d",
  "python": "3.12",
  "static": false,
  "isolated": false
}
```

Parent folders are created for you.

### `--verbose`

Also list imports the scanner could not resolve. Helpful when a module is missing at runtime.

### `--no-banner`

Print a single title line instead of the ASCII banner. Same as `ZORA_NO_BANNER=1`. Good for logs and screen readers.

### `--version`, `--help`

Print the version or the help text. Running `zorabuilder` with no arguments prints the help.

## Environment variables

| Variable | Used by | Effect |
| -------- | ------- | ------ |
| `NO_COLOR` | builder, installers | Disables colors |
| `ZORA_NO_BANNER` | builder | Same as `--no-banner` |
| `TMPDIR` | built binary | Where the temporary bundle is written |
| `ZORA_REF`, `ZORA_TARBALL_URL` | `install.sh` | Pick a branch or tag, or a custom download URL |

## Using ZORA Builder in scripts and CI

```bash
export NO_COLOR=1
zorabuilder app.py dist/app --no-banner --json-report dist/report.json
echo "exit code: $?"
```

- Exit code 0 means success; anything else is a failure (see [ARCHITECTURE.md](ARCHITECTURE.md#exit-codes)).
- Errors and warnings are on stderr, so `2>errors.log` captures only problems.
- Builds are deterministic up to the compiler: the bundle for the same inputs is byte-identical, and the report includes the SHA-256 of the result.

## Distributing a binary

A binary runs on a device that has:

- the same CPU architecture (check with `uname -m`),
- the same operating environment (Termux for a Termux build),
- the same Python version and install location the binary was built with.

Rebuild after upgrading Python: the binary is linked to `libpythonX.Y.so`, and the version is part of its name.

Do not build or run binaries from shared storage such as `/sdcard`; Android mounts it without execute permission. Use Termux's home directory.

## Finding where the binary lives

Inside a built program, `__file__` points at a temporary file that is deleted on exit. If your program needs its own location (for data files stored next to it), use:

```python
import os
binary_dir = os.path.dirname(os.path.realpath("/proc/self/exe"))
```

## Tips

- Develop with `--no-optimize --verbose`, ship without.
- Keep the bundle small: every start decompresses the payload and writes it to the temp directory.
- Test the binary in a clean shell to catch hidden dependence on your environment.
- If something fails, start with [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
