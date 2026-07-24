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
└── assets/
    ├── airbds_metric.yaml     → ../../../../metric/airbds_metric_v0.5.yaml
    └── review_template.yaml   → ../../../../reviews/review_template.yaml
```

Both channels currently point at v0.5; a channel may sit on an older metric, so
read the symlink rather than this diagram if you need a channel's actual version.

`assets/airbds_metric.yaml` is a complete description of the metric: every
question, its scope and weighting, the reviewer guidance attached to it, and the
grading rules that turn answers into a score and a grade.

`assets/review_template.yaml` is the structure the assessment is recorded in —
an answer slot and a free-text `comments` field for each question id, reviewer
and dataset blocks, and a `result` block for the weighted score and grade.

Both are **symlinks** into the canonical files elsewhere in this repository. The
build workflows dereference them into real files when they package a skill zip,
so a published skill is self-contained while the checked-in skill has no copy to
drift out of date. Nothing under `skills/` is ever the source of truth for
metric content.

## The metric is data, not prose

The body of `SKILL.md` does not restate the questions. It instructs the
assistant to read them from `assets/airbds_metric.yaml` and work through them,
which keeps a single definition of the metric across the skill, the review
tooling, and the [auto-airbds](https://github.com/AIBIO-UK/auto-airbds) frontend.

The version follows from the same choice. The skill reports the version it is
assessing against by reading `schema_version` out of the bundled metric file;
`SKILL.md` never hard-codes a version number. Pointing the symlink at a
different `metric/airbds_metric_v*.yaml` is therefore the entire mechanism for
moving a skill to a new metric version — see
[`MAINTENANCE.md`](MAINTENANCE.md) for the manifest bookkeeping that has to
accompany it.

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
