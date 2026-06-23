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
<https://raw.githubusercontent.com/AIBIO-UK/airbds-metric/main/skills/versions.json>.

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
[`metric-update-propagation` skill](../../metric/skills/SKILL.md) walks through
updating `versions.json` alongside every other coupled file; `versions.json`
is also listed in the Coupled File Groups manifest in
[`metric/README.md`](../../metric/README.md).

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
