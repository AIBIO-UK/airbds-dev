# `metric/src/` — metric-build tooling

Tooling that regenerates the canonical metric from its upstream source, and
publishes a finished version to the publication repository. Each metric version
pins how it is built:

- **v0.3** — from the committed spreadsheet in [`metric/upstream/`](../upstream/).
- **v0.4** — from the working group's public Google Sheet (the editing interface
  lives in Drive; the generated YAML in the repo is the source of truth).
- **v1.0.0** — from the working group's public Google Sheet (as v0.4), and also
  captures the sheet's Instructions tab into the metric YAML. Its generator is
  the v0.5 one renamed: v1.0.0 supersedes v0.5 unchanged, and v0.5 was withdrawn.

> **Review tooling** (the Google-Sheet → review-YAML converter and the review
> processor/scorer) lives under [`reviews/src/`](../../reviews/src/), beside the
> reviews it serves.

All commands run from the repo root.

## v0.3 — from the committed spreadsheet

`scripts/build_metric_yaml_from_spreadsheet_v0.3.py` regenerates
`metric/airbds_metric_v0.3.yaml` from the `.xlsx` in `metric/upstream/`.

```bash
python3 metric/src/scripts/build_metric_yaml_from_spreadsheet_v0.3.py          # regenerate
python3 metric/src/scripts/build_metric_yaml_from_spreadsheet_v0.3.py --check  # verify in sync
```

Needs Python 3 with `pyyaml` and `openpyxl`.

## v0.4 — from the public Google Sheet

`scripts/build_metric_from_google_sheet_v0.4.py` pulls the Scoring
and Lookups tabs from the [canonical sheet][sheet] (via the public CSV export —
no auth) and regenerates `metric/airbds_metric_v0.4.yaml`.

```bash
# Regenerate from the live sheet (also writes the provenance sidecar + breadcrumb)
python3 metric/src/scripts/build_metric_from_google_sheet_v0.4.py

# Verify the committed file still matches the live sheet (the drift check)
python3 metric/src/scripts/build_metric_from_google_sheet_v0.4.py --check

# Work offline from exported CSVs instead of fetching
python3 metric/src/scripts/build_metric_from_google_sheet_v0.4.py \
    --scoring-csv scoring.csv --lookups-csv lookups.csv
```

Needs only `pyyaml` — it reads the sheet's CSV export, not an `.xlsx`. (Fetching
and the CSV→worksheet adapter live in `scripts/sheet_source.py`.)

**Provenance.** A regenerate writes `metric/airbds_metric_v0.4.upstream.json`
(sheet id/url, a `content_sha256` of the source tabs — the content-addressed
"revision" — and a generation timestamp), plus a `# Source: … sha256 …`
breadcrumb at the top of the YAML.

**What `--check` means.** It compares **metric content**, not raw bytes: the
`# Source content sha256:` line is set aside for the comparison, and only a real
change to what the generator extracts fails (exit 1). This matters because that
hash covers the *raw* CSV of every source tab, so it moves whenever the sheet's
bytes move — including for edits the generator never reads: a cell in an unread
column, a heading in the excluded per-review data-entry block, even trailing
whitespace. Comparing it would report drift for a metric that is identical in
every field, and a check that cries wolf stops being believed.

A bare hash change is therefore reported as a `NOTE` and passes, naming the
recorded and live hashes so it stays auditable. The committed files are left
alone rather than churning a commit whose only difference is a hash line — so
the recorded hash pins the sheet state the *content* was last generated from,
which is what makes a review reproducible. The same rule governs the scheduled
[`metric-upstream-drift-check.yml`](../../.github/workflows/metric-upstream-drift-check.yml)
workflow, which now only opens an issue for a genuine metric change.

Note the boundary is *in the artifact vs not in the artifact*, not
substantive-vs-cosmetic: a typo inside the captured `instructions:` block does
change the metric and will fail the check, because that text ships to reviewers.

