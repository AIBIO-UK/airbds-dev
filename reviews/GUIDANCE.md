# Reviewer guidance

> **⚠️ Dormant — the manual review process is not live.** Nobody is currently
> running the human reviewer workflow this page supports, and the CI that scored
> submitted reviews is disabled. The procedure below still works if run by hand,
> and the scoring *concepts* remain accurate (they describe the metric itself),
> but the surrounding process does not run. See [`reviews/README.md`](README.md)
> for what in this directory is still live.

How to complete and submit a dataset review, and how the metric turns it into a
score and grade. The **authoritative, machine-readable** scoring definitions live
in the metric YAML (`metric/airbds_metric_v<version>.yaml`): `grade_points` (the
tier points) and `grading` (the per-grade thresholds). This page is the human
rationale behind them, plus the review procedure.

## Submitting a review

1. **Copy the template** — start from
   [`reviews/review_template.yaml`](review_template.yaml) (YAML) or
   [`reviews/review_template.csv`](review_template.csv) (spreadsheet).
2. **Name the file** `reviews/testing/<accession>_<initials>_<n>.yaml`, e.g.
   `reviews/testing/E-MTAB-1234_CH_1.yaml`. Initials are uppercase letters only
   (A–Z, 2–6 characters).
3. **Answer all 25 questions** with `"Yes"` or `"No"` — quoted, case-sensitive.
   For Ethics questions (ABC-23 to ABC-25), see [Ethics questions](#ethics-questions)
   below.
4. **Fill in the `result:` block yourself.** Scoring is no longer automated, so
   calculate `weighted_score` and `grade` by running the processor locally:
   ```bash
   pip install pyyaml
   python3 reviews/src/scripts/review_processor.py --files reviews/testing/<your-review-file>
   ```
   It performs the same validation and scoring the retired CI did, and reports
   errors the same way.
5. **Open a pull request** against `main` with the completed review file.

Where possible, a dataset should be reviewed independently by at least two
members before its review is merged. The fully worked step-by-step, including the
CSV variant, is in [`docs/tutorial-yaml.md`](docs/tutorial-yaml.md) and
[`docs/tutorial-csv.md`](docs/tutorial-csv.md).

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
