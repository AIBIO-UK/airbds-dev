# archive/

Features moved out of the active repo during a cleanup, kept intact for later triage — nothing here is deleted, and everything can be moved back to reactivate it.

## `skills/`

The AI-agent assessment skills (development/GF channels — the **testing** channel copy has been reactivated live at [`skills/airbds-assessment-skill/`](../skills/airbds-assessment-skill/)), the Claude Code plugin definition (`claude-plugin/marketplace.json`), the skill-version manifest and validator, and the three GitHub Actions workflows that built/released the skill zips. Also holds the `metric-update-propagation` maintainer skill (`metric/skills/SKILL.md`), moved from inside `metric/`.

To reactivate a piece: move it back to its original relative path (e.g. `archive/skills/development/` → `skills/development/`, workflow files back into `.github/workflows/`) and fix any cross-references that were repointed at the archive.

## `deactivated/`

- `reviews/` — the review template, completed reviews, scoring tooling (`review_processor.py`), the reviewer-spreadsheet-to-YAML converter, tutorials, and `GUIDANCE.md` (the scoring rationale doc). There is no live `reviews/` folder at the repo root anymore — dataset-review submission has been discontinued for now; everything related to it lives only here.
- `metric/` — the retired v0.3 build chain (`.xlsx` workbook + build script) and the CSV files both metric build scripts used to emit, plus `airbds_metric_v0.3.yaml` (the superseded version). The live v0.4 build tooling has since been reactivated at [`admin/`](../admin/) rather than moved back under `metric/`.
- `scripts/render-diagrams.sh` — renders `.d2` diagram sources to SVG.
- `workflows/` — five GitHub Actions workflows moved out of `.github/workflows/` (which disables them): `metric-alignment-check.yml`, `metric-source-sync-check.yml`, `review-check.yml`, `review-test.yml`, `render-diagrams.yml`. Moving a workflow file back into `.github/workflows/` re-enables it. (`metric-upstream-drift-check.yml` has been reactivated back into `.github/workflows/`.)
- `AGENTS.md` (with `CLAUDE.md`, a note about the former symlink) — the repo's AI-agent instructions file. There is currently no live agent-instructions file at the repo root.

The only workflow live in the repo is `.github/workflows/metric-upstream-drift-check.yml`; everything else above stays disabled until moved back.
