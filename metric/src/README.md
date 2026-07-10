# `metric/src/` — metric-build tooling

Tooling that regenerates the canonical metric from its upstream source: the
working group's public Google Sheet (the source of truth lives in Drive, not
the repo). Output is **YAML only**.

All commands run from the repo root.

## Building from the Google Sheet

`scripts/build_metric_yaml_and_csv_from_google_sheet_v0.4.py` pulls the Scoring
and Lookups tabs from the [canonical sheet][sheet] (via the public CSV export —
no auth) and regenerates `metric/airbds_metric_v0.4.yaml`. It writes YAML only.

```bash
# Regenerate from the live sheet (also writes the provenance sidecar + breadcrumb)
python3 metric/src/scripts/build_metric_yaml_and_csv_from_google_sheet_v0.4.py

# Verify the committed file still matches the live sheet (the drift check)
python3 metric/src/scripts/build_metric_yaml_and_csv_from_google_sheet_v0.4.py --check

# Work offline from exported CSVs instead of fetching
python3 metric/src/scripts/build_metric_yaml_and_csv_from_google_sheet_v0.4.py \
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

[sheet]: https://docs.google.com/spreadsheets/d/1eriM8bXAoNXsIR9l8OpI1XYEp8FbtBWt05CTIP9cVeg/edit
