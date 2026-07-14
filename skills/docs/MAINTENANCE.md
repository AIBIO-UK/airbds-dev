# Maintaining the AIRBDS assessment skills

This document is for **maintainers** of the assessment skills. People who only
want to *use* a skill need none of this — see [`../README.md`](../README.md).

## Release channels

The assessment skill is developed in channels, one directory each:

- `development/` — the working copy under active development.
- `testing/` — the copy promoted to a testing release.

There are no production skills yet. Each channel evolves independently: `testing`
may sit on an older AIRBDS metric version while `development` has moved ahead.

## The version manifest (`versions.json`)

`skills/versions.json` is the source of truth for the **current** assessment
skill on each channel. It is served over GitHub raw at
<https://raw.githubusercontent.com/AIBIO-UK/airbds-dev/main/skills/versions.json>.

> **Why `airbds-dev` and not `airbds-metric`?** The `testing` and `development`
> channels are development artifacts: the build workflows in this repo publish
> their zips as releases *here*, so the manifest and the `skill_update_url`s must
> point here too. These URLs previously pointed at `airbds-metric`, which worked
> only while that was this repo's name — creating a new repo at the old name
> removed the rename redirect and left the update check returning 404.
>
> A future *released* channel is expected to be served from the publication repo
> (`AIBIO-UK/airbds-metric`). **Do not repoint these URLs until that repo actually
> hosts a `versions.json` and the corresponding releases**, or the update check
> breaks again. Note that the URL is baked into each published skill zip, so a
> stranded skill cannot be repaired retroactively — only reinstallation picks up
> a new URL.

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

When a metric version bump is the trigger, follow the Coupled File Groups
manifest in [`metric/README.md`](../../metric/README.md), which lists
`versions.json` alongside every other coupled file.

## Release builds (GitHub Actions)

Each channel's downloadable skill zip is built and published by a GitHub Actions
workflow:

- `testing` → [`.github/workflows/build-assessment-skill-for-test.yml`](../../.github/workflows/build-assessment-skill-for-test.yml)
  (release tag `assessment-skill-testing`, asset `airbds-assessment-skill.zip`).
- `development` → [`.github/workflows/build-assessment-skill-for-development.yml`](../../.github/workflows/build-assessment-skill-for-development.yml)
  (release tag `assessment-skill-development`, asset `airbds-assessment-skill-dev.zip`).

Each pushes on `main`, zips its channel's skill directory (dereferencing the
symlinked metric/template into real files), and recreates its release so the
`skill_update_url` in `versions.json` always serves the latest build.

**These workflows are coupled to the skill directory structure — keep them in
step when it changes.** In particular, if you rename or restructure a skill's
bundle directory (e.g. the `templates/` → `assets/` move), update, for the
affected channel's workflow:

- the `on.push.paths` filter (so the right files actually trigger a rebuild — a
  stale path silently stops builds firing), and
- the `zip` step and its comment (so the new structure is what gets packaged).

A workflow file only takes effect once it's merged to the default branch, since
Actions runs the version of the workflow on `main`. Both build workflows also
support `workflow_dispatch`, so you can trigger a rebuild manually from the
Actions tab without a code change.

## Validation

`versions.json` is checked in CI by the `validate-skills-versions` workflow,
which runs [`scripts/validate-skills-versions.py`](../../scripts/validate-skills-versions.py).
It confirms the manifest is valid JSON, every channel has the required fields,
and every advertised `metric_version` has a matching
`metric/airbds_metric_v<version>.yaml`. Run it locally before committing a
manifest change:

```
python3 scripts/validate-skills-versions.py
```
