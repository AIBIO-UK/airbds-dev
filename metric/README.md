# metric/ — AIRBDS Metric Files

> **Before editing any file in this folder, read this document.**

The `metric/` folder is the **single source of truth** for the AIRBDS scoring metric. It contains the versioned question set, the scoring schema, and the blank review template — each in two machine-readable formats. Completed dataset reviews live in `reviews/`, not here.

Changes to this folder have a disproportionate downstream impact. Multiple files across the repository — scripts, GitHub Actions workflows, skills, tutorials, and documentation — all reference the exact metric version and file paths. A partial update (e.g. editing the YAML without regenerating the CSV, or bumping the version without updating the workflow paths) creates silent failures that corrupt inter-rater reliability or break the CI/CD pipeline.

---

## Files in This Folder

| Filename | Format | Purpose | Paired With |
|----------|--------|---------|-------------|
| `airbds_metric_v0.3.yaml` | YAML | **Canonical** 28-question metric: question text, grades, guidance, scopes | `airbds_metric_v0.3.csv` |
| `airbds_metric_v0.3.csv` | CSV | Identical content to the YAML metric; used by spreadsheet workflow | `airbds_metric_v0.3.yaml` |
| `scoring_schema.yaml` | YAML | Grade thresholds (Caution/Bronze/Silver/Gold pass-rates and `min_score`), weight-point definitions, versioning policy | `scoring_schema.csv` |
| `scoring_schema.csv` | CSV | Identical content to scoring_schema.yaml | `scoring_schema.yaml` |
| `review_template.yaml` | YAML | Blank review template (28 answer slots + reviewer metadata); no version in filename — always tracks current metric | `review_template.csv` |
| `review_template.csv` | CSV | Identical content to review_template.yaml | `review_template.yaml` |
| `README.md` | Markdown | This file — contributor guide for the metric folder | — |
| `SKILL.md` | Markdown | AI agent skill for propagating metric changes across the repo | — |

> **Note on versioning:** `scoring_schema` and `review_template` do not carry a version in their filenames, but both contain a `schema_version` field that must always match the current metric version. When the metric version advances, these files must be updated too.

> **Note on new metric versions:** A version bump creates new files (e.g. `airbds_metric_v0.4.yaml` + `.csv`). Old versions are **retained** for archival — reviews carry `schema_version` to record which version they were scored against.

---

## Why ALL Files Must Change Together

### The YAML ↔ CSV pairs must always be identical in content

YAML and CSV files are **not** derived from each other at read time — both are independent files that are read directly. The automated review processor (`scripts/review_processor.py`) loads whichever format was changed; the human spreadsheet workflow reads the CSV. If the YAML is updated but the CSV is not, a researcher using the spreadsheet workflow scores against a different version of the metric than one using the YAML workflow. This is **silent**, produces no error, and **invalidates inter-rater reliability**.

### The downstream impact chain

For any **MINOR** change (question additions, deletions, or rewordings) or **MAJOR** change (weight or grade threshold changes), the following files outside `metric/` must also be updated in the same commit or PR:

| File | What breaks if not updated |
|------|---------------------------|
| `scripts/review_processor.py` | `SCHEMA_VERSION` constant (line 31) still references old version; reviews may be validated against the wrong schema |
| `.github/workflows/review-check.yml` | `--metric metric/airbds_metric_v0.3.yaml` path (2 occurrences) still points to old metric; new reviews auto-scored with old questions |
| `.github/workflows/review-test.yml` | `--metric` path (5 occurrences) still points to old metric; test suite silently runs against old schema |
| `README.md` | Version badge, question table, download links, and processor command examples all reference the old version |
| `CHANGELOG.md` | No record of the change; violates the project's versioning contract with users |
| `CITATION.cff` | `version` and `date-released` fields are stale; published citations will reference the wrong version |
| `skills/GF/GF-airbds-assessment-skill/SKILL.md` | Embedded question table, YAML templates, `schema_version` value, and file paths all reference old version |
| `skills/testing/airbds-assessment-skill/SKILL.md` | Template filename reference (update only if the XLSX is also regenerated) |
| `docs/tutorial-yaml.md` | File path references to `v0.3` in instructions become broken |
| `docs/tutorial-csv.md` | Same as above for spreadsheet tutorial |

**PATCH** changes (guidance text only — no change to question meaning, weight, or ID) are lighter: update only the YAML/CSV pairs. Downstream files are not required unless they quote guidance text verbatim.

---

## Recommended Workflow for Proposing Changes

