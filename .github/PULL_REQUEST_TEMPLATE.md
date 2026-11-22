## Summary

<!-- What does this PR change, and why? Link the issue it closes: "Closes #123". -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Refactor (no behavior change)
- [ ] Documentation
- [ ] CI / tooling

## How was it tested?

- [ ] `python -m unittest discover -s tests -t . -v` passes locally
- [ ] I added or updated tests for the change
- [ ] I built and ran a real binary when the change touches the C loader, the compiler step or the bundler

Details (commands, platform, Python version):

## Checklist

- [ ] `ruff check .` is clean
- [ ] The CHANGELOG.md `[Unreleased]` section is updated
- [ ] User-facing docs are updated (README.md, docs/)
- [ ] No code comments or docstrings were added (see CONTRIBUTING.md)
- [ ] Shell scripts still pass `bash -n` and `shellcheck` (if touched)
- [ ] `./scripts/termux-check.sh` passes when the change affects builds, the loader or the installer

## Breaking changes

<!-- Describe any change in CLI flags, exit codes, output format or runtime behavior. Write "None" if there are none. -->
