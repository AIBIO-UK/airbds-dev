# Changelog

All notable changes to the AIRBDS AI-Readiness Dataset Scoring Metric are
documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
