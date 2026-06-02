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

### Removed
- Per-question `mapped_from` provenance codes (to be re-sourced for the
  reworded questions in a later revision).

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
