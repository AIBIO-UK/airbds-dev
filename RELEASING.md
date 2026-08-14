# Releasing

This is the running order for getting a new AIRBDS metric — and the assessment
skill that scores against it — out of this development repository and into the
publication repository, [AIBIO-UK/airbds-core][core].

It is a **map, not a manual.** Each stage says what has to be true and points at
the document that owns the actual steps, so the commands live in one place and
this file cannot drift out of step with them. What it does own is the *order*,
and the handful of things that fall between documents — which is where releases
go wrong.

- The metric's own rules: [`metric/README.md`](metric/README.md)
- The metric build and release tooling: [`metric/src/README.md`](metric/src/README.md)
- The skill's channels, manifest, and promotion: [`skills/docs/MAINTAINING.md`](skills/docs/MAINTAINING.md)
- The versioning policy: [`metric/README.md#versioning-policy`](metric/README.md#versioning-policy)

---

## What is being released

Two independently versioned artifacts, both ending up in `airbds-core`:

```
  metric/airbds_metric_v<X.Y.Z>.{yaml,json}
        │  release_metric_to_core.sh
        ▼
  airbds-core:airbds_metric.{yaml,json}          ← unversioned filenames

  skills/testing/airbds-assessment-skill/
        │  release_skill_to_core.sh (rewrites the channel)
        ▼
  airbds-core:skills/airbds-assessment-skill.zip ← unversioned filename
```

Every published filename is **unversioned**, and **nothing in `airbds-core` is
tagged**. The two repositories answer different questions: `airbds-core` answers
*"what is the AIRBDS metric?"* and always holds the current one, while
`airbds-dev` answers *"what was v0.4?"* — every version keeps its own filename
here, and superseded versions are retained rather than deleted.

So a release **overwrites** what is published. Anything that needs to depend on a
specific version references the versioned file in this repository; the
publication repo is not the place to pin.

## The coupling: the skill always carries the current metric

**A metric release is not finished when the metric is published.** The assessment
skill bundles the metric as `assets/airbds_metric.json` and reports the version it
scored against, so the skill also always needs to be updated and release when a new metric version is released. Treat stages 1–7 as one release.

The two artifacts still have separate version numbers and separate `CHANGELOG.md`
sections — a skill release can happen without a metric release, just not the
other way round.

## Before you start: decide the bump

Settle this *first*, because it decides how much of the work below applies. The
canonical rules are the **versioning policy** at
[`metric/README.md#versioning-policy`](metric/README.md#versioning-policy).

| Bump | Means | What has to move |
|---|---|---|
| **PATCH** (`1.0.0` → `1.0.1`) | Guidance text only — no question meaning, weight, or ID changed | Stages 1–7 |
| **MINOR** (`1.0.0` → `1.1.0`) | A question added, removed, or reworded | Stages 1–7, **plus Stage 3b** |
| **MAJOR** (`1.0.0` → `2.0.0`) | A weight value or grade threshold changed | Stages 1–7, **plus Stage 3b** |

Stage 3b is the version-carrying files — the ones that quote a version number in
prose rather than consume it. Skipping it on a MINOR or MAJOR leaves the
repository advertising a version that no longer exists, and **nothing checks for
this** — no CI, no script. It is the easiest stage to skip and the least likely
to announce itself.

Write all three components: the version is `1.0.1`, never `1.0`. It is a path
component, a JSON key in `skills/versions.json`, and each review's
`schema_version` — all matched exactly.

The issue-first workflow for proposing a change is at
[`metric/README.md#proposing-a-metric-change`](metric/README.md#proposing-a-metric-change).

## What you need before Stage 1

Each of these fails partway through a release rather than up front, so check them
first:

| | Needed for | How to check |
|---|---|---|
| Edit access to the working group's **Google Sheet** | Stage 1 — the metric is authored there | open the sheet linked from [`metric/src/README.md`](metric/src/README.md) |
| `python3` with **`pyyaml`** | Stages 1, 2, 4 | `python3 -c "import yaml"` |
| **`gh`**, authenticated | Stages 4 and 7 | `gh auth status` |
| **Write access to `AIBIO-UK/airbds-core`** | Stages 4 and 7 | `gh api repos/AIBIO-UK/airbds-core --jq .permissions` |

The last one is the one that catches people. Both release scripts clone, branch,
and commit happily without it, and only fail at the push — after the work is
done, though before anything is published. `--dry-run` never needs it, which is
another reason to rehearse.

---

## Stage 1 — Generate the metric

The metric is authored in the working group's Google Sheet and **generated, never
hand-edited**. Bump `schema_version` in the sheet, then regenerate: one run writes
the YAML, the JSON, and the `.upstream.json` provenance sidecar together.

→ [`metric/src/README.md#v100--from-the-public-google-sheet`](metric/src/README.md#v100--from-the-public-google-sheet)
for the generator, its `--check` drift mode, and offline use.

Each version keeps its own generator script. A new version normally reuses the
current one; a change to the *sheet's shape* means a new generator, not an edit
to the old one.

## Stage 2 — Regenerate the review template pair

`reviews/review_template.{yaml,csv}` are derived from the metric YAML and must be
regenerated for the new version. Archive the outgoing pair to
`reviews/archived_templates/review_template_v<old>.{yaml,csv}` **before**
overwriting the live pair.

→ [`reviews/src/README.md`](reviews/src/README.md) for `build_review_template.py`
and its `--check` mode; [`reviews/archived_templates/README.md`](reviews/archived_templates/README.md)
for the archiving convention.

## Stage 3 — Changelog

A new entry at the top of the **Metric** section of
[`CHANGELOG.md`](CHANGELOG.md), referencing the originating issue. If the bump
carries no content change — as v1.0.0 did, being v0.5 under a stable number — say
so explicitly, or it is indistinguishable from a release where something was
missed.

## Stage 3b — Version-carrying files *(MINOR and MAJOR only)*

These quote the metric version in prose. Nothing consumes them, so nothing fails
when they go stale — they simply start telling readers something untrue.

- **`README.md`** — version badge, question table, download links, and the
  processor command examples.
- **`CITATION.cff`** — `version:` and `date-released:`. Published citations
  otherwise reference the wrong version.
- **`LICENSE.md`** — the version and year in the **suggested-citation block**.
  Not the copyright year, which is the year of first publication and does not
  move. Keep it consistent with `CITATION.cff` and the Citation section of
  `README.md`.
- **`metric/README.md`** — its own version references, including the question
  counts and maximum score under *How Scoring Works*.
- **`reviews/docs/tutorial-yaml.md`** and **`tutorial-csv.md`** — `vX.Y.Z` path
  references. The human review workflow is dormant, so these are lower priority
  than the rest.

The review processor needs no update: it selects
`metric/airbds_metric_v<schema_version>.yaml` per review, so older reviews stay
scorable against the metric they were scored with.

Commit stages 1–3b and push to `main`.

## Stage 4 — Publish the metric to `airbds-core`

```bash
./metric/src/scripts/release_metric_to_core.sh 1.0.1 --dry-run   # rehearse
./metric/src/scripts/release_metric_to_core.sh 1.0.1
```

Both renderings go over in one commit, as `airbds_metric.yaml` and
`airbds_metric.json`, and the same commit restamps the metric version quoted in
`airbds-core`'s `skills/README.md`. A preflight refuses the release if the local
YAML and JSON disagree.

→ [`metric/src/README.md#releasing-a-version-to-airbds-core`](metric/src/README.md#releasing-a-version-to-airbds-core)
for the options and the full behaviour.

**This opens a pull request. It does not merge it.** Review and merge it
yourself.

## Stage 5 — Get the skill onto the new metric

This stage describes a **state to reach**, not necessarily work to do. Depending
on how the change was developed, the `testing` channel skill may already be on the new metric —
it can be repointed as soon as Stage 1 has written the file, well before the
metric is published. What matters by the end of this stage is that every channel
you intend to move is consistent.

Work through the channels in order — `development`, then `testing` — skipping any
already on the new metric.

**Move `development` first, by hand.** There is no automated step feeding it from
the metric, so:

- Repoint `skills/development/airbds-assessment-skill/assets/airbds_metric.json`
  at the new `metric/airbds_metric_v<version>.json`. The skill reads its
  `schema_version` from that file and never hard-codes a version, so the symlink
  *is* the update — no change to `SKILL.md`'s body is needed.
- Bump `development`'s `metric_version` in [`skills/versions.json`](skills/versions.json).
- Bump its `skill_version` **by at least a MINOR** — in `versions.json` *and* in
  `development`'s `SKILL.md` `metadata.version`, which must agree. See the rule
  below.
- Update the bundle diagram in [`skills/docs/DESIGN.md`](skills/docs/DESIGN.md),
  which spells out the symlink target.

**Then promote `development` → `testing` with the script**, which does the symlink
repoint, the channel-token rewrite, and the `testing` manifest bump in one step:

```bash
./skills/src/scripts/promote_skill_channel.py --dry-run   # rehearse
./skills/src/scripts/promote_skill_channel.py
```

→ [`skills/docs/MAINTAINING.md#promoting-development-to-testing`](skills/docs/MAINTAINING.md#promoting-development-to-testing).

Finally, add an entry under the **Assessment skill** section of `CHANGELOG.md`,
naming the version and the channels it applies to.

### A new metric is at least a MINOR skill bump

Never a patch. The bundle's contents change and it scores against a different
metric, so a patch-level bump would advertise two materially different artifacts
under versions that look interchangeable. `0.8.1` + a new metric → `0.9.0`, not
`0.8.2`.

### Validate before committing

```bash
python3 skills/src/scripts/validate_skills_versions.py --since HEAD
```

This is the safety net for the hand-editing above. It cross-checks each
source-backed channel's manifest entry against the bundle it describes — the
`SKILL.md` version and channel, and the `schema_version` of the metric the
symlink actually resolves to — so a repointed symlink with an unbumped manifest,
or the reverse, fails rather than shipping. With `--since` it also enforces the
minor-bump rule against the manifest's previous state. CI runs the same checks on
every push and pull request touching the manifest or a skill bundle.

Bump a channel's `metric_version` **only when that channel's symlink actually
moved**. A stale entry either suppresses an update prompt users need or nags
users who are already current — the runtime check compares the manifest's
`metric_version` against the `schema_version` in the skill's own bundled metric.
A channel deliberately held on the older metric is left alone entirely.

`production` is not touched here, and is not cross-checked by the validator
either — it has no source directory in this repo. It moves in Stage 7.

→ [`skills/docs/MAINTAINING.md#keeping-the-manifest-in-step`](skills/docs/MAINTAINING.md#keeping-the-manifest-in-step).

## Stage 6 — Let the channel builds republish

Pushing to `main` triggers the per-channel build workflows, which rezip the skill
(dereferencing the symlinks into real files) and recreate the release the
`skill_update_url` points at.

→ [`skills/docs/MAINTAINING.md#release-builds-github-actions`](skills/docs/MAINTAINING.md#release-builds-github-actions).

Check the workflow actually ran and the release asset is current before
promoting — Stage 7 publishes the built zip, so a failed or stale build promotes
the old bundle.

## Stage 7 — Promote to production

Production is not a directory in this repository: it is the `testing` bundle with
its release channel rewritten, published to `airbds-core`. Order matters, and the
script enforces it:

1. `testing` is current (stages 5 and 6 done, build green).
2. Set `channels.production` in `versions.json` to the version being promoted,
   and **commit it first** — the script refuses to publish a zip that entry does
   not advertise.
3. Run the promotion:

```bash
./skills/src/scripts/release_skill_to_core.sh --dry-run   # rehearse
./skills/src/scripts/release_skill_to_core.sh
```

→ [`skills/docs/MAINTAINING.md#promoting-to-production`](skills/docs/MAINTAINING.md#promoting-to-production)
and [`skills/src/README.md`](skills/src/README.md).

This too **opens a pull request rather than merging.** Merge it, and the release
is done. Installed production skills pick the new bundle up through
`skills/versions.json`, which is why nothing needs tagging for them to find it.

---

## Checklist

| # | Stage | Owner doc |
|---|---|---|
| 0 | Decide PATCH / MINOR / MAJOR | `metric/README.md` |
| 1 | Bump `schema_version` in the sheet; regenerate the metric YAML + JSON | `metric/src/README.md` |
| 2 | Archive the old review template pair; regenerate the new one | `reviews/src/README.md` |
| 3 | `CHANGELOG.md` (Metric) | — this file |
| 3b | MINOR/MAJOR only: `README.md`, `CITATION.cff`, `LICENSE.md`, `metric/README.md`, tutorials. Commit and push | — this file |
| 4 | `release_metric_to_core.sh` → **merge the PR** | `metric/src/README.md` |
| 5 | Repoint the skill symlinks; `versions.json`; `DESIGN.md`; `CHANGELOG.md` (Skill) | `skills/docs/MAINTAINING.md` |
| 6 | Confirm the channel build republished the release | `skills/docs/MAINTAINING.md` |
| 7 | `channels.production` first, then `release_skill_to_core.sh` → **merge the PR** | `skills/docs/MAINTAINING.md` |

## If something goes wrong after publishing

There is no tag to roll back to, and a release **overwrites** what `airbds-core`
publishes, so a bad metric is live for everyone reading `main` the moment the PR
merges. Recovery is a forward release, not a revert:

1. Fix it here first — regenerate under a **new** version number rather than
   rewriting the published one. A version that was live and wrong is part of the
   record; reusing its number means two different metrics answered to it.
2. Re-run Stage 4 for the version you want live. Because the destination filename
   is unversioned, republishing an *older* version is a legitimate move and needs
   no special handling — pass the older version to the release script and it
   overwrites cleanly.
3. Then walk stages 5–7 again, so the skill channels are not left carrying a
   metric that is no longer published.

The window before Stage 4 is entirely safe: everything up to that point is local
to this repository, and `--dry-run` reaches `airbds-core` only to read.

## What the tooling will never do for you

Worth stating plainly, because each is a step a script *could* have taken and
deliberately does not:

- **Merge a release pull request.** Both release scripts open one and stop.
  Publication is a working-group decision, not a script's.
- **Tag anything.** Neither repository tags metric releases, by design — see
  [`metric/README.md#versioning-policy`](metric/README.md#versioning-policy).
  Versions are carried by the filenames here, not by tags there. Don't add a tag
  step on the assumption one is missing.
- **Repoint a skill channel.** Deliberate per channel, because a channel may be
  intentionally held on an older metric — though under the coupling above, that
  should be a temporary state and a conscious one.

[core]: https://github.com/AIBIO-UK/airbds-core
