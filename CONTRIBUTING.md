# Contributing to the AIRBDS AI-Readiness Dataset Scoring Metric

Thank you for your interest in contributing! This document outlines how to
contribute to the **AIRBDS AI-Readiness Dataset Scoring Metric** — a versioned,
machine-readable framework for assessing the AI-readiness of bioscience
datasets, developed by the
[AI-Ready Bioscience Datasets (AIRBDS) working group](https://aibio.ac.uk/about/working-groups/airbds/)
of the AIBIO-UK network.

We primarily use a GitHub-based workflow. Contributions are made via Pull
Requests (PRs) which are reviewed and merged by the working group maintainers.

---

## Table of Contents

- [Ways to Contribute](#ways-to-contribute)
  - [Submitting Dataset Reviews](#submitting-dataset-reviews)
  - [Proposing Metric Changes](#proposing-metric-changes)
  - [Reporting Issues](#reporting-issues)
  - [Pull Requests](#pull-requests)
- [What to Contribute](#what-to-contribute)
- [What Not to Contribute](#what-not-to-contribute)
- [File Structure & YAML Format](#file-structure--yaml-format)
- [Versioning Policy](#versioning-policy)
- [Commit Message Convention](#commit-message-convention)
- [Review Process](#review-process)
- [Contribution Licensing](#contribution-licensing)
- [Code of Conduct](#code-of-conduct)

---

## Ways to Contribute

### Submitting Dataset Reviews

The primary contribution type is a completed dataset review scored using the
AIRBDS metric.

1. **Copy the template:** Start from
   [`reviews/review_template.yaml`](reviews/review_template.yaml) (YAML) or
   [`reviews/review_template.csv`](reviews/review_template.csv) (CSV spreadsheet).
2. **Name your file:** Use the convention
   `reviews/testing/<dataset_accession>_<reviewer_initials>_<n>.yaml`  
   e.g. `reviews/testing/E-MTAB-1234_CH_1.yaml`  
   Initials must be **uppercase letters only** (A-Z, 2–6 characters).
3. **Fill in all fields:** Answer all 27 questions (`"Yes"` or `"No"`, case-sensitive, quoted). For Ethics
   questions (ABC-24 to ABC-27), if the dataset contains no human or animal
   subject data record the answer as `"Yes"` and set `not_applicable: true`
   with a brief comment.
4. **Fill in the `result:` block yourself** — scoring is no longer automated (see
   the notice below), so calculate `weighted_score` and `grade` by running the
   review processor locally.
5. **Submit a PR** — see [Pull Requests](#pull-requests).

> **⚠️ The manual review process is not live.** The `Review Check & Score`
> workflow that used to run on every PR — validating the filename and fields,
> calculating the score and grade, generating the companion YAML/CSV, renaming
> the file, and committing the result back to your branch — has had its
> automatic triggers removed. **None of that happens now.** Run the processor
> yourself instead:
>
> ```bash
> pip install pyyaml
> python3 reviews/src/scripts/review_processor.py --files reviews/testing/<your-review-file>
> ```
>
> It performs the same validation and scoring locally and reports errors the same
> way. See [`reviews/README.md`](reviews/README.md) for what in that directory is
> still live.

Inter-rater reliability is important. Where possible, datasets should be
reviewed independently by at least two members before the review is merged.

---

### Proposing Metric Changes

Changes to the metric (new questions, reworded questions, new guidance,
weighting adjustments) should be proposed via a GitHub Issue before a PR is
opened. This ensures discussion and working-group consensus before any change
is committed.

**Before proposing a change:**
- Check open and closed Issues to avoid duplicates.
- Consult the [Versioning Policy](#versioning-policy) to understand how your
  proposed change will affect the version number.

**When opening an Issue for a metric change:**
- Use the title prefix `[Metric Change]`
- State which question(s) are affected (e.g. `ABC-12`)
- Describe the rationale for the change and any evidence or references that
  support it
- Indicate whether the change is: guidance-only (PATCH), question rewording
  (MINOR), or weight/threshold change (MAJOR)

---

### Reporting Issues

If you find an error, broken link, or inconsistency anywhere in the repository:

1. **Check existing issues** to see if it has been reported.
2. **Create a new issue** with a clear title and description. Include:
   - The file and line/field affected
   - What the error is and what you expected
   - Steps to reproduce (if applicable)

---

### Pull Requests

The example below is a metric change — the most common contribution now that the
manual review process is dormant. For a review, substitute the review file and
the `review:` commit prefix.

1. **Fork the repository** and create a new branch:
   ```bash
   git checkout -b metric/42-add-abc-29-reproducibility
   ```
2. **Make your changes** following the YAML formats described below.
3. **Validate your YAML** — ensure it is valid YAML:
   ```bash
   python3 -c "import yaml; yaml.safe_load(open('your_file.yaml'))"
   ```
4. **Commit your changes** using the [convention below](#commit-message-convention):
   ```bash
   git add metric/airbds_metric_v0.4.yaml CHANGELOG.md
   git commit -m "metric: add ABC-29 reproducibility question"
   ```
5. **Push to your fork:**
   ```bash
   git push origin metric/42-add-abc-29-reproducibility
   ```
6. **Open a PR** against the `main` branch. Provide:
   - A clear title and description
   - A summary of the proposed change and the originating Issue
   - The dataset name and accession (for review PRs)

---

## What to Contribute

- ✅ Completed dataset reviews (`reviews/testing/*.yaml`)
- ✅ Corrections to existing reviews (factual errors, updated dataset versions)
- ✅ Proposed question additions, removals, or rewordings — via Issue first
- ✅ Guidance clarifications (PATCH-level) — directly as a PR
- ✅ Fixes for typos, broken links, or formatting errors
- ✅ Improvements to the README, CONTRIBUTING guide, or documentation

---

## What Not to Contribute

- ❌ Changes to the core metric YAML without prior working-group discussion
  (open an Issue first)
- ❌ Proprietary or closed datasets that cannot be publicly linked
- ❌ Reviews submitted in formats other than YAML (e.g. Excel, CSV)
- ❌ Changes to CI/CD or repository infrastructure without prior discussion
- ❌ Promotional content unrelated to AI-ready bioscience datasets

---

## Which repository should a link point at?

There are two repositories, and the distinction is deliberate — please don't
"fix" one into the other:

| Kind of link | Repository | Examples |
|---|---|---|
| **Identity / attribution** — how the metric is cited and credited | [`airbds-metric`](https://github.com/AIBIO-UK/airbds-metric) (publication) | `CITATION.cff` `repository-code`, the suggested-citation blocks in `LICENSE.md` and `README.md`, the `repository:` field in the generated metric YAMLs, tutorial footers |
| **Actual use** — anything a reader clicks to *do* something | [`airbds-dev`](https://github.com/AIBIO-UK/airbds-dev) (this repo) | `git clone`, opening a PR, downloading a skill, the skills' update manifest and `skill_update_url`, `/plugin marketplace add` |

The canonical identity of the metric is the publication repository. But the
working material lives here, so anything actionable must resolve here for now.

> The `repository:` field in the metric YAMLs is **generated** — it comes from the
> `CONFIG` block in the build scripts under `metric/src/scripts/`. Change it there
> and regenerate; never hand-edit the YAML.

> The skills' update URLs are a special case: the URL is baked into each published
> skill zip, so repointing it strands every already-installed skill. See
> [`skills/docs/MAINTENANCE.md`](skills/docs/MAINTENANCE.md) before changing them.

---

## File Structure & YAML Format

```
airbds-dev/
├── metric/
│   └── airbds_metric_v0.4.yaml   # Canonical metric (questions, weights, grading rules)
├── reviews/                      # Reviews + review tooling
│   ├── review_template.yaml      # Blank template for new reviews
│   └── testing/                  # Completed dataset reviews (one file per review)
│       └── <accession>_<initials>_<n>.yaml
├── CITATION.cff
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE.md
├── CHANGELOG.md
└── README.md
```

All metric and review files are YAML. Key rules:
- Use `"Yes"` or `"No"` (quoted strings) for all answer fields.
- Do not leave required fields blank in submitted reviews (use `""` only in
  the template).
- Follow the exact field names defined in `review_template.yaml`.
- Ensure all YAML is valid before submitting (see `python3 -c "import yaml; ..."` above).

---

## Versioning Policy

The metric follows [Semantic Versioning](https://semver.org/)
(**MAJOR.MINOR.PATCH**):

| Change type | Version bump |
|---|---|
| Guidance-only clarifications (no change to question meaning) | PATCH |
| Question additions, deletions, or rewordings that change meaning | MINOR |
| Changes to scoring weights or grade thresholds | MAJOR |

The canonical metric file is versioned in its filename
(e.g. `airbds_metric_v0.4.yaml`). When a new version is released:
1. The new YAML file is added (e.g. `airbds_metric_v1.0.yaml`)
2. The old file is kept for archival purposes
3. `CHANGELOG.md` is updated
4. A GitHub Release is tagged (e.g. `v1.0.0`)
5. `CITATION.cff` is updated with the new version

Existing dataset reviews reference the metric version they were scored against
via the `schema_version` field.

---

## Commit Message Convention

Use the following prefixes for clarity:

| Prefix | Use for |
|---|---|
| `review:` | Adding or updating a dataset review |
| `metric:` | Changes to the metric YAML |
| `docs:` | Documentation changes (README, CONTRIBUTING, etc.) |
| `fix:` | Typo, broken link, or formatting fix |
| `chore:` | Repo infrastructure (CI, .gitignore, etc.) |
| `release:` | Version bump and release preparation |

Example: `review: add review for ArrayExpress E-GEOD-12345 (CH)`

---

## Review Process

Working group maintainers will review all Pull Requests.

- We aim to respond within **14 days**.
- Feedback may be provided via PR comments; please respond or revise promptly.
- For dataset reviews: a second independent review is encouraged before merging.
- For metric changes: working-group consensus (via the linked Issue) is required
  before merging.
- Once approved, a maintainer will merge into `main`.

---

## Contribution Licensing

By contributing, you agree that your contributions will be licensed under
[**CC BY 4.0**](https://creativecommons.org/licenses/by/4.0/). All contributed
content must respect the copyrights of others.

---

## Code of Conduct

All contributors are expected to abide by the
[Code of Conduct](CODE_OF_CONDUCT.md). Please read it before participating.
