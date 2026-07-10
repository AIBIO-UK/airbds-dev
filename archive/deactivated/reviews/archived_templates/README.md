# Archived review templates

Previous-version blank review templates, kept for reference and for reviewing a
dataset against an older metric version.

**For new reviews, use the current template in the parent directory**
([`reviews/review_template.yaml`](../review_template.yaml) /
[`review_template.csv`](../review_template.csv) — currently v0.4). You only need a
file from here if you specifically want to review against an earlier metric.

Each review carries a `schema_version` field; the review processor scores it
against the matching `metric/airbds_metric_v<schema_version>.yaml`, so older
reviews remain scorable.

| File | Metric version |
|------|----------------|
| `review_template_v0.3.yaml` / `.csv` | v0.3 — 28 questions, `ACM-1…28` |

When a new metric version becomes current, the outgoing
`reviews/review_template.{yaml,csv}` pair is copied here as
`review_template_v<old>.{yaml,csv}` before the live pair is overwritten.
