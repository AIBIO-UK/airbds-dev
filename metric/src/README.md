# `metric/src/` — metric-build tooling

Tooling that regenerates the canonical metric from its upstream source. Each
metric version pins how it is built:

- **v0.3** — from the committed spreadsheet in [`metric/upstream/`](../upstream/).
- **v0.4** — from the working group's public Google Sheet (the source of truth
  lives in Drive, not the repo).
- **v0.5** — from the working group's public Google Sheet (as v0.4), and also
  captures the sheet's Instructions tab into the metric YAML.

> **Review tooling** (the Google-Sheet → review-YAML converter and the review
> processor/scorer) lives under [`reviews/src/`](../../reviews/src/), beside the
> reviews it serves.

All commands run from the repo root.

## v0.3 — from the committed spreadsheet

`scripts/build_metric_yaml_from_spreadsheet_v0.3.py` regenerates
`metric/airbds_metric_v0.3.yaml` from the `.xlsx` in `metric/upstream/`.

```bash
python3 metric/src/scripts/build_metric_yaml_from_spreadsheet_v0.3.py          # regenerate
python3 metric/src/scripts/build_metric_yaml_from_spreadsheet_v0.3.py --check  # verify in sync
```

Needs Python 3 with `pyyaml` and `openpyxl`.

## v0.4 — from the public Google Sheet

`scripts/build_metric_yaml_from_google_sheet_v0.4.py` pulls the Scoring
and Lookups tabs from the [canonical sheet][sheet] (via the public CSV export —
no auth) and regenerates `metric/airbds_metric_v0.4.yaml`.

```bash
# Regenerate from the live sheet (also writes the provenance sidecar + breadcrumb)
python3 metric/src/scripts/build_metric_yaml_from_google_sheet_v0.4.py

# Verify the committed file still matches the live sheet (the drift check)
python3 metric/src/scripts/build_metric_yaml_from_google_sheet_v0.4.py --check

# Work offline from exported CSVs instead of fetching
python3 metric/src/scripts/build_metric_yaml_from_google_sheet_v0.4.py \
    --scoring-csv scoring.csv --lookups-csv lookups.csv
```

Needs only `pyyaml` — it reads the sheet's CSV export, not an `.xlsx`. (Fetching
and the CSV→worksheet adapter live in `scripts/sheet_source.py`.)

**Provenance.** A regenerate writes `metric/airbds_metric_v0.4.upstream.json`
(sheet id/url, a `content_sha256` of the source tabs — the content-addressed
"revision" — and a generation timestamp), plus a `# Source: … sha256 …`
breadcrumb at the top of the YAML. Because the hash is in the YAML, `--check`
(and the scheduled
[`metric-upstream-drift-check.yml`](../../.github/workflows/metric-upstream-drift-check.yml)
workflow) detect any change to the upstream sheet.

**Editorial metadata** not present in the sheet — license, the prose
description, and the scope descriptions — lives in the script's `CONFIG` block;
edit it there and re-run.

## v0.5 — from the public Google Sheet

`scripts/build_metric_yaml_from_google_sheet_v0.5.py` works like the v0.4
script (pulls the Scoring and Lookups tabs from the [v0.5 sheet][sheet-v05] via
the public CSV export and regenerates `metric/airbds_metric_v0.5.yaml`), with
two v0.5 differences:

- **Instructions capture.** It also pulls the sheet's **Instructions** tab and
  writes the generic reviewer guidance verbatim into a top-level `instructions:`
  block of the metric YAML, so downstream consumers (the review processor,
  auto-airbds, the assessment skills) read the same guidance the sheet shows.
  The per-review data-entry section on that tab is excluded. The Instructions
  tab is folded into the `content_sha256`, so an edit there is caught by
  `--check` and the drift workflow.
- **Restructured Lookups.** Per-question points now come from the
  `Points per Question` column of the Lookups `COUNTA of Grade` pivot (v0.4 read
  a flat `Grade / Points` table). The `Required proportions` grading table is
  unchanged.

```bash
# Regenerate from the live sheet (also writes the provenance sidecar + breadcrumb)
python3 metric/src/scripts/build_metric_yaml_from_google_sheet_v0.5.py

# Verify the committed file still matches the live sheet (the drift check)
python3 metric/src/scripts/build_metric_yaml_from_google_sheet_v0.5.py --check

# Work offline from exported CSVs (all three tabs required together)
python3 metric/src/scripts/build_metric_yaml_from_google_sheet_v0.5.py \
    --scoring-csv scoring.csv --lookups-csv lookups.csv \
    --instructions-csv instructions.csv
```

Offline tests run against committed fixtures of the three source tabs:

```bash
python3 metric/src/tests/test_build_metric_yaml_v05.py   # or: pytest metric/src/tests/
```

As with v0.4, editorial metadata not in the sheet lives in the script's `CONFIG`
block.

[sheet]: https://docs.google.com/spreadsheets/d/1eriM8bXAoNXsIR9l8OpI1XYEp8FbtBWt05CTIP9cVeg/edit
[sheet-v05]: https://docs.google.com/spreadsheets/d/13w-MiUQc2sLzRFqRQD_YT6BisE3Orv5Oj3i0YBw7r_M/edit
