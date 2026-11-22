# Frequently Asked Questions

## The basics

### What does ZORA Builder do?

It turns a Python script (plus the local and third-party modules it imports) into a single native ELF executable you can run like any other program: `./myapp`.

### Does it compile my Python to machine code?

No. It builds a small C program that contains your code as a compressed payload and starts the Python interpreter to run it. Your code runs exactly as it would with `python3 myapp.py`, with the same speed and the same behavior.

### Is the binary standalone?

It is a single file, but it is not self-contained. It needs the same Python installation (`libpythonX.Y.so`, the standard library and extension modules) that was used for the build. That is a deliberate trade-off: binaries stay tiny (about 18 KB plus your code) and extension modules keep working.

### Which platforms does it support?

Linux, with Termux on Android as the primary target. Any system with Python 3.10 or newer, a C compiler and the Python and zlib headers should work, on ARM and x86. It does not produce Windows or macOS executables.

### Which Python versions?

The builder requires Python 3.10 or newer. The binary uses the Python version that built it. CI tests 3.10, 3.11, 3.12, 3.13 and 3.14, and the device check has passed on Termux with Python 3.14.

## Comparisons and expectations

### How is it different from PyInstaller or Nuitka?

Those tools aim for portable, self-contained distributions, and handle many compiled packages and data files. ZORA Builder aims at something smaller and simpler: a tiny executable wrapper for scripts, built with just a C compiler, in an environment like Termux where other tools can be difficult to set up. Choose a larger tool if you need to ship to machines without Python, or to bundle compiled dependencies and data files.

### Will my program run faster?

No. Startup is slightly slower, because the payload is decompressed and written to a temp file every time.

### Does it protect or hide my source code?

**No.** The payload is compressed and base64-encoded, not encrypted. Anyone with the binary can recover your source. Never embed secrets. See [SECURITY.md](../SECURITY.md).

### Can I run the binary on another phone or computer?

Only if it has the same CPU architecture, the same kind of environment (Termux for Termux), and the same Python version and location. Otherwise, build on the target device.

## What gets bundled

### Why does it say "Found 0 bundleable module(s)" for my script?

Your script only imports the standard library, which is not bundled because it is loaded from the Python installation. That is normal. The binary still contains your script.

### Can I bundle the standard library?

Yes, selected modules: `--extra textwrap,json`. There is rarely a reason to.

### Can I bundle NumPy, Pillow, or other packages with C extensions?

No. Compiled extensions cannot be put in the bundle. Install them on the device and run the binary without `--isolated`; the binary will import them from the Python installation.

### Does it include data files, images or templates?

No, only `.py` files. Ship data next to the binary and find it with `os.path.realpath("/proc/self/exe")`.

### Why was my dynamically imported module missing?

The scanner reads import statements, not runtime behavior. Name such modules with `--extra`.

### Can I use `if __name__ == "__main__":`?

Yes. The entry script runs as `__main__`.

### Does `multiprocessing` work?

Threads and `subprocess` work as usual. `multiprocessing` can re-launch the interpreter and may not behave as expected inside a bundled binary; this is not a supported scenario at present. Test your program before relying on it.

## Running the binary

### Where does it write files?

Only one: a temporary `zora_XXXXXX.zip` in `$TMPDIR` (else `<prefix>/tmp`, else `/tmp`), removed when the program exits.

### Why does `__file__` look strange?

Code runs from the temporary bundle, so `__file__` is that file's path. To find the binary, use `os.path.realpath("/proc/self/exe")`.

### Why do I see `./app` in `sys.argv[0]`?

It is the path you used to start it, as with any program.

### Do `-h`, `--version` and `-c` reach my script?

Yes. They are your program's arguments, not Python's. (Earlier builds of ZORA Builder mishandled this; see the [changelog](../CHANGELOG.md).)

### What happens when I press Ctrl+C or send SIGTERM?

Ctrl+C raises `KeyboardInterrupt` in your script. On `SIGTERM` the temp file is removed and the process exits with status 143.

### I upgraded Python and the binary stopped working.

Rebuild it. The binary is tied to the Python version it was built with.

## Building

### How big are the binaries?

About 18 KB for the loader plus your compressed code, base64-encoded (roughly 1.33 times the compressed size).

### Can I cross-compile?

No. You build with the Python and compiler on the device that will run the binary.

### Can I reproduce a build?

The bundle is byte-for-byte deterministic for the same inputs. The final binary also depends on the compiler, so compare SHA-256 hashes only for the same toolchain.

### Where are the generated files?

Nowhere, unless you ask: `--keep-c` keeps the C source as `<output>.c`, and `--json-report` writes a report.

### Does the builder send any data anywhere?

No. See [PRIVACY.md](../PRIVACY.md).

## Project

### How do I install or remove it?

See the README. Install with `install.sh`; remove with `uninstall.sh`, which touches only what the installer created and never your built binaries.

### How can I contribute?

See [CONTRIBUTING.md](../CONTRIBUTING.md).
