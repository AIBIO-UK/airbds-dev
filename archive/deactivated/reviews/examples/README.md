# Review Examples

> **⚠️ Archived** along with the rest of the review-submission subsystem — see
> [`archive/deactivated/reviews/`](../). Paths below are relative to this
> archived location, not the (paused) live `reviews/` folder.

This directory contains example review files for testing and reference.

| File | Format | Compliant? | Purpose |
|------|--------|-----------|---------|
| `E-MTAB-0001_TS_1.yaml` | YAML | Yes | Compliant review — all 28 questions answered |
| `E-MTAB-0002_TS_1.csv` | CSV | Yes | Compliant review in CSV format |
| `bad-filename_noinit.yaml` | YAML | No | Bad filename (initials not uppercase) |
| `E-MTAB-0003_TS_1.yaml` | YAML | No | Bad content (4 errors: empty name, date format, wrong-case answer, missing question block) |
| `E-MTAB-0004_TS_1.csv` | CSV | No | Bad CSV content (4 errors: empty name, date format, uppercase answer, missing URL scheme) |

## How to test the processor locally

```bash
pip install pyyaml

# Test a compliant YAML (should rename file and generate CSV companion)
echo "archive/deactivated/reviews/examples/E-MTAB-0001_TS_1.yaml" > /tmp/test.txt
python3 archive/deactivated/reviews/src/scripts/review_processor.py --files /tmp/test.txt
echo "Exit code: $?"

# Test non-compliant content (should exit 1 with errors)
echo "archive/deactivated/reviews/examples/E-MTAB-0003_TS_1.yaml" > /tmp/test.txt
python3 archive/deactivated/reviews/src/scripts/review_processor.py --files /tmp/test.txt
echo "Exit code: $?"
```

> **Note:** Files in this directory were excluded from the automated CI workflow
> when it was live. See the archived [workflow](../../workflows/review-check.yml)
> for details. To trigger a full end-to-end test, see the archived
> [test workflow](../../workflows/review-test.yml).
