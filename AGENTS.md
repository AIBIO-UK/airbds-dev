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
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — versioning policy and how metric changes
  are proposed.

## Memory Management
- When you learn something important about this project (build commands, architecture decisions, code conventions, debugging insights, workflow preferences. etc), update this file and other documentation to record it.
