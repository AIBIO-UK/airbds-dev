---
name: metric-update-propagation
description: >
  Use this skill when any file under metric/ has been changed and the change
  needs to be propagated consistently to all coupled files across the repository.
  Triggers include: the metric-alignment-check GitHub Actions workflow failing,
  a request to "update the metric", "bump the metric version", "propagate metric
  changes", or "fix the alignment check". Do NOT use for adding new dataset
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

**When to invoke this skill:**
- The `metric-alignment-check` GitHub Actions workflow has flagged an out-of-sync state (a GitHub Issue or PR comment was created)
- A contributor has updated a metric file and asks you to "propagate the change"
- You are implementing a metric version bump (PATCH, MINOR, or MAJOR)

**When NOT to invoke this skill:**
- Adding a new dataset review (use `skills/GF/GF-airbds-assessment-skill/SKILL.md` instead)
- Making changes outside of the metric (e.g. editing reviews, scripts, or docs unrelated to the metric version)

---

## Step 0 — Read These Files First

Before doing anything else, read the following files so you have complete context:

1. `metric/airbds_metric_v*.yaml` — identify the **current metric version** from the `version:` field
2. `metric/scoring_schema.yaml` — current grade thresholds and weight definitions
3. `metric/review_template.yaml` — current blank review template schema
4. `metric/README.md` — the Coupled File Groups manifest (your checklist)
5. `CHANGELOG.md` — understand the existing entry format before adding a new one
6. The file(s) that were actually changed — determine from `git status`, `git diff`, or the GitHub Actions output that triggered this skill

If running in response to a failed alignment check, read the GitHub Issue or PR comment body — it lists the exact files that are missing from the update.

---

## Step 1 — Determine the Change Type

Classify the change using the table below. The change type determines which files you must update.

| Change type | Definition | Version bump example | Files to update |
|-------------|-----------|---------------------|-----------------|
| **PATCH** | Guidance text clarification only — no change to question meaning, weight tier, or question ID | `0.3` → `0.3.1` | Groups A, B, C only |
| **MINOR** | Question added, removed, or reworded; or `schema_version` field changes | `0.3` → `0.4` | Groups A, B, C, and D |
| **MAJOR** | Weight point value (Critical/Important/Optional) or grade threshold (Caution/Bronze/Silver/Gold) changed | `0.3` → `1.0` | Groups A, B, C, and D |

**How to determine the type from a diff:**
- If only `guidance:` text changed under any question → PATCH
- If any `question:`, `grade:`, `scope:`, `theme:` field, or a question id (the map key), changed, or a question was added/removed → MINOR
- If any value under `grade_points` or `grading` changed → MAJOR

---

## Step 2 — Propagation Procedure

Work through the relevant steps below. Mark each as complete before moving to the next.

---

### For ALL change types (PATCH, MINOR, MAJOR)

#### A. Verify the primary YAML file content

Confirm the intended change is correct and complete in the YAML file before regenerating any companions.

#### B. Regenerate the CSV companion for each changed YAML

The CSV files must exactly mirror their YAML counterparts in content. Use the existing CSV file as a structural reference for column order and formatting.

**For `metric/airbds_metric_vX.Y.csv`:**
The CSV has one header row and one row per question. Columns (in order):
`question_id, scope, theme, weight, weight_points, mapped_from, question, guidance, not_applicable_default`

Read `metric/airbds_metric_v0.3.csv` to confirm the exact column names and order before writing.

**For `metric/scoring_schema.csv`:**
Read the existing `metric/scoring_schema.csv` to confirm the structure (it mirrors the YAML sections for `answers`, `weights`, and `grades`).

**For `metric/review_template.csv`:**
The CSV template has two sections:
- Section A: metadata rows (`field, value` format; one row per reviewer/dataset field)
- Section B: question rows (`question_id, answer, comments, not_applicable` format; one blank row per question)

