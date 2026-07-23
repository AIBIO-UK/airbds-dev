# metric/ — AIRBDS Metric Files

This README has two clearly separated parts: **Part 1** explains the metric
itself and how scoring works (for anyone assessing a dataset); **Part 2** is
the contributor/maintainer guide for updating the metric files in this folder.

---

## Part 1 — The Metric & Scoring

### What the Metric Is

The AIRBDS metric is a versioned, machine-readable checklist for assessing how
suitable a bioscience dataset is for AI/ML use. The current version (v0.5) is a
**25-question** set, grouped into scopes (Infrastructure, Metadata, Content,
Ethics) and three weight tiers (Critical, Important, Optional), plus the
`grade_points` and `grading` rules that turn a set of Yes/No answers into a
weighted score and a grade.

The working group's **Google Sheet** is where the metric is authored — the
upstream source of truth. `metric/airbds_metric_v0.5.yaml` is generated from it
and is the canonical machine-readable artifact that everything in this
repository (and downstream consumers) reads: the exact question text, guidance,
scopes, and scoring rules.

### Use the Metric

Two ways to use v0.5 directly:

- **[Open the Google Sheet](https://docs.google.com/spreadsheets/d/13w-MiUQc2sLzRFqRQD_YT6BisE3Orv5Oj3i0YBw7r_M/edit)** — the live source of truth, with built-in formulas that calculate the weighted score and grade automatically as you fill in answers. **Recommended for scoring a dataset today.**
- **[`airbds_metric_v0.5.yaml`](airbds_metric_v0.5.yaml)** — the generated YAML, for anything programmatic.

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

A dataset's weighted score is the sum of points for its `Yes` answers. In v0.5
the 25 questions split into 9 Critical, 10 Important, and 6 Optional, giving a
maximum score of **782**. These point values are the human-readable rationale —
the **authoritative, machine-readable** numbers live in the metric YAML's
`grade_points` block.

### Grades

A dataset earns the **highest** grade for which it meets *both* the per-tier
pass-rate criteria *and* that grade's minimum total score (`min_score`). The
exact `min_score` and pass-rate values live in the metric YAML's `grading` block
and can differ between metric versions — the summaries below are v0.5.

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

Changes to this folder have a disproportionate downstream impact. Multiple files across the repository — scripts, GitHub Actions workflows, skills, tutorials, and documentation — all reference the exact metric version and file paths. A partial update (e.g. regenerating the metric YAML without updating the review template, or bumping the version without updating the workflow paths) creates silent failures that corrupt inter-rater reliability or break the CI/CD pipeline.

### Files in This Folder

| Filename | Format | Purpose |
|----------|--------|---------|
| `airbds_metric_v0.5.yaml` | YAML | **Canonical — current.** 25-question metric: question text, grades, guidance, scopes, `instructions`, and the `grade_points`/`grading` scoring rules |
| `airbds_metric_v0.5.upstream.json` | JSON | v0.5 provenance: source sheet id/url + `content_sha256` "revision" + generation timestamp |
| `airbds_metric_v0.4.yaml` | YAML | **Previous version — retained.** 27-question metric; reviews carrying `schema_version: "0.4"` still score against it |
| `airbds_metric_v0.3.yaml` | YAML | **Previous version — retained.** 28-question metric; reviews carrying `schema_version: "0.3"` still score against it |
| `README.md` | Markdown | This file — contributor guide for the metric folder |

Metric output is **YAML-only**. (The *review template* under `reviews/` still
ships in both YAML and CSV — that is a separate file, see Group B below.)

> **v0.5 is the current version.** `airbds_metric_v0.5.*` is generated from the working group's Google Sheet (see [How the v0.5 metric files are generated](#how-the-v05-metric-files-are-generated) and the `[0.5]` entry in [CHANGELOG.md](../CHANGELOG.md)). **v0.4 and v0.3 are retained** for reference and for re-scoring older reviews — the review processor auto-selects the metric matching each review's `schema_version`.

> **Note on versioning:** the **current** `review_template` pair (under `reviews/`) is **not** versioned in its filename — `reviews/review_template.{yaml,csv}` always tracks the current metric (now v0.5), so non-technical reviewers always download the right file. It carries a `schema_version` field that must match the current metric version, so it is updated on every bump. On a bump, the outgoing pair is first copied to `reviews/archived_templates/review_template_v<old>.{yaml,csv}` (e.g. `review_template_v0.4.{yaml,csv}`) before the unversioned pair is overwritten — so previous versions stay retrievable as files, not just in git history.

> **Note on new metric versions:** A version bump creates a new file (e.g. `airbds_metric_v0.5.yaml`). Old versions are **retained** for archival — reviews carry `schema_version` to record which version they were scored against.

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

### How the v0.5 metric files are generated

From v0.4 the metric is authored in the working group's **public Google Sheet** rather than a committed `.xlsx`. `metric/src/scripts/build_metric_yaml_from_google_sheet_v0.5.py` pulls the Scoring, Lookups, and Instructions tabs and regenerates `airbds_metric_v0.5.yaml`, recording which sheet and a content-hash "revision" in `airbds_metric_v0.5.upstream.json` plus a `# Source:` breadcrumb in the YAML. (v0.5 also captures the sheet's Instructions tab into a top-level `instructions:` block.) See [`metric/src/README.md`](src/README.md) for the commands, the `--check` drift check, and offline use. A weekly workflow (`.github/workflows/metric-upstream-drift-check.yml`) confirms each committed YAML still matches its Sheet, opening an issue if it has drifted. Each committed version keeps its own generator (`…_v0.4.py`, `…_v0.5.py`); the v0.3 `.xlsx` chain stays in place unchanged.

