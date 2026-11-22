# Roadmap

These are ideas, not promises. Priorities change with feedback. To discuss one, open a [feature request](https://github.com/djunekz/zorabuilder/issues/new?template=feature_request.yml) or comment on an existing issue.

## Under consideration

| Idea | Why |
| ---- | --- |
| `--ascii` output mode | Replace Unicode status symbols (`ℹ ✓ ⚠ ✗ ⟳ ◈`) and box-drawing separators with plain ASCII for screen readers and limited fonts. See [ACCESSIBILITY.md](../ACCESSIBILITY.md). |
| Load the bundle from memory | Use `memfd_create` where available so no temp file is needed, removing the leftover-file problem on `SIGKILL`. |
| Correct `__file__` and `__spec__` | Make `__file__` point to a meaningful location so more scripts work unchanged. |
| Bundle data files | Optional inclusion of non-Python files (`--data PATTERN`) accessible at runtime. |
| `--quiet` | Print only warnings and errors. |
| Better scanning of dynamic imports | Recognize common patterns such as `importlib.import_module("literal")`. |
| Dependency check mode | `--check` to scan and report what would be bundled, without compiling. |
| Configuration file | Read defaults from `zora.toml` or `pyproject.toml`. |
| Shell completions | bash, zsh and fish completion scripts. |
| Man page | `zorabuilder(1)`. |
| Termux package | Distribution through a Termux package repository. |

## Exploring

- Support for scripts with compiled dependencies (needs a different approach to bundling extension modules)
- Reproducible final binaries across identical toolchains
- Optional payload integrity check at startup (hash verified before running)
- Optional payload encryption. This would raise the bar for casual inspection but cannot provide real secrecy, because the key must be in the binary. Documentation would have to be very explicit.

## Non-goals

- **Replacing full-featured packagers.** The project stays small and focused on simple scripts in Termux-like environments.
- **Windows and macOS executables.** The output is ELF.
- **Cross-compilation.** Build where you run.
- **Runtime dependencies in the builder.** The builder stays standard-library only.
- **Telemetry of any kind.**

## Recently done

See [CHANGELOG.md](../CHANGELOG.md).