**Editorial metadata** not present in the sheet — license, the prose
description, and the scope descriptions — lives in the script's `CONFIG` block;
edit it there and re-run.

## v1.0.0 — from the public Google Sheet

`scripts/build_metric_from_google_sheet_v1.0.0.py` works like the v0.4
script (pulls the Scoring and Lookups tabs from the [v1.0.0 sheet][sheet-v100] via
the public CSV export and regenerates `metric/airbds_metric_v1.0.0.yaml`), with
three differences, all inherited from v0.5:

- **Instructions capture.** It also pulls the sheet's **Instructions** tab and
  writes the generic reviewer guidance verbatim into a top-level `instructions:`
  block of the metric YAML, so downstream consumers (the review processor,
  auto-airbds, the assessment skills) read the same guidance the sheet shows.
  The per-review data-entry section on that tab is excluded. The Instructions
  tab is folded into the `content_sha256`, so an edit there is caught by
  `--check` and the drift workflow.
- **Restructured Lookups.** Per-question points now come from the
  `Points per Question` column of the Lookups `COUNTA of Grade` pivot (v0.4 read
  a flat `Grade / Points` table). The `Required proportions` grading table is
  unchanged.
- **A JSON rendering alongside the YAML.** Each run also writes
  `metric/airbds_metric_v1.0.0.json` for consumers that cannot depend on a YAML
  parser — chiefly the assessment skill's bundled scorer, which must run in
  whatever environment the user's AI assistant provides. It is produced by
  parsing the YAML the run has just rendered and re-serialising it, so it is the
  same document rather than a second pass over the sheet, and the two cannot
  drift apart. The YAML stays canonical: it carries the explanatory comments and
  is what people read. `--check` covers both files — and since the JSON carries
  no comments it is a pure content rendering, so any difference in it is a real
  one and it is compared in full.

```bash
# Regenerate from the live sheet (also writes the provenance sidecar + breadcrumb)
python3 metric/src/scripts/build_metric_from_google_sheet_v1.0.0.py

# Verify the committed file still matches the live sheet (the drift check)
python3 metric/src/scripts/build_metric_from_google_sheet_v1.0.0.py --check

# Work offline from exported CSVs (all three tabs required together)
python3 metric/src/scripts/build_metric_from_google_sheet_v1.0.0.py \
    --scoring-csv scoring.csv --lookups-csv lookups.csv \
    --instructions-csv instructions.csv
```

Offline tests run against committed fixtures of the three source tabs:

```bash
python3 metric/src/tests/test_build_metric_yaml_v100.py   # or: pytest metric/src/tests/
```

As with v0.4, editorial metadata not in the sheet lives in the script's `CONFIG`
block.

## Releasing a version to `airbds-core`

`scripts/release_metric_to_core.sh` publishes one metric version to the
publication repository, [AIBIO-UK/airbds-core][core]. It copies
`metric/airbds_metric_v<version>.yaml` and `metric/airbds_metric_v<version>.json`
to that repository's **root** as the unversioned **`airbds_metric.yaml`** and
**`airbds_metric.json`**, commits them together on a release branch, pushes, and
opens a pull request for working-group review.

Both renderings are one release. They describe the same metric in two formats —
the YAML for readers, the JSON for consumers that parse it without a YAML
library, the assessment skill among them — so a release that moved only one would
leave the publication repo asserting two different metrics at once. Before
anything is cloned, the script runs

```bash
python3 metric/src/scripts/check_metric_renderings_match.py \
    metric/airbds_metric_v1.0.0.yaml metric/airbds_metric_v1.0.0.json
```

which compares the two as parsed objects — formatting and the YAML's comments are
irrelevant — and names the differing top-level keys if they disagree. A mismatch
aborts the release. The generator writes both files from one parsed object, so a
failure here means one of them was edited or rebuilt on its own; regenerate the
pair rather than patching either.

