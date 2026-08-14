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
python3 skills/src/scripts/validate_skills_versions.py --since HEAD
```

It confirms the manifest is valid JSON with a non-empty `channels` map, that each
channel carries non-empty `metric_version`, `skill_version`, and
`skill_update_url` fields, and that every advertised `metric_version` has a
matching `metric/airbds_metric_v<version>.yaml`. It exits 0 when valid, or 1
listing every problem found.

The manifest restates facts the bundles already carry, and both copies are
hand-maintained, so the rest of the checks are cross-checks. For each channel
with a source directory here — `development` and `testing`; `production` has none
— it compares:

| Manifest field | Against |
|---|---|
| `skill_version` | that channel's `SKILL.md` `metadata.version` |
| `metric_version` | the `schema_version` of the metric `assets/airbds_metric.json` resolves to |
| *(channel identity)* | `SKILL.md` `metadata.channel` vs the directory it sits in |

The middle row is the one that matters most: it means a symlink repointed at a
new metric without a manifest bump — or a manifest bump without the repoint —
fails instead of publishing a skill that misreports the metric it scored against.

With `--since <git-ref>` it additionally enforces that a channel whose
`metric_version` changed has had its `skill_version` raised by at least a MINOR.
See [`skills/docs/MAINTENANCE.md`](../docs/MAINTENANCE.md#keeping-the-manifest-in-step)
for that rule.

A stale manifest fails silently in the worst way — it either suppresses an update
prompt users need or nags users who are already current — so all of this is also
checked in CI by
[`validate-skills-versions.yml`](../../.github/workflows/validate-skills-versions.yml),
which runs this same script whenever the manifest, a skill bundle, the metric
YAMLs, or the script itself change. CI resolves the `--since` ref itself and
falls back to the stateless checks when there is no usable baseline.

Needs only the Python 3 standard library. Tested in
[`src/tests/test_validate_skills_versions.py`](tests/test_validate_skills_versions.py)
(14 tests).

## Promoting a channel (`development` → `testing`)

`scripts/promote_skill_channel.py` takes one channel's bundle and makes another
channel a copy of it — by default `development` → `testing`. A bundle carries its
channel inside it (`metadata.channel` and the update-check prose), so this is not
a plain copy: it substitutes the channel token, keeps the symlinked metric and
template as symlinks, and moves the target channel's `skills/versions.json` entry
to describe what was promoted.

```bash
python3 skills/src/scripts/promote_skill_channel.py --dry-run   # rehearse
python3 skills/src/scripts/promote_skill_channel.py             # do it
python3 skills/src/scripts/promote_skill_channel.py --check     # already promoted?
```

The token substitution reuses `rechannel_skill_zip.rewrite_text`, so it carries
the same reversibility proof as the production channel rewrite — only the channel
changed. It writes the working tree and stops: review, run
`validate_skills_versions.py`, and commit yourself; pushing to `main` rebuilds the
target channel's release. `--from`/`--to` override the default pair.

Needs only the Python 3 standard library. Tested in
[`src/tests/test_promote_skill_channel.py`](tests/test_promote_skill_channel.py)
(13 tests). See [`skills/docs/MAINTENANCE.md`](../docs/MAINTENANCE.md#promoting-development-to-testing).

## Publishing the skill to `airbds-core` (the push to production)

`scripts/release_skill_to_core.sh` promotes the **testing** channel's skill zip
to the publication repository, [AIBIO-UK/airbds-core][core], as
`skills/airbds-assessment-skill.zip`, on a release branch with a pull request left
open for review.

```bash
./skills/src/scripts/release_skill_to_core.sh --dry-run   # rehearse
./skills/src/scripts/release_skill_to_core.sh             # branch, push, PR
```

**It promotes, it does not rebuild.** The zip is downloaded from this repo's
`assessment-skill-testing` release — the artifact the build workflow produced and
that people have actually been testing. Rebuilding locally would risk a different
zip (symlink dereferencing, file ordering, a dirty working tree) reaching
production under the same version number. The download is checked against the
digest GitHub recorded at upload.

**One thing does change: the release channel.** A bundle carries its channel
inside it, so shipping the tested bytes untouched marks production users as
`testing` — the bug the current `airbds-core` zip has. So the promotion runs the
artifact through [`scripts/rechannel_skill_zip.py`](#rewriting-a-bundles-channel),
which substitutes the channel token in `SKILL.md`, copies everything else
verbatim, and verifies that is all it did. The PR body carries both the source
and published sha256s, and the `--check` command a reviewer can run to confirm
the published zip really is the tested one modulo the channel.

Before publishing, it reads `SKILL.md` out of the zip and refuses to proceed if:

- the bundle is not from the `testing` channel;
- its `metadata.version` disagrees with the **`production`** entry in
  [`versions.json`](../versions.json); or
- the channel rewrite cannot be verified.

The second check matters because `versions.json` is what installed skills poll:
publishing a zip the manifest does not advertise ships users a version nothing
announces. The `production` entry is the one that governs, since that is what an
installed production skill reads. A mismatch usually means it was not bumped
before promoting — do that first, and check the release is current, before
reaching for `--force`.

**The prose ships with the bytes.** `airbds-core`'s `skills/README.md` quotes the
skill and metric versions it is serving, and the same commit restamps them via
[`scripts/stamp_core_versions.py`](../../scripts/stamp_core_versions.py) — those
numbers are part of the release, not a follow-up someone has to remember. They
live inside HTML comment markers (`<!--skill-version-->0.8.0<!--/skill-version-->`),
which render as nothing, so the page reads unchanged and only the source carries
the machinery. A README missing its markers fails the release rather than
publishing a stale sentence; a stale README with an unchanged zip is still a
release. See [MAINTENANCE.md](../docs/MAINTENANCE.md#the-readme-stamp).

| Option | Effect |
|---|---|
| `--dry-run` | Commit locally only; no push, no PR |
| `--zip <file>` | Publish a local zip instead of downloading the release (skips the digest check) |
| `--branch <name>` | Release branch name (default `release/skill-v<version>`) |
| `--force` | Publish despite a manifest disagreement. Never overrides a failed channel rewrite — that would publish an unprovable artifact |
| `--draft` | Open the pull request as a draft |

Like the metric release it never merges and never tags. The published filename
carries neither channel nor version: `airbds-core` holds the current production
skill, and an installed skill tracks its channel through
[`skills/versions.json`](../versions.json) rather than pinning a build.

Offline tests drive the script against a throwaway local repository with a
stubbed `gh` and a synthesised zip, so they neither reach the network nor touch
the real publication repository:

```bash
python3 skills/src/tests/test_release_skill_to_core.py   # or: pytest skills/src/tests/
python3 scripts/tests/test_stamp_core_versions.py        # the README stamper
```

## Rewriting a bundle's channel

`scripts/rechannel_skill_zip.py` turns the tested `testing` bundle into the
`production` one, and — more to the point — proves that is all it did. The
release script calls it; you rarely run it directly except to audit a published
zip.

```bash
# derive production from a tested bundle
skills/src/scripts/rechannel_skill_zip.py \
  --in airbds-assessment-skill-testing.zip --out airbds-assessment-skill.zip

# check an already-published bundle really is that derivation
skills/src/scripts/rechannel_skill_zip.py \
  --in airbds-assessment-skill-testing.zip --check airbds-assessment-skill.zip
```

It substitutes the channel token in `SKILL.md` — the `metadata.channel`
frontmatter field and the prose naming which `channels.<name>` entry of the
update manifest is the skill's own — and copies every other member across
unchanged: same names, same order, same modification times, same permissions,
same bytes. Both modes then verify the result:

- undoing the substitution must reproduce the source `SKILL.md` byte for byte, so
  the change is provably nothing but the channel;
- no member other than `SKILL.md` may differ, in content or in metadata;
- the result must not still mention the old channel — that would mean the zip
  was published unrewritten, the failure this whole step exists to prevent.

It refuses when the source already mentions the target channel anywhere in
`SKILL.md`, since a substitution that cannot be undone cannot be checked. Reword
the mention, rebuild the `testing` release, and promote again. `--from` and
`--to` default to `testing` and `production`.

```bash
python3 skills/src/tests/test_rechannel_skill_zip.py   # or: pytest skills/src/tests/
```

Needs only the Python 3 standard library.

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
