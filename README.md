# AIRBDS AI-Readiness Dataset Scoring Metric

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Version](https://img.shields.io/badge/metric%20version-v0.3-blue)](CHANGELOG.md)
[![AIBIO-UK](https://img.shields.io/badge/AIBIO--UK-AIRBDS%20Working%20Group-green)](https://aibio.ac.uk/about/working-groups/airbds/)

A versioned, machine-readable scoring metric for evaluating the **AI-readiness
of bioscience datasets**. Developed by the
[AI-Ready Bioscience Datasets (AIRBDS) Working Group](https://aibio.ac.uk/about/working-groups/airbds/)
of the [AIBIO-UK](https://aibio.ac.uk) network, funded by BBSRC.

---

## Overview

The AIRBDS metric provides a structured checklist that researchers, data
curators, and repository managers can use to assess how suitable a bioscience
dataset is for use in AI/ML workflows. Each of the **28 questions** is answered
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
| Infrastructure | ACM-1 – ACM-10 | Critical, Important, Optional |
| Metadata | ACM-11 – ACM-17 | Critical, Important, Optional |
| Content | ACM-18 – ACM-23 | Critical, Important, Optional |
| Ethics | ACM-24 – ACM-28 | Critical, Important, Optional |

**Weight points:** Critical = 80 pts · Important = 5 pts · Optional = 2 pts

> **Ethics note:** Questions ACM-24 to ACM-28 apply to datasets containing
> human or animal subject data. For datasets with no such data, these questions
> default to "Yes" (not applicable) and should be noted in the review file.

---

## Repository Structure

```
airbds-metric/
├── metric/
│   ├── airbds_metric_v0.3.yaml   # Canonical metric — all 28 questions (YAML)
│   ├── airbds_metric_v0.3.csv    # Canonical metric — all 28 questions (CSV)
│   ├── scoring_schema.yaml       # Grade thresholds, weight definitions (YAML)
│   ├── scoring_schema.csv        # Grade thresholds, weight definitions (CSV)
│   ├── review_template.yaml      # Blank review template (YAML)
│   └── review_template.csv       # Blank review template (CSV / spreadsheet)
├── reviews/                      # Completed dataset review files
├── docs/
│   ├── tutorial-csv.md           # Beginner tutorial — Excel / Google Sheets
│   └── tutorial-yaml.md          # Intermediate tutorial — text editor / CLI
├── AIRBDS Core Metric scoring v0.3 - _initials_-_#_ TEMPLATE.xlsx
│                                 # Original working-group spreadsheet (archived)
├── CHANGELOG.md
├── CITATION.cff
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE.md
└── README.md
```

---

## Formats & Tutorials

The metric is available in two formats. Both cover the same 28 questions and produce the same grade — choose whichever suits your workflow.

| Format | Best for | Template | Tutorial |
|---|---|---|---|
| **CSV** | Beginners · Excel or Google Sheets · no coding required | [review_template.csv](metric/review_template.csv) | [Beginner CSV Tutorial](docs/tutorial-csv.md) |
| **YAML** | Intermediate · text editor / command line | [review_template.yaml](metric/review_template.yaml) | [Intermediate YAML Tutorial](docs/tutorial-yaml.md) |

---

## Quick Start (YAML)

For the spreadsheet workflow, see the [Beginner CSV Tutorial](docs/tutorial-csv.md).

1. **Copy the template:**
   ```bash
   cp metric/review_template.yaml reviews/<accession>_<initials>_1.yaml
   ```
2. **Answer all 28 questions** (`"Yes"` or `"No"`) in your copy.
3. **Calculate score:** multiply each answer (1/0) by its weight points
   (Critical=80, Important=5, Optional=2) and sum.
4. **Assign grade** using the thresholds in `metric/scoring_schema.yaml`.
5. **Submit a PR** — see [CONTRIBUTING.md](CONTRIBUTING.md).

Full reviewer instructions are in [`metric/scoring_schema.yaml`](metric/scoring_schema.yaml).

---

## Metric Questions at a Glance

### Infrastructure (ACM-1 – ACM-10)

| ID | Theme | Weight | Question (short) |
|---|---|---|---|
| ACM-1 | Access | Important | Can the dataset be accessed in its entirety? |
| ACM-2 | Access | Important | Is there a standardised communications protocol for accessing the dataset? |
| ACM-3 | Access | Optional | Does the access protocol allow for authentication/authorisation where necessary? |
| ACM-4 | License | **Critical** | Is the dataset provided with a clear data-use license? |
| ACM-5 | License | **Critical** | Does the license permit use in AI/ML model training? |
| ACM-6 | Download | Important | Is there a mechanism to download the entire dataset at once? |
| ACM-7 | Resource | Optional | Is the hosting resource specifically designed for scientific data? |
| ACM-8 | Resource | Optional | Is the dataset hosted in a searchable infrastructure? |
| ACM-9 | UID | **Critical** | Does the dataset have a globally unique, persistent identifier? |
| ACM-10 | Updates | Optional | If subject to updates, does it use a version control system? |

### Metadata (ACM-11 – ACM-17)

| ID | Theme | Weight | Question (short) |
|---|---|---|---|
| ACM-11 | Bias | Important | Is consideration of bias documented in the metadata? |
| ACM-12 | Metadata | **Critical** | Does the dataset use a machine-readable, domain-appropriate metadata standard? |
| ACM-13 | Metadata | **Critical** | Does the metadata include the identifier of the dataset? |
| ACM-14 | Metadata | Optional | Does the metadata specify intended access controls? |
| ACM-15 | Metadata | Optional | Does the metadata document the modalities used? |
| ACM-16 | Preprocessing | Important | Are transformation and preprocessing steps documented to be reproducible? |
| ACM-17 | Provenance | **Critical** | Is the provenance of the dataset clearly documented? |

### Content (ACM-18 – ACM-23)

| ID | Theme | Weight | Question (short) |
|---|---|---|---|
| ACM-18 | Quality | Important | Is the dataset free of duplicate records? |
| ACM-19 | Quality | Important | Does the dataset include all expected records and content? |
| ACM-20 | Format | **Critical** | Are units, data types and parameter names consistent between entries? |
| ACM-21 | Standards | Important | Does the dataset follow domain standards for units, data types, parameter names? |
| ACM-22 | Format | Optional | Does the data use an appropriate file format? |
| ACM-23 | Format | Optional | Is the data available in at least one open, non-proprietary format? |

### Ethics (ACM-24 – ACM-28) †

| ID | Theme | Weight | Question (short) |
|---|---|---|---|
| ACM-24 | Ethics | **Critical** | Does the dataset include an ethical assessment covering acquisition? |
| ACM-25 | Privacy | **Critical** | Does the dataset preserve the privacy of human subjects? |
| ACM-26 | Ethics | Important | Does the dataset include an ethical assessment covering data management? |
| ACM-27 | Security | Important | Does the dataset have necessary authentication and access controls? |
| ACM-28 | Metadata | Optional | Does the metadata document data protection declarations? |

† *Default answer "Yes" if dataset contains no human or animal subject data.*

Full questions with complete guidance text are in
[`metric/airbds_metric_v0.3.yaml`](metric/airbds_metric_v0.3.yaml) (YAML) and
[`metric/airbds_metric_v0.3.csv`](metric/airbds_metric_v0.3.csv) (CSV).

---

## Versioning

This repository uses [Semantic Versioning](https://semver.org/):

- **PATCH** — guidance clarifications only (e.g. v0.3.1)
- **MINOR** — question additions, deletions, or rewordings (e.g. v0.4.0)
- **MAJOR** — changes to weights or grade thresholds (e.g. v1.0.0)

Each metric version is a separate YAML file (`metric/airbds_metric_vX.Y.yaml`).
Completed reviews reference the metric version they were scored with via the
`schema_version` field. See [CHANGELOG.md](CHANGELOG.md) for full history.

---

## Contributing

We welcome contributions including dataset reviews, metric improvements, and
documentation fixes. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before
opening a PR. All contributors must abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Citation

If you use this metric, please cite it as:

> AIRBDS Working Group, AIBIO-UK. (2025). *AIRBDS AI-Readiness Dataset
> Scoring Metric* (v0.3). GitHub.
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
| Justin Clark-Casey | BioFAIR | Member |
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
