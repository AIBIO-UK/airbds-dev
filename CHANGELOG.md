# Changelog

All notable changes to this repository are documented here, grouped by what
each change belongs to. The repository produces two independently versioned
artifacts, plus a body of work that carries no version at all:

| Section | Versioned by | Released as |
|---|---|---|
| [Metric](#metric) | `schema_version` — 0.3, 0.4, 0.5 | a new `metric/airbds_metric_vX.Y.yaml` |
| [Assessment skill](#assessment-skill) | `skills/versions.json`, per channel | the `assessment-skill-development` / `assessment-skill-testing` release builds |
| [Repository](#repository) | nothing | nothing — recorded by date |

The metric and the assessment skill follow
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and
[Semantic Versioning](https://semver.org/spec/v2.0.0.html); the metric's bump
rules are in [CONTRIBUTING.md](CONTRIBUTING.md#versioning-policy). Repository
changes have no version to be released under, so they are recorded by month,
newest first.

---

# Metric

Changes to the scored questions, weights, grading rules, and the generation
pipeline that produces `metric/airbds_metric_vX.Y.yaml`.

## [Unreleased]

Nothing yet.

---

## [0.5] — current

> **v0.5 is now the current version.** The metric, the review template
> (`reviews/review_template.{yaml,csv}`), and the sheet→YAML converter target
> v0.5. The version-aware review processor scores each review against the metric
> matching its `schema_version`, so v0.4 and v0.3 reviews still score correctly;
> those metrics and their archived review templates are retained. Both
> assessment skill channels target v0.5 (see
> [Assessment skill](#assessment-skill)).

### Added
- `instructions:` — a new top-level block in the metric YAML, captured verbatim
  from the source sheet's Instructions tab, so downstream reviewers (human and
  AI) read the same generic guidance.
- `metric/src/scripts/build_metric_yaml_from_google_sheet_v0.5.py` — generates
  `airbds_metric_v0.5.yaml` from the v0.5 Google Sheet (Scoring, Lookups, and
  Instructions tabs), recording provenance in `airbds_metric_v0.5.upstream.json`.
- `reviews/src/scripts/build_review_template.py` — generates the
  `review_template.{yaml,csv}` pair from the metric YAML so the two formats can
  never drift.
- v0.5 regression coverage for the sheet→YAML converter (no converter code
  change needed — it is metric-version-agnostic).

### Changed
- **25 questions (was 27).** Ethics drops to 3 (`ABC-23`–`ABC-25`, all Critical);
  Metadata and Content are 6 each; Infrastructure 10. Questions reworded and
  regrouped throughout.
- Grade distribution is 9 Critical / 10 Important / 6 Optional, giving a
  **maximum score of 782** (was 711). Weight tiers unchanged (Critical 80,
  Important 5, Optional 2). Grade thresholds: Gold 776, Silver 745, Bronze 640,
  Caution 0.
- Metric metadata trimmed: dropped the redundant top-level `version` field (it
  duplicated `schema_version`, which remains the pairing key) and the unused
  `short_name` field (v0.5 only); reordered to lead with `metric_name`.
- The outgoing v0.4 review-template pair was archived to
  `reviews/archived_templates/review_template_v0.4.{yaml,csv}` before the live
  pair was regenerated to v0.5.

---

## [0.4]

> **v0.4 was the current version.** The review templates
> (`reviews/review_template.{yaml,csv}`), the sheet→YAML converter, and
> `review_processor.py` all defaulted to / supported it. The review processor is
> version-aware — it scores each review against the metric matching its
> `schema_version`, so existing v0.3 reviews still score correctly, and the v0.3
> metric and review template are retained (the latter under
> `reviews/archived_templates/`).

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
  (`metric/scoring_schema.yaml`) — later removed, see
  [Repository → 2026-06](#2026-06)
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

### Amended in place after release (2026-06-02)

> These changes were made to `metric/airbds_metric_v0.3.yaml` after the initial
> 0.3 release **without a version bump** — the published file is still v0.3.
> They are recorded here, under the version they altered, rather than under a
> version of their own.

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

---

*Previous iterations of this metric were developed internally by the AIRBDS
working group as a collaborative Google Sheets template. v0.3 represents the
first versioned, publicly released, machine-readable edition.*

---

# Assessment skill

Changes to the AIRBDS assessment skill (`skills/`). Each channel —
`development` and `testing` — carries its own version in
`skills/versions.json` and is published by its own build workflow, so a version
below is scoped to the channel(s) named in its heading. See
[`skills/docs/MAINTENANCE.md`](skills/docs/MAINTENANCE.md).

## [0.4.1] — `testing` (2026-07-23)

- Promoted the `development` assessment skill to the `testing` channel: the
  `testing` skill now assesses against AIRBDS metric v0.5 (was v0.4) at skill
  version 0.4.1 (was 0.3.1). It adopts the metric-version-agnostic form — the
  bundled assets are version-less symlinks (`assets/airbds_metric.yaml` →
  v0.5, `assets/review_template.yaml`), the metric version is read from the
  bundled `schema_version` at runtime, and the `metric_version` frontmatter
  field is dropped. `skills/versions.json` `channels.testing` is bumped to match.

## [0.4.1] — `development` (2026-07-23)

- Removed the option to contribute the saved assessment to the public AIRBDS
  results site (auto-airbds) from the optional saved-YAML step, and dropped the
  related reference to the results site when capturing the dataset title. The
  skill still offers to save the assessment locally and continues to instruct
  the model not to upload or send the file anywhere itself.
  `skills/versions.json` `channels.development.skill_version` is bumped to match.

## [0.4.0] — `development` (2026-07-23)

- Made the skill metric-version-agnostic and repointed it at AIRBDS metric v0.5
  (was v0.4). The bundled assets are now version-less symlinks
  (`assets/airbds_metric.yaml`, `assets/review_template.yaml`), and `SKILL.md`
  reads the metric version from the bundled metric's `schema_version` at runtime
  rather than hard-coding it — so a future metric bump only repoints the symlink.
  Dropped the `metric_version` frontmatter field; `skills/versions.json`
  `channels.development` is bumped to `metric_version` 0.5 / `skill_version`
  0.4.0 to match. The `testing` channel is unchanged at this point (still v0.4,
  skill 0.3.1).

## [0.3.1] — `development`, `testing` (2026-06-29)

- In the optional saved-YAML step, dropped the not-yet-ready manual submission
  option and marked the public results site (auto-airbds) as a test site under
  construction whose submissions are purely for test purposes.

## [0.3.0] — `testing` (2026-06-29)

- Promoted the `development` assessment skill to the `testing` channel: the
  `testing` skill now assesses against AIRBDS metric v0.4 (was v0.3) at skill
  version 0.3.0 (was 0.2.1), bundling the metric and review template under
  `assets/` (was `templates/`). `skills/versions.json` `channels.testing` is
  bumped to match.

---

# Repository

Changes to the repository itself — workflows, tooling, documentation, and
layout — that carry no version of their own. Recorded by month, newest first.

## 2026-07

### Changed
- Disabled the `Review Check & Score` workflow (`.github/workflows/review-check.yml`):
  its `push`/`pull_request` triggers on `reviews/testing/**` are removed, leaving
  it `workflow_dispatch`-only. The manual review process is not live, and a
  passing check implied reviews were being validated and scored as part of a
  working pipeline. The workflow is retained, not deleted, so the process can be
  revived by restoring the triggers. Reviews can still be scored by running
  `reviews/src/scripts/review_processor.py` directly.
- Marked the dormant manual-review material in `reviews/` — `GUIDANCE.md`, the
  `docs/` tutorials, `examples/`, and `archived_templates/` — with notices, and
  gave `reviews/README.md` a header distinguishing what is dormant from what is
  still live in that directory: `src/google-sheet-converter/` (published as the
  npm package `@airbds/converter-tools` and consumed by auto-airbds, resolving
  the metric YAML by relative path) and `review_template.yaml` (the schema
  contract the converter emits against). `reviews/` is therefore kept in the live
  tree rather than archived wholesale as in PR #14.

### Removed
- The `metric-update-propagation` agent skill (`metric/skills/SKILL.md`) and
  the `metric-alignment-check` workflow. The skill duplicated the Coupled File
  Groups manifest in `metric/README.md` and went stale quickly; the manifest
  is now the single source of truth for propagating metric changes.
- The metric CSV distribution format (`metric/airbds_metric_v0.3.csv` and
  `metric/airbds_metric_v0.4.csv`): the metric is now YAML-only. The CSV was
  development-only and had no meaningful consumers — auto-airbds reads the
  YAML. The generator scripts were renamed accordingly
  (`build_metric_yaml_from_spreadsheet_v0.3.py`,
  `build_metric_yaml_from_google_sheet_v0.4.py`). Reintroduces the metric
  half of the slim-down from PR #14 in adapted form. The review template
  (`reviews/review_template.{yaml,csv}`) is unaffected and keeps both formats.

## 2026-06

### Deprecated
- Gemini ('Gem') support for the assessment skill is paused until the AIRBDS
  assessment reaches v1.0. A Gem can't be built from this repository — it has to
  be created and shared manually, so it can't be kept in sync or tested
  automatically. Use Claude (Web, Desktop, or Code) in the meantime. See
  `skills/README.md`.

### Removed
- `metric/scoring_schema_v0.3.{yaml,csv}` — redundant with the metric YAML
  (`grade_points` / `grading`). The tier rationale, grade meanings, and badge
  colours moved to `reviews/GUIDANCE.md`; the versioning policy already lives in
  `CONTRIBUTING.md`.
