# Changelog

All notable changes to this repository are documented here, grouped by what
each change belongs to. The repository produces two independently versioned
artifacts, plus a body of work that carries no version at all:

| Section | Versioned by | Released as |
|---|---|---|
| [Metric](#metric) | `schema_version` — 0.3, 0.4, 1.0.0, 1.0.1 | a new `metric/airbds_metric_v<version>.yaml` |
| [Assessment skill](#assessment-skill) | `skills/versions.json`, per channel | the `assessment-skill-development` / `assessment-skill-testing` release builds |
| [Repository](#repository) | nothing | nothing — recorded by date |

The metric and the assessment skill follow
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and
[Semantic Versioning](https://semver.org/spec/v2.0.0.html); the metric's bump
rules are in [metric/README.md](metric/README.md#versioning-policy). Repository
changes have no version to be released under, so they are recorded by month,
newest first.

---

# Metric

Changes to the scored questions, weights, grading rules, and the generation
pipeline that produces `metric/airbds_metric_v<version>.yaml`.

## [Unreleased]

Nothing yet.

---

## [1.0.1] — current

> **Grading is now by total score alone.** v1.0.1 clarifies a scoring rule that
> v1.0.0 encoded too strictly. The per-tier "Yes" proportions that v1.0.0 carried
> as `min_proportion_yes` — and applied as a hard gate alongside each grade's
> `min_score` — were only ever the working the metric author used to *derive*
> those score thresholds, not an independent requirement. The source sheet now
> labels them "Threshold calculation proportions" to say so, and the metric drops
> them: a dataset earns the highest grade whose `min_score` its total score
> reaches. **The 25 questions, the Critical/Important/Optional weights, and every
> numeric `min_score` threshold are unchanged from [1.0.0].**
>
> This is a change in scored outcomes, not only in wording: where the proportion
> gate — and not the score — was the binding constraint, a dataset can now earn a
> higher grade than it would have under v1.0.0. It is released as a PATCH because
> it corrects the published metric to the author's intended definition rather than
> changing that definition: the proportions were never meant to be a rule.

### Changed
- **Grading is by total score alone.** The scorer
  (`reviews/src/scripts/airbds_scoring.py`, shared with `review_processor.py` and
  bundled by the assessment skill as `score.py`) no longer evaluates the per-tier
  proportion gate; it returns the highest grade whose `min_score` the total
  weighted score reaches. This applies to *every* metric version the scorer runs
  against: a retained metric that still carries `min_proportion_yes` (v1.0.0 and
  earlier) is now graded the same way, with the proportions ignored. The per-tier
  yes/total/proportion counts are still reported alongside the grade as context —
  they just no longer gate it.
- **The source sheet was reorganised**, so v1.0.1 has its own generator
  (`metric/src/scripts/build_metric_from_google_sheet_v1.0.1.py`): the reviewer
  instructions moved from a dedicated Instructions tab onto a Header tab (an
  `Instructions:` cell above a `Review information` data-entry block), and the
  Lookups grading table was retitled from "Required proportions" to "Threshold
  calculation proportions". The tab classifiers and the instructions reader were
  adapted to match; the grade-points and grading-threshold readers are unchanged,
  since they key off the pivot's column headers rather than those titles.
- Two grade descriptions were reworded in the sheet (Gold and Silver), and the
  `instructions:` block drops the redundant "AIRBDS Dataset Metric v1.0.0" title
  line the old Instructions tab carried. Question text, weights, and every
  threshold are byte-identical to [1.0.0].
- The outgoing v1.0.0 review-template pair was archived to
  `reviews/archived_templates/review_template_v1.0.0.{yaml,csv}` before the live
  `reviews/review_template.{yaml,csv}` pair was regenerated to v1.0.1 (version
  strings only — the questions are unchanged).

### Removed
- **`min_proportion_yes`** from the metric's `grading` block. Each grade now
  carries only `name`, `description`, and `min_score`.

### Added
- `metric/airbds_metric_v1.0.1.{yaml,json,upstream.json}`, generated from the
  v1.0.1 Google Sheet. As with v1.0.0 the JSON is written by the same build run
  as the YAML and covered by `--check`; the YAML remains canonical.

---

## [1.0.0] — superseded by [1.0.1]

> **v1.0.0 has been superseded by [1.0.1] and is retained.** It declared the
> metric stable — [0.5] unchanged, the same 25 questions, the same
> Critical/Important/Optional weights, the same grade thresholds — released under
> a stable version number. While current it was the target of the metric, the
> review template (`reviews/review_template.{yaml,csv}`), the sheet→YAML
> converter, and all three assessment skill channels
> (see [Assessment skill](#assessment-skill)); [1.0.1] is now current.
>
> **v0.5 was withdrawn rather than retained.** Retention exists so a review can
> be re-scored against the metric it was scored with, and no review ever carried
> `schema_version: "0.5"`. A retained file identical to its successor in
> everything but its version number would only invite the question of which to
> use — and would have doubled the generator, the provenance sidecar, and the
> drift-check matrix entry, so every working-group sheet edit opened two issues
> for one drift. v0.4 and v0.3 are retained as before.

### Added
- `metric/airbds_metric_v1.0.0.{yaml,json,upstream.json}`, generated from the
  working group's Google Sheet by
  `metric/src/scripts/build_metric_from_google_sheet_v1.0.0.py` — the v0.5
  generator renamed, so the git history of both is continuous.
- The JSON rendering, first added during v0.5 development: written by the same
  build run as the YAML and covered by its `--check`, so consumers that cannot
  depend on a YAML parser (chiefly the assessment skill's bundled scorer) can
  read the metric. Produced by parsing the rendered YAML and re-serialising it,
  so the two are the same document; the YAML remains canonical.

### Changed
- **Version strings now carry all three components**, trailing zeros included:
  `1.0.0`, not `1.0`, matching how the working group labels the metric in the
  source sheet. The string is a path component, a `skills/versions.json` key, and
  each review's `schema_version`, all matched exactly, so the shape is
  load-bearing. Two places parse it rather than match it and were widened for the
  third component: `release_metric_to_core.sh`'s version argument, which rejected
  it outright, and the converter's `detectSchemaVersion`, which silently
  truncated a `v1.0.0` sheet label to `1.0` and would then have resolved to a
  metric file that does not exist. The retained v0.4 and v0.3 metrics keep their
  two-part names — committed reviews carry those exact strings — so both forms
  resolve and neither is normalised into the other.
- Two edits made in the sheet alongside the version bump, neither affecting
  scoring: the Gold grade's description gained "(or equivalent)", and the
  Instructions tab's own heading now names v1.0.0. Question text, weights, and
  every threshold are byte-identical to v0.5.
- `build_metric_yaml_from_google_sheet_v0.{4,5}.py` renamed to
  `build_metric_from_google_sheet_v0.4.py` / `…_v1.0.0.py` — they no longer
  produce only YAML. Both were renamed together because the drift-check workflow
  builds the script name from its version matrix.
- The v0.5 review-template pair was **not** archived to
  `reviews/archived_templates/`, unlike the v0.4 pair before it: v0.5 was
  withdrawn rather than superseded, and an archived template for a metric file
  that no longer exists could not be filled in and scored.

### Fixed
- **`--check` compares metric content, not raw bytes**, in both the v0.4 and
  v1.0.0 generators. The `# Source content sha256:` breadcrumb is set aside for the
  comparison: it hashes the raw source CSVs, so it moved whenever the sheet's
  bytes moved — including for edits the generators never read (a cell in an
  unread pivot column, a heading in the excluded data-entry block, trailing
  whitespace). The check had been failing for exactly this reason while every
  extracted field was byte-identical, which also made the scheduled
  `metric-upstream-drift-check.yml` open issues for a metric that had not
  changed. A bare hash difference is now a passing `NOTE` naming both hashes; a
  real content change still exits 1. `test_committed_yaml_regenerates_byte_for_byte`
  was failing on this and now passes, with new coverage asserting that a genuine
  content change is still caught and a hash-only change is not.

---

## [0.5] — superseded by [1.0.0], withdrawn

> **v0.5 is no longer in the repository.** [1.0.0] is this metric unchanged, under
> a stable version number; `metric/airbds_metric_v0.5.*` was removed rather than
> retained because no review was ever scored against it. This entry is kept as
> the record of what changed at v0.5 — every change below is in v1.0.0.

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
`development`, `testing`, and `production` — carries its own version in
`skills/versions.json`, so a version below is scoped to the channel(s) named in
its heading. `development` and `testing` are published by their own build
workflows here; `production` is published to `airbds-core` by
`skills/src/scripts/release_skill_to_core.sh`. See
[`skills/docs/MAINTAINING.md`](skills/docs/MAINTAINING.md).

## [0.8.1] — all channels (2026-08-04)

- **Expanded AIRBDS correctly.** `SKILL.md` glossed the acronym as "AI-Ready
  Biological Data Sets" in two places — the frontmatter `description` and the
  goal statement. The working group, and every other file in this repository
  (`README.md`, `CONTRIBUTING.md`, `CITATION.cff`, every metric YAML header),
  calls it **AI-Ready Bioscience Datasets**. The skill was the only thing using
  the other wording, and it is the artifact users install, so it was also the
  most visible place to have it wrong.
- Wording only: no change to the questions, the scoring, the bundled metric, or
  any behaviour. A PATCH bump on all three channels — `development` and
  `testing` rebuilt from source, `production` promoted from the `testing` build
  as usual. The `description` is what an assistant matches on when deciding to
  invoke the skill, so it ships in the bundle rather than waiting for the next
  substantive release.
- The same correction was applied to the retained (deprecated) Gemini variant at
  `skills/GF/GF-airbds-assessment-skill/SKILL.md`, which carries no version.

## [0.8.0] — all channels (2026-08-04)

- **Repointed at AIRBDS metric v1.0.0** (was 0.5), by moving each channel's
  `assets/airbds_metric.json` symlink to `metric/airbds_metric_v1.0.0.json`.
  Nothing in `SKILL.md` names a metric version — the skill reads `schema_version`
  out of the bundle — so repointing the symlink is the whole change, and both
  channels' bundled `score.py` scores an all-Yes sheet at 782/Gold exactly as
  before. The metric is the same instrument under a stable version number (see
  the `[1.0.0]` entry under [Metric](#metric)); the version users are told they
  are being assessed against is what changes.
- Promoted `development` to `testing` at 0.8.0: `SKILL.md` copied across with
  only the channel-specific references swapped (`development` → `testing`), so
  the two files differ in that word alone.
- `skills/versions.json` `channels.{development,testing}` bumped to
  `metric_version` 1.0.0 / `skill_version` 0.8.0. A MINOR bump, not a patch: the
  skill now assesses against a different metric document, which is a change in
  what it does rather than a fix to how it does it.
- Both build workflows' `paths:` filters follow the repointed symlink to
  `metric/airbds_metric_v1.0.0.json`; a stale filter would have left each
  published zip carrying the withdrawn metric, silently.
- **Promoted to `production`**, published to `airbds-core` as
  `skills/airbds-assessment-skill.zip` — the `testing` build with its channel
  rewritten, verified reversible. This is the first bundle actually published
  under the `production` channel: the channel was introduced at [0.7.1] but
  superseded by this release before it shipped, so no production skill ever
  reported 0.7.1.

## [0.7.1] — `production` (2026-08-03)

- **`production` is now a release channel.** It has no source directory here: the
  production bundle is the `testing` build with its release channel rewritten,
  published to
  [AIBIO-UK/airbds-core](https://github.com/AIBIO-UK/airbds-core) as
  `skills/airbds-assessment-skill.zip` and existing nowhere else, so there is no
  second copy to drift from it.
- **This fixes a production skill that reported the wrong channel.** The zip
  already in `airbds-core` was the `testing` artifact published untouched, so
  every production install declared `metadata.channel: testing` and ran its
  update check against `channels.testing`. A bundle carries its channel inside
  it, so promoting without a rewrite could not have produced anything else.
- `skills/versions.json` gains `channels.production` (metric 1.0.0, skill 0.7.1).
  Its `skill_update_url` points at `airbds-core`, where the production zip
  genuinely lives; `testing` and `development` still point at this repo's
  releases, and the manifest itself still lives — and is still served from — here.

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
  `skills/docs/MAINTAINING.md` and `skills/docs/DESIGN.md` that described the
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
  `skills/docs/MAINTAINING.md` records the layout, the validator command, and why
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

## 2026-08

### Changed
- **Removed `CONTRIBUTING.md`.** It was created early without working-group
  discussion and had accumulated claims nobody had agreed to — a "respond within
  14 days" review SLA chief among them — alongside a dataset-review walkthrough
  for a now-dormant process and a hand-maintained repository-structure tree that
  would drift. With no active outside contributors, a real contributing guide is
  better written when there are contributors to write it for. The content worth
  keeping was relocated rather than lost:
  - The **versioning policy** and **how a metric change is proposed** moved to
    [`metric/README.md`](metric/README.md) (the metric's own reference doc), where
    `RELEASING.md`, `README.md`, `AGENTS.md`, and this changelog now deep-link.
  - The **which-repository-does-a-link-point-at** convention moved to
    [`AGENTS.md`](AGENTS.md), as an editing rule for anyone working in the repo.
  - The **review procedure** moved to [`reviews/GUIDANCE.md`](reviews/GUIDANCE.md),
    already the dormant reviewer doc, which now covers both completing/submitting a
    review and how scoring works; the tutorials keep the full worked walkthrough.
  A stale "CI scores it on the way in" in `reviews/src/README.md` was corrected in
  passing — that CI is disabled.

- Renamed `skills/docs/MAINTENANCE.md` to `skills/docs/MAINTAINING.md`, matching
  the gerund form of the top-level process file it complements
  (`RELEASING.md`, `CONTRIBUTING.md`). All references updated; the file's content
  is unchanged.

### Added
- **`skills/src/scripts/promote_skill_channel.py` — promotes one channel's bundle
  to another** (`development` → `testing` by default), a step that was a manual
  directory copy plus a hand-edit of the channel token in `SKILL.md`. A bundle
  carries its channel inside it, so the manual version was easy to get wrong: a
  copy that dereferenced the symlinked metric and template into real files (so the
  channel silently stopped tracking them), a missed mention of the old channel in
  the update-check prose, or a promotion that left `skills/versions.json`
  describing the previous bundle. The script substitutes the channel token —
  reusing `rechannel_skill_zip.rewrite_text`, so it carries the same reversibility
  proof as the production channel rewrite — recreates symlinks as symlinks, and
  moves the target channel's manifest entry to describe what was promoted. It
  writes the working tree and stops: no commit, build, or push. `--dry-run`,
  `--check`, and `--from`/`--to` are provided. Tested in
  `skills/src/tests/test_promote_skill_channel.py` (13 tests).

- **`validate_skills_versions.py` now cross-checks the manifest against the
  bundles it describes**, and enforces that a channel moving to a new metric
  bumps its `skill_version` by at least a MINOR. The manifest restates facts the
  bundles already carry — a channel's skill version is also in its `SKILL.md`
  `metadata.version`, and the metric it scores against is whatever its
  `assets/airbds_metric.json` symlink resolves to — and every copy was
  hand-maintained with nothing comparing them. The validator previously checked
  only that an advertised `metric_version` had a matching file *somewhere*, so it
  would have passed a channel advertising v1.0.1 while still bundling v1.0.0:
  exactly the mistake the repoint step invites. It now compares `skill_version`
  to `SKILL.md`, `metadata.channel` to the directory, and `metric_version` to the
  bundled metric's `schema_version`; `production` is exempt, having no source
  directory. `--since <git-ref>` adds the bump rule by reading the manifest at an
  earlier commit — a new metric changes what the bundle contains and what it
  scores against, so it is never a patch-level change to the skill. CI resolves
  that ref itself (a PR's branch point, a push's preceding commit) and falls back
  to the stateless checks when there is no usable baseline. Tested in
  `skills/src/tests/test_validate_skills_versions.py` (14 tests), which had none
  before.

- `RELEASING.md` — the running order for a release, top level, covering the
  metric and the assessment skill that carries it. The steps themselves stay in
  the READMEs that own them; what this adds is the *order*, and the things that
  fall between documents: that the skill channels are repointed after the metric
  is published rather than before, that a release *overwrites* what
  `airbds-core` publishes because the filenames there are unversioned, and which
  files quote a version in prose and go quietly stale.

- **Stated that neither repository tags metric releases**, in
  `CONTRIBUTING.md`'s versioning policy. Both release scripts and three READMEs
  said the opposite — that "a tag or release in `airbds-core` is what downstream
  consumers pin to" — written when the release script was built and never acted
  on: `airbds-core` has no tags and no releases, across five publications. The
  pinning story it described did not exist. The real one, now written down, is
  that `airbds-core` carries the current metric under an unversioned filename
  while this repository retains every version under its own name, which is what
  anything depending on a specific version references.

### Changed
- **Marked the `skills/GF/` variant dormant.** It scores against metric v0.3 and
  was never carried forward to v0.4 or v1.0.0, so its embedded question table,
  weights, and grading describe a metric three versions old — while the
  coupled-file manifest still listed it as something to update on every release.
  Banners now say so in `skills/GF/README.md`, in the skill's own `SKILL.md` and
  its frontmatter `note` (so an assistant reading the file is warned too), and in
  `skills/README.md`. Nothing is deleted: the variant is kept as a record of the
  ideas it prototyped.

- **Removed the Coupled File Groups manifest from `metric/README.md`** (~90
  lines: *Why ALL Files Must Change Together*, the downstream impact chain,
  *Recommended Workflow for Proposing Changes*, the manifest itself, and the
  *Versioning Quick Reference*). It arrived in May 2026 as the written spec for
  the `metric-alignment-check` workflow and the propagation skill, both deleted
  in July, and had drifted accordingly: it told readers to update a template
  filename "only if the XLSX is also regenerated" when the XLSX had been removed
  from the skill long before, and its group letters had already been reshuffled
  once by the retirement of `metric/scoring_schema`. The people running releases
  had never read it. The parts with no other home — the version-carrying files,
  including the `LICENSE.md` citation block and its copyright-year trap — moved
  into `RELEASING.md`; the rest was already covered better by
  `CONTRIBUTING.md`'s versioning policy and metric-change workflow, which
  `metric/README.md` now points at.

- `metric/src/scripts/release_metric_to_core.sh` publishes the metric's **JSON
  rendering alongside its YAML**, as `airbds_metric.json` and
  `airbds_metric.yaml` in one commit. The generator has written both files since
  v1.0.0, but the release moved only the YAML, so the JSON reached `airbds-core`
  by hand — and the copy that landed there was a different generation, carrying a
  `source` block and an `instructions` field that its own `airbds_metric.yaml`
  did not agree with. Publishing both from one commit is what stops the
  publication repo holding two versions of one metric. From v1.0.0 the JSON is
  required and a missing one aborts the release; the retained v0.3 and v0.4
  metrics predate the rendering and still publish as YAML alone.

- `scripts/publish-to-core.sh` accepts **repeated `--src`/`--dest` pairs**,
  copying each source to the destination in the same position and committing them
  together. A release was already more than one file — `--post-copy` exists
  because the publication repo's prose has to move with the artifact — so this
  generalises the engine along the axis it was already bending on, without
  teaching it anything about metrics or skills. Unequal counts and a repeated
  `--dest` are errors rather than guesses. Single-pair callers are unaffected:
  the skill release passes the same arguments it always did.

### Added
- `metric/src/scripts/check_metric_renderings_match.py` — confirms a metric's
  YAML and JSON hold the same data before either is published, comparing them as
  parsed objects so formatting and the YAML's comments cannot register as a
  difference, and naming the differing top-level keys when they do disagree. The
  two files cannot drift while they are generated together in one pass; this is
  the guard for when they are not. Run as a preflight by the metric release, and
  tested in `metric/src/tests/test_check_metric_renderings_match.py` (7 tests).

- `scripts/stamp_core_versions.py` — restamps the version numbers `airbds-core`'s
  `skills/README.md` quotes, so a release updates the prose describing it in the
  same commit that lands the artifact. That sentence ("currently at version 0.8.0
  and assessing against AIRBDS metric v1.0.0") is how a reader learns what they
  are downloading, and nothing in the release path had been touching it: the
  v0.8.0 / metric v1.0.0 numbers were added by hand *after* both release PRs
  merged. The numbers now live inside HTML comment markers, which render as
  nothing — the published page is unchanged, and the stamper gets an unambiguous
  target rather than a regex hunting version-shaped strings through prose that
  will be reworded. Only the versions passed are rewritten, which is what lets a
  metric release leave the skill version alone; rewriting is idempotent; a
  missing marker is an error, not a silent skip. `--check` reports drift without
  writing. Tested in `scripts/tests/test_stamp_core_versions.py` (12 tests).

- `skills/src/scripts/rechannel_skill_zip.py` — derives the `production` skill
  bundle from the tested `testing` one by substituting the channel token in
  `SKILL.md`, and proves that is all it did. A bundle carries its channel inside
  itself (`metadata.channel`, plus the prose naming which `channels.<name>` entry
  of the update manifest to read), so the alternative to rewriting is either
  shipping production users a bundle marked `testing`, or maintaining a third
  copy of `SKILL.md` in a `production/` directory that differs from `testing` by
  one word — duplication that drifts, and a build workflow publishing a
  "production" release from the repo where production does not live. The rewrite
  copies every other member verbatim (bytes, times, permissions, order) and
  verifies the result: undoing the substitution must reproduce the source
  `SKILL.md` byte for byte, nothing else may differ, and the result must not
  still mention the old channel. It refuses when the source already mentions
  `production`, the one case where a substitution cannot be undone and so cannot
  be checked. `--check` runs the same verification against an already-published
  zip, so a reviewer of the `airbds-core` PR can audit the artifact rather than
  trust it. Tested in `skills/src/tests/test_rechannel_skill_zip.py` (9 tests).

### Changed
- `scripts/publish-to-core.sh` gained `--post-copy <cmd>`, a hook run inside the
  clone after the released file is copied and before the commit, with anything it
  changes committed alongside. A release is not always one file — the publication
  repo's prose quotes what it ships — but the engine still knows nothing about
  metrics or skills, only that a caller may need a second edit in the same commit.
  The hook runs *before* the "already identical" check, so a release whose
  artifact is unchanged but whose prose has drifted is still a release rather than
  a no-op. A non-zero exit aborts before anything is pushed.
- `skills/src/scripts/release_skill_to_core.sh` and
  `metric/src/scripts/release_metric_to_core.sh` now stamp `skills/README.md` in
  `airbds-core` through that hook — the skill release setting both the skill and
  metric versions (the latter from `versions.json`, and only when it has one),
  the metric release setting only the metric version. Each moves the number it
  actually published and leaves the other alone. Both PR bodies and commit
  messages say so, and a README without the markers fails the release loudly.
- `skills/src/scripts/release_skill_to_core.sh` now publishes to the
  **`production`** channel rather than republishing the `testing` artifact as-is.
  It still promotes rather than rebuilds — same download, same digest check — and
  runs the result through `rechannel_skill_zip.py` before committing it, so what
  ships is provably the tested artifact modulo the channel token. The version
  gate moved from the `testing` entry in `skills/versions.json` to the
  `production` entry, because that is what an installed production skill polls;
  bump it before promoting. The PR body carries both sha256s and the `--check`
  command that verifies them. `--force` still overrides a manifest disagreement
  but never a failed rewrite: that would publish an artifact nobody can check.

## 2026-07

### Added
- `skills/src/scripts/release_skill_to_core.sh` — the push to production for the
  assessment skill. Promotes the **testing** channel's zip to
  [AIBIO-UK/airbds-core](https://github.com/AIBIO-UK/airbds-core) as
  `skills/airbds-assessment-skill.zip` (no channel, no version in the filename),
  on a `release/skill-v<version>` branch with a PR left open for review. It
  **promotes rather than rebuilds**: the zip is downloaded from this repo's
  `assessment-skill-testing` release, so production gets byte-for-byte what was
  tested instead of a locally rebuilt artifact that could differ (symlink
  dereferencing, file ordering, a dirty tree) under the same version number. The
  download is checked against the digest GitHub recorded at upload, and the PR
  body carries the sha256 for the reviewer. Before publishing it reads `SKILL.md`
  out of the zip and refuses a bundle from the wrong channel, or one whose
  `metadata.version` disagrees with the `testing` entry in `skills/versions.json`
  — that manifest is what installed skills poll, so publishing a version it does
  not advertise would ship users a release nothing announces. `--force`
  overrides, `--zip` publishes a local file, `--dry-run` rehearses. Documented in
  `skills/src/README.md` and `skills/docs/MAINTAINING.md`; tested offline in
  `skills/src/tests/test_release_skill_to_core.py` (9 tests, synthesised zip and
  stubbed `gh`).
- `scripts/publish-to-core.sh` — the shared engine behind both release scripts.
  It knows nothing about metrics or skills, only how to land a file in
  `airbds-core` safely: clone to a temp dir, guard against an existing release
  branch, commit, push, open a PR, never merge, never tag. The metric release was
  refactored onto it rather than having the skill release duplicate ~100 lines of
  the same shell; its existing tests passed unchanged across the refactor. Lives
  in top-level `scripts/` because it genuinely spans domains — both `metric/` and
  `skills/` publish through it.
- `metric/src/scripts/release_metric_to_core.sh` — publishes one metric version
  to the publication repository,
  [AIBIO-UK/airbds-core](https://github.com/AIBIO-UK/airbds-core). It copies
  `metric/airbds_metric_v<version>.yaml` to that repository's root as the
  **unversioned `airbds_metric.yaml`**, commits it on a `release/metric-v<version>`
  branch, pushes, and opens a PR for working-group review. Because the published
  filename carries no version, a tag or GitHub release in `airbds-core` is what
  downstream consumers pin to — so the script stops at the PR and never merges or
  tags. It clones the publication repo into a temporary directory each run rather
  than using a local checkout, publishes the YAML only, refuses to overwrite an
  existing release branch, and is a no-op when the published file already matches.
  `--dry-run` rehearses the whole thing without pushing. Documented in
  `metric/src/README.md` and `metric/README.md`; tested offline in
  `metric/src/tests/test_release_metric_to_core.py`, which drives the script
  against a throwaway local repository with a stubbed `gh`.
- `skills/docs/DESIGN.md` — how the assessment skill is put together: what
  `SKILL.md`'s frontmatter and body each do, what the bundled `assets/` carry,
  and why the metric is shipped as a symlinked data file rather than restated as
  prose in the instructions. Complements `skills/docs/MAINTAINING.md`, which
  covers the operational side (channels, the version manifest, release builds).
  Linked from `skills/README.md` and added to the Group C coupled-file list in
  `metric/README.md`, since its bundle diagram names the symlink's metric
  version.

### Changed
- **Moved the skills-manifest validator into the skills domain**:
  `scripts/validate-skills-versions.py` → `skills/src/scripts/validate_skills_versions.py`
  (renamed to snake_case to match the scripts already under `metric/src/` and
  `reviews/src/`). It validates `skills/versions.json` and nothing else, so it
  belongs beside the skills it serves rather than in top-level `scripts/`, which
  is for helpers that span the whole repo — now just `render-diagrams.sh`.
  Coupled change across the script's own path references, the
  `validate-skills-versions.yml` workflow (both `paths:` filters and the `run:`
  step — a stale path filter would silently stop the check firing),
  `skills/docs/MAINTAINING.md`, `metric/README.md`, and the top-level `README.md`
  structure tree. Added `skills/src/README.md` documenting the script, matching
  the `README.md` each sibling `src/` folder already carries.
- **Both skill assets now name their channel in full**:
  `airbds-assessment-skill-testing.zip` (was `airbds-assessment-skill.zip`, with
  no channel at all) and `airbds-assessment-skill-development.zip` (was
  `airbds-assessment-skill-dev.zip`). A downloaded file now says which channel it
  came from, and the two names are formed the same way instead of one spelling the
  channel out and the other abbreviating it. Coupled change per channel across its
  build workflow (both the `zip` step and `files:`), its `skill_update_url` in
  `skills/versions.json`, and the asset name in `skills/docs/MAINTAINING.md`, plus
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
  makes `skills/docs/MAINTAINING.md`'s description of the workflows — "each
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
  rename; `skills/docs/MAINTAINING.md` records this so nobody plans around a
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