### Why ALL Files Must Change Together

#### The review-template YAML ↔ CSV pair must always be identical in content

The **review template** ships in both formats (`reviews/review_template.{yaml,csv}`) and they are **not** derived from each other at read time — both are independent files that are read directly. The review processor (`reviews/src/scripts/review_processor.py`) loads whichever format the reviewer submitted; the human spreadsheet workflow reads the CSV. If one is updated without the other, a researcher using the spreadsheet workflow scores against a different template than one using the YAML workflow. This is **silent**, produces no error, and **invalidates inter-rater reliability**.

#### The downstream impact chain

For any **MINOR** change (question additions, deletions, or rewordings) or **MAJOR** change (weight or grade threshold changes), the following files outside `metric/` must also be updated in the same commit or PR:

| File | What breaks if not updated |
|------|---------------------------|
| `README.md` | Version badge, question table, download links, and processor command examples all reference the old version |
| `CHANGELOG.md` | No record of the change; violates the project's versioning contract with users |
| `CITATION.cff` | `version` and `date-released` fields are stale; published citations will reference the wrong version |
| `LICENSE.md` | Its suggested-citation block names a version and year; if not updated it contradicts `CITATION.cff` and `README.md` |
| `skills/GF/GF-airbds-assessment-skill/SKILL.md` | Embedded question table, YAML templates, `schema_version` value, and file paths all reference old version |
| `skills/testing/airbds-assessment-skill/SKILL.md` | Template filename reference (update only if the XLSX is also regenerated) |
| `reviews/docs/tutorial-yaml.md` | File path references to `v0.3` in instructions become broken |
| `reviews/docs/tutorial-csv.md` | Same as above for spreadsheet tutorial |

**PATCH** changes (guidance text only — no change to question meaning, weight, or ID) are lighter: regenerate the metric YAML and update the review-template pair. Downstream files are not required unless they quote guidance text verbatim.

### Recommended Workflow for Proposing Changes

