# Changelog

All notable changes to the AIRBDS AI-Readiness Dataset Scoring Metric are
documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Changed
- Reworded ACM-2, ACM-3, ACM-5, ACM-6, and ACM-7 to the canonical AIRBDS
  question set (e.g. ACM-2 now covers metadata colocation, ACM-3 dataset
  integrity, ACM-6 FAIR-compliant archives).
- Regraded ACM-5 (Critical → Important) and ACM-7 (Optional → Important). The
  metric now comprises 8 Critical, 12 Important, and 8 Optional questions
  (maximum score 716, previously 713).
- Grading now requires a minimum total weighted score (`min_score`) in addition
  to the per-tier pass-rate thresholds, so `scripts/review_processor.py` and the
  auto-airbds web frontend grade datasets identically.
- Reworked the metric YAML structure: questions are a map keyed by question id,
  using `grade`/`question`/`guidance` fields, with top-level `grade_points` and
  `grading` (with `min_score`) driving scoring.
- Refreshed per-question `mapped_from` provenance codes to match the reworded
  questions.

### Removed
- `metric/scoring_schema_v0.3.{yaml,csv}` — redundant with the metric YAML
  (`grade_points` / `grading`). The tier rationale, grade meanings, and badge
  colours moved to `reviews/GUIDANCE.md`; the versioning policy already lives in
  `CONTRIBUTING.md`.

---

## [0.4] — current

> **v0.4 is now the current version.** The review templates
> (`reviews/review_template.{yaml,csv}`), the sheet→YAML converter, and
> `review_processor.py` all default to / support it. The review processor is
> version-aware — it scores each review against the metric matching its
> `schema_version`, so existing v0.3 reviews still score correctly, and the v0.3
> metric and review template are retained (the latter under
> `reviews/archived_templates/`). Migration of auto-airbds and the assessment
> skills to v0.4 is tracked separately.

### Changed
- Authored in and generated from the working group's public Google Sheet (via
  `metric/src/scripts/build_metric_yaml_and_csv_from_google_sheet_v0.4.py`)
  rather than the v0.3 `.xlsx`. The source sheet and a content-hash "revision"
  are recorded in `airbds_metric_v0.4.upstream.json` and a `# Source:` YAML
  breadcrumb.
- Question ids changed from `ACM-N` to zero-padded `ABC-NN`.
- 27 questions (was 28): Ethics drops to 4 — the v0.3 authentication /
  access-controls question (ACM-27) has no v0.4 successor.
- Questions reworded throughout.
- Grade thresholds (`min_score`) are now fractional (e.g. Silver 667.5);
  maximum score 711 (was 716). Weight tiers unchanged (Critical 80, Important 5,
  Optional 2).

### Removed
- The per-question `theme` and `mapped_from` fields (absent from the v0.4 source
  sheet).

---

## [0.3] — Initial public release

### Added
- 28 scored questions across four scopes: Infrastructure, Metadata, Content,
  and Ethics
- Three weight tiers: Critical (80 pts), Important (5 pts), Optional (2 pts)
- Four grade thresholds: Caution, Bronze, Silver, Gold
- Machine-readable YAML encoding of the full metric
  (`metric/airbds_metric_v0.3.yaml`)
- Supplementary scoring schema and reviewer instructions
  (`metric/scoring_schema.yaml`)
- Blank review template (`metric/review_template.yaml`)
- `CITATION.cff` with working group member credits
- `LICENSE.md` (CC BY 4.0)
- `CODE_OF_CONDUCT.md`
- `CONTRIBUTING.md` with YAML submission workflow and versioning policy

### Scope
- Infrastructure (ACM-1 to ACM-10): access, licensing, UID, version control
- Metadata (ACM-11 to ACM-17): bias, standards, preprocessing, provenance
- Content (ACM-18 to ACM-23): quality, format, consistency
- Ethics (ACM-24 to ACM-28): acquisition, privacy, management, security,
  data protection declarations

---

*Previous iterations of this metric were developed internally by the AIRBDS
working group as a collaborative Google Sheets template. v0.3 represents the
first versioned, publicly released, machine-readable edition.*
