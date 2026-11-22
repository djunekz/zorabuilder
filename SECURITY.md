# Security Policy

## Supported versions

Security fixes are released for the latest minor version only.

| Version | Supported |
| ------- | --------- |
| 2.1.x   | Yes       |
| < 2.1   | No        |

## Reporting a vulnerability

**Please do not open a public issue for security problems.**

Use GitHub's private vulnerability reporting:

1. Go to the [Security tab](https://github.com/djunekz/zorabuilder/security) of the repository.
2. Choose **Report a vulnerability**, or open the [report form](https://github.com/djunekz/zorabuilder/security/advisories/new) directly.
3. Describe the problem and how to reproduce it.

If you cannot use that form, email the maintainer at **gab288.gab288@passinbox.com** with the subject `[zorabuilder security]`. You can ask for an encrypted channel before sending sensitive details. Do not put exploit details in a public message, an issue, or a pull request.

### What to include

- ZORA Builder version (`zorabuilder --version`), Python version, platform and CPU architecture
- The command you ran and a minimal script or input that triggers the problem
- What you expected, what happened, and the impact you see
- If relevant, the generated C source (`--keep-c`)

### What to expect

These are targets for a volunteer-run project, not guarantees:

| Step | Target |
| ---- | ------ |
| Acknowledge your report | within 7 days |
| Initial assessment (accepted, needs more info, or declined) | within 14 days |
| Fix or mitigation for accepted, high-impact issues | as soon as practical, usually within 90 days |

You will be kept informed. When a fix is released, the advisory credits you unless you prefer to stay anonymous. Please give us reasonable time to release a fix before public disclosure.

## Scope

In scope:

- The builder: `zorabuilder.py` and the `core/` package
- The C loader that `core/codegen.py` generates, and therefore every binary built with it
- `install.sh`, `uninstall.sh` and the scripts in `scripts/`
- The GitHub workflows in `.github/`

Out of scope:

- Vulnerabilities in Python, clang, zlib, UPX or Termux themselves. Report those upstream.
- Vulnerabilities in the scripts or third-party packages you bundle
- Issues that require an attacker who already controls your device, your account or your build environment
- Denial of service by feeding the builder absurdly large inputs on your own machine

## Security model and known limitations

Knowing what ZORA Builder does **not** protect is part of using it safely.

**The bundle is not protected.** Your script and bundled modules are stored compressed (zlib) and base64-encoded inside the binary. That is packaging, not encryption or obfuscation. Anyone with the binary can recover your source. Never embed passwords, tokens, API keys or private keys in a script you bundle.

**A temporary file exists while the program runs.** The loader writes the bundle to `zora_XXXXXX.zip` in `$TMPDIR` (falling back to `<prefix>/tmp`, then `/tmp`) with owner-only permissions (`0600`, created with `mkstemps`) and deletes it on normal exit, on uncaught exceptions, and on `SIGTERM`. A hard kill (`SIGKILL`) or a crash of the device cannot run cleanup and can leave the file behind. Point `TMPDIR` at a private directory if the system temp directory is shared.

**The runtime environment is trusted unless you isolate it.** By default the binary honors Python environment variables such as `PYTHONPATH` and loads `site-packages`. Build with `--isolated` to ignore them when the binary may run in an environment you do not control.

**Binaries depend on the local Python installation.** The binary loads `libpythonX.Y.so`, the standard library and extension modules from the Python install it was built against. Whoever can modify those files can change what your binary executes.

**You bundle what is installed on the build machine.** ZORA Builder copies the modules it finds on the builder's `sys.path`. A compromised package on the build machine ends up inside your binary. Build in a clean environment and pin your dependencies.

**Installer.** `install.sh` downloads a source archive from GitHub over HTTPS and installs it under a prefix you control. Piping a script into a shell (`curl | bash`) trusts the network path and the repository. If that is not acceptable, download the script, read it, and run it from a checkout. Use `--ref` with a release tag to pin a version. The scripts never use `sudo` unless you let them install system packages, and `--no-deps` disables that.

## Safe usage checklist

- Build from a clean virtual environment or a fresh Termux install
- Pin and review third-party dependencies before bundling them
- Use `--isolated` for binaries you distribute
- Verify downloads against the `SHA256SUMS` file attached to each release
- Treat the built binary as readable source, not as a secret store

## Disclosure

Fixed vulnerabilities are published as GitHub Security Advisories and noted in [CHANGELOG.md](CHANGELOG.md).
