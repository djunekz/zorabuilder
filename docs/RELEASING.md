# Releasing

Maintainer guide. Releases follow [Semantic Versioning](https://semver.org): `MAJOR.MINOR.PATCH`.

| Bump | When |
| ---- | ---- |
| PATCH | Bug fixes, documentation, internal changes with no user-visible behavior change |
| MINOR | New options or features that are backward compatible; behavior fixes that change output in minor ways |
| MAJOR | Removed or renamed options, changed exit codes, changed runtime behavior of built binaries |

## Single source of truth

The version lives in one place: `VERSION` in `core/cli.py`. `pyproject.toml` reads it, and the release workflow checks that the git tag matches it.

## One-time repository setup

Some workflows need GitHub features that are switched off by default. Enable them once under **Settings**:

| Setting | Where | Needed by |
| ------- | ----- | --------- |
| Dependency graph | Settings, Advanced Security (or Code security), Dependency graph | `dependency-review.yml`; without it the job fails with "Dependency review is not supported on this repository" |
| Dependabot alerts | Same page | Security updates, and the PRs from `dependabot.yml` |
| Private vulnerability reporting | Same page | The report link in [SECURITY.md](../SECURITY.md) |
| Code scanning | Same page; CodeQL uploads results by itself | `codeql.yml` |
| Actions: read and write permissions for releases | Settings, Actions, General, Workflow permissions | `release.yml` publishes through its own `contents: write` permission, so the default read-only setting is fine; only change it if your organization overrides workflow permissions |
| Branch protection on `main` | Settings, Branches | Require the CI jobs (`Lint`, `Shell scripts`, `Tests`, `Package install`) before merging |

### If Dependency review reports "skipped"

Before it runs the review, the job asks GitHub's dependency graph API for the diff of the pull request and prints the answer. If GitHub does not answer with HTTP 200, the review is skipped and the job ends with a warning annotation that names the HTTP status and GitHub's message, instead of failing the pull request.

Open the job, read the annotation, and use this table:

| Annotation says | Usually means | What to do |
| --------------- | ------------- | ---------- |
| `HTTP 403` and "Resource not accessible by integration" | The workflow token is not allowed to read the dependency graph; common for runs started by Dependabot | Check the job's `permissions`; try the same check on a pull request opened by a person |
| `HTTP 403` with another message | Dependency graph is switched off | Open `https://github.com/djunekz/zorabuilder/settings/security_analysis`, enable **Dependency graph**, then re-run |
| `HTTP 404` | The graph has not finished indexing the commits | Wait a few minutes and re-run |
| `HTTP 000` | The runner could not reach `api.github.com` | Re-run |

When the status is 200, the real review runs and fails the pull request on findings of moderate severity or higher.

## Checklist

1. **Make sure `main` is green.** CI passes, and the end-to-end tests ran (not skipped).
2. **Run the device check** on a real Android device in Termux: `./scripts/termux-check.sh` (see [TESTING.md](TESTING.md#device-check-termux-and-linux)).
3. **Choose the version** using the table above.
4. **Update `VERSION`** in `core/cli.py`.
5. **Update `CHANGELOG.md`:** rename the `[Unreleased]` content into a new section and add a fresh empty `[Unreleased]`:

   ```markdown
   ## [Unreleased]

   ---

   ## [v2.2.0] - 2026-12-01
   ```

   The heading must be exactly `## [vX.Y.Z] - YYYY-MM-DD`. The release workflow extracts the notes by that heading.
6. **Commit:** `git commit -am "chore(release): v2.2.0"` and open a pull request, or commit to `main` if that is the project's current practice.
7. **Tag and push:**

   ```bash
   git tag -a v2.2.0 -m "v2.2.0"
   git push origin v2.2.0
   ```

8. **Watch the Release workflow.** It checks that the tag matches `VERSION`, runs the tests, extracts the notes from the changelog, creates the source archive `zorabuilder-vX.Y.Z.tar.gz` with a matching `zorabuilder-vX.Y.Z.tar.gz.sha256sum`, and publishes a GitHub Release with exactly those two files. GitHub adds its own `Source code` archives and, for immutable releases, a release attestation; those cannot be removed.
9. **Verify the release page:** the title reads `ZoraBuilder vX.Y.Z`, notes look right, the two assets are attached and `sha256sum -c zorabuilder-vX.Y.Z.tar.gz.sha256sum` passes after downloading them, and `install.sh --ref v2.2.0` works on a clean machine.
10. **Announce** if appropriate.

## If the workflow fails

- *Tag does not match VERSION*: delete the tag (`git push --delete origin vX.Y.Z`, `git tag -d vX.Y.Z`), fix `VERSION`, tag again.
- *No CHANGELOG section found*: fix the heading, then re-run the workflow manually from the Actions tab and give it the tag.
- *Tests failed*: fix forward in a new patch release rather than moving a published tag.

## Hotfixes

For a security or critical bug: branch from the last release tag, apply the fix, bump PATCH, update the changelog, and tag. Merge the fix back into `main`. Coordinate disclosure per [SECURITY.md](../SECURITY.md).

## Yanking

If a release is seriously broken, edit the GitHub Release to mark it clearly, publish a fixed version quickly, and note the problem in the changelog. Do not delete or move tags that people may have pinned.

## Supported versions

Only the latest minor version receives security fixes. Update the table in [SECURITY.md](../SECURITY.md) when a new minor version is released.
