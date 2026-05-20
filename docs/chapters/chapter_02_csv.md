---
tags:
    - CSV
    - Excel
    - Google Sheets
    - beginner
---

# CSV Walkthrough

**Beginner · No coding required · Works in Excel or Google Sheets**

!!! overview "Overview"

    **Questions:**

    - How do I download and open the CSV template?
    - How do I fill in my reviewer details and answer all 28 questions?
    - How do I calculate my score and grade?
    - How do I save and submit my review?

    **Learning Objectives**

    By the end of this chapter, you will be able to:

    1. Open the review template in a spreadsheet application
    2. Fill in all 28 questions with Yes/No answers
    3. Correctly handle the Ethics questions (ACM-24–28)
    4. Calculate a weighted score and assign a grade
    5. Save and name your file ready for submission

    **Time:** 30–60 minutes per dataset review (depending on how well you know the dataset)

    **Prerequisite:** Complete [Chapter 1](chapter_01.md) to confirm CSV is the right format for you.

---

## Step 1 — Download the template

Download the blank review template:

**[metric/review_template.csv](https://github.com/AIBIO-UK/airbds-metric/raw/main/metric/review_template.csv)**

On GitHub: click the link, then click the **Download raw file** button (down-arrow icon, top-right of the file view).

!!! tip "Reference file"
    The full question reference — with complete guidance text, weights, and source mappings — is also available as a CSV:
    [metric/airbds_metric_v0.3.csv](https://github.com/AIBIO-UK/airbds-metric/raw/main/metric/airbds_metric_v0.3.csv)

---

## Step 2 — Open in Excel or Google Sheets

=== "Microsoft Excel"

    File → Open → browse to the downloaded `.csv` file. If prompted about the file format, choose to keep it as CSV.

=== "Google Sheets"

    1. Go to [sheets.google.com](https://sheets.google.com)
    2. Click **Blank**
    3. File → Import → Upload the `.csv` file
    4. Choose **Comma** as the separator type
    5. Click **Import data**

Once open, you will see two sections:

| Rows | Content |
|---|---|
| 1–12 | **Section A** — Reviewer and dataset information (fill in the `value` column) |
| 13 | Blank separator row |
| 14 | Column headers for the answer table |
| 15–42 | **Section B** — 28 questions (fill in `answer` and `comments` columns) |

---

## Step 3 — Fill in Section A: your details

Click in the **`value`** cell next to each field and type your information:

| Field | What to enter |
|---|---|
| `schema_version` | Leave as `0.3` |
| `reviewer_name` | Your full name |
| `reviewer_initials` | Your initials (e.g. `CH`) |
| `reviewer_orcid` | Your ORCID (e.g. `0000-0000-0000-0000`) — leave blank if none |
| `reviewer_affiliation` | Your institution |
| `review_date` | Today's date in `YYYY-MM-DD` format (e.g. `2025-06-01`) |
| `dataset_name` | Name of the dataset you are reviewing |
| `dataset_url` | URL of the dataset's landing page |
| `dataset_accession` | Accession number (e.g. `E-MTAB-1234`) if available |
| `hosting_resource` | Where the dataset is hosted (e.g. `ArrayExpress`, `Zenodo`) |
| `process_comments` | Any notes about your review process (optional) |

---

## Step 4 — Answer the 28 questions (Section B)

Scroll to **row 15**. You will see the answer table:

| Column | Purpose |
|---|---|
| `question_id` | Question code (ACM-1 to ACM-28) — **do not edit** |
| `scope` | Topic area — **do not edit** |
| `theme` | Sub-topic — **do not edit** |
| `weight` | Critical / Important / Optional — **do not edit** |
| `question` | The question text — **read this** |
| `guidance` | Detailed explanation to help you decide — **read this** |
| **`answer`** | **Type `Yes` or `No` here** |
| **`not_applicable`** | **See Step 5 (Ethics questions only)** |
| **`comments`** | **Optional: add any notes about your answer** |

Work through each of the 28 rows. Read the `question` and `guidance` columns, then type `Yes` or `No` in the `answer` column.

!!! tip "Hide the guidance column"
    Once you have read the guidance, you can hide that column to make the table less cluttered.
    Right-click the column header → **Hide column** (Excel) or **Hide column** (Google Sheets).

!!! warning "Weight matters"
    Questions marked **Critical** carry 80 points each. Getting one wrong has a large effect on the grade. Read the guidance carefully for ACM-4, ACM-5, ACM-9, ACM-12, ACM-13, ACM-17, ACM-20, and ACM-24/25.

---

## Step 5 — Handle Ethics questions (ACM-24 to ACM-28)

The last five questions apply only to datasets that contain **human or animal subject data**.

!!! info "Does your dataset contain human or animal subjects?"

    === "No human or animal subjects"

        For each of ACM-24 to ACM-28:

        - Type **`Yes`** in the `answer` column
        - Type **`TRUE`** in the `not_applicable` column
        - Optionally add a comment such as "No human or animal subject data in this dataset"

    === "Human or animal subjects present"

        Answer each of ACM-24 to ACM-28 normally (`Yes` or `No`) based on what you find in the dataset documentation. Leave `not_applicable` as `FALSE`.

---

## Step 6 — Calculate your score

The score for each question = **1** (if `Yes`) or **0** (if `No`), multiplied by the weight points.

| Weight tier | Points |
|---|---|
| Critical | 80 |
| Important | 5 |
| Optional | 2 |

Use these copy-paste formulas (assumes `weight` is in column D, `answer` in column G, rows 15–42):

**Count Yes answers per tier:**
```
=COUNTIFS(D15:D42,"Critical",G15:G42,"Yes")
=COUNTIFS(D15:D42,"Important",G15:G42,"Yes")
=COUNTIFS(D15:D42,"Optional",G15:G42,"Yes")
```

**Pass rates per tier (proportion answered Yes):**
```
Critical pass rate:  =COUNTIFS(D15:D42,"Critical",G15:G42,"Yes") / COUNTIF(D15:D42,"Critical")
Important pass rate: =COUNTIFS(D15:D42,"Important",G15:G42,"Yes") / COUNTIF(D15:D42,"Important")
Optional pass rate:  =COUNTIFS(D15:D42,"Optional",G15:G42,"Yes") / COUNTIF(D15:D42,"Optional")
```

**Total weighted score in one formula:**
```
=SUMPRODUCT(
  (G15:G42="Yes") * (D15:D42="Critical") * 80
  + (G15:G42="Yes") * (D15:D42="Important") * 5
  + (G15:G42="Yes") * (D15:D42="Optional") * 2
)
```

!!! note "Adjusting column letters"
    The formulas above assume the standard column layout of the template. If you have added extra columns, update the column letters (D, G) to match your spreadsheet.

---

## Step 7 — Determine the grade

Look up your pass rates in this table:

| Grade | Critical pass rate | Important pass rate | Optional pass rate |
|---|---|---|---|
| 🔴 **Caution** | < 0.875 (< 7/8) | any | any |
| 🟤 **Bronze** | ≥ 0.875 (≥ 7/8) | any | any |
| ⚪ **Silver** | = 1.0 (all 8) | ≥ 0.5 | any |
| 🟡 **Gold** | = 1.0 (all 8) | = 1.0 (all 11) | ≥ 0.5 |

The full grade reference is in [`metric/scoring_schema.csv`](https://github.com/AIBIO-UK/airbds-metric/blob/main/metric/scoring_schema.csv).

---

## Step 8 — Save and name your file

Save your completed spreadsheet as a **CSV** file using this naming convention:

```
<dataset_accession>_<your_initials>_<review_number>.csv
```

Examples:
- `E-MTAB-1234_CH_1.csv`
- `PRJNA987654_GF_1.csv`

If there is no accession number, use a short descriptive name for the dataset.

In Excel: File → Save As → select **CSV (Comma delimited)** as the file type.
In Google Sheets: File → Download → **Comma-separated values (.csv)**.

---

## Step 9 — Submit your review

Completed reviews are stored in the [`reviews/`](https://github.com/AIBIO-UK/airbds-metric/tree/main/reviews) folder.

See [CONTRIBUTING.md](https://github.com/AIBIO-UK/airbds-metric/blob/main/CONTRIBUTING.md) for full submission instructions. The short version:

1. Fork the repository on GitHub
2. Add your CSV to the `reviews/` folder
3. Open a pull request against `main`

!!! tip "Not sure how to use GitHub?"
    If pull requests are unfamiliar, you can email your completed CSV to the working group. Contact details are at [aibio.ac.uk/about/working-groups/airbds/](https://aibio.ac.uk/about/working-groups/airbds/).

---

Well done — you have completed a dataset review using the CSV format! 🎉

Continue to [Further Resources](../follow_up_training.md) or return to the [About page](../index.md).
