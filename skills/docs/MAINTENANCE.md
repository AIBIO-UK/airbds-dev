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

> **Why `airbds-dev` and not the publication repo?** The `testing` and
> `development` channels are development artifacts: the build workflows in this
> repo publish their zips as releases *here*, so the manifest and the
> `skill_update_url`s must point here too.
>
> These URLs once pointed at `airbds-metric`, which worked only while that was
> this repo's name. This repo was renamed to `airbds-dev`, a new placeholder repo
> was created at the vacated `airbds-metric` name, and that severed GitHub's
> rename redirect and left the update check returning 404.
>
> That placeholder has since been renamed again, to `AIBIO-UK/airbds-core`, which
> is now the publication repo. Two consequences are worth knowing before you
> touch any URL here:
>
> - `AIBIO-UK/airbds-metric` now **301s to `airbds-core`** — so a surviving old
>   link lands on the publication repo, not on this one.
> - Freeing the `airbds-metric` name did **not** restore this repo's original
>   rename redirect. It was verified still broken immediately after the rename:
>   `raw.githubusercontent.com/AIBIO-UK/airbds-metric/main/skills/versions.json`
>   returns 404. Severed redirects do not come back; do not plan around one.
>
> A future *released* channel is expected to be served from `airbds-core`.
> **Do not repoint these URLs until that repo actually hosts a `versions.json`
> and the corresponding releases** — a redirect resolving is not the same as the
> file being there, and the update check breaks again if it isn't. Note that the
> URL is baked into each published skill zip, so a stranded skill cannot be
> repaired retroactively — only reinstallation picks up a new URL.

Each entry under `channels` records, for that channel's current skill:

- `metric_version` — the AIRBDS metric version it assesses against;
- `skill_version` — its skill version;
- `skill_update_url` — where a user gets the latest build.

## How the runtime update check works

At start-up an assessment skill makes a **best-effort** fetch of this manifest
and compares the manifest's `metric_version` for **its own channel only**
against its own metric version — the `schema_version` field of its bundled
metric file (`assets/airbds_metric.json`):

- If the manifest is **strictly newer**, the skill pauses and **asks the user**
  whether to proceed with the older bundled metric or stop and update to the
  newer skill first — it does not start the assessment until they choose.
- If the fetch **fails** (no network, unsupported, error, timeout) it is
  silently skipped — a failed fetch never blocks an assessment.
- A skill never looks at other channels, so a `testing` skill is **not** nudged
  when `development` moves ahead.

For this to work, each skill declares its channel in its `SKILL.md` frontmatter
and bundles the metric file whose `schema_version` is the version it assesses
against. Keep the manifest's `metric_version` for a channel in step with that
bundled `schema_version`. Neither channel's skill carries a `metric_version`
frontmatter field any more — both derive their metric version from the bundled
`schema_version`.

The channel and skill version live **under `metadata`** —
`metadata.channel`, `metadata.version`. The Agent Skills specification defines a
closed set of top-level frontmatter fields (`name`, `description`, `license`,
`compatibility`, `metadata`, `allowed-tools`) and `metadata` is the mapping
provided for everything else, so a conformant client is entitled to reject a
skill that puts its own keys at the top level. `channel` is read by the skill
itself for the update check, so a client that dropped it would break that check
silently. Validate with the reference library before publishing:

```bash
pip install skills-ref   # provides the `agentskills` command
agentskills validate skills/development/airbds-assessment-skill
```

Note it parses frontmatter with StrictYAML, which is stricter than YAML proper:
inline flow style (`tags: [science]`) is rejected, so use block sequences.

**`metadata.hermes` is deliberately non-conformant — leave it nested.** The spec
describes `metadata` as a map of string keys to *string* values, so a strict
reader flattens the nested block to a string (`agentskills read-properties`
returns `"{'tags': ['science'], 'category': 'science'}"` — a Python repr, not
even valid JSON). It is kept nested because that is the shape Hermes' own skill
files use, and Hermes reads it with an ordinary YAML parser, which yields the
structure intended. Flattening to `hermes-tags` / `hermes-category` would be
spec-clean but would stop matching what Hermes expects. Revisit only if Hermes
documents a different layout.

Both channels follow this layout.

## Keeping the manifest in step

Bump a channel's `metric_version` in `versions.json` **only when that channel's
skill is actually repointed to a new metric** — i.e. when you repoint the skill's
bundled `assets/airbds_metric.json` symlink at a new `metric/airbds_metric_v*.json`
(so its `schema_version` changes). Leave a channel untouched if it intentionally
stays on the older metric. A stale entry will either suppress a needed update
prompt or nag users who are already current.

When a metric version bump is the trigger, follow the Coupled File Groups
manifest in [`metric/README.md`](../../metric/README.md), which lists
`versions.json` alongside every other coupled file.

Record every skill version bump — and every channel promotion — under the
**Assessment skill** section of [`CHANGELOG.md`](../../CHANGELOG.md), with a
heading naming the version and the channel(s) it applies to. Skill versions are
tracked separately from metric versions there, because the two move
independently.

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
