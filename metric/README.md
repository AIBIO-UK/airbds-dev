# metric/ — AIRBDS Metric Files

> **Before editing any file in this folder, read this document.**

The `metric/` folder is the **single source of truth** for the AIRBDS scoring metric — the versioned question set plus the `grade_points`/`grading` scoring rules, in a machine-readable YAML format. The blank review template and completed dataset reviews live in `reviews/`.

Changes to this folder have a disproportionate downstream impact. `README.md`, `CHANGELOG.md`, and `CITATION.cff` all reference the exact metric version. A partial update (e.g. bumping the version without updating the README) creates silent inconsistencies.

---

## Use the Metric

Two ways to use v0.4 directly:

- **[Open the Google Sheet](https://docs.google.com/spreadsheets/d/1eriM8bXAoNXsIR9l8OpI1XYEp8FbtBWt05CTIP9cVeg/edit)** — the live source of truth. Browse, filter, or copy it.
- **[`airbds_metric_v0.4.yaml`](airbds_metric_v0.4.yaml)** — the generated YAML, for anything programmatic.

To score a dataset against the metric, see the **[interactive tutorial site](https://aibio-uk.github.io/airbds-metric-tutorial/)** for a step-by-step walkthrough, and [`reviews/GUIDANCE.md`](../reviews/GUIDANCE.md) for the rationale behind the weighting and grades (`grade_points` / `grading` below are the authoritative numbers).

There is no automated scorer right now — scores are calculated manually (e.g. in a spreadsheet against the Google Sheet). Automated YAML-based scoring is planned infrastructure, not yet built.

A weekly check (`.github/workflows/metric-upstream-drift-check.yml`) confirms the committed YAML still matches the Google Sheet.

---

## Files in This Folder

| Filename | Format | Purpose |
|----------|--------|---------|
| `airbds_metric_v0.4.yaml` | YAML | **Canonical — current.** 27-question metric: question text, grades, guidance, scopes, and the `grade_points`/`grading` scoring rules |
| `airbds_metric_v0.4.upstream.json` | JSON | v0.4 provenance: source sheet id/url + `content_sha256` "revision" + generation timestamp |
| `airbds_metric_v0.3.yaml` | YAML | Previous version, retained — reviews carrying `schema_version: "0.3"` score against it |
| `CHANGELOG.md` | Markdown | Full version history of the metric |
| `README.md` | Markdown | This file — contributor guide for the metric folder |

Metric output is YAML-only.

---

## How the v0.4 metric file is generated

The metric is authored in the working group's **public Google Sheet**. `metric/src/scripts/build_metric_yaml_and_csv_from_google_sheet_v0.4.py` pulls the Scoring and Lookups tabs and regenerates `airbds_metric_v0.4.yaml`, recording which sheet and a content-hash "revision" in `airbds_metric_v0.4.upstream.json` plus a `# Source:` breadcrumb in the YAML. See [`metric/src/README.md`](src/README.md) for the commands, the `--check` drift check, and offline use.

---

## Why Downstream Files Must Change Together

For any **MINOR** change (question additions, deletions, or rewordings) or **MAJOR** change (weight or grade threshold changes), the following files outside `metric/` must also be updated in the same commit or PR:

| File | What breaks if not updated |
|------|---------------------------|
| `README.md` | Version badge and question table reference the old version |
| `metric/CHANGELOG.md` | No record of the change; violates the project's versioning contract with users |
| `CITATION.cff` | `version` and `date-released` fields are stale; published citations will reference the wrong version |

**PATCH** changes (guidance text only — no change to question meaning, weight, or ID) are lighter: update only the metric YAML. Downstream files are not required unless they quote guidance text verbatim.

---

## Recommended Workflow for Proposing Changes

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

---

## Coupled File Groups Manifest

Use this as a checklist when implementing any metric change.

### Group A — Core metric file
- `metric/airbds_metric_vX.Y.yaml`

> Never hand-edit. For v0.4 (current) it is generated from the working group's Google Sheet by `metric/src/scripts/build_metric_yaml_and_csv_from_google_sheet_v0.4.py`. See [How the v0.4 metric file is generated](#how-the-v04-metric-file-is-generated).

### Group B — Downstream version-carrying files *(MINOR or MAJOR changes only)*
- `README.md` — version badge, question table
- `metric/CHANGELOG.md` — add a new entry at the top referencing the originating Issue
- `CITATION.cff` — update `version:` and `date-released:` fields

---

## Versioning Quick Reference

| Change type | Description | Version bump | Files to update |
|-------------|-------------|-------------|-----------------|
| **PATCH** | Guidance text clarification only — no change to question meaning, weights, or IDs | `0.4` → `0.4.1` | Group A |
| **MINOR** | Question added, removed, or reworded | `0.4` → `0.5` | Groups A, B |
| **MAJOR** | Weight point value or grade threshold changed | `0.4` → `1.0` | Groups A, B |

The canonical versioning policy is defined in [CONTRIBUTING.md](../CONTRIBUTING.md).

---

## Questions?

Open an Issue at [github.com/AIBIO-UK/airbds-metric/issues](https://github.com/AIBIO-UK/airbds-metric/issues) or contact the working group at [info@aibio.ac.uk](mailto:info@aibio.ac.uk).
