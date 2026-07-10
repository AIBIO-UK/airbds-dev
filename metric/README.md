# metric/ — AIRBDS Metric Files

This README has two clearly separated parts: **Part 1** explains the metric
itself and how scoring works (for anyone assessing a dataset); **Part 2** is
the contributor/maintainer guide for updating the metric files in this folder.

---

## Part 1 — The Metric & Scoring

### What the Metric Is

The AIRBDS metric is a versioned, machine-readable checklist for assessing
how suitable a bioscience dataset is for AI/ML use. It's a **27-question**
set, grouped into scopes (Infrastructure, Metadata, Content, Ethics) and
three weight tiers (Critical, Important, Optional), plus the `grade_points`
and `grading` rules that turn a set of Yes/No answers into a weighted score
and a grade. `metric/airbds_metric_v0.4.yaml` is the single **source of
truth** for all of this — the exact question text, guidance, scopes, and
scoring rules.

### Use the Metric

Two ways to use v0.4 directly:

- **[Open the Google Sheet](https://docs.google.com/spreadsheets/d/1eriM8bXAoNXsIR9l8OpI1XYEp8FbtBWt05CTIP9cVeg/edit)** — the live source of truth, with built-in formulas that calculate the weighted score and grade automatically as you fill in answers. **Recommended for scoring a dataset today.**
- **[`airbds_metric_v0.4.yaml`](airbds_metric_v0.4.yaml)** — the generated YAML, for anything programmatic. There's no tool yet that takes a filled-in YAML review and scores it for you — automated YAML-based scoring is planned infrastructure, not yet built (see [How the v0.4 metric file is generated](#how-the-v04-metric-file-is-generated) for the one piece of automation that does exist: the Sheet → YAML sync).

To score a dataset against the metric, see the **[interactive tutorial site](https://aibio-uk.github.io/airbds-metric-tutorial/)** for a step-by-step walkthrough.

### How Scoring Works

Each question is graded into one of three tiers, worth different points when
answered `Yes` (a `No` always scores 0):

| Tier | Points | Why |
|------|--------|-----|
| **Critical** | 80 | Failing a Critical question indicates a fundamental problem that severely limits the dataset's suitability for AI/ML use. |
| **Important** | 5 | Important questions represent best practices affecting reproducibility, interoperability, or usability. |
| **Optional** | 2 | Optional questions capture desirable but non-essential characteristics. |

A dataset's weighted score is the sum of points for its `Yes` answers. These
point values are the human-readable rationale — the **authoritative,
machine-readable** numbers live in the metric YAML's `grade_points` block.

### Grades

A dataset earns the **highest** grade for which it meets *both* the per-tier
pass-rate criteria *and* that grade's minimum total score (`min_score`). The
exact `min_score` and pass-rate values are in the metric YAML's `grading`
block and can differ between metric versions.

| Grade | Badge colour | Means |
|-------|--------------|-------|
| 🟡 **Gold** | `#ffc107` | Passes all Critical and Important questions, plus ≥ 50% of Optional. |
| ⚪ **Silver** | `#c0c0c0` | Passes all Critical, plus ≥ 50% of Important. |
| 🟤 **Bronze** | `#cd7f32` | Passes most Critical questions. |
| 🔴 **Caution** | `#dc3545` | May have serious issues — fails one or more Critical criteria. |

The badge colours are a presentation reference only — no tool reads them
from the repo.

### Ethics Questions

Ethics-scope questions (ABC-24 – ABC-27) default to `"Yes"` for datasets
that contain **no human or animal subject data** — set `not_applicable:
true` and note it in the comments. In the metric these questions carry
`not_applicable_default: "Yes"`.

---

## Part 2 — Updating & Maintaining the Metric

> **Before editing any file in this folder, read this section.**

Changes to this folder have a disproportionate downstream impact. `README.md`, `CHANGELOG.md`, and `CITATION.cff` all reference the exact metric version. A partial update (e.g. bumping the version without updating the README) creates silent inconsistencies.

### Files in This Folder

| Filename | Format | Purpose |
|----------|--------|---------|
| `airbds_metric_v0.4.yaml` | YAML | **Canonical — current.** 27-question metric: question text, grades, guidance, scopes, and the `grade_points`/`grading` scoring rules |
| `CHANGELOG.md` | Markdown | Full version history of the metric |
| `README.md` | Markdown | This file — contributor guide for the metric folder |

The generator script, its provenance sidecar (`airbds_metric_v0.4.upstream.json`), and the drift-check workflow live in [`admin/`](../admin/) — see [How the v0.4 metric file is generated](#how-the-v04-metric-file-is-generated).

Metric output is YAML-only.

### How the v0.4 metric file is generated

The metric is authored in the working group's **public Google Sheet**. [`admin/scripts/build_metric_yaml_and_csv_from_google_sheet_v0.4.py`](../admin/scripts/build_metric_yaml_and_csv_from_google_sheet_v0.4.py) pulls the Scoring and Lookups tabs and regenerates `airbds_metric_v0.4.yaml`, recording which sheet and a content-hash "revision" in [`admin/airbds_metric_v0.4.upstream.json`](../admin/airbds_metric_v0.4.upstream.json) plus a `# Source:` breadcrumb in the YAML. See [`admin/README.md`](../admin/README.md) for the commands, the `--check` drift check, and offline use. A weekly check (`.github/workflows/metric-upstream-drift-check.yml`) confirms the committed YAML still matches the Google Sheet.

### Why Downstream Files Must Change Together

For any **MINOR** change (question additions, deletions, or rewordings) or **MAJOR** change (weight or grade threshold changes), the following files outside `metric/` must also be updated in the same commit or PR:

| File | What breaks if not updated |
|------|---------------------------|
| `README.md` | Version badge and question table reference the old version |
| `metric/CHANGELOG.md` | No record of the change; violates the project's versioning contract with users |
| `CITATION.cff` | `version` and `date-released` fields are stale; published citations will reference the wrong version |

**PATCH** changes (guidance text only — no change to question meaning, weight, or ID) are lighter: update only the metric YAML. Downstream files are not required unless they quote guidance text verbatim.

### Recommended Workflow for Proposing Changes

1. **Check existing Issues** at [github.com/AIBIO-UK/airbds-metric/issues](https://github.com/AIBIO-UK/airbds-metric/issues) before opening a new one — the change may already be under discussion.

2. **Open a GitHub Issue** before writing any code or YAML. Use the title prefix `[Metric Change]`. In the body, state:
   - Which question(s) are affected (e.g. ABC-12, ABC-16)
   - The rationale for the change
   - Whether this is a guidance-only change (**PATCH**), a question rewording/addition/deletion (**MINOR**), or a weight/threshold change (**MAJOR**)

   See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full versioning policy.

3. **Discuss on the Issue** until working-group consensus is reached. A maintainer will label the issue `metric-change-pending`.

4. **Fork the repository** and create a branch named `metric/<issue-number>-brief-description` (e.g. `metric/42-add-acm-29-reproducibility`).

5. **Update ALL coupled files** as described in the Coupled File Groups manifest below. This is **not optional** — review carefully before merging, there is no automated check for it.

6. **Open a pull request** referencing the original Issue (e.g. `Closes #42`).

7. **Working-group review** and merge by a maintainer.

### Coupled File Groups Manifest

Use this as a checklist when implementing any metric change.

**Group A — Core metric file**
- `metric/airbds_metric_vX.Y.yaml`

> Never hand-edit. For v0.4 (current) it is generated from the working group's Google Sheet by `admin/scripts/build_metric_yaml_and_csv_from_google_sheet_v0.4.py`. See [How the v0.4 metric file is generated](#how-the-v04-metric-file-is-generated).

**Group B — Downstream version-carrying files** *(MINOR or MAJOR changes only)*
- `README.md` — version badge, question table
- `metric/CHANGELOG.md` — add a new entry at the top referencing the originating Issue
- `CITATION.cff` — update `version:` and `date-released:` fields

### Versioning Quick Reference

| Change type | Description | Version bump | Files to update |
|-------------|-------------|-------------|-----------------|
| **PATCH** | Guidance text clarification only — no change to question meaning, weights, or IDs | `0.4` → `0.4.1` | Group A |
| **MINOR** | Question added, removed, or reworded | `0.4` → `0.5` | Groups A, B |
| **MAJOR** | Weight point value or grade threshold changed | `0.4` → `1.0` | Groups A, B |

The canonical versioning policy is defined in [CONTRIBUTING.md](../CONTRIBUTING.md).

---

## Questions?

Open an Issue at [github.com/AIBIO-UK/airbds-metric/issues](https://github.com/AIBIO-UK/airbds-metric/issues) or contact the working group at [info@aibio.ac.uk](mailto:info@aibio.ac.uk).
