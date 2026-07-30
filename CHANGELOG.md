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

### Added
- `metric/airbds_metric_v0.5.json` — a JSON rendering of the v0.5 metric,
  written by the same build run as the YAML and covered by its `--check`. It
  exists so consumers that cannot depend on a YAML parser (chiefly the
  assessment skill's bundled scorer) can read the metric. Produced by parsing
  the rendered YAML and re-serialising it, so the two are the same document; the
  YAML remains canonical and is the version humans read.

### Fixed
- **`--check` now compares metric content, not raw bytes**, in both the v0.4 and
  v0.5 generators. The `# Source content sha256:` breadcrumb is set aside for the
  comparison: it hashes the raw source CSVs, so it moved whenever the sheet's
  bytes moved — including for edits the generators never read (a cell in an
  unread pivot column, a heading in the excluded data-entry block, trailing
  whitespace). The v0.5 check had been failing for exactly this reason while
  every extracted field was byte-identical, which also made the scheduled
  `metric-upstream-drift-check.yml` open issues for a metric that had not
  changed. A bare hash difference is now a passing `NOTE` naming both hashes; a
  real content change still exits 1. `test_committed_yaml_regenerates_byte_for_byte`
  was failing on this and now passes, with new coverage asserting that a genuine
  content change is still caught and a hash-only change is not.

### Changed
- `build_metric_yaml_from_google_sheet_v0.{4,5}.py` renamed to
  `build_metric_from_google_sheet_v0.{4,5}.py` — they no longer produce only
  YAML. Both were renamed together because the drift-check workflow builds the
  script name from its version matrix.

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
- `metric/src/scripts/build_metric_from_google_sheet_v0.5.py` — generates
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

## [0.7.1] — `testing` (2026-07-30)

- Promoted the `development` assessment skill to the `testing` channel, taking it
  from 0.5.1 to 0.7.1. `testing` therefore picks up everything under [0.7.0] and
  [0.7.1] — `development` below: mechanical scoring by the bundled
  `scripts/score.py`, the examine-and-revise phase before the assessment is
  saved, the dropped `## Files:` section, and the spec-conformant frontmatter.
  `SKILL.md` was copied from `development` with only the channel-specific
  references swapped (`development` → `testing`); the two files differ in that
  word alone.
- **The bundle gains `scripts/` and swaps the metric for its JSON rendering**, to
  match `development`: `assets/airbds_metric.yaml` → `assets/airbds_metric.json`
  (still v0.5 — the JSON is the same document, so
  `channels.testing.metric_version` stays at 0.5), plus a new
  `scripts/score.py` → `reviews/src/scripts/airbds_scoring.py` symlink. The
  `testing` build workflow's `paths:` filter follows the new symlink targets, and
  now lists `scripts/*`; a stale filter would silently stop rebuilds firing.
- `skills/versions.json` `channels.testing.skill_version` bumped to match. With
  `testing` now on the `metadata.version`/`metadata.channel` layout, the notes in
  `skills/docs/MAINTENANCE.md` and `skills/docs/DESIGN.md` that described the
  JSON metric, `scripts/`, and the conformant frontmatter as `development`-only
  no longer apply and were removed.

## [0.7.1] — `development` (2026-07-29)

- **Dropped the `## Files:` section.** All 37 lines of it restated things stated
  where they are used — the metric's field names appear in steps 2 and 3, the
  review template's in step 5, and the version manifest's logic and URL in step 1
  — or described structure discoverable by opening the file. The Agent Skills
  best-practice test is "would the agent get this wrong without this
  instruction?", and a manifest at the end of the file is also the "see
  references/ for details" anti-pattern its guidance warns against: a file
  reference is more use at its point of need, carrying the condition for reading
  it. 168 lines to 130 (~4,360 to ~3,860 tokens, against the spec's 500-line /
  5,000-token guidance). Only one clause was kept, folded into step 3 — that the
  scorer needs no packages installed, without which a model may attempt `pip
  install` in a sandbox with no network.
- **Frontmatter made spec-conformant.** `version` and `channel` move under
  `metadata`; `tags: [science]` becomes a block sequence. The specification
  defines a closed set of top-level fields and the reference validator
  (`agentskills validate`) rejects any others outright — it also parses with
  StrictYAML, which forbids inline flow style. Worth fixing rather than ignoring
  because `channel` is read by the skill itself for the update check, so a strict
  client would either reject the skill or drop the field and break that check
  silently. `SKILL.md` step 1 now names `metadata.channel`, and
  `skills/docs/MAINTENANCE.md` records the layout, the validator command, and why
  `metadata.hermes` stays nested despite not being conformant (it matches Hermes'
  own skill files). Both the checked-in skill and the built zip validate clean.
  `testing` still carries the old layout and will be brought into line at its
  next promotion.

## [0.7.0] — `development` (2026-07-29)

Minor rather than patch: the skill gains an interaction phase it did not have.
An assessment could previously only be delivered and saved; it can now be
examined, and an answer revised on evidence — which re-scores the dataset and can
change the grade it is reported as having earned.

- **Added a follow-up step (new step 4; saving the YAML becomes step 5).** Once
  the report is delivered the skill invites the user to examine any part of the
  assessment — a particular answer, the evidence behind it, why a higher grade was
  missed, what would most improve the score — in the same breath as offering the
  saved file, so it costs one question rather than two. The model's weakest answers
  are those where a resource was unreachable, and the user frequently knows the
  dataset better than its landing page shows.
- **The bar for changing an answer is set explicitly**, so the invitation cannot
  turn into negotiation. Two grounds qualify: evidence the model did not account
  for (never saw, could not reach, or overlooked), and a flaw in how it judged
  evidence it *did* see — an aspect it failed to weigh, a misreading, or the wrong
  `guidance` applied. The second is included deliberately: restricting revision to
  new material would leave a user unable to argue the commonest case of all, that
  the model read the right page wrongly.
- What qualifies a ground is its specificity, not its kind: the user must name
  something that survives checking. The model re-examines what it is pointed at —
  re-fetching where it can, judging the resource rather than a description of it —
  then reaches its own conclusion; looking again and explaining why the answer
  stands is called out as a perfectly good outcome. It is pushed to revise **down**
  as readily as up, since users press on "No" answers and an assessment that only
  ratchets upward is useless for comparing datasets.
- The step is written as an examination, not a dispute: users are assumed to act in
  good faith, so there is no instruction to resist them. The counterweight against
  abandoning a correct answer under a well-meant "are you sure?" is framed as a
  service to the user — revising something you have checked and still believe leaves
  them with a worse assessment than they arrived with.
- A revised answer **re-enters the scoring path**: the model re-runs
  `scripts/score.py` on the corrected answers rather than adjusting the total
  itself, and the saved YAML records the assessment's final state. Revisions are
  not otherwise flagged in the file — a correction on good evidence is simply a
  better assessment.

## [0.6.0] — `development` (2026-07-29)

- **Scoring is now mechanical.** The skill bundles `scripts/score.py`, which takes
  a flat `{question-id: "Yes"|"No"}` JSON document and returns the final score,
  the overall grade, and the per-tier yes/total/proportion counts. The model
  supplies only its own judgements; the tiers, weights and grading thresholds
  come from the bundle. This removes the model from the one part of an assessment
  with a single correct answer — in particular the grading rule, a conjunction
  over three tier proportions plus a score floor that weaker models evaluate
  unreliably. Minor rather than patch: the assessment's central calculation
  changes hands, and the bundle gains two files.
- The script is the **same code that scores submitted reviews** —
  `scripts/score.py` symlinks to `reviews/src/scripts/airbds_scoring.py`, from
  which `review_processor.py` now imports `score_review`. A skill-produced
  assessment and a hand-written review can no longer be graded by two
  implementations that have drifted apart.
- It refuses to score an answer set with a missing question, an unknown id, or
  an answer that is not exactly `"Yes"`/`"No"`, reporting the problems instead.
  Transcribing 25 answers is where the residual risk now sits, so it fails
  loudly rather than grading a partial set.
- **The bundled metric is now JSON, and only JSON.** `assets/airbds_metric.yaml`
  is replaced by `assets/airbds_metric.json`, symlinked to the new
  `metric/airbds_metric_v0.5.json`. The scorer needs JSON so it can depend on
  the standard library alone — PyYAML cannot be assumed in the environments a
  skill runs in — and the model reads the same file, so the questions it answers
  and the metric it is scored against are one document. Shipping both renderings
  would have duplicated the metric inside the bundle for no gain: nothing the
  skill reads from the metric lives in a YAML comment. The YAML remains
  canonical in `metric/` for people to read.
- The bundle gains a `scripts/` directory, following the agentskills.io layout —
  data the skill reads in `assets/`, executables in `scripts/`.
- **The script is an optimisation, never a precondition.** Where the bundle's
  files are not unpacked, Python is unavailable, or execution is not permitted,
  `SKILL.md` instructs the model to fall back to scoring by hand using the rules
  it still states in full.
- **The fallback is disclosed, but only when it happens.** The reporting step's
  "Access warning" is broadened to a **Warnings** section carrying two
  independent warnings: the existing access-failure one, and a new one stating
  that the score and grade were calculated by the model rather than the script,
  why the script could not be run, that the table's answers are unaffected, and
  that re-running somewhere it can execute will calculate them mechanistically.
  A score the script produced is reported with no commentary at all, and the
  section is omitted entirely when neither warning applies — so the user can tell
  which of two differently-trustworthy numbers they have without the successful
  path adding noise that teaches them to skip warnings.
- Both skill build workflows now list the symlink *targets* in their
  `paths:` triggers. A GitHub path filter matches the committed path and never
  follows a symlink, so a commit changing the metric or the scorer previously
  left the published zip holding stale content without any signal. This was
  already true of the metric before this release.
- `skills/versions.json` `channels.development.skill_version` is bumped to
  0.6.0; the metric is unchanged at v0.5. The `testing` channel stays at 0.5.1
  until promoted, and does not yet bundle the scorer.

## [0.5.1] — `testing` (2026-07-28)

- Promoted the `development` assessment skill to the `testing` channel, so the
  `testing` skill picks up the widened access-warning trigger described under
  [0.5.1] — `development` below. Skill version 0.5.1 (was 0.5.0); copied from
  `development` with only the channel-specific references swapped. The metric is
  unchanged, so no asset symlink was repointed and
  `channels.testing.metric_version` stays at 0.5. `skills/versions.json`
  `channels.testing.skill_version` is bumped to match.

## [0.5.1] — `development` (2026-07-28)

- Widened the access-warning wording in the reporting step to match the tracking
  step, which already covered API endpoints, downloads, FTP/S3 listings and
  resolver lookups as well as web pages. The warning's trigger condition read
  "only if any *page* could not be retrieved", so a model blocked from an API but
  able to read every page could satisfy step 2's tracking and still skip the
  warning, silently restoring the pre-0.5.0 behaviour for exactly the
  API-restricted case the warning was added for. "page" and "URLs" are now
  "resource"/"resources" in all three places.
  `skills/versions.json` `channels.development.skill_version` is bumped to match;
  the metric is untouched. The `testing` channel stays at 0.5.0 until promoted.

## [0.5.0] — `testing` (2026-07-28)

- Promoted the `development` assessment skill to the `testing` channel, so the
  `testing` skill now carries the access-failure tracking and end-of-report
  warning described under [0.5.0] — `development` below. Skill version 0.5.0 (was
  0.4.1); copied from `development` with only the channel-specific references
  swapped. The metric is unchanged — both channels were already on v0.5, so no
  asset symlink was repointed and `channels.testing.metric_version` stays at 0.5.
  `skills/versions.json` `channels.testing.skill_version` is bumped to match.

## [0.5.0] — `development` (2026-07-28)

- The skill now reports when it could not see everything it needed. Assistants
  running in restricted environments are frequently unable to retrieve some of
  what an assessment depends on — not only web pages, but API endpoints, direct
  file downloads, FTP/S3/cloud-container listings, DOI resolvers, and registry or
  schema lookups. Previously such a failure was invisible in the output: the
  report presented a complete-looking table and a final score, with no signal
  that some answers rested on evidence the model had never actually seen.
- The assessment step now instructs the model to keep a running note of each
  resource it could not retrieve — what it was trying to establish, why the
  retrieval failed, and which question IDs are affected — and the reporting step
  requires a prominent warning at the very end of the report, after the score,
  grade and summary justification. The warning names the unreachable resources
  and the reasons, identifies the affected question IDs as resting on partial or
  no evidence (so the true score may be higher), and tells the user to re-run the
  assessment somewhere with access or to check those questions themselves. It is
  emitted only when a failure was actually recorded; a clean run is unchanged.
- No metric change: `channels.development.metric_version` stays at 0.5.
  `skills/versions.json` `channels.development.skill_version` is bumped to match.

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

### Added
- `skills/docs/DESIGN.md` — how the assessment skill is put together: what
  `SKILL.md`'s frontmatter and body each do, what the bundled `assets/` carry,
  and why the metric is shipped as a symlinked data file rather than restated as
  prose in the instructions. Complements `skills/docs/MAINTENANCE.md`, which
  covers the operational side (channels, the version manifest, release builds).
  Linked from `skills/README.md` and added to the Group C coupled-file list in
  `metric/README.md`, since its bundle diagram names the symlink's metric
  version.

### Changed
- **Both skill assets now name their channel in full**:
  `airbds-assessment-skill-testing.zip` (was `airbds-assessment-skill.zip`, with
  no channel at all) and `airbds-assessment-skill-development.zip` (was
  `airbds-assessment-skill-dev.zip`). A downloaded file now says which channel it
  came from, and the two names are formed the same way instead of one spelling the
  channel out and the other abbreviating it. Coupled change per channel across its
  build workflow (both the `zip` step and `files:`), its `skill_update_url` in
  `skills/versions.json`, and the asset name in `skills/docs/MAINTENANCE.md`, plus
  the install link in `skills/README.md`. The asset URL is not baked into a
  published skill — the runtime update check reads `skill_update_url` out of the
  manifest it fetches — so installed skills are unaffected, but each old download
  URL stops resolving once that channel's next build replaces its release.
- **Dropped "zip" from both release names** — "AIRBDS assessment testing skill",
  not "…skill zip". The release *is* the skill; naming the container made it read
  as an archive with a skill somewhere inside it, which is the wrong mental model
  for something a user installs whole.
- **Both skill build workflows now trigger on `main` only.** They also listed a
  `skills-testing` / `skills-development` branch; neither exists on the remote
  (`skills-testing` was deleted once its work had merged, `skills-development`
  never existed). Nothing else in the repository referenced either name. This
  makes `skills/docs/MAINTENANCE.md`'s description of the workflows — "each
  pushes on `main`" — exact; a rebuild from another branch is still available
  through `workflow_dispatch`.
- **The docs now name the YAML as the metric's source of truth and the Google
  Sheet as its editing interface**, rather than the other way round: the sheet is
  where the working group authors the metric, but `metric/airbds_metric_vX.Y.yaml`
  is what the repository and downstream consumers read and what reviews are
  scored against. Reworded in the main `README.md`, `metric/README.md`, and
  `metric/src/README.md`. The same passages now record that
  `metric/airbds_metric_v0.5.json` is subsidiary to the YAML — same document,
  same build run, for consumers without a YAML parser — and the JSON was added to
  the "Files in This Folder" table in `metric/README.md`, which had omitted it.
- The main `README.md`'s "Use the Metric" sheet link pointed at the **v0.4**
  sheet while the section describes v0.5; it now points at the v0.5 sheet
  (`13w-MiUQ…`), matching `metric/airbds_metric_v0.5.upstream.json`.
- The publication repository was renamed from `AIBIO-UK/airbds-metric` to
  `AIBIO-UK/airbds-core`, and every identity/attribution reference here follows
  it: `CITATION.cff` `repository-code`, the suggested-citation blocks in
  `LICENSE.md` and `README.md`, the tutorial footers in `reviews/docs/`, the
  repository table in `CONTRIBUTING.md`, and the `repository:` field of all three
  metric YAMLs (changed in the `METADATA` block of the generator scripts and
  regenerated, never hand-edited). Actionable links — clone URLs, PR targets, the
  skills' update manifest and `skill_update_url`s — still point at `airbds-dev`
  and are unaffected.
- `airbds-metric` now 301s to `airbds-core`, so surviving old links resolve.
  Freeing the `airbds-metric` name did **not** restore this repo's own original
  rename redirect, which was verified still returning 404 immediately after the
  rename; `skills/docs/MAINTENANCE.md` records this so nobody plans around a
  redirect that does not exist.
- The `airbds-metric-tutorial` repository and its GitHub Pages URLs were
  deliberately left alone — renaming it is a separate migration with its own
  broken-link cost, so all `aibio-uk.github.io/airbds-metric-tutorial/` links are
  unchanged.
- Regenerating v0.5 picked up a new source-content sha256 for its Google Sheet
  (`1cb615af…` → `b831706c…`). The extracted YAML is otherwise byte-identical, so
  the sheet was edited in a way that touches nothing the metric consumes; the v0.4
  sheet hash is unchanged. Recorded here because the regeneration also updates the
  drift baseline in `metric/airbds_metric_v0.5.upstream.json`.
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
  `build_metric_from_google_sheet_v0.4.py`). Reintroduces the metric
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
