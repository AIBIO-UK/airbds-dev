---
airbds_process_log: true
schema_version: "1.0.1"
dataset:
  name: ""
  url: ""
reviewer: ""        # model id that performed the assessment, e.g. claude-opus-4-8
review_date: ""     # ISO 8601, e.g. 2026-08-31T14:32:05Z
pairs_with: ""      # filename of the assessment YAML this log explains
---

<!--
AIRBDS assessment process log — template for metric v1.0.1

Companion to the assessment YAML. It records HOW each answer was reached: the
sources consulted, the checks performed, and the reasoning to the verdict. The
YAML remains the authoritative record of the answers and score; this log is the
human-readable audit trail behind them.

Fill in every question block below, in this order, covering every question id
and no others. Keep it terse:

  - **Answer:** echo the FINAL Yes/No from the YAML verbatim, so the two files
    can be cross-checked for drift.
  - **Sources:** each page, file, API endpoint, or record you accessed, and what
    you inspected in it. One per line. Omit the block only if you consulted
    nothing (e.g. a question answered purely from another question's evidence —
    say which).
  - **Checks:** what you looked for and what you found, as `looked for → found`.
    One observation per line.
  - **Rationale:** one or two lines tying the checks to the verdict.

Every question carries at least one Source and one Check — including answers
that follow from the metric's own guidance or from a property of the hosting
repository/platform (cite the clause, and the record that establishes the
repository). The only block you may collapse to a bare Answer line is an Ethics
question that does not apply (no human/animal subjects): write **Answer:** Yes —
no human/animal subjects (not applicable).

Do not add or remove question blocks — this list is fixed for metric v1.0.1.
The ✅/❌ markers used in the report are presentation only; they are optional
here and never override the YAML answer.

Worked example of a filled block:

  ### ABC-02 — Is metadata provided along with the data?
  *Infrastructure · Important*

  **Answer:** No

  **Sources**
  - https://example.org/dataset/123 — landing page, "Files" and "Description" tabs
  - `dataset_bundle.zip` — listed contents; no metadata file inside

  **Checks**
  - Looked for a metadata record collocated with the data → only a link to an
    external journal article, which the metric excludes.
  - Looked for packaged metadata inside the download → archive holds data files
    only, no README/manifest/schema.

  **Rationale**
  No metadata travels with the data and the external article does not count → No.
-->

# AIRBDS assessment process log

- **Dataset:** <name>
- **URL:** <url>
- **Metric version:** 1.0.1
- **Reviewer:** <model id>
- **Date:** <ISO 8601>
- **Pairs with:** <assessment YAML filename>

---

## Infrastructure

### ABC-01 — Can the dataset be accessed in its entirety?
*Infrastructure · Important*

**Answer:** <Yes|No>

**Sources**
- <resource> — <what you inspected>

**Checks**
- <what you looked for> → <what you found>

**Rationale**
<one or two lines to the verdict>

### ABC-02 — Is metadata provided along with the data?
*Infrastructure · Important*

**Answer:** <Yes|No>

**Sources**
- <resource> — <what you inspected>

**Checks**
- <what you looked for> → <what you found>

**Rationale**
<one or two lines to the verdict>

### ABC-03 — Does the dataset include a mechanism for verifying its integrity?
*Infrastructure · Optional*

**Answer:** <Yes|No>

**Sources**
- <resource> — <what you inspected>

**Checks**
- <what you looked for> → <what you found>

**Rationale**
<one or two lines to the verdict>

### ABC-04 — Is the dataset released with a clear licence or terms of use?
*Infrastructure · Critical*

**Answer:** <Yes|No>

**Sources**
- <resource> — <what you inspected>

**Checks**
- <what you looked for> → <what you found>

**Rationale**
<one or two lines to the verdict>

### ABC-05 — Is the licence standardised and machine-readable?
*Infrastructure · Important*

**Answer:** <Yes|No>

**Sources**
- <resource> — <what you inspected>

**Checks**
- <what you looked for> → <what you found>

**Rationale**
<one or two lines to the verdict>

### ABC-06 — Is the dataset deposited in a FAIR-compliant archive?
*Infrastructure · Important*

**Answer:** <Yes|No>

**Sources**
- <resource> — <what you inspected>

**Checks**
- <what you looked for> → <what you found>

**Rationale**
<one or two lines to the verdict>

### ABC-07 — Is the dataset deposited in a domain-appropriate infrastructure?
*Infrastructure · Important*

**Answer:** <Yes|No>

**Sources**
- <resource> — <what you inspected>

**Checks**
- <what you looked for> → <what you found>

**Rationale**
<one or two lines to the verdict>

### ABC-08 — Is the dataset hosted in a searchable infrastructure?
*Infrastructure · Optional*

**Answer:** <Yes|No>

**Sources**
- <resource> — <what you inspected>

**Checks**
- <what you looked for> → <what you found>

**Rationale**
<one or two lines to the verdict>

### ABC-09 — Does the dataset have a globally unique, persistent identifier?
*Infrastructure · Critical*

**Answer:** <Yes|No>

**Sources**
- <resource> — <what you inspected>

**Checks**
- <what you looked for> → <what you found>

**Rationale**
<one or two lines to the verdict>

