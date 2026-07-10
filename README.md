# AIRBDS AI-Readiness Dataset Scoring Metric

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Version](https://img.shields.io/badge/metric%20version-v0.4-blue)](metric/CHANGELOG.md)
[![AIBIO-UK](https://img.shields.io/badge/AIBIO--UK-AIRBDS%20Working%20Group-green)](https://aibio.ac.uk/about/working-groups/airbds/)
[![Metric Upstream Drift Check](https://github.com/AIBIO-UK/airbds-metric/actions/workflows/metric-upstream-drift-check.yml/badge.svg)](https://github.com/AIBIO-UK/airbds-metric/actions/workflows/metric-upstream-drift-check.yml)

A versioned, machine-readable scoring metric for evaluating the **AI-readiness
of bioscience datasets**. Developed by the
[AI-Ready Bioscience Datasets (AIRBDS) Working Group](https://aibio.ac.uk/about/working-groups/airbds/)
of the [AIBIO-UK](https://aibio.ac.uk) network, funded by BBSRC.

---

## Overview

The AIRBDS metric provides a structured checklist that researchers, data
curators, and repository managers can use to assess how suitable a bioscience
dataset is for use in AI/ML workflows. Each of the **27 questions** is answered
Yes/No and contributes a weighted score. Datasets are then assigned one of four
grades:

| Grade | Description |
|---|---|
| 🔴 **Caution** | May have serious issues — fails one or more Critical criteria |
| 🟤 **Bronze** | Passes most Critical questions (≥ 7/8) |
| ⚪ **Silver** | Passes all Critical + ≥ 50% of Important questions |
| 🟡 **Gold** | Passes all Critical and Important + ≥ 50% of Optional questions |

Questions are grouped into **four scopes** and **three weight tiers**:

| Scope | Questions | Weight tiers covered |
|---|---|---|
| Infrastructure | ABC-01 – ABC-10 | Critical, Important, Optional |
| Metadata | ABC-11 – ABC-17 | Critical, Important, Optional |
| Content | ABC-18 – ABC-23 | Critical, Important, Optional |
| Ethics | ABC-24 – ABC-27 | Critical, Important, Optional |

**Weight points:** Critical = 80 pts · Important = 5 pts · Optional = 2 pts

> **Ethics note:** Questions ABC-24 to ABC-27 apply to datasets containing
> human or animal subject data. For datasets with no such data, these questions
> default to "Yes" (not applicable) and should be noted in the review file.

---

## Use the Metric

Two ways to use the current metric (v0.4) directly — pick whichever suits you:

| | Link | Best for |
|---|---|---|
| 📊 **Google Sheet** (live source of truth) | [Open the sheet](https://docs.google.com/spreadsheets/d/1eriM8bXAoNXsIR9l8OpI1XYEp8FbtBWt05CTIP9cVeg/edit) | Browsing, filtering, or copying into your own spreadsheet — no coding required |
| 📄 **YAML file** (generated from the sheet) | [`metric/airbds_metric_v0.4.yaml`](metric/airbds_metric_v0.4.yaml) | Scripting, tooling, or anything that reads the metric programmatically |

The YAML is machine-generated from the Google Sheet and kept in sync automatically — see [`metric/README.md`](metric/README.md) for how.

---

## Repository Structure

```
airbds-metric/
├── metric/    # The versioned scoring metric (YAML), synced live from the Google Sheet, and CHANGELOG
└── reviews/   # Deposit dataset reviews here — see reviews/README.md for the format
```

`metric/` carries its own `README.md` with full details. (Kept one level deep on purpose, so it doesn't drift out of date.)

---

## Tutorial

**[→ Interactive tutorial site](https://aibio-uk.github.io/airbds-metric-tutorial/)** — step-by-step guide to scoring a dataset against the metric.

Guidance comes from one of two places: the **Google Sheet** or the **YAML metric** (see [Use the Metric](#use-the-metric) above). For the rationale behind scoring and grades, see [`reviews/GUIDANCE.md`](reviews/GUIDANCE.md). There is no automated scorer right now — scores are calculated manually; automated YAML-based scoring is planned infrastructure, not yet built.

---

## Metric Questions at a Glance

### Infrastructure (ABC-01 – ABC-10)

| ID | Weight | Question (short) |
|---|---|---|
| ABC-01 | Important | Can the dataset be accessed in its entirety? |
| ABC-02 | Important | Is the metadata provided along with the data? |
| ABC-03 | Optional | Does the dataset include a mechanism for verifying its integrity? |
| ABC-04 | **Critical** | Is the dataset released with a clear licence or terms of use? |
| ABC-05 | Important | Is the licence standardised and machine-readable? |
| ABC-06 | Important | Is the dataset deposited in a FAIR-compliant archive? |
| ABC-07 | Important | Is the dataset deposited in a domain-appropriate infrastructure? |
| ABC-08 | Optional | Is the dataset hosted in a searchable infrastructure? |
| ABC-09 | **Critical** | Does the dataset have a globally unique, persistent identifier? |
| ABC-10 | Optional | If subject to updates, does it use a version control system? |

### Metadata (ABC-11 – ABC-17)

| ID | Weight | Question (short) |
|---|---|---|
| ABC-11 | **Critical** | Does the dataset use a machine-readable, domain-appropriate metadata standard? |
| ABC-12 | **Critical** | Does the metadata include the identifier of the dataset? |
| ABC-13 | Optional | Does the metadata specify intended access controls? |
| ABC-14 | Optional | Does the metadata document the modalities used? |
| ABC-15 | Important | Are transformation and preprocessing steps documented to be reproducible? |
| ABC-16 | **Critical** | Is the provenance of the dataset clearly documented? |
| ABC-17 | Important | Is consideration of bias documented in the metadata? |

### Content (ABC-18 – ABC-23)

| ID | Weight | Question (short) |
|---|---|---|
| ABC-18 | Important | Is the dataset free of duplicate records? |
| ABC-19 | Important | Does the dataset include all expected records and content? |
| ABC-20 | **Critical** | Are units, data types and parameter names consistent between entries? |
| ABC-21 | Important | Does the dataset follow domain standards for units, data types, parameter names? |
| ABC-22 | Optional | Does the data use an appropriate file format? |
| ABC-23 | Optional | Is the data available in at least one open, non-proprietary format? |

### Ethics (ABC-24 – ABC-27) †

| ID | Weight | Question (short) |
|---|---|---|
| ABC-24 | **Critical** | Does the dataset include an ethical assessment covering acquisition? |
| ABC-25 | **Critical** | Does the dataset preserve the privacy of human subjects? |
| ABC-26 | Important | Does the dataset include an ethical assessment covering data management? |
| ABC-27 | Optional | Does the metadata document data protection declarations? |

† *Default answer "Yes" if dataset contains no human or animal subject data.*

Full questions with complete guidance text are in
[`metric/airbds_metric_v0.4.yaml`](metric/airbds_metric_v0.4.yaml).

---

## AI Agent Skill (Beta)

Automated AIRBDS assessment via an AI agent skill is in beta at
**[AIBIO-UK/airbds-skill](https://github.com/AIBIO-UK/airbds-skill)**.

---

## Versioning

This repository uses [Semantic Versioning](https://semver.org/):

- **PATCH** — guidance clarifications only (e.g. v0.4.1)
- **MINOR** — question additions, deletions, or rewordings (e.g. v0.4.0)
- **MAJOR** — changes to weights or grade thresholds (e.g. v1.0.0)

Each metric version is a separate YAML file (`metric/airbds_metric_vX.Y.yaml`).
Completed reviews reference the metric version they were scored with via the
`schema_version` field. See [CHANGELOG.md](metric/CHANGELOG.md) for full history.

> **v0.4 is the current version.** See the `[0.4]` entry in
> [CHANGELOG.md](metric/CHANGELOG.md).

---

## Contributing

We welcome contributions including dataset reviews, metric improvements, and
documentation fixes. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before
opening a PR. All contributors must abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Citation

If you use this metric, please cite it as:

> AIRBDS Working Group, AIBIO-UK. (2026). *AIRBDS AI-Readiness Dataset
> Scoring Metric* (v0.4). GitHub.
> <https://github.com/AIBIO-UK/airbds-metric>

Full citation metadata (including all working group members) is available in
[`CITATION.cff`](CITATION.cff) and is automatically recognised by GitHub's
"Cite this repository" feature.

### Working Group Members

The AIRBDS metric was developed by the following members of the AIRBDS Working
Group, AIBIO-UK:

| Name | Affiliation | Role |
|---|---|---|
| Charlie Harrison | Aberystwyth University | Working Group Lead |
| Justin Clark-Casey | Honest but Curious Consulting | Member |
| Gavin Farrell | University of Padova; EMBL-EBI | Member |
| Alexandra Gibbs | University of Nottingham | Member |
| Annalisa Occhipinti | Teesside University | Member |
| Ian Overton | Queen's University Belfast | Member |
| Rachel Rusholme Pilcher | Earlham Institute | Member |
| Matt Spick | University of Surrey | Member |
| Tulsi Suchak | University of Surrey | Member |
| Melanie Vollmar | EMBL-EBI | Member |
| Reyer Zwiggelaar | Aberystwyth University | Member |

AIBIO-UK is funded by the Biotechnology and Biological Sciences Research
Council (BBSRC).

---

## License

This work is licensed under a
[Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE.md)
licence.
