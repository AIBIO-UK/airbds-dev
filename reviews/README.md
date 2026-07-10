# reviews/

Deposit completed AIRBDS dataset reviews here.

**[→ Interactive tutorial site](https://aibio-uk.github.io/airbds-metric-tutorial/)** — step-by-step guide to filling out a review.

## Format

- One file per review, YAML: `<dataset_accession>_<reviewer_initials>_<n>.yaml`
  (e.g. `E-MTAB-1234_CH_1.yaml`).
  - `<dataset_accession>` — the repository accession or a short descriptive token
  - `<reviewer_initials>` — uppercase letters only (2–6 characters, no digits)
  - `<n>` — review number (start at 1; increment if you review the same dataset again)
- Base your questions on the metric's Google Sheet or [`metric/airbds_metric_v0.4.yaml`](../metric/airbds_metric_v0.4.yaml) — see [Use the Metric](../metric/README.md#use-the-metric).
- Answer each of the 27 questions `"Yes"` or `"No"` (quoted strings).
- Leave the `result:` block empty — see **Scoring** below.

## Scoring

See [`GUIDANCE.md`](GUIDANCE.md) for how the weighted score and grade are calculated; the authoritative numbers live in the metric YAML's `grade_points` / `grading`.

There is no automated scorer right now — calculate the score yourself (e.g. in a spreadsheet against the Google Sheet) and fill in the `result:` block before submitting. Automated YAML-based scoring is planned infrastructure, not yet built.

See [CONTRIBUTING.md](../CONTRIBUTING.md) for how to submit a review.