Read `metric/review_template.csv` to confirm the exact structure before writing.

#### C. Write the regenerated CSV file(s) to disk

Use the Write tool to overwrite the existing CSV file(s) with the regenerated content.

---

### For MINOR and MAJOR changes only (new metric version required)

> For PATCH changes, skip this section entirely. PATCH changes edit the existing `v0.3.yaml/csv` files in place; no new version file is created and no downstream files need updating.

#### D. Determine the new version number

Using semantic versioning:
- MINOR bump: increment the second component (e.g. `0.3` → `0.4`)
- MAJOR bump: increment the first component, reset second (e.g. `0.3` → `1.0`)

Confirm the current version by reading the `version:` field in `metric/airbds_metric_v0.3.yaml`.

#### E. Create new metric version files (keep old versions)

Create:
- `metric/airbds_metric_vNEW.yaml` — copy from the old YAML, apply your changes, update the `version:` and `schema_version:` fields to `"NEW"`
- `metric/airbds_metric_vNEW.csv` — regenerate from the new YAML content

**Do NOT delete** `metric/airbds_metric_v0.3.yaml` or `metric/airbds_metric_v0.3.csv`. Old versions are retained for archival so that existing reviews (which carry `schema_version: "0.3"`) can still be validated.

#### F. Update `metric/scoring_schema.yaml`

Update the following fields:
- `schema_version: "0.3"` → `"NEW"`
- Under `versioning:`, update `current_version: "0.3"` → `"NEW"`

Then regenerate `metric/scoring_schema.csv`.

#### G. Update `metric/review_template.yaml`

Update `schema_version: "0.3"` → `"NEW"`.

Then regenerate `metric/review_template.csv`.

#### H. Update `scripts/review_processor.py`

Three locations to update:
1. **Line 31:** `SCHEMA_VERSION = "0.3"` → `SCHEMA_VERSION = "NEW"`
2. In the script's docstring or module comment: update the `--metric metric/airbds_metric_v0.3.yaml` example path
3. The `help=` string in the argparse `--metric` argument definition (search for `"Path to airbds_metric_v0.3.yaml"`)

Use `grep -n "0\.3" scripts/review_processor.py` to find all occurrences before editing.

#### I. Update `.github/workflows/review-check.yml`

Search for `airbds_metric_v0.3.yaml` in this file. There are 2 occurrences:
- Line 64: `--metric metric/airbds_metric_v0.3.yaml` in the `Process review files` step
- Line 104: in the Fork PR notice step summary

Update both to `--metric metric/airbds_metric_vNEW.yaml`.

#### J. Update `.github/workflows/review-test.yml`

Search for `airbds_metric_v0.3.yaml`. There are 5 occurrences (one per test case). Update all to `metric/airbds_metric_vNEW.yaml`.

#### K. Update `README.md`

Search for `v0.3` and `0.3` throughout the file. Key locations:
- Version badge URL (e.g. `img.shields.io/badge/metric%20version-v0.3-blue`)
- File structure listing (filename references to `airbds_metric_v0.3`)
- Download link references
- Question table (update if any question text changed — MINOR/MAJOR with question changes)
- Processor command example: `--metric metric/airbds_metric_v0.3.yaml`

Use `grep -n "v0\.3\|0\.3" README.md` to locate all occurrences before editing.

#### L. Update `CHANGELOG.md`

Add a new entry **at the top**, above the existing `## [0.3]` entry. Format:

```markdown
## [NEW] — YYYY-MM-DD

### Changed
- <Describe the change; reference the originating GitHub Issue number, e.g. "(#42)">

### Added  ← (only if a new question was added)
- <Description>

### Removed  ← (only if a question was removed)
- <Description>
```

Use today's date in `YYYY-MM-DD` format. Follow the existing entry style in `CHANGELOG.md` exactly.

#### M. Update `CITATION.cff`

Update two fields:
- `version: "0.3"` → `"NEW"`
- `date-released: "YYYY"` → current year

