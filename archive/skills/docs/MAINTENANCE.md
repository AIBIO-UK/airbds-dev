# Maintaining the AIRBDS assessment skills

> **⚠️ Archived.** The assessment skills, this manifest, and their build
> workflows have all moved from `skills/` / `.github/workflows/` to
> `archive/skills/` — not deleted, just no longer live. The build workflows
> below do not run (they're out of `.github/workflows/`), and the runtime
> update-check URL is stale until reactivated. See root
> [`README.md`](../../../README.md) for current repo structure.

This document is for **maintainers** of the assessment skills. People who only
want to *use* a skill need none of this — see [`../README.md`](../README.md).

## Release channels

The assessment skill is developed in channels, one directory each:

- `development/` — the working copy under active development.
- `testing/` — the copy promoted to a testing release.

There are no production skills yet. Each channel evolves independently: `testing`
may sit on an older AIRBDS metric version while `development` has moved ahead.

## The version manifest (`versions.json`)

`versions.json` (in this folder's parent, `archive/skills/versions.json`) is the
source of truth for the **current** assessment skill on each channel. When live,
it was served over GitHub raw at
`raw.githubusercontent.com/AIBIO-UK/airbds-metric/main/skills/versions.json` —
that URL is now stale (the file no longer lives at that path) until reactivated.

Each entry under `channels` records, for that channel's current skill:

- `metric_version` — the AIRBDS metric version it assesses against;
- `skill_version` — its skill version;
- `skill_update_url` — where a user gets the latest build.

## How the runtime update check works

At start-up an assessment skill makes a **best-effort** fetch of this manifest
and compares the manifest's `metric_version` for **its own channel only**
against the `metric_version` declared in its own frontmatter:

- If the manifest is **strictly newer**, the skill pauses and **asks the user**
  whether to proceed with the older bundled metric or stop and update to the
  newer skill first — it does not start the assessment until they choose.
- If the fetch **fails** (no network, unsupported, error, timeout) it is
  silently skipped — a failed fetch never blocks an assessment.
- A skill never looks at other channels, so a `testing` skill is **not** nudged
  when `development` moves ahead.

For this to work, each skill declares `metric_version` and `channel` in its
`SKILL.md` frontmatter. Keep those in step with the manifest.

## Keeping the manifest in step

Bump a channel's `metric_version` in `versions.json` **only when that channel's
skill is actually repointed to a new metric** — i.e. when you update the skill's
bundled `templates/airbds_metric_v*.yaml` and its `metric_version` frontmatter.
Leave a channel untouched if it intentionally stays on the older metric. A stale
entry will either suppress a needed update prompt or nag users who are already
current.

When a metric version bump is the trigger, the
[`metric-update-propagation` skill](../metric/skills/SKILL.md) (also archived,
alongside this one) walks through updating `versions.json` alongside every
other coupled file; `versions.json` is also listed in the Coupled File Groups
manifest in [`metric/README.md`](../../../metric/README.md) (the live, current
metric folder — not archived).

## Release builds (GitHub Actions) — archived, do not currently run

Each channel's downloadable skill zip used to be built and published by a
GitHub Actions workflow; both are archived at `archive/skills/workflows/` and
no longer execute (moving a workflow file out of `.github/workflows/` is what
disables it):

- `testing` → [`build-assessment-skill-for-test.yml`](../workflows/build-assessment-skill-for-test.yml)
  (release tag `assessment-skill-testing`, asset `airbds-assessment-skill.zip`).
- `development` → [`build-assessment-skill-for-development.yml`](../workflows/build-assessment-skill-for-development.yml)
  (release tag `assessment-skill-development`, asset `airbds-assessment-skill-dev.zip`).

Each pushed on `main`, zipped its channel's skill directory (dereferencing the
symlinked metric/template into real files), and recreated its release so the
`skill_update_url` in `versions.json` always served the latest build.

**These workflows are coupled to the skill directory structure — keep them in
step when it changes, if reactivated.** In particular, if you rename or
restructure a skill's bundle directory (e.g. the `templates/` → `assets/`
move), update, for the affected channel's workflow:

- the `on.push.paths` filter (so the right files actually trigger a rebuild — a
  stale path silently stops builds firing), and
- the `zip` step and its comment (so the new structure is what gets packaged).

To reactivate, move the relevant workflow file(s) back into `.github/workflows/`
— they only take effect once merged to the default branch, since Actions runs
the version of the workflow on `main`. Both build workflows also support
`workflow_dispatch`, so a rebuild can be triggered manually from the Actions
tab without a code change, once reactivated.

## Validation

`versions.json` used to be checked in CI by the `validate-skills-versions`
workflow (also archived, at
[`../workflows/validate-skills-versions.yml`](../workflows/validate-skills-versions.yml)),
which runs [`validate-skills-versions.py`](../scripts/validate-skills-versions.py).
It confirms the manifest is valid JSON, every channel has the required fields,
and every advertised `metric_version` has a matching
`metric/airbds_metric_v<version>.yaml`. Run it locally before committing a
manifest change:

```
python3 archive/skills/scripts/validate-skills-versions.py
```
