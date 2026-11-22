# Troubleshooting

Find your message, apply the fix. If nothing here helps, open a [bug report](https://github.com/djunekz/zorabuilder/issues/new?template=bug_report.yml) or a [build failure report](https://github.com/djunekz/zorabuilder/issues/new?template=build_failure.yml).

## Quick diagnosis

Run these and keep the output; you will be asked for it.

```bash
zorabuilder --version
python3 --version
uname -m
clang --version || gcc --version
python3 -c "import sysconfig; print(sysconfig.get_paths()['include']); print(sysconfig.get_config_var('LIBDIR'))"
```

Then retry the failing build with more detail:

```bash
zorabuilder app.py app --verbose --no-optimize --keep-c
```

## Using the command

### `error: the following arguments are required: script, output`

You gave too few arguments. Both are required, and options go last:

```bash
zorabuilder myapp.py myapp
```

### `Script not found: ...`

The path to your script is wrong. Check the spelling and the current directory (`pwd`, `ls`).

### `Syntax error in app.py, line N: ...`

The builder refuses to bundle a script Python cannot parse. Fix the error shown. Run `python3 app.py` to see it in context.

### `Output would overwrite the input script: ...`

Output and script are the same file. Choose a different output name, for example `zorabuilder app.py app`.

### `Output is a directory, give a file name: ...`

The output path is an existing folder. Give a file name inside it: `zorabuilder app.py bin/app`.

### `Output folder does not exist: ...`

Create the folder first: `mkdir -p bin`.

### `Compiler not found: NAME`

`--cc NAME` names a program that is not installed or not on `PATH`. Remove `--cc` to auto-detect, or install the compiler.

## Toolchain problems

### `Python headers not found: ... Run: pkg install python clang`

`Python.h` is missing.

- Termux: `pkg install python clang`
- Debian/Ubuntu: `sudo apt-get install python3-dev`

If you installed Python some other way (pyenv, a custom build), make sure the headers were installed with it. Check with:

```bash
python3 -c "import sysconfig, os; p=sysconfig.get_paths()['include']; print(p, os.path.exists(p + '/Python.h'))"
```

### `No C compiler found (tried clang, cc, gcc)`

Install one: `pkg install clang` (Termux) or `sudo apt-get install gcc`.

### `Compilation failed!` with `cannot find -lpythonX.Y`

The linker cannot find `libpythonX.Y.so`. Check the library directory printed by the diagnosis command above, and that it contains `libpython3.*`.

- Termux: `pkg install python` provides it.
- Debian/Ubuntu: `sudo apt-get install libpython3-dev` (match your Python version).
- Python built from source: configure it with `--enable-shared`.

### `Compilation failed!` with `cannot find -lz` or `zlib.h: No such file`

Install the zlib headers: `pkg install zlib` (Termux) or `sudo apt-get install zlib1g-dev`.

### Linker errors mentioning `lto`, `plugin`, or `gold`

Link-time optimization is not available with your toolchain. Build faster and without LTO:

```bash
zorabuilder app.py app --no-optimize
```

### `UPX not found, skipping` / `UPX failed, keeping uncompressed binary`

Install UPX (`pkg install upx`), or build without `--upx`. The binary is still produced without it. Some Android devices cannot run UPX-packed ELF files; if the packed binary crashes at startup, rebuild without `--upx`.

### `Static link failed, retrying dynamic...`

Expected on most systems: there is no static `libpython`. The dynamic build that follows is fine.

## Problems when running the binary

### `bash: ./app: Permission denied`

- You are on shared storage (`/sdcard`, `/storage/emulated/0`). Android mounts it without execute permission. Build and run inside Termux's home directory (`~`).
- Or the file lost its permission bit after being copied: `chmod +x app`.

### `Exec format error`

The binary was built for a different CPU architecture or a different OS. Compare `uname -m` on the build and run devices, and rebuild on the device where it will run.

### `CANNOT LINK EXECUTABLE ... library "libpythonX.Y.so" not found`

The Python version on the device changed since the build (for example after `pkg upgrade`). Rebuild the binary with the current Python.

### `Fatal Python error: ... init_fs_encoding` / `No module named 'encodings'` / `[zora] python init failed: ...`

The binary cannot find the Python standard library at the location it was built against. Typical causes:

- Python was upgraded or moved since the build. Rebuild.
- The binary was copied to a device with a different Python installation. Build on the target device.

### `[zora] decode failed` / `[zora] decompress failed`

The payload inside the binary is damaged. Usually a truncated copy or a failed transfer, or the file was modified after the build (for example by `strip` or a different packer). Rebuild or copy it again, and compare the SHA-256 with the build report.

### `[zora] mkstemps failed (tmpdir=...)` / `[zora] failed to write temp bundle`

The loader could not create its temporary file. Point `TMPDIR` to a writable folder with enough space:

```bash
mkdir -p ~/tmp
TMPDIR=~/tmp ./app
```

### `[zora] temp path too long (tmpdir=...)`

`TMPDIR` is very long. Use a shorter directory.

### `[zora] bundle has no __main__` / `cannot open bundle` / `zipimport unavailable`

Internal consistency errors. Rebuild; if it persists, report a bug and attach the build output and the `--keep-c` source.

### `ModuleNotFoundError: No module named 'x'`

The module was not bundled and is not importable at runtime. Check, in order:

1. **Dynamic import.** `__import__("x")` or `importlib.import_module(name)` is invisible to the scanner. Add `--extra x`.
2. **Not found at build time.** Rebuild with `--verbose` and look for `Not found: x`. The package must be installed in the Python that runs the builder. With a virtualenv, run `./venv/bin/python zorabuilder.py ...`.
3. **C extension.** Compiled modules cannot be bundled (you will have seen `Skip C-ext` or a warning about C extensions). Make sure the package is installed on the device that runs the binary, and do not use `--isolated`.
4. **`--no-bundle`.** Remove it.
5. **Standard library submodule you expected inside the bundle.** The standard library is not bundled; it comes from Python. Use `--extra` only if you really want a copy.

### `FileNotFoundError` for a data file

Only `.py` files are bundled. Ship data files next to the binary and locate them with `/proc/self/exe` (see [USAGE.md](USAGE.md#finding-where-the-binary-lives)); `__file__` points at a temporary file.

### Tracebacks show `/tmp/zora_XXXXXX.zip/__main__.py`

Normal. The code runs from the temporary bundle, and line numbers refer to your original script.

### A leftover `zora_XXXXXX.zip` in the temp folder

A process was killed with `SIGKILL` (or the device lost power) before it could clean up. The file is safe to delete.

### The binary starts slowly

Every start decodes and decompresses the payload and writes it to disk. Keep the bundle small (`--no-bundle` for single files, fewer dependencies) and use fast storage for `TMPDIR`.

### Ctrl+C handling

Ctrl+C reaches your script as `KeyboardInterrupt`, like with normal Python.

## Display problems

| Symptom | Fix |
| ------- | --- |
| Strange characters like `[0;36m` | Your terminal does not interpret colors. `export NO_COLOR=1`. |
| Empty boxes instead of `ℹ ✓ ⚠ ✗` | Your font lacks those symbols. Use a font with broader Unicode coverage, for example a Nerd Font or the default Termux font. |
| Banner is too wide or noisy | `--no-banner` or `export ZORA_NO_BANNER=1`. |
| Help text wraps badly | Set `COLUMNS`, for example `COLUMNS=70 zorabuilder --help`. |

## Installer problems

### `install.sh: ... is not in your PATH`

The launcher was installed, but its folder is not on `PATH`. Add the folder shown in the message, for example:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### `... already exists and was not created by this installer`

A different file with that name exists. Move it away, or pass `--force` to overwrite.

### `Python >= 3.10 is required`

Upgrade Python (`pkg upgrade python`, or install a newer `python3` on your distribution).

### `download failed`

No network, or GitHub is unreachable. Check connectivity, or clone the repository and run `./install.sh` from the checkout.

### `root privileges are required`

On Debian-like systems the installer installs system packages through `sudo`. Run as root, install `sudo`, or install the packages yourself and pass `--no-deps`.

## Still stuck?

See [SUPPORT.md](../SUPPORT.md).