#### N. Update `skills/GF/GF-airbds-assessment-skill/SKILL.md`

This file contains multiple version-specific references. Update the following:

1. **Frontmatter `version:` field** — increment the MINOR component of the skill version (e.g. `0.1.0-GF` → `0.2.0-GF`) because the embedded content changed
2. **"using the AIRBDS Metric v0.3"** in the initialization behavior section → `vNEW`
3. **`metric/airbds_metric_v0.3.yaml`** in the Scoring Reference Files section → `metric/airbds_metric_vNEW.yaml`
4. **Embedded YAML template** — update `schema_version: "0.3"` → `"NEW"` in the schema example
5. **`process_comments: "Review conducted against AIRBDS Metric v0.3."`** → `vNEW`
6. **Files table at the bottom** — update `metric/airbds_metric_v0.3.yaml` → `metric/airbds_metric_vNEW.yaml`
7. **Question list table** — if any question text or weight tier changed (MINOR/MAJOR with question changes), update the embedded question list in full to match the new metric

Use `grep -n "v0\.3\|0\.3\|0\.1\.0-GF" skills/GF/GF-airbds-assessment-skill/SKILL.md` to locate all occurrences before editing.

#### O. Update `skills/testing/airbds-assessment-skill/SKILL.md`

> **Important:** This skill references an XLSX spreadsheet template. Do NOT update the template filename in this SKILL.md unless the XLSX file has also been regenerated. Updating the path to a non-existent XLSX will silently break the testing skill.

If the XLSX has been regenerated with the new version, update:
- The template filename reference (e.g. `AIRBDS-Core-Metric-scoring-v0.3.xlsx` → `vNEW.xlsx`)

If the XLSX has **not** been regenerated:
- Add a comment inline in the SKILL.md noting: `# NOTE: This skill still references the v0.3 XLSX template. Update when XLSX is regenerated for vNEW.`

#### P. Update `docs/tutorial-yaml.md`

Run `grep -n "v0\.3" docs/tutorial-yaml.md` to find all occurrences. Update all file path references from `airbds_metric_v0.3` to `airbds_metric_vNEW`.

#### Q. Update `docs/tutorial-csv.md`

Same as above: `grep -n "v0\.3" docs/tutorial-csv.md`, update all path references.

#### R. Verify `.claude-plugin/marketplace.json`

Read this file and confirm the skills path `./skills/testing/airbds-assessment-skill` is still valid. This file does not carry the metric version directly — no update is typically needed. If the path has changed for any reason, update it.

#### S. Update `metric/README.md` (this file)

Search for any `v0.3` version references in `metric/README.md` (the contributor guide). Update any stale version numbers to `vNEW`.

---

## Step 3 — Version Number Conventions

**Two independent versioning schemes exist in this repository. Keep them separate.**

| Scheme | Used in | Example | Governs |
|--------|---------|---------|---------|
| **Metric version** | `airbds_metric_vX.Y.yaml`, `schema_version` field, `SCHEMA_VERSION` constant | `0.3`, `0.4`, `1.0` | The scoring metric itself (questions, weights, grades) |
| **Skill version** | `SKILL.md` frontmatter `version:` field | `0.1.2`, `0.2.0-GF` | The assessment skill's behaviour and embedded content |

When the metric version changes:
- The **metric version** always increments (PATCH/MINOR/MAJOR as classified in Step 1)
- The **skill version** increments **only if the skill's embedded content changed** as a result — which is true for all MINOR and MAJOR metric changes (embedded question table, YAML templates, file paths all need updating)
- The **testing skill version** (`skills/testing/airbds-assessment-skill/SKILL.md`) increments only if the testing skill's XLSX content or behaviour changed

---

## Step 4 — XLSX Caveat

The root-level file `AIRBDS Core Metric scoring v0.3 - _initials_-_#_ TEMPLATE.xlsx` is **not programmatically regenerated** by this skill. It is an archived working-group spreadsheet that carries the version in its filename.

