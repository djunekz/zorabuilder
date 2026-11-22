# Accessibility

ZORA Builder is a command-line tool, and it is often used on a phone, in a small terminal, over screen readers, or in logs read by other programs. We want it, and its documentation, to be usable by as many people as possible.

This document explains what we do, what is not good enough yet, and how to tell us about a barrier.

## Our commitments

- **Meaning is never carried by color alone.** Every status line starts with a symbol and is written as plain words (`✓ Build successful`, `⚠ ...`, `✗ ...`).
- **Color is optional.** Color turns off automatically when output is not a terminal (pipes, files, CI logs) and when the `NO_COLOR` environment variable is set.
- **The decorative banner is optional.** The ASCII-art banner can be replaced by a single plain line.
- **Errors are text, on the right stream.** Warnings and errors go to stderr, results go to stdout, and exit codes are meaningful, so scripts and assistive tools can tell them apart.
- **No time-based or interactive prompts during a build.** Nothing waits for a keypress, nothing animates, and nothing depends on reading a spinner. The only prompt in the project is the confirmation in `uninstall.sh`, which `--yes` skips.
- **Output adapts to the terminal width.** The help text wraps to the terminal width, and the banner fits in about 42 columns, so it works on narrow phone terminals.
- **Messages are complete sentences with the fix included**, for example `Output would overwrite the input script: app.py`, rather than codes that need a lookup.
- **Documentation is written to be readable**: a logical heading order, descriptive link text, tables with header rows, code in fenced blocks with a language, and no information conveyed only by an image.

## Using ZORA Builder with assistive technology

| You want to...                                  | Do this                                                    |
| ----------------------------------------------- | ---------------------------------------------------------- |
| Turn off all colors                             | `export NO_COLOR=1`                                        |
| Replace the ASCII banner with one plain line    | `zorabuilder --no-banner ...` or `export ZORA_NO_BANNER=1` |
| Get machine-readable results                    | `--json-report build.json`                                 |
| Keep the build output short                     | Redirect stdout; read stderr for problems only             |
| Read the help without the banner                | `zorabuilder --no-banner --help`                           |

Tip for screen reader users: set both variables once in your shell profile.

```bash
export NO_COLOR=1
export ZORA_NO_BANNER=1
```

## Known limitations

We prefer to be honest about what does not work well yet.

- **Unicode symbols.** Status lines use `ℹ ✓ ⚠ ✗ ⟳ ◈`. Some screen readers read them oddly, and some fonts show them as empty boxes. There is no ASCII-only mode yet. It is on the [roadmap](docs/ROADMAP.md).
- **ASCII-art banner.** Screen readers read it as noise. Use `--no-banner`.
- **Box-drawing rules.** The report uses `━` lines as separators, which can be verbose when read aloud.
- **English only.** All messages and documentation are in English.
- **Terminal-dependent rendering.** We cannot control fonts, contrast or zoom; these come from your terminal. Colors are chosen to work on dark backgrounds, which is the usual case in Termux. Use `NO_COLOR` if contrast is a problem.

## Documentation conventions

When you write docs for this project:

- Use one `#` heading per file, and do not skip heading levels.
- Use meaningful link text (`see the troubleshooting guide`, not `click here`).
- Give code blocks a language (`bash`, `python`, `text`).
- Prefer text and tables over screenshots. If you must use an image, add alt text that conveys the same information.
- Write short sentences and define abbreviations the first time you use them.
- Do not use color or emoji as the only way to mark something important.

## Reporting a barrier

If something in ZORA Builder, its output, or its documentation is hard to use for you, please tell us. Open a [documentation issue](https://github.com/djunekz/zorabuilder/issues/new?template=documentation.yml) and choose **Accessibility**, or a [bug report](https://github.com/djunekz/zorabuilder/issues/new?template=bug_report.yml) for tool behavior. Tell us:

- What you were trying to do
- What got in the way (and which assistive technology or terminal you use, if you are comfortable sharing)
- What would have helped

Accessibility reports are treated as bugs, not as feature requests.
