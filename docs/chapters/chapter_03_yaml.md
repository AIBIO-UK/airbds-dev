---
tags:
    - YAML
    - command line
    - Git
    - intermediate
---

# YAML Walkthrough

**Intermediate · Requires a text editor and basic command-line familiarity**

!!! overview "Overview"

    **Questions:**

    - How do I clone the repository and copy the template?
    - How do I fill in reviewer details and answer all 28 questions in YAML?
    - How do I validate the file and calculate a grade?
    - How do I submit via pull request?

    **Learning Objectives**

    By the end of this chapter, you will be able to:

    1. Clone the repository and copy the YAML review template
    2. Fill in all reviewer metadata and 28 question answers
    3. Correctly handle the Ethics questions with the `not_applicable` field
    4. Validate the YAML file and resolve common errors
    5. Calculate a grade and submit via a pull request

    **Time:** 30–60 minutes per dataset review (depending on how well you know the dataset)

    **Prerequisite:** Complete [Chapter 1](chapter_01.md) to confirm YAML is the right format for you.

---

## Prerequisites

Before you begin, make sure you have:

- [Git](https://git-scm.com/) installed — run `git --version` to check
- A plain-text editor (VS Code, Sublime Text, nano, vim, or similar)
- Python 3 — run `python3 --version` to check (used for validation in Step 6)

---

## Step 1 — Get the repository

If you plan to **submit your review**, fork the repository on GitHub first, then clone your fork:

```bash
git clone https://github.com/<your-username>/airbds-metric.git
cd airbds-metric
```

If you just want to **explore locally** without submitting, clone the main repo directly:

```bash
git clone https://github.com/AIBIO-UK/airbds-metric.git
cd airbds-metric
```

---

## Step 2 — Copy the template

Create your review file in the `reviews/` folder using this naming convention:

```
<dataset_accession>_<your_initials>_<review_number>.yaml
```

```bash
cp metric/review_template.yaml reviews/E-MTAB-1234_CH_1.yaml
```

Replace `E-MTAB-1234` with the dataset's accession number and `CH` with your initials. Use a short descriptive name if there is no accession number.

Open the new file in your text editor.

!!! tip "Reference file"
    Keep [`metric/airbds_metric_v0.3.yaml`](https://github.com/AIBIO-UK/airbds-metric/blob/main/metric/airbds_metric_v0.3.yaml) open in another tab — it contains the full question text and guidance for each ACM ID.

---

## Step 3 — Fill in reviewer and dataset metadata

The top of the file has two blocks. Fill in every field:

```yaml
reviewer:
  name: "Charlie Harrison"
  initials: "CH"
  orcid: "0000-0001-2345-6789"   # leave as "" if you don't have an ORCID
  affiliation: "Aberystwyth University"
  review_date: "2025-06-01"      # YYYY-MM-DD format

dataset:
  name: "My Dataset Name"
  url: "https://www.ebi.ac.uk/arrayexpress/experiments/E-MTAB-1234/"
  hosting_resource: "ArrayExpress"
  accession: "E-MTAB-1234"
  comments: ""

process_comments: ""
```

---

## Step 4 — Answer the 28 questions

Scroll to the `answers:` block. For each question, set `answer` to `"Yes"` or `"No"`:

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
    comments: "No authentication required — dataset is fully public."
```

!!! warning "Formatting rules"
    - `answer` must be exactly `"Yes"` or `"No"` — case-sensitive and quoted.
    - `comments` is optional — leave as `""` if you have nothing to add.
    - Do **not** delete any question block, even if the answer is `"No"`.
    - YAML is **indentation-sensitive** — do not mix tabs and spaces.

Work through all 28 question blocks (ACM-1 through ACM-28). The full question text and guidance for each ID is in [`metric/airbds_metric_v0.3.yaml`](https://github.com/AIBIO-UK/airbds-metric/blob/main/metric/airbds_metric_v0.3.yaml).

!!! tip "Weight matters"
    Eight questions are marked **Critical** (80 pts each): ACM-4, ACM-5, ACM-9, ACM-12, ACM-13, ACM-17, ACM-20, and ACM-24. Read the guidance carefully for these — failing one has a large impact on the grade.

---

## Step 5 — Handle Ethics questions (ACM-24 to ACM-28)

These five questions apply only to datasets containing **human or animal subject data**.

!!! info "Does your dataset contain human or animal subjects?"

    === "No human or animal subjects"

        Set `not_applicable: true` and `answer: "Yes"` for each of ACM-24 to ACM-28:

        ```yaml
          ACM-24:
            answer: "Yes"
            not_applicable: true
            comments: "No human or animal subject data in this dataset."
          ACM-25:
            answer: "Yes"
            not_applicable: true
            comments: ""
          ACM-26:
            answer: "Yes"
            not_applicable: true
            comments: ""
          ACM-27:
            answer: "Yes"
            not_applicable: true
            comments: ""
          ACM-28:
            answer: "Yes"
            not_applicable: true
            comments: ""
        ```

    === "Human or animal subjects present"

        Answer each of ACM-24 to ACM-28 normally (`"Yes"` or `"No"`) and leave `not_applicable: false`.

---

## Step 6 — Validate your YAML

Before calculating the score, check that your file is syntactically valid:

```bash
python3 -c "import yaml; yaml.safe_load(open('reviews/E-MTAB-1234_CH_1.yaml')); print('YAML is valid')"
```

If you see `YAML is valid`, proceed. If you see an error, it will show the line number.

**Common mistakes:**

| Symptom | Likely cause |
|---|---|
| `could not find expected ':'` | Missing colon after a key |
| `found character '\t'` | Tab used instead of spaces for indentation |
| `expected a block sequence entry` | `answer` value not quoted — write `"Yes"` not `Yes` |
| `mapping values are not allowed here` | Colon inside an unquoted string — quote the value |

---

## Step 7 — Calculate the score

Use these weight values:

| Weight tier | Points | Questions |
|---|---|---|
| Critical | 80 | ACM-4, 5, 9, 12, 13, 17, 20, 24 (8 total) |
| Important | 5 | ACM-1, 2, 6, 11, 16, 18, 19, 21, 25, 26, 27 (11 total) |
| Optional | 2 | ACM-3, 7, 8, 10, 14, 15, 22, 23, 28 (9 total) |

Compute pass rates (proportion of questions answered "Yes" per tier):

```
Critical pass rate  = (Critical "Yes" count) / 8
Important pass rate = (Important "Yes" count) / 11
Optional pass rate  = (Optional "Yes" count) / 9
```

The full scoring reference is in [`metric/scoring_schema.yaml`](https://github.com/AIBIO-UK/airbds-metric/blob/main/metric/scoring_schema.yaml).

---

## Step 8 — Determine the grade

| Grade | Critical pass rate | Important pass rate | Optional pass rate |
|---|---|---|---|
| 🔴 **Caution** | < 0.875 (< 7/8) | any | any |
| 🟤 **Bronze** | ≥ 0.875 (≥ 7/8) | any | any |
| ⚪ **Silver** | = 1.0 (all 8) | ≥ 0.5 | any |
| 🟡 **Gold** | = 1.0 (all 8) | = 1.0 (all 11) | ≥ 0.5 |

Record the score and grade in the `result:` block at the bottom of your YAML file:

```yaml
result:
  weighted_score: 595
  grade: "Silver"
```

---

## Step 9 — Submit via pull request

```bash
# Create a feature branch
git checkout -b review/add-E-MTAB-1234

# Stage your file
git add reviews/E-MTAB-1234_CH_1.yaml

# Commit
git commit -m "review: add review for E-MTAB-1234 (CH)"

# Push to your fork
git push -u origin review/add-E-MTAB-1234
```

Then open a **pull request** on GitHub against the `main` branch of [AIBIO-UK/airbds-metric](https://github.com/AIBIO-UK/airbds-metric).

!!! info "Commit message convention"

    | Prefix | Use for |
    |---|---|
    | `review:` | Adding or updating a dataset review |
    | `metric:` | Changes to the metric YAML |
    | `docs:` | Documentation updates |
    | `fix:` | Typos, broken links, formatting |

For full contribution guidelines see [CONTRIBUTING.md](https://github.com/AIBIO-UK/airbds-metric/blob/main/CONTRIBUTING.md).

---

Well done — you have completed a dataset review using the YAML format! 🎉

Continue to [Further Resources](../follow_up_training.md) or return to the [About page](../index.md).
