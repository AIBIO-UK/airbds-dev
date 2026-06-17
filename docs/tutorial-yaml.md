# How to Score a Dataset with the AIRBDS Metric

**Format: YAML · Intermediate · Requires a text editor and basic command-line familiarity**

> **Full interactive version:** [airbds-metric-tutorial](https://aibio-uk.github.io/airbds-metric-tutorial/chapters/chapter_03_yaml/) — rendered lesson site with navigation, tips, and format chooser.

This tutorial walks you through scoring a bioscience dataset for AI-readiness using the YAML workflow. It assumes you are comfortable opening a terminal, running basic commands, and editing plain text files.

---

## What you will do

Copy the YAML review template, fill in your answers to 28 Yes/No questions, validate the file, calculate a grade, and submit your review via a pull request.

---

## Prerequisites

- A plain-text editor (VS Code, Sublime Text, nano, vim, or similar)
- [Git](https://git-scm.com/) installed
- Python 3 (for YAML validation) — run `python3 --version` to check

---

## Step 1 — Get the repository

Clone the repository to your local machine:

```bash
git clone https://github.com/AIBIO-UK/airbds-metric.git
cd airbds-metric
```

Or, if you plan to submit your review, fork the repository on GitHub first, then clone your fork.

---

## Step 2 — Copy the template

Create a new file in the `reviews/testing/` folder using the naming convention `<accession>_<initials>_<n>.yaml`:

```bash
cp reviews/review_template.yaml reviews/testing/E-MTAB-1234_CH_1.yaml
```

Replace `E-MTAB-1234` with the dataset's accession number and `CH` with your initials. If there is no accession number, use a short descriptive slug.

Open the new file in your text editor.

---

## Step 3 — Fill in reviewer and dataset metadata

The top of the file has two blocks. Fill in every field:

```yaml
reviewer:
  name: "Charlie Harrison"
  initials: "CH"
  orcid: "0000-0001-2345-6789"   # optional — leave as "" if you don't have one
  affiliation: "Aberystwyth University"
  review_date: "2025-06-01"      # YYYY-MM-DD

dataset:
  name: "My Dataset Name"
  url: "https://www.ebi.ac.uk/arrayexpress/experiments/E-MTAB-1234/"
  hosting_resource: "ArrayExpress"
  accession: "E-MTAB-1234"
  comments: ""
```

---

## Step 4 — Answer the 28 questions

Scroll to the `answers:` block. For each question, set the `answer` field to `"Yes"` or `"No"`:

```yaml
answers:
  ACM-1:
    answer: "Yes"
    comments: "Dataset is fully downloadable via FTP."
  ACM-2:
    answer: "Yes"
    comments: ""
  ACM-3:
    answer: "No"
    comments: "No authentication required — dataset is public."
  # ... continue for all 28 questions
```

Rules:
- `answer` must be exactly `"Yes"` or `"No"` (case-sensitive, quoted).
- `comments` is optional — leave as `""` if you have nothing to add.
- Do not delete any question block, even if you answer `"No"`.

The question text and guidance for each ID are in [`metric/airbds_metric_v0.3.yaml`](../metric/airbds_metric_v0.3.yaml).

---

## Step 5 — Handle Ethics questions (ACM-24 to ACM-28)

These five questions apply only to datasets containing **human or animal subject data**.

If your dataset contains **no human or animal subjects**, set `not_applicable: true` and `answer: "Yes"` for each:

```yaml
  ACM-24:
    answer: "Yes"
    not_applicable: true
    comments: "No human or animal subject data."
  ACM-25:
    answer: "Yes"
    not_applicable: true
    comments: ""
  # ... repeat for ACM-26, ACM-27, ACM-28
```

If the dataset **does contain** human or animal subjects, answer normally and leave `not_applicable: false`.

---

## Step 6 — Validate your YAML

Before calculating the score, check that your file is valid YAML:

```bash
python3 -c "import yaml; yaml.safe_load(open('reviews/testing/E-MTAB-1234_CH_1.yaml')); print('YAML is valid')"
```

If you see `YAML is valid`, proceed. If you see an error, it will show you the line number to fix (common mistakes: missing quotes around `Yes`/`No`, inconsistent indentation).

---

## Step 7 — Calculate the score

Use these weight values:

| Weight | Points |
|---|---|
| Critical | 80 |
| Important | 5 |
| Optional | 2 |

The score for each question = 1 if `answer: "Yes"`, 0 if `answer: "No"`, multiplied by the weight points.

Calculate pass rates per tier (proportion of questions answered Yes):

```
Critical pass rate  = (number of Critical "Yes" answers) / 8
Important pass rate = (number of Important "Yes" answers) / 12
Optional pass rate  = (number of Optional "Yes" answers) / 8
```

See [`metric/airbds_metric_v0.3.yaml`](../metric/airbds_metric_v0.3.yaml) for which questions belong to each tier.

---

## Step 8 — Determine the grade

| Grade | Critical pass rate | Important pass rate | Optional pass rate |
|---|---|---|---|
| 🔴 Caution | < 0.875 | any | any |
| 🟤 Bronze | ≥ 0.875 | any | any |
| ⚪ Silver | = 1.0 | ≥ 0.5 | any |
| 🟡 Gold | = 1.0 | = 1.0 | ≥ 0.5 |

Record the final score and grade in the `result:` block at the bottom of your YAML file:

```yaml
result:
  weighted_score: 595
  grade: "Silver"
```

Full grade thresholds and rationale are in [`metric/scoring_schema.yaml`](../metric/scoring_schema.yaml).

---

## Step 9 — Submit via pull request

1. Stage and commit your file:

```bash
git checkout -b review/add-E-MTAB-1234
git add reviews/testing/E-MTAB-1234_CH_1.yaml
git commit -m "review: add review for E-MTAB-1234 (CH)"
```

2. Push to your fork:

```bash
git push -u origin review/add-E-MTAB-1234
```

3. Open a pull request on GitHub against the `main` branch of [AIBIO-UK/airbds-metric](https://github.com/AIBIO-UK/airbds-metric).

For full contribution guidelines, including naming conventions and inter-rater reliability recommendations, see [CONTRIBUTING.md](../CONTRIBUTING.md).

---

## Commit message convention

| Prefix | Use for |
|---|---|
| `review:` | Adding or updating a dataset review |
| `metric:` | Changes to the metric YAML |
| `docs:` | Documentation updates |
| `fix:` | Typos, broken links, formatting |

---

*AIRBDS Working Group, AIBIO-UK · Licensed CC BY 4.0 · [github.com/AIBIO-UK/airbds-metric](https://github.com/AIBIO-UK/airbds-metric)*
