# `metric/src/` — metric-build tooling

Tooling that regenerates the canonical metric from its source spreadsheet.

> **Review tooling** (the Google-Sheet → review-YAML converter and the review
> processor/scorer) lives under [`reviews/src/`](../../reviews/src/), beside the
> reviews it serves.

## Python

- `scripts/build_metric_yaml_and_csv_from_spreadsheet_v0.3.py` — regenerates
  `metric/airbds_metric_v0.3.{yaml,csv}` from the source spreadsheet in
  `metric/source/`. Run from the repo root:
  ```bash
  python3 metric/src/scripts/build_metric_yaml_and_csv_from_spreadsheet_v0.3.py
  ```

Needs Python 3 with `pyyaml` and `openpyxl`.