If a new metric version is released and the team decides to update the XLSX:
1. Open the XLSX in a spreadsheet application and make the necessary changes manually
2. Rename the file: `AIRBDS Core Metric scoring vNEW - _initials_-_#_ TEMPLATE.xlsx`
3. Then update `skills/testing/airbds-assessment-skill/SKILL.md` to reference the new filename (Step O above)

**Do not update the testing skill's XLSX path until the XLSX file actually exists.**

---

## Step 5 — Summary Output

After completing all applicable steps, produce a structured summary for the contributor:

```
## Metric Update Propagation Summary

**Change type:** PATCH / MINOR / MAJOR
**Old metric version:** 0.3
**New metric version:** NEW (or "0.3 — in-place PATCH, no version bump")

### Files modified:
- metric/airbds_metric_vNEW.yaml — [description of change]
- metric/airbds_metric_vNEW.csv — regenerated from YAML
- metric/scoring_schema.yaml — schema_version updated to NEW
- metric/scoring_schema.csv — regenerated
- metric/review_template.yaml — schema_version updated to NEW
- metric/review_template.csv — regenerated
- scripts/review_processor.py — SCHEMA_VERSION and --metric path updated
- .github/workflows/review-check.yml — --metric path updated (2 occurrences)
- .github/workflows/review-test.yml — --metric path updated (5 occurrences)
- README.md — version badge, file listing, download links updated
- CHANGELOG.md — new entry added for vNEW
- CITATION.cff — version and date-released updated
- skills/GF/GF-airbds-assessment-skill/SKILL.md — embedded templates, paths, skill version updated
- docs/tutorial-yaml.md — path references updated
- docs/tutorial-csv.md — path references updated
- metric/README.md — version references updated

### Files NOT updated and why:
- skills/testing/airbds-assessment-skill/SKILL.md — XLSX not regenerated; left a NOTE comment
- AIRBDS Core Metric scoring v0.3...xlsx — requires manual regeneration

### Next step:
Open a pull request referencing the originating GitHub Issue (#N):
  https://github.com/AIBIO-UK/airbds-metric/compare
```

---

## Quick Reference: Files Changed by Change Type

| File | PATCH | MINOR | MAJOR |
|------|-------|-------|-------|
| `metric/airbds_metric_vX.Y.yaml` (in-place or new) | ✅ | ✅ | ✅ |
| `metric/airbds_metric_vX.Y.csv` | ✅ | ✅ | ✅ |
| `metric/scoring_schema.yaml` | ✅* | ✅ | ✅ |
| `metric/scoring_schema.csv` | ✅* | ✅ | ✅ |
| `metric/review_template.yaml` | ✅* | ✅ | ✅ |
| `metric/review_template.csv` | ✅* | ✅ | ✅ |
| `scripts/review_processor.py` | — | ✅ | ✅ |
| `.github/workflows/review-check.yml` | — | ✅ | ✅ |
| `.github/workflows/review-test.yml` | — | ✅ | ✅ |
| `README.md` | — | ✅ | ✅ |
| `CHANGELOG.md` | — | ✅ | ✅ |
| `CITATION.cff` | — | ✅ | ✅ |
| `skills/GF/GF-airbds-assessment-skill/SKILL.md` | — | ✅ | ✅ |
| `skills/testing/airbds-assessment-skill/SKILL.md` | — | if XLSX regenerated | if XLSX regenerated |
| `docs/tutorial-yaml.md` | — | ✅ | ✅ |
| `docs/tutorial-csv.md` | — | ✅ | ✅ |
| `metric/README.md` (this folder) | — | ✅ | ✅ |

> *For `scoring_schema` and `review_template`: only update if the PATCH affects those specific files (e.g. a guidance-only change to `scoring_schema.yaml`). If only the metric question YAML was patched, these files may not need to change.
