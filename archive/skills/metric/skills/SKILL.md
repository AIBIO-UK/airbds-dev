---
name: metric-update-propagation
description: >
  Use this skill when any file under metric/ has been changed and the change
  needs to be propagated consistently to all coupled files across the repository.
  Triggers include: a request to "update the metric", "bump the metric version",
  or "propagate metric changes". Do NOT use for adding new dataset
  reviews — use the assessment skill for that.
version: 1.0.0
scope: metric/
metadata:
  hermes:
    tags: [maintenance, versioning, governance]
    category: maintenance
---

# AIRBDS Metric Update Propagation Skill

You are an expert in the AIRBDS metric repository structure. This skill guides you through propagating a change made to one file in `metric/` consistently to **all coupled files** across the repository — so that every file references the same metric version and no downstream tool silently operates on stale data.

> **Repository note:** as of this reorganisation, `metric/` produces **YAML only** — the CSV companion format has been dropped from the metric pipeline. The v0.3 `.xlsx`-sourced build, the `reviews/` submission/scoring subsystem, the assessment skills (`skills/`), and the automated `metric-alignment-check` workflow have all been moved to `archive/skills/` or `archive/deactivated/` and are currently inactive. Steps below that touch those areas are marked **(archived)** — skip them unless the relevant subsystem has been reactivated. The one thing that stays live and must not be broken is the v0.4 metric ↔ Google Sheet sync (`metric/src/scripts/build_metric_yaml_and_csv_from_google_sheet_v0.4.py`, checked by `.github/workflows/metric-upstream-drift-check.yml`).

**When to invoke this skill:**
- A contributor has updated a metric file and asks you to "propagate the change"
- You are implementing a metric version bump (PATCH, MINOR, or MAJOR)

**When NOT to invoke this skill:**
- Adding a new dataset review (use `archive/skills/GF/GF-airbds-assessment-skill/SKILL.md` instead, currently archived)
- Making changes outside of the metric (e.g. editing reviews, scripts, or docs unrelated to the metric version)

---

## Step 0 — Read These Files First

Before doing anything else, read the following files so you have complete context:

1. `metric/airbds_metric_v*.yaml` — identify the **current metric version** from the `version:` field, and the `grade_points`/`grading` scoring rules
2. `metric/README.md` — the Coupled File Groups manifest (your checklist)
3. `metric/CHANGELOG.md` — understand the existing entry format before adding a new one
4. The file(s) that were actually changed — determine from `git status` or `git diff`
5. **(archived)** `archive/deactivated/reviews/review_template.yaml` — current blank review template schema, if the reviews subsystem is being reactivated alongside this change

---

## Step 1 — Determine the Change Type

Classify the change using the table below. The change type determines which files you must update.

| Change type | Definition | Version bump example | Files to update |
|-------------|-----------|---------------------|-----------------|
| **PATCH** | Guidance text clarification only — no change to question meaning, weight tier, or question ID | `0.4` → `0.4.1` | Group A only |
| **MINOR** | Question added, removed, or reworded; or `schema_version` field changes | `0.4` → `0.5` | Groups A and C |
| **MAJOR** | Weight point value (Critical/Important/Optional) or grade threshold (Caution/Bronze/Silver/Gold) changed | `0.4` → `1.0` | Groups A and C |

**How to determine the type from a diff:**
- If only `guidance:` text changed under any question → PATCH
- If any `question:`, `grade:`, `scope:` field, or a question id (the map key), changed, or a question was added/removed → MINOR
- If any value under `grade_points` or `grading` changed → MAJOR

---

## Step 2 — Propagation Procedure

Work through the relevant steps below. Mark each as complete before moving to the next.

---

### For ALL change types (PATCH, MINOR, MAJOR)

#### A. Verify the primary YAML file content

Confirm the intended change is correct and complete in the YAML file. `metric/` has no CSV companion to regenerate — YAML is the only committed format.

#### B. Regenerate from the Google Sheet, or hand-edit and keep in sync with it