1. **Check existing Issues** at [github.com/AIBIO-UK/airbds-dev/issues](https://github.com/AIBIO-UK/airbds-dev/issues) before opening a new one — the change may already be under discussion.

2. **Open a GitHub Issue** before writing any code or YAML. Use the title prefix `[Metric Change]`. In the body, state:
   - Which question(s) are affected (e.g. ABC-12, ABC-16)
   - The rationale for the change
   - Whether this is a guidance-only change (**PATCH**), a question rewording/addition/deletion (**MINOR**), or a weight/threshold change (**MAJOR**)

   See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full versioning policy.

3. **Discuss on the Issue** until working-group consensus is reached. A maintainer will label the issue `metric-change-pending`.

4. **Fork the repository** and create a branch named `metric/<issue-number>-brief-description` (e.g. `metric/42-add-abc-29-reproducibility`).

5. **Update ALL coupled files** as described in the Coupled File Groups manifest below. This is **not optional** — a partial update silently corrupts inter-rater reliability, and there is no automated check for it. Review carefully before merging.

6. **Open a pull request** referencing the original Issue (e.g. `Closes #42`).

7. **Working-group review** and merge by a maintainer.

### Coupled File Groups Manifest

Use this as a checklist when implementing any metric change.

#### Group A — Core metric *(generated, never hand-edited)*
- `metric/airbds_metric_vX.Y.yaml`

> Never hand-edit these files. v0.5 (current) is generated from the working group's Google Sheet by `metric/src/scripts/build_metric_yaml_from_google_sheet_v0.5.py` (v0.4 by the `…_v0.4.py` script); v0.3 by `metric/src/scripts/build_metric_yaml_from_spreadsheet_v0.3.py`. See [How the v0.5 metric files are generated](#how-the-v05-metric-files-are-generated).

#### Group B — Review template pair *(always change together)*
- `reviews/review_template.yaml`
- `reviews/review_template.csv`

#### Group C — Downstream version-carrying files *(MINOR or MAJOR changes only)*
- `README.md` — version badge, question table, download links, processor command examples
- `CHANGELOG.md` — add a new entry at the top referencing the originating Issue
- `CITATION.cff` — update `version:` and `date-released:` fields
- `LICENSE.md` — update the version and year in the suggested-citation block (not the copyright year, which is the year of first publication). Keep it consistent with `CITATION.cff` and the Citation section of `README.md`
- The review processor needs **no update** — it auto-selects `metric/airbds_metric_v<schema_version>.yaml` per review. Its workflows need none either, and neither runs automatically now: `review-check.yml` is disabled (the manual review process is not live) and `review-test.yml` is `workflow_dispatch`-only.
- `skills/GF/GF-airbds-assessment-skill/SKILL.md` — update embedded templates, question table, file paths, skill version
- `skills/testing/airbds-assessment-skill/SKILL.md` — update template filename **only if the XLSX is also regenerated**
- `skills/versions.json` — per-channel update manifest the assessment skills read at runtime; bump a channel's `metric_version` only when that channel's skill is actually repointed to the new metric (leave channels intentionally kept on the old metric untouched). Validate with `scripts/validate-skills-versions.py`
- `reviews/docs/tutorial-yaml.md` — update all `vX.Y` path references
- `reviews/docs/tutorial-csv.md` — update all `vX.Y` path references

> `metric/README.md` is a documentation file. Update its version references — including the question counts and maximum score under [How Scoring Works](#how-scoring-works) in Part 1 — when implementing MINOR or MAJOR changes.

### Versioning Quick Reference

| Change type | Description | Version bump | Files to update |
|-------------|-------------|-------------|-----------------|
| **PATCH** | Guidance text clarification only — no change to question meaning, weights, or IDs | `0.5` → `0.5.1` | Groups A, B |
| **MINOR** | Question added, removed, or reworded | `0.5` → `0.6` | Groups A, B, C |
| **MAJOR** | Weight point value or grade threshold changed | `0.5` → `1.0` | Groups A, B, C |

The canonical versioning policy is defined in [CONTRIBUTING.md](../CONTRIBUTING.md).

---

## Questions?

Open an Issue at [github.com/AIBIO-UK/airbds-dev/issues](https://github.com/AIBIO-UK/airbds-dev/issues) or contact the working group at [info@aibio.ac.uk](mailto:info@aibio.ac.uk).
