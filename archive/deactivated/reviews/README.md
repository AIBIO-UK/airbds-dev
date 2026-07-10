# Reviews

This directory holds the blank review template, the completed reviews (under
[`testing/`](testing/) for now — nothing is in production yet), reference
[`examples/`](examples/), and the tooling that produces and scores them
([`src/`](src/)).

Completed review files are YAML and CSV. Each follows the schema defined in
[`review_template.yaml`](review_template.yaml) (YAML) or
[`review_template.csv`](review_template.csv) (CSV). These always track the
**current** metric version (v0.4). Previous versions are retained under
[`archived_templates/`](archived_templates/) — use one only if you specifically
need to review against an older metric.

**Naming convention:** `<dataset_accession>_<reviewer_initials>_<n>.<yaml|csv>`

Example: `E-MTAB-1234_CH_1.yaml`

- `<dataset_accession>` — the repository accession or a short descriptive token
- `<reviewer_initials>` — your initials in **uppercase letters only** (2–6 A-Z characters, no digits)
- `<n>` — review number (start at 1; increment if you review the same dataset again)

---

## What happens after you submit

When you open a pull request containing a review file, an automated workflow runs and:

1. **Validates your filename** — if it doesn't match the convention, you'll see an error with a suggested fix
2. **Validates all required fields** — empty required fields, wrong date formats, and invalid answer values are each reported individually
3. **Calculates your weighted score and grade** — no manual calculation needed; leave the `result:` block as `null` / `""`
4. **Generates the companion format** — submit YAML and get a CSV; submit CSV and get a YAML
5. **Renames your file** to include the score and grade:
   ```
   E-MTAB-1234_CH_1.yaml  →  E-MTAB-1234_CH_1_595_Silver.yaml
   ```
6. **Commits the renamed and converted files back** to your branch automatically

If the check fails, open the **Actions** tab of your pull request to see a full error report. Fix each reported issue and push again.

---

## Reference examples

The [`examples/`](examples/) subdirectory contains reference files demonstrating
compliant and non-compliant formats. These files are excluded from the automated
scoring workflow and are for reference only.
