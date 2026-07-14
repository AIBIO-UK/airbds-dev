# Reviewer guidance — understanding AIRBDS scores

> **⚠️ Dormant — the manual review process is not live.** Nobody is currently
> running the human reviewer workflow this page supports, and the CI that scored
> submitted reviews is disabled. The scoring *concepts* below remain accurate
> (they describe the metric itself), but the surrounding process does not run.
> See [`reviews/README.md`](README.md) for what in this directory is still live.

Background on how the metric turns a review into a score and grade, to help
interpret a result. The **authoritative, machine-readable** definitions live in
the metric YAML (`metric/airbds_metric_v<version>.yaml`): `grade_points` (the
tier points) and `grading` (the per-grade thresholds). This page is the human
rationale behind them.

## Why questions are weighted

Each question is graded into one of three tiers, worth different points when
answered `Yes` (a `No` always scores 0):

| Tier | Points | Why |
|------|--------|-----|
| **Critical** | 80 | Failing a Critical question indicates a fundamental problem that severely limits the dataset's suitability for AI/ML use. |
| **Important** | 5 | Important questions represent best practices affecting reproducibility, interoperability, or usability. |
| **Optional** | 2 | Optional questions capture desirable but non-essential characteristics. |

A dataset's weighted score is the sum of points for its `Yes` answers.

## Grades

A dataset earns the **highest** grade for which it meets *both* the per-tier
pass-rate criteria *and* that grade's minimum total score (`min_score`). The
exact `min_score` and pass-rate values are in the metric YAML's `grading` block
and can differ between metric versions.

| Grade | Badge colour | Means |
|-------|--------------|-------|
| 🟡 **Gold** | `#ffc107` | Passes all Critical and Important questions, plus ≥ 50% of Optional. |
| ⚪ **Silver** | `#c0c0c0` | Passes all Critical, plus ≥ 50% of Important. |
| 🟤 **Bronze** | `#cd7f32` | Passes most Critical questions. |
| 🔴 **Caution** | `#dc3545` | May have serious issues — fails one or more Critical criteria. |

The badge colours are a presentation reference only — no tool reads them from
the repo.

## Ethics questions

Ethics-scope questions default to `"Yes"` for datasets that contain **no human
or animal subject data** — set `not_applicable: true` and note it in the
comments. In the metric these questions carry `not_applicable_default: "Yes"`.
