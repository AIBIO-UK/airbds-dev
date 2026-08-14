# AGENTS.md

## General Instructions
- Documentation must be kept up to date with any relevant changes to the project. 
- Keep documentation organized and concise. A new file in docs/ can be split off and referenced from here when necessary.
- All new functionality must have an accompanying passing unit test.
- Document and code should follow the DRY (Don't Repeat Yourself) principle when reasonable.
- Tests should always be run after making any changes and any fails fixed.

## Key Documents
- [`RELEASING.md`](RELEASING.md) — the running order for publishing a new metric
  version and the assessment skill that carries it. Read it before changing
  anything in the release path (`scripts/publish-to-core.sh`, the two
  `release_*_to_core.sh` scripts, `skills/versions.json`), and keep it in step
  when that path changes.
- [`metric/README.md`](metric/README.md) — the metric's reference doc, including
  the versioning policy and how a metric change is proposed.

## Which repository does a link point at?

There are two repositories, and the split is deliberate — don't "fix" one into
the other:

- **Identity / attribution** (how the metric is cited and credited) → the
  publication repo, [`airbds-core`](https://github.com/AIBIO-UK/airbds-core):
  `CITATION.cff` `repository-code`, the suggested-citation blocks in `LICENSE.md`
  and `README.md`, the generated metric YAMLs' `repository:` field, tutorial
  footers.
- **Actual use** (anything a reader clicks to *do* something) → this repo,
  `airbds-dev`: `git clone`, opening a PR, downloading a skill, the skills'
  update manifest and `skill_update_url`, `/plugin marketplace add`.

The `repository:` field in the metric YAMLs is **generated** from the `CONFIG`
block in `metric/src/scripts/` — change it there, never hand-edit the YAML. The
skills' update URLs are baked into each published zip, so repointing one strands
already-installed skills; see [`skills/docs/MAINTAINING.md`](skills/docs/MAINTAINING.md)
first.

## Memory Management
- When you learn something important about this project (build commands, architecture decisions, code conventions, debugging insights, workflow preferences. etc), update this file and other documentation to record it.