For v0.4, the canonical source is the working group's Google Sheet, not the YAML file itself — see `metric/src/README.md`. If the change originated in the sheet, regenerate with:
```
python3 metric/src/scripts/build_metric_yaml_and_csv_from_google_sheet_v0.4.py
```
If you hand-edit `metric/airbds_metric_v0.4.yaml` directly instead, be aware `.github/workflows/metric-upstream-drift-check.yml` will report drift against the sheet on its next scheduled run until the sheet is updated to match.

#### C. **(archived)** Update `archive/deactivated/reviews/review_template.yaml`

Only relevant if the reviews subsystem has been reactivated. Update `schema_version` to match, then regenerate `archive/deactivated/reviews/review_template.csv`.

---

### For MINOR and MAJOR changes only (new metric version required)

> For PATCH changes, skip this section entirely. PATCH changes edit the existing `vX.Y.yaml` file in place; no new version file is created and no downstream files need updating.

#### D. Determine the new version number

Using semantic versioning:
- MINOR bump: increment the second component (e.g. `0.4` → `0.5`)
- MAJOR bump: increment the first component, reset second (e.g. `0.4` → `1.0`)

Confirm the current version by reading the `version:` field in `metric/airbds_metric_v0.4.yaml`.

#### E. Create new metric version file (keep old versions)

Create `metric/airbds_metric_vNEW.yaml` — copy from the old YAML, apply your changes, update the `version:` and `schema_version:` fields to `"NEW"`.

**Do NOT delete** older `metric/airbds_metric_v*.yaml` files. Old versions are retained for archival so that existing reviews (which carry a matching `schema_version`) can still be validated if the reviews subsystem is reactivated.

#### F. **(archived)** Review processor & review workflows

`archive/deactivated/reviews/src/scripts/review_processor.py` and its CI workflows are archived under `archive/deactivated/`. If reactivated, no path changes are needed there — the processor is metric-driven and auto-selects `metric/airbds_metric_v<schema_version>.yaml`.

#### G. Update `README.md`

Search for the old version string throughout the file. Key locations:
- Version badge URL (e.g. `img.shields.io/badge/metric%20version-v0.4-blue`)
- Question table (update if any question text changed — MINOR/MAJOR with question changes)
- Any download link references

Use `grep -n "v0\.4\|0\.4"` README.md`` to locate all occurrences before editing.

#### H. Update `metric/CHANGELOG.md`

Add a new entry **at the top**, above the existing latest entry. Format:

```markdown
## [NEW] — YYYY-MM-DD

### Changed
- <Describe the change; reference the originating GitHub Issue number, e.g. "(#42)">

### Added  ← (only if a new question was added)
- <Description>

### Removed  ← (only if a question was removed)
- <Description>
```

Use today's date in `YYYY-MM-DD` format. Follow the existing entry style in `metric/CHANGELOG.md` exactly.

#### I. Update `CITATION.cff`

Update two fields:
- `version: "0.4"` → `"NEW"`
- `date-released: "YYYY"` → current year

#### J. **(archived)** Update the assessment skills

`archive/skills/GF/GF-airbds-assessment-skill/SKILL.md`, `archive/skills/testing/airbds-assessment-skill/`, and `archive/skills/development/airbds-assessment-skill/` all embed version-specific metric content. These are archived and inactive — only update them if the skills subsystem is being reactivated alongside this metric change. When reactivated, also update `archive/skills/versions.json` (the per-channel runtime update manifest) and validate with `python3 archive/skills/scripts/validate-skills-versions.py`.

#### K. **(archived)** Update the reviews tutorials

`archive/deactivated/reviews/docs/tutorial-yaml.md` and `tutorial-csv.md` contain version-specific path references. Only relevant if the reviews subsystem is reactivated.

#### L. Verify `archive/skills/claude-plugin/marketplace.json`

**(archived)** This file does not carry the metric version directly. Only relevant if the skills/plugin subsystem is reactivated — confirm its `skills` path still points at a valid, live skill directory before reactivating.

