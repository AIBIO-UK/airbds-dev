---
tags:
    - AI-readiness
    - bioscience datasets
    - FAIR data
    - scoring metric
---

# AIRBDS AI-Readiness Dataset Scoring Metric

**A practical guide to evaluating bioscience datasets for AI/ML use**

Developed by the [AIRBDS Working Group](https://aibio.ac.uk/about/working-groups/airbds/), AIBIO-UK · Funded by BBSRC · Licensed CC BY 4.0

---

!!! overview "Overview"

    **Questions this tutorial answers:**

    - What does the AIRBDS metric measure, and why does it matter?
    - Should I use the CSV (spreadsheet) or YAML (text file) format?
    - How do I work through all 28 questions and calculate a grade?
    - How do I submit my completed review?

    **Learning Objectives**

    By the end of this tutorial, you will be able to:

    1. Describe what the AIRBDS metric assesses and how it is scored
    2. Choose the format (CSV or YAML) that suits your technical background
    3. Complete a full dataset review and assign a grade (Caution / Bronze / Silver / Gold)
    4. Submit a completed review to the repository

    **Who this is for:** Researchers, data curators, and repository managers working with bioscience datasets

    **Skill levels covered:** Beginner (CSV path) · Intermediate (YAML path)

    **Estimated time:** 30–60 minutes per dataset review

---

## What is the AIRBDS Metric?

The AIRBDS metric is a structured checklist of **28 Yes/No questions** that assesses whether a bioscience dataset is ready for use in AI and machine learning workflows. Questions cover four areas:

| Scope | Questions | What it checks |
|---|---|---|
| **Infrastructure** | ACM-1 – ACM-10 | Access, licensing, unique identifiers, version control |
| **Metadata** | ACM-11 – ACM-17 | Bias documentation, standards, preprocessing, provenance |
| **Content** | ACM-18 – ACM-23 | Completeness, consistency, format |
| **Ethics** | ACM-24 – ACM-28 | Consent, privacy, security, data protection |

Each answer contributes to a weighted score. Datasets receive one of four grades:

| Grade | Meaning |
|---|---|
| 🔴 **Caution** | Fails one or more Critical criteria — serious limitations for AI/ML use |
| 🟤 **Bronze** | Passes most Critical questions (≥ 7/8) |
| ⚪ **Silver** | Passes all Critical + ≥ 50% of Important questions |
| 🟡 **Gold** | Passes all Critical and Important + ≥ 50% of Optional questions |

---

## How to use this tutorial

**Start here → [Chapter 1: Getting Started — Choose Your Format](chapters/chapter_01.md)**

Chapter 1 explains the difference between the CSV and YAML formats and helps you choose the right one based on your experience level. You will then follow either:

- **Chapter 2** — CSV walkthrough (beginner, no coding required, Excel or Google Sheets)
- **Chapter 3** — YAML walkthrough (intermediate, text editor and command line)

---

!!! note "Citation"
    If you use this metric in your research, please cite:

    > AIRBDS Working Group, AIBIO-UK. (2025). *AIRBDS AI-Readiness Dataset Scoring Metric* (v0.3). GitHub. <https://github.com/AIBIO-UK/airbds-metric>

    Full citation metadata is in [`CITATION.cff`](https://github.com/AIBIO-UK/airbds-metric/blob/main/CITATION.cff).
