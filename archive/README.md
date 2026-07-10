# archive/

Features moved out of the active repo during a cleanup, kept intact for later triage — nothing here is deleted, and everything can be moved back to reactivate it.

## `skills/`

The AI-agent assessment skills (development/testing/GF channels), the Claude Code plugin definition (`claude-plugin/marketplace.json`), the skill-version manifest and validator, and the three GitHub Actions workflows that built/released the skill zips. Also holds the `metric-update-propagation` maintainer skill (`metric/skills/SKILL.md`), moved from inside `metric/`.

To reactivate a piece: move it back to its original relative path (e.g. `archive/skills/testing/` → `skills/testing/`, workflow files back into `.github/workflows/`) and fix any cross-references that were repointed at the archive.

## `deactivated/`

- `reviews/` — the review template, completed reviews, scoring tooling (`review_processor.py`), the reviewer-spreadsheet-to-YAML converter, and tutorials. The current `reviews/` folder at the repo root is a simple drop folder with none of this.
- `metric/` — the retired v0.3 build chain (`.xlsx` workbook + build script) and the CSV files both metric build scripts used to emit.
- `scripts/render-diagrams.sh` — renders `.d2` diagram sources to SVG.
- `workflows/` — five GitHub Actions workflows moved out of `.github/workflows/` (which disables them): `metric-alignment-check.yml`, `metric-source-sync-check.yml`, `review-check.yml`, `review-test.yml`, `render-diagrams.yml`. Moving a workflow file back into `.github/workflows/` re-enables it.

The only workflow still active is `.github/workflows/metric-upstream-drift-check.yml` — it was never touched by this cleanup.
