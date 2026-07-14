# How to Score a Dataset with the AIRBDS Metric

> **⚠️ Dormant — the submission process in this tutorial does not run.** The
> manual review workflow is not live: the CI that validated, scored, and
> committed back submitted review files is disabled. You can still follow the
> tutorial to *fill in* a review, but the steps describing what happens after you
> open a pull request will not happen. See [`reviews/README.md`](../README.md).

**Format: CSV · Beginner · No coding required · Works in Excel or Google Sheets**

> **Full interactive version:** [airbds-metric-tutorial](https://aibio-uk.github.io/airbds-metric-tutorial/chapters/chapter_02_csv/) — rendered lesson site with navigation, tips, and format chooser.

This tutorial walks you through scoring a bioscience dataset for AI-readiness using a spreadsheet. No programming knowledge is needed — you only need Excel, Google Sheets, or any equivalent tool.

---

## What you will do

You will open a CSV template, fill in your answers to 27 Yes/No questions about a dataset, and calculate a grade (Caution / Bronze / Silver / Gold) that summarises its AI-readiness.

---

## Step 1 — Get the template

Download the blank review template directly from the repository:

**[reviews/review_template.csv](../review_template.csv)**

To download: click the link above, then on GitHub click the **Download raw file** button (the down-arrow icon near the top-right of the file view).

> The canonical question reference — with full guidance text and weights — is in [metric/airbds_metric_v0.4.yaml](../../metric/airbds_metric_v0.4.yaml).

---

## Step 2 — Open in Excel or Google Sheets

- **Excel:** File → Open → browse to the downloaded `.csv` file.
- **Google Sheets:** Go to [sheets.google.com](https://sheets.google.com), click **Blank**, then File → Import → Upload the `.csv` file. Choose "Comma" as the separator and click **Import data**.

You will see two sections in the spreadsheet:

| Rows | Contents |
|---|---|
| 1–12 | **Section A** — Reviewer and dataset information (fill in the `value` column) |
| 13 | Blank separator row |
| 14 | Column headers for the answer table |
| 15–41 | **Section B** — 27 questions (fill in the `answer` and `comments` columns) |

---

## Step 3 — Fill in Section A: reviewer and dataset information

Click in the **`value`** cell next to each field and type your information:

| Field | What to enter |
|---|---|
| `schema_version` | Leave as `0.4` |
| `reviewer_name` | Your full name |
| `reviewer_initials` | Your initials (e.g. `CH`) |
| `reviewer_orcid` | Your ORCID (e.g. `0000-0000-0000-0000`), or leave blank |
| `reviewer_affiliation` | Your institution |
| `review_date` | Today's date in `YYYY-MM-DD` format (e.g. `2025-06-01`) |
| `dataset_name` | Name of the dataset you are reviewing |
| `dataset_url` | URL of the dataset's landing page |
| `dataset_accession` | Accession number (e.g. `E-MTAB-1234`), if available |
| `hosting_resource` | Where the dataset is hosted (e.g. `ArrayExpress`, `Zenodo`) |
| `process_comments` | Any notes about your review process (optional) |

---

## Step 4 — Answer the 27 questions (Section B)

Scroll down to row 15. You will see the answer table with these columns:

| Column | Purpose |
|---|---|
| `question_id` | Question identifier (ABC-01 through ABC-27) — do not edit |
| `scope` | Topic area — do not edit |
| `weight` | Critical / Important / Optional — do not edit |
| `question` | The question text — do not edit |
| `guidance` | Explanation to help you decide — read this, do not edit |
| **`answer`** | **Type `Yes` or `No` here** |
| **`not_applicable`** | **See Step 5** |
| **`comments`** | **Optional notes about your answer** |

For each of the 27 rows, read the `question` and `guidance` columns, then type **`Yes`** or **`No`** in the `answer` column.

> **Tip:** You can hide the `guidance` column once you have read it to make the table easier to navigate. Right-click the column header and choose "Hide column".

---

## Step 5 — Handle Ethics questions (ABC-24 to ABC-27)

The last four questions (ABC-24 to ABC-27) apply only to datasets that contain **human or animal subject data**.

- **If your dataset contains no human or animal subjects:** type **`Yes`** in the `answer` column and **`TRUE`** in the `not_applicable` column for each of ABC-24 to ABC-27.
- **If your dataset does contain human or animal subjects:** answer each question normally (`Yes` or `No`) and leave `not_applicable` as `FALSE`.

---

## Step 6 — Calculate your weighted score

The score is the sum of (answer × weight points) across all 27 questions.

- Yes = 1, No = 0
- Critical = 80 pts, Important = 5 pts, Optional = 2 pts

### Excel / Sheets formula

Add a new column (or use a blank cell elsewhere) and paste this formula. It assumes your answer table starts at row 15 with `weight` in column C and `answer` in column F — adjust column letters if your spreadsheet differs.

This formula counts the number of Yes answers per weight tier:

```
Critical Yes count:
=COUNTIFS(C15:C41,"Critical",F15:F41,"Yes")

Important Yes count:
=COUNTIFS(C15:C41,"Important",F15:F41,"Yes")

Optional Yes count:
=COUNTIFS(C15:C41,"Optional",F15:F41,"Yes")
```

Then compute pass rates (proportion correct per tier):

```
Critical pass rate:   =COUNTIFS(C15:C41,"Critical",F15:F41,"Yes") / COUNTIF(C15:C41,"Critical")
Important pass rate:  =COUNTIFS(C15:C41,"Important",F15:F41,"Yes") / COUNTIF(C15:C41,"Important")
Optional pass rate:   =COUNTIFS(C15:C41,"Optional",F15:F41,"Yes") / COUNTIF(C15:C41,"Optional")
```

Or for the total weighted score in one formula:

```
=SUMPRODUCT(
  (F15:F41="Yes") * (C15:C41="Critical") * 80
  + (F15:F41="Yes") * (C15:C41="Important") * 5
  + (F15:F41="Yes") * (C15:C41="Optional") * 2
)
```

---

## Step 7 — Determine the grade

Look up your critical, important, and optional pass rates in this table:

| Grade | Emoji | Critical pass rate | Important pass rate | Optional pass rate |
|---|---|---|---|---|
| Caution | 🔴 | < 7/8 (0.875) | any | any |
| Bronze | 🟤 | ≥ 7/8 (0.875) | any | any |
| Silver | ⚪ | = 1.0 (all) | ≥ 0.5 | any |
| Gold | 🟡 | = 1.0 (all) | = 1.0 (all) | ≥ 0.5 |

What the grades mean is explained in [reviews/GUIDANCE.md](../GUIDANCE.md); the thresholds are in the metric (`airbds_metric_v0.4.yaml`).

---

## Step 8 — Save and name your file

Save your completed spreadsheet using this naming convention:

```
<dataset_accession>_<your_initials>_<review_number>.csv
```

Examples:
- `E-MTAB-1234_CH_1.csv`
- `PRJNA987654_GF_1.csv`

If there is no accession number, use a short descriptive name for the dataset.

---

## Step 9 — Share your review

Completed reviews are collected in the [`reviews/testing/`](../testing/) folder of this repository.

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for full submission instructions. The short version:

1. Fork the repository on GitHub.
2. Add your CSV to the `reviews/testing/` folder.
3. Open a pull request against `main`.

If you are not familiar with GitHub pull requests, you can also email your completed CSV to the working group — contact details are at [aibio.ac.uk/about/working-groups/airbds/](https://aibio.ac.uk/about/working-groups/airbds/).

---

## Quick reference: weight tiers

| Weight | Points | Meaning |
|---|---|---|
| Critical | 80 | Fundamental — failing severely limits AI/ML suitability |
| Important | 5 | Best practice — affects reproducibility and interoperability |
| Optional | 2 | Desirable but not essential |

---

*AIRBDS Working Group, AIBIO-UK · Licensed CC BY 4.0 · [github.com/AIBIO-UK/airbds-metric](https://github.com/AIBIO-UK/airbds-metric)*
