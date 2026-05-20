---
tags:
    - CSV
    - YAML
    - format choice
---

# Getting Started — Choose Your Format

!!! overview "Overview"

    **Questions:**

    - What is the difference between CSV and YAML?
    - Which format is right for me?

    **Learning Objectives**

    By the end of this chapter, you will be able to:

    1. Explain in plain terms what CSV and YAML files are
    2. Select the format that best matches your technical background
    3. Navigate to the correct walkthrough chapter

    **Time:** 5 minutes

---

## What format do I need to choose?

The AIRBDS metric is available in two file formats. Both ask exactly the same 28 questions and produce the same grade — the only difference is how you open and fill in the template.

=== "What is CSV?"

    **CSV** stands for **Comma-Separated Values**.

    It is a plain-text table that opens directly in **Microsoft Excel**, **Google Sheets**, or any other spreadsheet program. Each row is a question; you type `Yes` or `No` in a column.

    You do **not** need to install any software or use a terminal. If you can use a spreadsheet, you can use the CSV format.

    Example of what it looks like in Excel:

    | question_id | weight | question | answer |
    |---|---|---|---|
    | ACM-1 | Important | Can the dataset be accessed in its entirety? | Yes |
    | ACM-4 | Critical | Is the dataset provided with a clear data-use license? | No |

=== "What is YAML?"

    **YAML** stands for **YAML Ain't Markup Language**.

    It is a structured plain-text format widely used in scientific computing and software development. You open it in a **text editor** (VS Code, Sublime Text, nano, vim) and edit fields by hand. You also use a **terminal** to copy files, validate them, and submit via Git.

    You need basic familiarity with the command line (e.g. `cp`, `git add`, `git push`).

    Example of what it looks like in a text editor:

    ```yaml
    ACM-1:
      answer: "Yes"
      comments: "Dataset available via FTP."
    ACM-4:
      answer: "No"
      comments: "License not clearly stated."
    ```

---

## Which format should I use?

!!! tip "Recommendation"

    **Never used a terminal or command line?** → Use **CSV** (Chapter 2).

    **Comfortable opening a terminal and running commands?** → Use **YAML** (Chapter 3).

    Both formats produce an identical review. You can always switch later.

:::cards cols=2

- title: "📊 CSV — Beginner"
  content: "Open in Excel or Google Sheets. Type Yes/No in a table. No installation required. Recommended if you are new to this workflow."
  url: chapter_02_csv.md

- title: "🗂 YAML — Intermediate"
  content: "Edit in a text editor. Submit via Git. Requires basic command-line familiarity. Recommended for researchers comfortable with version control."
  url: chapter_03_yaml.md

:::

---

## What you will need

=== "For the CSV path"

    - The [review_template.csv](https://github.com/AIBIO-UK/airbds-metric/raw/main/metric/review_template.csv) file (download from the repository)
    - Microsoft Excel, Google Sheets, LibreOffice Calc, or equivalent
    - The dataset you want to evaluate (its landing page / documentation)

=== "For the YAML path"

    - [Git](https://git-scm.com/) installed on your machine
    - A plain-text editor (VS Code, Sublime Text, nano, vim, or similar)
    - Python 3 (for YAML validation — run `python3 --version` to check)
    - The dataset you want to evaluate

---

!!! info "Ethics questions (ACM-24 to ACM-28)"

    Five of the 28 questions cover ethics, privacy, and security. These apply **only to datasets containing human or animal subject data**. If your dataset has no such data, you answer "Yes" and mark them as not applicable. Both tutorials explain this step clearly.

---

**Ready? Jump to your chapter:**

- [Chapter 2 — CSV Walkthrough (Beginner, no coding)](chapter_02_csv.md)
- [Chapter 3 — YAML Walkthrough (Intermediate, command line)](chapter_03_yaml.md)