From **v1.0.0 the JSON is required**, and a missing one is an error rather than a
silent YAML-only release: it almost always means the generator was not rerun. The
retained v0.3 and v0.4 metrics predate the JSON rendering and are exempt.

```bash
./metric/src/scripts/release_metric_to_core.sh 1.0.0             # branch, push, PR
./metric/src/scripts/release_metric_to_core.sh 1.0.0 --dry-run   # rehearse locally
```

Needs `git`, and the [GitHub CLI](https://cli.github.com) authenticated with
`repo` scope (not needed for `--dry-run`). The default push URL is
`git@github.com:AIBIO-UK/airbds-core.git` — override with `--remote` (or
`AIRBDS_CORE_REMOTE`) where SSH is unavailable, such as in CI.

Useful options — `--help` lists them all:

| Option | Effect |
|---|---|
| `--dry-run` | Commit locally only; no push, no PR. Keeps the temporary clone and prints its path so the result can be inspected |
| `--branch <name>` | Release branch name (default `release/metric-v<version>`) |
| `--base <name>` | Branch the PR targets (default `main`) |
| `--draft` | Open the pull request as a draft |
| `--repo`, `--remote` | Target a different repository or push URL |

The clone/branch/commit/push/PR mechanics live in the shared
[`scripts/publish-to-core.sh`](../../scripts/publish-to-core.sh), which the skill
release ([`skills/src/scripts/release_skill_to_core.sh`](../../skills/src/scripts/release_skill_to_core.sh))
uses too; this script computes the files, their destinations, the branch, and the
PR text, and forwards the rest. The engine takes repeated `--src`/`--dest` pairs,
which is how both renderings land in a single commit.

The same commit also restamps the metric version quoted in `airbds-core`'s
`skills/README.md`, via
[`scripts/stamp_core_versions.py`](../../scripts/stamp_core_versions.py). Because
the published YAML is unversioned, that sentence is where a reader learns which
metric is current — it has to move with the file. The skill version in that
README is left alone; it belongs to the skill release. The number sits inside
HTML comment markers, which render as nothing, and a README missing them fails
the release rather than publishing a stale version. See
[MAINTENANCE.md](../../skills/docs/MAINTENANCE.md#the-readme-stamp).

Things it deliberately does **not** do:

- **It never merges and never tags.** The PR is left open; tagging the release in
  `airbds-core` is a separate step after merge. Since the published filename
  carries no version, a tag or GitHub release is what downstream consumers pin
  to.
- **It never touches a local `airbds-core` checkout.** The publication repo is
  cloned into a temporary directory each run and removed afterwards, so the
  release can never pick up unrelated local state.
- **It publishes only the YAML** — not the subsidiary `.json`, the
  `.upstream.json` provenance sidecar, or any surrounding repo file.

It refuses to run if the release branch already exists on the remote (pass
`--branch` or delete it), and exits successfully without creating a branch or PR
if the published files *both* already match the version being released. It warns
if either source has uncommitted changes, and publishes the working-tree version
— the PR body records the `airbds-dev` commit the files came from, noting when
they were dirty.

Offline tests drive the whole script against a throwaway local repository with a
stubbed `gh`, so they neither reach the network nor touch the real publication
repository:

```bash
python3 metric/src/tests/test_release_metric_to_core.py        # release script
python3 metric/src/tests/test_check_metric_renderings_match.py # the preflight
# or, for both: pytest metric/src/tests/
```

[core]: https://github.com/AIBIO-UK/airbds-core
[sheet]: https://docs.google.com/spreadsheets/d/1eriM8bXAoNXsIR9l8OpI1XYEp8FbtBWt05CTIP9cVeg/edit
[sheet-v100]: https://docs.google.com/spreadsheets/d/13w-MiUQc2sLzRFqRQD_YT6BisE3Orv5Oj3i0YBw7r_M/edit
