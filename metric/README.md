# metric/ — AIRBDS Metric Files

This README has two clearly separated parts: **Part 1** explains the metric
itself and how scoring works (for anyone assessing a dataset); **Part 2** is
the contributor/maintainer guide for updating the metric files in this folder.

---

## Part 1 — The Metric & Scoring

### What the Metric Is

The AIRBDS metric is a versioned, machine-readable checklist for assessing how
suitable a bioscience dataset is for AI/ML use. The current version (v1.0.0) is a
**25-question** set, grouped into scopes (Infrastructure, Metadata, Content,
Ethics) and three weight tiers (Critical, Important, Optional), plus the
`grade_points` and `grading` rules that turn a set of Yes/No answers into a
weighted score and a grade.

`metric/airbds_metric_v1.0.0.yaml` is the **source of truth**: the canonical
machine-readable artifact that everything in this repository (and downstream
consumers) reads — the exact question text, guidance, scopes, and scoring rules.
The working group's **Google Sheet** is the **editing interface** where the
metric is authored; edits made there are pulled into the YAML by the build
script, which also writes a subsidiary `airbds_metric_v1.0.0.json` rendering of
the same document.

### Use the Metric

Two ways to use v1.0.0 directly:

- **[Open the Google Sheet](https://docs.google.com/spreadsheets/d/13w-MiUQc2sLzRFqRQD_YT6BisE3Orv5Oj3i0YBw7r_M/edit)** — the live editing interface, with built-in formulas that calculate the weighted score and grade automatically as you fill in answers. **Recommended for scoring a dataset today.**
- **[`airbds_metric_v1.0.0.yaml`](airbds_metric_v1.0.0.yaml)** — the source of truth, for anything programmatic (or [`airbds_metric_v1.0.0.json`](airbds_metric_v1.0.0.json), subsidiary to it, where a YAML parser is unavailable).

To score a **filled-in YAML or CSV review** rather than the Sheet, use the review
processor, which validates the file, computes the weighted score and grade, and
generates the companion format:

```bash
pip install pyyaml
echo "reviews/testing/<your-review>.yaml" > /tmp/files.txt
python3 reviews/src/scripts/review_processor.py --files /tmp/files.txt
```

It is version-aware: each review carries a `schema_version` and is scored against
the matching `metric/airbds_metric_v<version>.yaml`. Note that the **automated**
path — scoring on pull request via CI — is currently disabled, so run the
processor yourself; see [`reviews/README.md`](../reviews/README.md).

For a step-by-step walkthrough of assessing a dataset, see the
**[interactive tutorial site](https://aibio-uk.github.io/airbds-metric-tutorial/)**.

### How Scoring Works

Each question is graded into one of three tiers, worth different points when
answered `Yes` (a `No` always scores 0):

| Tier | Points | Why |
|------|--------|-----|
| **Critical** | 80 | Failing a Critical question indicates a fundamental problem that severely limits the dataset's suitability for AI/ML use. |
| **Important** | 5 | Important questions represent best practices affecting reproducibility, interoperability, or usability. |
| **Optional** | 2 | Optional questions capture desirable but non-essential characteristics. |

A dataset's weighted score is the sum of points for its `Yes` answers. In v1.0.0
the 25 questions split into 9 Critical, 10 Important, and 6 Optional, giving a
maximum score of **782**. These point values are the human-readable rationale —
the **authoritative, machine-readable** numbers live in the metric YAML's
`grade_points` block.

### Grades

A dataset earns the **highest** grade for which it meets *both* the per-tier
pass-rate criteria *and* that grade's minimum total score (`min_score`). The
exact `min_score` and pass-rate values live in the metric YAML's `grading` block
and can differ between metric versions — the summaries below are v1.0.0.

| Grade | Badge colour | Means |
|-------|--------------|-------|
| 🟡 **Gold** | `#ffc107` | Passes all Critical and Important questions, plus ≥ 50% of Optional. |
| ⚪ **Silver** | `#c0c0c0` | Passes all Critical, plus ≥ 50% of Important. |
| 🟤 **Bronze** | `#cd7f32` | Passes most Critical questions (≥ 88.9%). |
| 🔴 **Caution** | `#dc3545` | May have serious issues — fails one or more Critical criteria. |

The badge colours are a presentation reference only — no tool reads them from
the repo. Further rationale for the weighting and grades is in
[`reviews/GUIDANCE.md`](../reviews/GUIDANCE.md).

### Ethics Questions

Ethics-scope questions (ABC-23 – ABC-25) default to `"Yes"` for datasets that
contain **no human or animal subject data** — set `not_applicable: true` and note
it in the comments. In the metric these questions carry
`not_applicable_default: "Yes"`.

---

## Part 2 — Updating & Maintaining the Metric

> **Before editing any file in this folder, read this section.**

Changes to this folder have a disproportionate downstream impact. The review
template is generated from the metric, the assessment skill bundles it and
reports the version it scored against, and several documents quote that version
in prose. Regenerating the metric without carrying the rest along leaves those
out of step, and nothing in CI will tell you. [`RELEASING.md`](../RELEASING.md)
is the running order that keeps them together.

### Files in This Folder

| Filename | Format | Purpose |
|----------|--------|---------|
| `airbds_metric_v1.0.0.yaml` | YAML | **Canonical — current.** 25-question metric: question text, grades, guidance, scopes, `instructions`, and the `grade_points`/`grading` scoring rules |
| `airbds_metric_v1.0.0.json` | JSON | **Subsidiary to the YAML.** The same v1.0.0 document, written by the same generator run, for consumers that cannot parse YAML — cite and change the YAML, not this |
| `airbds_metric_v1.0.0.upstream.json` | JSON | v1.0.0 provenance: source sheet id/url + `content_sha256` "revision" + generation timestamp |
| `airbds_metric_v0.4.yaml` | YAML | **Previous version — retained.** 27-question metric; reviews carrying `schema_version: "0.4"` still score against it |
| `airbds_metric_v0.3.yaml` | YAML | **Previous version — retained.** 28-question metric; reviews carrying `schema_version: "0.3"` still score against it |
| `README.md` | Markdown | This file — contributor guide for the metric folder |

The metric is **authored as YAML**, with the JSON a subsidiary rendering of it
(introduced with v0.5, and carried into v1.0.0). (The *review template* under
`reviews/` also ships in both YAML and CSV — a separate file, generated from the
metric by [`reviews/src/scripts/build_review_template.py`](../reviews/src/scripts/build_review_template.py).)

> **v1.0.0 is the current version.** `airbds_metric_v1.0.0.*` is generated from the working group's Google Sheet (see [How the v1.0.0 metric files are generated](#how-the-v100-metric-files-are-generated) and the `[1.0.0]` entry in [CHANGELOG.md](../CHANGELOG.md)). **v0.4 and v0.3 are retained** for reference and for re-scoring older reviews — the review processor auto-selects the metric matching each review's `schema_version`. **v0.5 was withdrawn**, not retained: v1.0.0 is the same metric under a stable version number, and no review ever carried `schema_version: "0.5"`, so there was nothing to re-score. Retention exists for reviews, not for completeness.

> **Note on versioning:** the **current** `review_template` pair (under `reviews/`) is **not** versioned in its filename — `reviews/review_template.{yaml,csv}` always tracks the current metric (now v1.0.0), so non-technical reviewers always download the right file. It carries a `schema_version` field that must match the current metric version, so it is updated on every bump. On a bump, the outgoing pair is first copied to `reviews/archived_templates/review_template_v<old>.{yaml,csv}` (e.g. `review_template_v0.4.{yaml,csv}`) before the unversioned pair is overwritten — so previous versions stay retrievable as files, not just in git history.

> **Note on new metric versions:** A version bump creates a new file (e.g. `airbds_metric_v1.1.0.yaml`). Old versions are **retained** for archival — reviews carry `schema_version` to record which version they were scored against. The exception is a version nothing was ever scored against, which may be withdrawn instead (as v0.5 was on the move to v1.0.0) — a retained file that duplicates its successor only invites the question of which to use.

### How the v0.3 metric files are generated

`airbds_metric_v0.3.yaml` is **generated, not hand-edited.** It is produced from a single source — the scoring spreadsheet (`AIRBDS Core Metric scoring v0.3 - _initials_-_#_ TEMPLATE.xlsx` in `metric/upstream/`) — by one script:

```
metric/src/scripts/build_metric_yaml_from_spreadsheet_v0.3.py
```

- **To change metric content** (questions, themes, grades, mapped-from references): edit the `Scoring` and `Lookups` sheets of the spreadsheet, then regenerate:
  ```
  python3 metric/src/scripts/build_metric_yaml_from_spreadsheet_v0.3.py
  ```
- **Document-level metadata not held in the spreadsheet** (licence, repository, contact, the prose description, scope descriptions) lives in a `CONFIG` block at the top of the script — edit it there.
- **To verify** the committed file is in sync with the spreadsheet (suitable for CI):
  ```
  python3 metric/src/scripts/build_metric_yaml_from_spreadsheet_v0.3.py --check
  ```
  This exits non-zero if the file is out of date.

> The YAML carries a **GENERATED FILE — DO NOT EDIT BY HAND** banner. Edit the spreadsheet (or the script's `CONFIG`) and regenerate rather than editing the YAML directly.

### How the v1.0.0 metric files are generated

From v0.4 the metric is authored in the working group's **public Google Sheet** rather than a committed `.xlsx`. `metric/src/scripts/build_metric_from_google_sheet_v1.0.0.py` pulls the Scoring, Lookups, and Instructions tabs and regenerates `airbds_metric_v1.0.0.yaml`, recording which sheet and a content-hash "revision" in `airbds_metric_v1.0.0.upstream.json` plus a `# Source:` breadcrumb in the YAML. (From v0.5 the sheet's Instructions tab is also captured into a top-level `instructions:` block.) See [`metric/src/README.md`](src/README.md) for the commands, the `--check` drift check, and offline use. A weekly workflow (`.github/workflows/metric-upstream-drift-check.yml`) confirms each committed YAML still matches its Sheet, opening an issue if it has drifted. Each committed version keeps its own generator (`…_v0.4.py`, `…_v1.0.0.py` — the last being the v0.5 generator renamed); the v0.3 `.xlsx` chain stays in place unchanged.

### Publishing a Version to `airbds-core`

This is the **development** repository; the canonical metric is published from
[AIBIO-UK/airbds-core](https://github.com/AIBIO-UK/airbds-core). Once a version
here is final, `metric/src/scripts/release_metric_to_core.sh` publishes it:

```bash
./metric/src/scripts/release_metric_to_core.sh 1.0.0 --dry-run   # rehearse first
./metric/src/scripts/release_metric_to_core.sh 1.0.0
```

It copies `metric/airbds_metric_v1.0.0.yaml` **and**
`metric/airbds_metric_v1.0.0.json` to the root of `airbds-core` as the
**unversioned `airbds_metric.yaml`** and **`airbds_metric.json`**, in one commit
on a `release/metric-v1.0.0` branch, and opens a pull request. It does not merge
and does not tag. `airbds-core` carries the **current** metric and only the
current one; every version, superseded ones included, stays here under its own
name — so anyone depending on a specific version references this repository, not
a tag over there. See [`metric/src/README.md`](src/README.md) for the options and
the full behaviour.

Both renderings go over together, and a preflight
(`metric/src/scripts/check_metric_renderings_match.py`) refuses the release if
they do not hold the same data. Publishing one without the other would leave
`airbds-core` asserting two different metrics at once. From v1.0.0 the JSON is
required; the retained v0.3 and v0.4 metrics predate it and publish as YAML
alone.

### Changing the metric

A metric change is proposed on an issue before any YAML is written, and the size
of the version bump follows from what changed. Both are documented in
[`CONTRIBUTING.md`](../CONTRIBUTING.md):

- [Proposing metric changes](../CONTRIBUTING.md#proposing-metric-changes) — the
  issue-first workflow, the `[Metric Change]` title prefix, and what the issue
  needs to state.
- [Versioning policy](../CONTRIBUTING.md#versioning-policy) — which kind of
  change bumps which component, why all three components are always written out,
  and what happens to the outgoing version.

Once a change is agreed, [`RELEASING.md`](../RELEASING.md) is the running order
for getting it out: regenerating the metric, the files that have to move with it,
publishing to `airbds-core`, and repointing the assessment skill at the new
version.

---

## Questions?

Open an Issue at [github.com/AIBIO-UK/airbds-dev/issues](https://github.com/AIBIO-UK/airbds-dev/issues) or contact the working group at [info@aibio.ac.uk](mailto:info@aibio.ac.uk).