1. **Check existing Issues** at [github.com/AIBIO-UK/airbds-metric/issues](https://github.com/AIBIO-UK/airbds-metric/issues) before opening a new one — the change may already be under discussion.

2. **Open a GitHub Issue** before writing any code or YAML. Use the title prefix `[Metric Change]`. In the body, state:
   - Which question(s) are affected (e.g. ACM-12, ACM-17)
   - The rationale for the change
   - Whether this is a guidance-only change (**PATCH**), a question rewording/addition/deletion (**MINOR**), or a weight/threshold change (**MAJOR**)
   
   See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full versioning policy.

3. **Discuss on the Issue** until working-group consensus is reached. A maintainer will label the issue `metric-change-pending`.

4. **Fork the repository** and create a branch named `metric/<issue-number>-brief-description` (e.g. `metric/42-add-acm-29-reproducibility`).

5. **Update ALL coupled files** as described in the Coupled File Groups manifest below. This is **not optional** — the automated alignment check will flag partial updates and create a GitHub Issue.

6. **Open a pull request** referencing the original Issue (e.g. `Closes #42`). The `metric-alignment-check` workflow runs automatically on your PR. If it flags any files as out of sync, fix them before requesting review.

7. **Working-group review** and merge by a maintainer.

---

## Coupled File Groups Manifest

Use this as a checklist when implementing any metric change.

### Group A — Core metric pair *(always change together)*
- `metric/airbds_metric_vX.Y.yaml`
- `metric/airbds_metric_vX.Y.csv`

### Group B — Scoring schema pair *(always change together)*
- `metric/scoring_schema.yaml`
- `metric/scoring_schema.csv`

### Group C — Review template pair *(always change together)*
- `metric/review_template.yaml`
- `metric/review_template.csv`

### Group D — Downstream version-carrying files *(MINOR or MAJOR changes only)*
- `README.md` — version badge, question table, download links, processor command examples
- `CHANGELOG.md` — add a new entry at the top referencing the originating Issue
- `CITATION.cff` — update `version:` and `date-released:` fields
- `scripts/review_processor.py` — update `SCHEMA_VERSION` constant and `--metric` path references
- `.github/workflows/review-check.yml` — update `--metric metric/airbds_metric_vX.Y.yaml` (2 occurrences)
- `.github/workflows/review-test.yml` — update `--metric` path (5 occurrences)
- `skills/GF/GF-airbds-assessment-skill/SKILL.md` — update embedded templates, question table, file paths, skill version
- `skills/testing/airbds-assessment-skill/SKILL.md` — update template filename **only if the XLSX is also regenerated**
- `docs/tutorial-yaml.md` — update all `vX.Y` path references
- `docs/tutorial-csv.md` — update all `vX.Y` path references

> `metric/README.md` and `metric/SKILL.md` are documentation files. They do not have YAML/CSV counterparts and are excluded from the automated pair-checking. Update their version references when implementing MINOR or MAJOR changes.

---

## Automated Alignment Check

Every push or pull request that touches a file under `metric/` triggers the `.github/workflows/metric-alignment-check.yml` workflow. It performs the following checks automatically:

**1. YAML ↔ CSV pair check.** For every versioned metric YAML changed, it verifies the matching CSV was also changed in the same commit range, and vice versa. The same check applies to `scoring_schema` and `review_template` pairs.

**2. New-version downstream check.** If a new versioned metric YAML is detected as _Added_ (e.g. `airbds_metric_v0.4.yaml` appears for the first time), the workflow also checks whether `CHANGELOG.md` and `README.md` were updated in the same commit range.

**On misalignment (push events):** The workflow creates a GitHub Issue in this repository titled `[metric-alignment] Out-of-sync metric files detected`, tagged with the `metric-alignment` label. The issue body lists the exact files that are missing and provides remediation instructions.

**On misalignment (pull request events):** In addition to the Issue, the workflow posts a comment directly on the PR listing the files that need to be added before the PR can be merged.

**Deduplication:** If an open `metric-alignment` issue already exists for the same PR or commit SHA, the workflow adds a comment to the existing issue rather than creating a duplicate.

**On alignment restored:** When a subsequent push resolves the misalignment, the workflow closes any open `metric-alignment` issue it finds for that PR/SHA.

**Using the agent skill to fix misalignment:** If you are using Claude Code in this repository, invoke the `metric/SKILL.md` skill to propagate changes automatically. The skill will read the changed file(s), determine the change type, and update all coupled files with a summary of what was modified.

---

## Versioning Quick Reference

| Change type | Description | Version bump | Files to update |
|-------------|-------------|-------------|-----------------|
| **PATCH** | Guidance text clarification only — no change to question meaning, weights, or IDs | `0.3` → `0.3.1` | Groups A, B, C |
| **MINOR** | Question added, removed, or reworded | `0.3` → `0.4` | Groups A, B, C, D |
| **MAJOR** | Weight point value or grade threshold changed | `0.3` → `1.0` | Groups A, B, C, D |

The canonical versioning policy is defined in `metric/scoring_schema.yaml` under `versioning:` and in [CONTRIBUTING.md](../CONTRIBUTING.md).

---

## Questions?

Open an Issue at [github.com/AIBIO-UK/airbds-metric/issues](https://github.com/AIBIO-UK/airbds-metric/issues) or contact the working group at [info@aibio.ac.uk](mailto:info@aibio.ac.uk).
