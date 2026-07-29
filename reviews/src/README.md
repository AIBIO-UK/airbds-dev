# `reviews/src/` — review tooling

The tooling that turns assessments into review files and validates/scores them.
The design rationale lives in [`docs/DESIGN.md`](docs/DESIGN.md).

## TypeScript

**`google-sheet-converter/`** is a reusable library (its own npm package — `package.json`,
dependencies, and `tsconfig.json` live there; see
[`google-sheet-converter/README.md`](google-sheet-converter/README.md) to work on it) that turns an AIRBDS
assessment spreadsheet into a review YAML conforming to
[`review_template.yaml`](../review_template.yaml). It is the shared
core — the CLI uses it today, and a website will use it server-side to parse
incoming spreadsheet links. The CLI is
`scripts/convert_review_google_sheet_to_yaml.mts`; it reads the metric version
from the sheet (the "AIRBDS … Metric vX.Y" label on the Instructions tab) and
loads the matching metric automatically, so one command handles any version.

### Setup & run

```bash
# 1. Install Bun (macOS / Linux), then restart your shell or `source ~/.bashrc`
curl -fsSL https://bun.sh/install | bash

# 2. Install dependencies (one-time — they live in the converter package)
cd reviews/src/google-sheet-converter
bun install

# 3. Convert a sheet → review YAML (run the CLI from reviews/src/scripts)
cd ../scripts
bun ./convert_review_google_sheet_to_yaml.mts <google-sheets-url-or-id> review.yaml
```

The first argument is the sheet, the second (optional) is the output path
(default: stdout). You can pass either the full Google Sheets URL or just its id
— the token in `docs.google.com/spreadsheets/d/<id>/edit`. The spreadsheet must
be shared **"anyone with the link"** for the public CSV export to work.

Offline / private sheets — export the two relevant tabs to CSV yourself and pass
them in instead of `--sheet`:

```bash
bun ./convert_review_google_sheet_to_yaml.mts \
    --review-csv review-info.csv --questions-csv questions.csv review.yaml
```

Notes:

- The converter **does not score**. It leaves `result` blank; `review_processor.py`
  / CI compute the weighted score and grade and rename the file.
- The spreadsheet has no reviewer initials, ORCID, or affiliation, so those are
  left blank for you to fill in (warnings flag them). Warnings also list any
  unanswered questions — the file is a draft until every question is `Yes`/`No`.
- After converting, name the file per
  [`CONTRIBUTING.md`](../../CONTRIBUTING.md) (`<accession>_<INITIALS>_<n>.yaml`) and
  submit it; CI scores it on the way in.

## Python

- `scripts/review_processor.py` — validates, scores, and converts review files (CI + local).
- `scripts/airbds_scoring.py` — the scoring itself: answers in, weighted score
  and grade out. `review_processor.py` imports it, and the assessment skill
  bundles it as `scripts/score.py` (see
  [`skills/docs/DESIGN.md`](../../skills/docs/DESIGN.md)) so a skill-produced
  assessment and a submitted review are graded by one implementation. Standard
  library only — the skill runs wherever the user's assistant runs, so it reads
  the metric JSON rather than the YAML:

  ```bash
  # {"ABC-01": "Yes", ...} for every question id in the metric
  python3 reviews/src/scripts/airbds_scoring.py answers.json \
      --metric metric/airbds_metric_v0.5.json
  ```

- `scripts/build_review_template.py` — generates the blank template pair
  ([`review_template.yaml`](../review_template.yaml) /
  [`review_template.csv`](../review_template.csv)) from the metric YAML, so the
  two formats always agree. Regenerate on a metric bump; `--check` for drift:

  ```bash
  python3 reviews/src/scripts/build_review_template.py --version 0.5          # regenerate
  python3 reviews/src/scripts/build_review_template.py --version 0.5 --check  # verify in sync
  ```

Needs Python 3 with `pyyaml`, except `airbds_scoring.py`, which deliberately
needs nothing beyond the standard library.

Tests: `pytest reviews/src/tests/`.
