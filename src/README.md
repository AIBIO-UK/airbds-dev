# `src/` — AIRBDS tooling

A self-contained workspace for the project's tooling, kept out of the repository
root. The design rationale lives in [`docs/DESIGN.md`](docs/DESIGN.md).

## TypeScript

**`google-sheet-converter/`** is a reusable library (its own npm package — `package.json`,
dependencies, and `tsconfig.json` live there; see
[`google-sheet-converter/README.md`](google-sheet-converter/README.md) to work on it) that turns an AIRBDS
assessment spreadsheet into a review YAML conforming to
[`metric/review_template.yaml`](../metric/review_template.yaml). It is the shared
core — the CLI uses it today, and a website will use it server-side to parse
incoming spreadsheet links. The CLI is
`scripts/convert_review_google_sheet_to_yaml_v0.3.mts`.

### Setup & run

```bash
# 1. Install Bun (macOS / Linux), then restart your shell or `source ~/.bashrc`
curl -fsSL https://bun.sh/install | bash

# 2. Install dependencies (one-time — they live in the converter package)
cd src/google-sheet-converter
bun install

# 3. Convert a sheet → review YAML (run the CLI from src/scripts)
cd ../scripts
bun ./convert_review_google_sheet_to_yaml_v0.3.mts <google-sheets-url-or-id> review.yaml
```

The first argument is the sheet, the second (optional) is the output path
(default: stdout). You can pass either the full Google Sheets URL or just its id
— the token in `docs.google.com/spreadsheets/d/<id>/edit`. The spreadsheet must
be shared **"anyone with the link"** for the public CSV export to work.

Offline / private sheets — export the two relevant tabs to CSV yourself and pass
them in instead of `--sheet`:

```bash
bun ./convert_review_google_sheet_to_yaml_v0.3.mts \
    --review-csv review-info.csv --questions-csv questions.csv review.yaml
```

Notes:

- The converter **does not score**. It leaves `result` blank; `review_processor.py`
  / CI compute the weighted score and grade and rename the file.
- The spreadsheet has no reviewer initials, ORCID, affiliation, or review date, so
  those are left blank for you to fill in (warnings flag them). Warnings also list
  any unanswered questions — the file is a draft until every question is `Yes`/`No`.
- After converting, name the file per
  [`CONTRIBUTING.md`](../CONTRIBUTING.md) (`<accession>_<INITIALS>_<n>.yaml`) and
  submit it; CI scores it on the way in.

## Python

- `scripts/review_processor.py` — validates, scores, and converts review files (CI + local).
- `scripts/build_metric_yaml_and_csv_from_spreadsheet_v0.3.py` — regenerates the
  metric YAML/CSV from the source spreadsheet.

These need Python 3 with `pyyaml` (and `openpyxl` for the build script).
