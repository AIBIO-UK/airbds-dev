# Skill design

Why the AIRBDS assessment skill is shaped the way it is. Scope: the anatomy of
the skill bundle and how work is divided between the instruction file and the
data files it carries. The operational side — release channels, the version
manifest, build workflows — is in [`MAINTENANCE.md`](MAINTENANCE.md).

## What a skill is

A skill is a directory containing an instruction file, `SKILL.md`, that an AI
assistant loads when the task at hand matches what the skill covers. The
directory may also carry reference material, templates, scripts, and other
supporting resources, which the instructions refer to by relative path.

`SKILL.md` has two parts. Its frontmatter declares **when the skill should be
invoked** — for AIRBDS, when a user asks for an assessment of a dataset at a
given URL. Its body is the instructions the assistant follows once invoked.

## What the AIRBDS bundle contains

```
airbds-assessment-skill/
├── SKILL.md
├── assets/
│   ├── airbds_metric.json     → ../../../../metric/airbds_metric_v1.0.0.json
│   └── review_template.yaml   → ../../../../reviews/review_template.yaml
└── scripts/
    └── score.py               → ../../../../reviews/src/scripts/airbds_scoring.py
```

The split follows the [agentskills.io](https://agentskills.io) layout: data the
skill reads lives in `assets/`, executables in `scripts/`. `score.py` therefore
looks for its metric in `../assets/` rather than beside itself.

Both source channels — `development/` and `testing/` — have this layout and
currently point at v1.0.0; a channel may sit on an older metric, so read the
symlink rather than this diagram if you need a channel's actual version. The
`production` bundle is derived from the `testing` one at release time and so has
the same layout by construction (see
[`MAINTENANCE.md`](MAINTENANCE.md#promoting-to-production)).

`assets/airbds_metric.json` is a complete description of the metric: every
question, its scope and weighting, the reviewer guidance attached to it, and the
grading rules that turn answers into a score and a grade. **The bundle carries
the JSON rendering only** — the model and `scripts/score.py` read the same file,
so there is no way for the questions the model answers and the metric it is
scored against to be different documents. The canonical YAML stays in `metric/`
for people to read; nothing the skill needs from the metric lives in a YAML
comment, so the bundle loses nothing by omitting it. See
[Scoring is mechanical, not modelled](#scoring-is-mechanical-not-modelled).

`assets/review_template.yaml` is the structure the assessment is recorded in —
an answer slot and a free-text `comments` field for each question id, reviewer
and dataset blocks, and a `result` block for the weighted score and grade.

All three are **symlinks** into the canonical files elsewhere in this repository.
The build workflows dereference them into real files when they package a skill
zip, so a published skill is self-contained while the checked-in skill has no
copy to drift out of date. Nothing under `skills/` is ever the source of truth
for metric content.

Because they are symlinks, the build workflows list the symlink *targets* in
their `paths:` triggers as well as `assets/*` and `scripts/*`: a GitHub path
filter matches the committed path and never follows a link, so without the
targets a commit that changed the metric or the scorer would leave the published
zip holding stale content. That list has to be kept in step with the symlinks.

## The metric is data, not prose

The body of `SKILL.md` does not restate the questions. It instructs the
assistant to read them from `assets/airbds_metric.json` and work through them,
which keeps a single definition of the metric across the skill, the review
tooling, and the [auto-airbds](https://github.com/AIBIO-UK/auto-airbds) frontend.

The version follows from the same choice. The skill reports the version it is
assessing against by reading `schema_version` out of the bundled metric file;
`SKILL.md` never hard-codes a version number. Pointing the symlink at a
different `metric/airbds_metric_v*` pair is therefore the entire mechanism for
moving a skill to a new metric version — see
[`MAINTENANCE.md`](MAINTENANCE.md) for the manifest bookkeeping that has to
accompany it.

## Scoring is mechanical, not modelled

Turning answers into a grade is arithmetic plus a threshold rule, and asking a
model to do it invites non-determinism in the one part of an assessment that has
a single correct answer. The grading rule is the sharp edge: a dataset earns the
highest grade for which *every* per-tier proportion clears a minimum **and** the
total clears a score floor. That is a conjunction over three tiers plus a floor,
evaluated highest-grade-first — much easier to get subtly wrong than a sum, and
weaker models get it wrong more often.

So the skill bundles `scripts/score.py`. The model supplies a flat
`{question-id: "Yes"|"No"}` document — the judgements only it can make — and the
script returns the score, the grade, and the per-tier counts. Everything fixed
comes from the bundle; nothing that is already known is transcribed by the model.
Handing the model the metric's tiers and thresholds to pass back in would have
re-introduced exactly the transcription risk the script exists to remove, and a
mistyped threshold would produce a wrong grade wearing the authority of having
been "calculated".

The script also refuses to score an answer set that is missing a question,
carries an unknown id, or holds anything other than exactly `"Yes"` or `"No"`.
Transcribing 25 answers is now where the residual risk lives, so that step fails
loudly rather than scoring a partial set into a plausible-looking grade.

Three consequences shaped the design:

- **It is the same code that scores submitted reviews.** `score.py` is a symlink
  to `reviews/src/scripts/airbds_scoring.py`, which `review_processor.py`
  imports. A skill-produced assessment and a hand-written review cannot be
  graded by two different implementations.
- **The bundled metric is JSON.** The script must run wherever the user's
  assistant runs, and PyYAML cannot be assumed there — so the metric is also
  generated as `metric/airbds_metric_vX.Y.json` and the script depends on
  nothing outside the standard library. The JSON is produced by parsing the YAML
  the build script has just rendered and re-serialising it, so it is that
  document rather than a second reading of the sheet. Since nothing the skill
  reads from the metric lives in a YAML comment, the bundle ships the JSON alone
  and the model reads it too — carrying both renderings would have duplicated
  the metric inside the bundle to no end. The YAML remains canonical in
  `metric/`, where its comments serve the people maintaining it.
- **It is an optimisation, never a precondition.** Some environments will not
  unpack the bundle's files, or cannot execute Python, or will not permit it.
  `SKILL.md` therefore keeps the scoring rules in full and instructs the model to
  fall back to working the score out itself. A skill that refused to assess where
  it could not run a script would be worse than one that occasionally does the
  arithmetic itself.

  The fallback is **disclosed, but only when it happens.** A score the script
  produced is reported with no commentary; a score the model calculated carries a
  warning saying so, why the script could not be run, and that the user should
  check it. The asymmetry is deliberate: the user cannot otherwise tell which of
  two quite differently-trustworthy numbers they are looking at, and announcing
  the mechanism on every successful run would be noise that trains them to skip
  the warnings section — the place a genuine problem has to be noticed.

## The assessment is open to challenge, but not to pressure

The report is not the end of the exchange. A follow-up step invites the user to
examine any part of the assessment — a particular answer, the evidence behind it,
why a higher grade was missed — in the same breath as offering them the saved
file. Two things motivate it. The model's weakest answers are the ones where a
resource was unreachable, and the user often knows the dataset better than a
crawl of its landing page does; and a score someone cannot interrogate is a score
they have no reason to trust.

That invitation creates the obvious hazard, so `SKILL.md` sets the bar for
changing an answer explicitly. Two grounds qualify: **evidence** the model did
not account for — never saw, could not reach, or overlooked — and a **flaw in
how it judged evidence it did see**, such as an aspect it failed to weigh or the
wrong `guidance` applied. The second matters as much as the first. Restricting
revision to new material would leave a user unable to argue the most ordinary
case of all: that the model looked at the right page and read it wrongly.

What qualifies a ground is not its kind but its specificity: the user must name
something that survives checking. The model is told to re-examine what it is
pointed at — re-fetching the resource where it can, and judging it rather than
accepting a description of it — and then to reach its own conclusion, with looking
again and explaining why the answer stands called out as a perfectly good outcome.
Re-examining is not conceding.

The step is deliberately written as an examination rather than a dispute. Users
are assumed to be acting in good faith, because they overwhelmingly are, and an
instruction to resist them would sour a conversation whose whole purpose is to
improve the assessment. But the risk this guards against never depended on bad
faith: a well-meant "are you sure?" is exactly what makes a model abandon a
correct answer. So the counterweight is put as a service to the user rather than a
defence against them — changing an answer you have checked and still believe leaves
them with a worse assessment than they arrived with.

It is pushed to revise **down** as readily as up, because the pressure in these
conversations runs one way: users press on "No" answers, and an assessment that
only ever ratchets upward is worthless for comparing datasets.

A revision is not recorded in the saved file. The comment fields carry the final
reasoning, and an assessment corrected on good evidence is simply a better
assessment — not a suspect one that needs flagging.

Any change to an answer re-enters the scoring path rather than being patched
arithmetically: the model re-runs `scripts/score.py` on the corrected answers.
This is the moment the temptation to adjust a total by hand is strongest, and
giving in to it would forfeit the determinism the script exists to provide.

## The output is the shared review template

An assessment produced by the skill is written in the same
`review_template.yaml` shape a human reviewer fills in by hand, so machine- and
human-produced assessments are scored by the same
`reviews/src/scripts/review_processor.py` and are directly comparable.

Recording `schema_version` and the reviewer's `review_date` alongside the
answers is what makes an assessment reproducible after the fact: the metric a
review was scored against is recoverable from the review itself, which is why
superseded metric versions are retained rather than deleted.

The one place the skill departs from human use is attribution. `SKILL.md`
instructs the assistant to put its own model identifier (e.g.
`claude-opus-4-8`) in `reviewer.name` and leave `initials`, `orcid`, and
`affiliation` blank, then tell the user they can substitute their own details
before using the file anywhere a named reviewer is expected. The template gains
no model-specific field; the provenance rides in the existing one, and an
unedited machine assessment is recognisable as such.
