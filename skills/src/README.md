# `skills/src/` — skill tooling

Tooling that serves the assessment skills in [`skills/`](../), beside the skills
it serves — as [`metric/src/`](../../metric/src/) and
[`reviews/src/`](../../reviews/src/) do for theirs.

All commands run from the repo root.

## Validating the update manifest

`scripts/validate_skills_versions.py` checks
[`skills/versions.json`](../versions.json), the per-channel manifest the
published skills fetch at runtime to tell a user when a newer skill is available
for their channel.

```bash
python3 skills/src/scripts/validate_skills_versions.py
```

It confirms the manifest is valid JSON with a non-empty `channels` map, that each
channel carries non-empty `metric_version`, `skill_version`, and
`skill_update_url` fields, and that every advertised `metric_version` has a
matching `metric/airbds_metric_v<version>.yaml`. It exits 0 when valid, or 1
listing every problem found.

A stale manifest fails silently in the worst way — it either suppresses an update
prompt users need or nags users who are already current — so it is also checked
in CI by
[`validate-skills-versions.yml`](../../.github/workflows/validate-skills-versions.yml),
which runs this same script whenever the manifest, the metric YAMLs, or the
script itself change.

Needs only the Python 3 standard library.

## Publishing the skill to `airbds-core` (the push to production)

`scripts/release_skill_to_core.sh` promotes the **testing** channel's skill zip
to the publication repository, [AIBIO-UK/airbds-core][core], as
`skill/airbds-assessment-skill.zip`, on a release branch with a pull request left
open for review.

```bash
./skills/src/scripts/release_skill_to_core.sh --dry-run   # rehearse
./skills/src/scripts/release_skill_to_core.sh             # branch, push, PR
```

**It promotes, it does not rebuild.** The zip is downloaded from this repo's
`assessment-skill-testing` release — the artifact the build workflow produced and
that people have actually been testing — so what ships is byte-for-byte what was
tested. Rebuilding locally would risk a different zip (symlink dereferencing,
file ordering, a dirty working tree) reaching production under the same version
number. The download is checked against the digest GitHub recorded at upload, and
the PR body carries the sha256 so a reviewer can confirm it against the release.

Before publishing, it reads `SKILL.md` out of the zip and refuses to proceed if:

- the bundle is not from the `testing` channel, or
- its `metadata.version` disagrees with the `testing` entry in
  [`versions.json`](../versions.json).

That second check matters because `versions.json` is what installed skills poll:
publishing a zip the manifest does not advertise ships users a version nothing
announces. A mismatch usually means the manifest was not bumped alongside the
skill, or the release predates the bump — check both before reaching for
`--force`.

| Option | Effect |
|---|---|
| `--dry-run` | Commit locally only; no push, no PR |
| `--zip <file>` | Publish a local zip instead of downloading the release (skips the digest check) |
| `--branch <name>` | Release branch name (default `release/skill-v<version>`) |
| `--force` | Publish despite a manifest disagreement |
| `--draft` | Open the pull request as a draft |

Like the metric release it never merges and never tags. The published filename
carries neither channel nor version, so a tag or GitHub release in `airbds-core`
is what downstream consumers pin to.

Offline tests drive the script against a throwaway local repository with a
stubbed `gh` and a synthesised zip, so they neither reach the network nor touch
the real publication repository:

```bash
python3 skills/src/tests/test_release_skill_to_core.py   # or: pytest skills/src/tests/
```

> Both this and the metric release share one engine,
> [`scripts/publish-to-core.sh`](../../scripts/publish-to-core.sh), which owns the
> clone/branch/commit/push/PR mechanics. Options it takes (`--base`, `--repo`,
> `--remote`) are forwarded from here.

> The skill **build** pipeline is not here: each channel is packaged by its own
> workflow under [`.github/workflows/`](../../.github/workflows/). See
> [`skills/docs/MAINTENANCE.md`](../docs/MAINTENANCE.md) for channels, the
> version manifest, and release builds, and
> [`skills/docs/DESIGN.md`](../docs/DESIGN.md) for how a skill bundle is put
> together.

[core]: https://github.com/AIBIO-UK/airbds-core
