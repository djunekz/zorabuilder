# Privacy Policy

**Short version: ZORA Builder collects nothing, sends nothing, and phones home never.**

## The builder

- It runs entirely on your device.
- It makes **no network connections**.
- It has **no telemetry, analytics or crash reporting**.
- It reads the script you point it at, the modules that script imports, and the local Python installation. It writes the binary, and optionally the C source (`--keep-c`) and a JSON report (`--json-report`), where you tell it to.
- The build report contains file paths, module names, sizes and a SHA-256 hash. It stays on your device unless you share it. Review it before attaching it to a public issue, because paths can reveal your username or project names.

## Binaries you build

A binary built with ZORA Builder contains your code and the modules you bundled. The loader inside it does not contact any server. Anything your own script does (network access, logging, analytics) is entirely your own responsibility.

At runtime the loader writes a temporary file (`zora_XXXXXX.zip`) to your temp directory and removes it when the program exits. See [SECURITY.md](SECURITY.md) for details.

## The installer

`install.sh` contacts GitHub to download the source archive when you do not run it from a checkout, and, unless you pass `--no-deps`, your system package manager (`pkg` or `apt-get`) to install Python, a compiler and zlib. It sends nothing about you beyond what those normal requests involve (your IP address and standard HTTP headers). `uninstall.sh` makes no network connections.

## This repository

The project is hosted on GitHub. When you open an issue, comment, or submit a pull request, GitHub processes that content and your public profile under [GitHub's privacy statement](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement). Do not post secrets, tokens, or private information in issues or logs. If you accidentally do, tell a maintainer so it can be removed, and rotate the secret.

## Changes

If this policy ever changes, the change will be listed in [CHANGELOG.md](CHANGELOG.md).
