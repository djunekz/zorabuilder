# Governance

ZORA Builder is a small project with a simple governance model. This document says how decisions are made so contributors know what to expect.

## Roles

**Maintainer.** Currently [@djunekz](https://github.com/djunekz) (gab288.gab288@passinbox.com). Maintainers review and merge pull requests, triage issues, cut releases, enforce the [Code of Conduct](CODE_OF_CONDUCT.md), and have the final say on direction.

**Contributor.** Anyone who opens an issue, comments, improves docs or submits code. No special permission is needed.

**Collaborator.** A contributor who has been invited to help with triage and review, with write access. Collaborators are invited by maintainers after a track record of constructive, reliable contributions.

## How decisions are made

- **Small changes** (bug fixes, docs, tests) are merged by a maintainer after review and green CI.
- **Larger changes** (new flags, changes to runtime behavior, anything that alters exit codes or output formats) are discussed in an issue first. Maintainers look for rough consensus; when there is no consensus, the maintainer decides.
- **Breaking changes** are avoided. When unavoidable they ship in a major version, are labeled `breaking`, and are described in the changelog with a migration note.
- **Security fixes** may be developed privately and released before they are discussed publicly. See [SECURITY.md](SECURITY.md).

## Project principles

These guide the trade-offs we make:

1. **Zero runtime dependencies.** The builder uses only the Python standard library.
2. **Honest about limits.** Documentation states what the tool cannot do (see the limitations in the README and FAQ).
3. **Predictable output.** Stable exit codes, stderr for problems, deterministic bundles.
4. **Works on a phone.** Termux on Android is the primary target; narrow screens and slow storage matter.
5. **Small and readable.** A new contributor should be able to understand the whole code base in an afternoon.

## Versioning and releases

The project follows [Semantic Versioning](https://semver.org). The process is in [docs/RELEASING.md](docs/RELEASING.md).

## Becoming a collaborator

Contribute regularly, review other people's work thoughtfully, follow the Code of Conduct, and say you are interested. A maintainer will invite you.

## Changing this document

Open a pull request. Governance changes need the maintainer's approval.