#### M. Update `metric/README.md` (this folder)

Search for any old version references in `metric/README.md` (the contributor guide). Update any stale version numbers to `vNEW`.

---

## Step 3 — Version Number Conventions

**Two independent versioning schemes exist in this repository. Keep them separate.**

| Scheme | Used in | Example | Governs |
|--------|---------|---------|---------|
| **Metric version** | `airbds_metric_vX.Y.yaml` filename; the metric's and each review's `schema_version` field | `0.3`, `0.4`, `1.0` | The scoring metric itself (questions, weights, grades) |
| **Skill version** | `SKILL.md` frontmatter `version:` field (archived skills) | `0.1.2`, `0.2.0-GF` | The assessment skill's behaviour and embedded content |

When the metric version changes:
- The **metric version** always increments (PATCH/MINOR/MAJOR as classified in Step 1)
- The **skill version** (if the skills subsystem is reactivated) increments only if the skill's embedded content changed as a result

---

## Step 4 — The metric's source

The **live, canonical source** for v0.4 is the working group's public Google Sheet. `metric/src/scripts/build_metric_yaml_and_csv_from_google_sheet_v0.4.py` pulls the Scoring and Lookups tabs and regenerates `metric/airbds_metric_v0.4.yaml` (YAML only). `.github/workflows/metric-upstream-drift-check.yml` polls this sheet weekly and opens an issue if the committed YAML has drifted from it. **Do not break this path.**

**(archived)** The v0.3 metric was instead sourced from a hand-edited `.xlsx` workbook (`archive/deactivated/metric/upstream/`) via `archive/deactivated/metric/src/scripts/build_metric_yaml_and_csv_from_spreadsheet_v0.3.py`. This pathway is retired; v0.3 files are kept only for scoring old reviews if the reviews subsystem is reactivated.

---

## Step 5 — Summary Output

After completing all applicable steps, produce a structured summary for the contributor:

```
## Metric Update Propagation Summary

**Change type:** PATCH / MINOR / MAJOR
**Old metric version:** 0.4
**New metric version:** NEW (or "0.4 — in-place PATCH, no version bump")

### Files modified:
- metric/airbds_metric_vNEW.yaml — [description of change]
- README.md — version badge, question table, download links updated
- metric/CHANGELOG.md — new entry added for vNEW
- CITATION.cff — version and date-released updated
- metric/README.md — version references updated

### Files NOT updated and why:
- archive/skills/... assessment skills, archive/deactivated/reviews/... — archived/inactive; only touch if that subsystem is being reactivated alongside this change
- archive/deactivated/metric/upstream/... — retired v0.3 source; not regenerated

### Next step:
Open a pull request referencing the originating GitHub Issue (#N):
  https://github.com/AIBIO-UK/airbds-metric/compare
```

---

## Quick Reference: Files Changed by Change Type

| File | PATCH | MINOR | MAJOR |
|------|-------|-------|-------|
| `metric/airbds_metric_vX.Y.yaml` (in-place or new) | ✅ | ✅ | ✅ |
| `README.md` | — | ✅ | ✅ |
| `metric/CHANGELOG.md` | — | ✅ | ✅ |
| `CITATION.cff` | — | ✅ | ✅ |
| `metric/README.md` (this folder) | — | ✅ | ✅ |
| `.github/workflows/metric-upstream-drift-check.yml` | — | — | — |
| *(archived)* `archive/deactivated/reviews/review_template.yaml` | ✅* | ✅ | ✅ |
| *(archived)* `archive/skills/GF/GF-airbds-assessment-skill/SKILL.md` | — | ✅ | ✅ |
| *(archived)* `archive/skills/versions.json` | — | per channel reactivated | per channel reactivated |
| *(archived)* `archive/deactivated/reviews/docs/tutorial-{yaml,csv}.md` | — | ✅ | ✅ |

> *For `review_template`: only relevant if the reviews subsystem is reactivated, and only if the PATCH affects it.
