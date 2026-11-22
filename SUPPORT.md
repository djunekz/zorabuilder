# Getting Support

Thanks for using ZORA Builder. This page helps you find the fastest way to an answer.

## 1. Check the docs first

| Problem                                              | Read                                               |
| ---------------------------------------------------- | -------------------------------------------------- |
| How do I build my script?                             | [README](README.md), [docs/USAGE.md](docs/USAGE.md) |
| The build fails, or the binary does not start         | [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |
| Can ZORA Builder do X? Why does it behave like Y?     | [docs/FAQ.md](docs/FAQ.md)                         |
| How does it work internally?                          | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)       |
| What changed in a version?                            | [CHANGELOG.md](CHANGELOG.md)                       |

## 2. Ask or report

| You have...                          | Open                                                                                      |
| ------------------------------------ | ----------------------------------------------------------------------------------------- |
| A bug                                | [Bug report](https://github.com/djunekz/zorabuilder/issues/new?template=bug_report.yml)    |
| A compiler or linker error           | [Build failure](https://github.com/djunekz/zorabuilder/issues/new?template=build_failure.yml) |
| An idea                              | [Feature request](https://github.com/djunekz/zorabuilder/issues/new?template=feature_request.yml) |
| A docs problem                       | [Documentation](https://github.com/djunekz/zorabuilder/issues/new?template=documentation.yml) |
| A security vulnerability             | [Private report](https://github.com/djunekz/zorabuilder/security/advisories/new). See [SECURITY.md](SECURITY.md) |
| A conduct concern                    | Email **gab288.gab288@passinbox.com**. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) |

## 3. Write a good report

The quickest fixes come from reports that include:

- The output of `zorabuilder --version`, `python3 --version` and `uname -m`
- Your platform: Termux (and Android version), Debian, Ubuntu, other
- The exact command you ran
- The **full** terminal output, as text rather than a cropped screenshot
- The smallest script that reproduces the problem
- What you expected to happen

Run with `--verbose` when the problem is about missing modules, and `--keep-c` if a maintainer asks for the generated C source.

## What support covers

ZORA Builder is maintained by volunteers in their spare time. Maintainers can help with problems in ZORA Builder itself. They cannot debug your application, third-party packages you bundle, or your Android/Termux setup in general. Response times vary; please be patient and kind (see the [Code of Conduct](CODE_OF_CONDUCT.md)).

## Contributing a fix

Found the cause already? A pull request is the fastest route. See [CONTRIBUTING.md](CONTRIBUTING.md).
