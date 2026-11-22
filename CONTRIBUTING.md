# Contributing to ZORA Builder

Thanks for wanting to help. Bug reports, documentation fixes, tests, and code are all welcome, from first-time contributors too.

By taking part you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

By contributing, you agree that your contributions are licensed under the project's [MIT License](LICENSE).

## Ways to contribute

- **Report a bug or a build failure** with the [issue forms](https://github.com/djunekz/zorabuilder/issues/new/choose). A minimal script that reproduces the problem is the most valuable thing you can attach.
- **Suggest a feature.** Check [docs/ROADMAP.md](docs/ROADMAP.md) first.
- **Improve the docs.** Typos, unclear sentences and missing examples are real bugs.
- **Fix something.** Look for issues labeled `good first issue` or `help wanted`.
- **Test on your device.** Real-world reports from different Android versions, CPU architectures and Python versions are very helpful.

For security problems, do not open an issue. Follow [SECURITY.md](SECURITY.md).

## Development setup

```bash
git clone https://github.com/djunekz/zorabuilder.git
cd zorabuilder
python3 -m pip install -r requirements-dev.txt
python3 zorabuilder.py --help
python3 -m unittest discover -s tests -t . -v
```

You need Python 3.10 or newer, a C compiler (clang, cc or gcc) and the Python and zlib headers. On Termux: `pkg install python clang zlib`. On Debian/Ubuntu: `sudo apt-get install python3-dev gcc zlib1g-dev`. See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for details.

## Workflow

1. **Open or find an issue** for anything bigger than a small fix, so we can agree on the approach before you invest time.
2. **Fork** the repository and create a branch from `main`:
   `fix/keep-c-overwrite`, `feat/ascii-mode`, `docs/usage-examples`.
3. **Make your change** in small, focused commits.
4. **Add or update tests.** A bug fix needs a test that fails without the fix.
5. **Run the checks** listed below.
6. **Update the docs and the changelog.**
7. **Open a pull request** against `main` and fill in the template.

## Checks to run before opening a PR

```bash
python3 -m unittest discover -s tests -t . -v
ruff check .
bash -n install.sh && bash -n uninstall.sh && bash -n scripts/termux-check.sh
shellcheck --severity=warning install.sh uninstall.sh scripts/termux-check.sh
```

If your change touches the C loader, the compiler step or the bundler, also build and run a real binary:

```bash
python3 zorabuilder.py examples/app.py /tmp/app && /tmp/app a b
```

The end-to-end tests do this automatically when a C toolchain is available. On a phone, `./scripts/termux-check.sh` runs a complete check of the install, builds, signals and uninstall.

## Code conventions

- **No comments and no docstrings** in source files. Express intent with clear names, small functions and tests, and put explanations in `docs/`. The only exception is the shebang line.
- Keep modules focused. Follow the layout in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
- Python 3.10 compatible. Standard library only: the builder has no runtime dependencies and should stay that way.
- Lines up to 120 characters; four-space indentation; UTF-8; LF line endings (see `.editorconfig`).
- User mistakes (bad arguments, missing files) go through `ui.die` with a clear message and exit code 1. Unexpected internal failures raise exceptions that `cli.run` reports.
- Warnings and errors go to stderr. Never rely on color alone to convey meaning; see [ACCESSIBILITY.md](ACCESSIBILITY.md).
- Shell scripts: `bash`, `set -eu`, quoted variables, ShellCheck clean.
- The generated C code must compile without warnings under `-Wall -Wextra`. A test enforces this.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
fix(loader): pass binary arguments through to sys.argv
feat(cli): add --no-banner
docs: explain the temp file used at runtime
test(scanner): cover namespace packages
```

Common types: `feat`, `fix`, `docs`, `test`, `refactor`, `ci`, `chore`. Mark breaking changes with `!` (`feat(cli)!: ...`) and explain them in the body.

## Pull request guidelines

- One logical change per PR. Large PRs are hard to review and slow to merge.
- Explain **why** the change is needed, not only what it does.
- Describe how you tested it: platform, Python version, commands.
- Keep the PR green. CI runs lint, shell checks, tests on Python 3.10 to 3.14, and a packaging check.
- Be responsive to review comments. Maintainers may push small fixes to your branch.

## Changelog

Every user-visible change gets a line in the `[Unreleased]` section of [CHANGELOG.md](CHANGELOG.md), in the format already used there:

```
- `core/cli.py` - new `--example` option
```

Sections are `Added`, `Changed`, `Fixed` and `Removed`.

## Adding a feature: where does it go?

| You want to change...                  | Look at                         |
| -------------------------------------- | ------------------------------- |
| Command-line options, help text         | `core/cli.py`                   |
| Colors, banner, log lines               | `core/ui.py`                    |
| Which modules get bundled               | `core/scanner.py`               |
| What goes into the ZIP, compression     | `core/bundler.py`               |
| Runtime behavior of the binary          | `core/codegen.py` (C template)  |
| Compiler flags, linking, UPX            | `core/compiler.py`              |
| Build report and JSON output            | `core/report.py`                |
| Installation                            | `install.sh`, `uninstall.sh`    |
| Device check script                     | `scripts/termux-check.sh`       |

## Releasing

Maintainers follow [docs/RELEASING.md](docs/RELEASING.md).

## Questions

See [SUPPORT.md](SUPPORT.md).