### ABC-10 — If the dataset is subject to updates, does it use a version control system?
*Infrastructure · Optional*

**Answer:** <Yes|No>

**Sources**
- <resource> — <what you inspected>

**Checks**
- <what you looked for> → <what you found>

**Rationale**
<one or two lines to the verdict>

---

## Metadata

### ABC-11 — Does the dataset use a machine-readable, domain-appropriate metadata standard?
*Metadata · Critical*

**Answer:** <Yes|No>

**Sources**
- <resource> — <what you inspected>

**Checks**
- <what you looked for> → <what you found>

**Rationale**
<one or two lines to the verdict>

### ABC-12 — Does the downloadable metadata include the identifier of the dataset?
*Metadata · Critical*

**Answer:** <Yes|No>

**Sources**
- <resource> — <what you inspected>

**Checks**
- <what you looked for> → <what you found>

**Rationale**
<one or two lines to the verdict>

### ABC-13 — Does the metadata document the modalities used?
*Metadata · Optional*

**Answer:** <Yes|No>

**Sources**
- <resource> — <what you inspected>

**Checks**
- <what you looked for> → <what you found>

**Rationale**
<one or two lines to the verdict>

### ABC-14 — Are transformation and preprocessing steps documented well enough to reproduce them?
*Metadata · Important*

**Answer:** <Yes|No>

**Sources**
- <resource> — <what you inspected>

**Checks**
- <what you looked for> → <what you found>

**Rationale**
<one or two lines to the verdict>

### ABC-15 — Is the provenance of the dataset clearly documented?
*Metadata · Critical*

**Answer:** <Yes|No>

**Sources**
- <resource> — <what you inspected>

**Checks**
- <what you looked for> → <what you found>

**Rationale**
<one or two lines to the verdict>

### ABC-16 — Is the dataset's sampling strategy or inclusion criteria documented in the metadata?
*Metadata · Important*

**Answer:** <Yes|No>

**Sources**
- <resource> — <what you inspected>

**Checks**
- <what you looked for> → <what you found>

**Rationale**
<one or two lines to the verdict>

---

## Content

### ABC-17 — Is the dataset free of duplicate records?
*Content · Important*

**Answer:** <Yes|No>

**Sources**
- <resource> — <what you inspected>

**Checks**
- <what you looked for> → <what you found>

**Rationale**
<one or two lines to the verdict>

### ABC-18 — Does the dataset include all expected records and content?
*Content · Important*

**Answer:** <Yes|No>

**Sources**
- <resource> — <what you inspected>

**Checks**
- <what you looked for> → <what you found>

**Rationale**
<one or two lines to the verdict>

### ABC-19 — Are units, data types and parameter names consistent between entries?
*Content · Critical*

**Answer:** <Yes|No>

**Sources**
- <resource> — <what you inspected>

**Checks**
- <what you looked for> → <what you found>

**Rationale**
<one or two lines to the verdict>

### ABC-20 — Does the dataset follow domain standards with respect to units, data types, parameter names?
*Content · Important*

**Answer:** <Yes|No>

**Sources**
- <resource> — <what you inspected>

**Checks**
- <what you looked for> → <what you found>

**Rationale**
<one or two lines to the verdict>

### ABC-21 — Does the data use an appropriate file format?
*Content · Optional*

**Answer:** <Yes|No>

**Sources**
- <resource> — <what you inspected>

**Checks**
- <what you looked for> → <what you found>

**Rationale**
<one or two lines to the verdict>

### ABC-22 — Is the data available in at least one open, non-proprietary format?
*Content · Optional*

**Answer:** <Yes|No>

**Sources**
- <resource> — <what you inspected>

**Checks**
- <what you looked for> → <what you found>

**Rationale**
<one or two lines to the verdict>

---

## Ethics

<!-- If the dataset has no human or animal subject data, each Ethics answer is
"Yes" (not applicable); collapse the block to the single Answer line shown. -->

### ABC-23 — If the dataset contains data from animal or human subjects, is an ethical assessment that covers acquisition present in the metadata or a linked clinical trial record?
*Ethics · Critical*

**Answer:** <Yes|No>  <!-- Yes — no human/animal subjects (not applicable), if so -->

**Sources**
- <resource> — <what you inspected>

**Checks**
- <what you looked for> → <what you found>

**Rationale**
<one or two lines to the verdict>

### ABC-24 — If the dataset contains data from human subjects, is data management with respect to privacy documented in the metadata or a linked clinical trial record?
*Ethics · Critical*

**Answer:** <Yes|No>  <!-- Yes — no human/animal subjects (not applicable), if so -->

**Sources**
- <resource> — <what you inspected>

**Checks**
- <what you looked for> → <what you found>

**Rationale**
<one or two lines to the verdict>

### ABC-25 — If the dataset contains data from human subjects, is the legal basis for data collection and processing documented in the metadata or a linked clinical trial record?
*Ethics · Critical*

**Answer:** <Yes|No>  <!-- Yes — no human/animal subjects (not applicable), if so -->

**Sources**
- <resource> — <what you inspected>

**Checks**
- <what you looked for> → <what you found>

**Rationale**
<one or two lines to the verdict>
