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
   git add metric/airbds_metric_v0.4.yaml metric/CHANGELOG.md
   git commit -m "metric: add ABC-29 reproducibility question"
   ```
5. **Push to your fork:**
   ```bash
   git push origin metric/42-add-abc-29-reproducibility
   ```
6. **Open a PR** against the `main` branch. Provide:
   - A clear title and description
   - A summary of the proposed change and the originating Issue

---

## What to Contribute

- ✅ Proposed question additions, removals, or rewordings — via Issue first
- ✅ Guidance clarifications (PATCH-level) — directly as a PR
- ✅ Fixes for typos, broken links, or formatting errors
- ✅ Improvements to the README, CONTRIBUTING guide, or documentation

---

## What Not to Contribute

- ❌ Changes to the core metric YAML without prior working-group discussion
  (open an Issue first)
- ❌ Proprietary or closed datasets that cannot be publicly linked
- ❌ Changes to CI/CD or repository infrastructure without prior discussion
- ❌ Promotional content unrelated to AI-ready bioscience datasets

---

## File Structure & YAML Format

```
airbds-metric/
├── metric/
│   ├── airbds_metric_v0.4.yaml   # Canonical metric (questions, weights, grading rules)
│   └── CHANGELOG.md
├── CITATION.cff
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE.md
└── README.md
```

The metric is YAML. Key rules:
- Use `"Yes"` or `"No"` (quoted strings) for all answer fields.
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
3. `metric/CHANGELOG.md` is updated
4. A GitHub Release is tagged (e.g. `v1.0.0`)
5. `CITATION.cff` is updated with the new version

---

## Commit Message Convention

Use the following prefixes for clarity:

| Prefix | Use for |
|---|---|
| `metric:` | Changes to the metric YAML |
| `docs:` | Documentation changes (README, CONTRIBUTING, etc.) |
| `fix:` | Typo, broken link, or formatting fix |
| `chore:` | Repo infrastructure (CI, .gitignore, etc.) |
| `release:` | Version bump and release preparation |

Example: `metric: add ABC-29 reproducibility question`

---

## Review Process

Working group maintainers will review all Pull Requests.

- We aim to respond within **14 days**.
- Feedback may be provided via PR comments; please respond or revise promptly.
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
