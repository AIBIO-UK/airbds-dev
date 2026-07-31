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

> The skill **build** pipeline is not here: each channel is packaged by its own
> workflow under [`.github/workflows/`](../../.github/workflows/). See
> [`skills/docs/MAINTENANCE.md`](../docs/MAINTENANCE.md) for channels, the
> version manifest, and release builds, and
> [`skills/docs/DESIGN.md`](../docs/DESIGN.md) for how a skill bundle is put
> together.
