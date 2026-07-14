# Reviews

> ## ⚠️ The manual review process is not live
>
> **Nobody is running the human reviewer workflow described below**, and the CI
> that used to score submitted reviews is switched off. Opening a pull request
> with a review file will *not* validate it, score it, or commit anything back.
> Do not follow the tutorials or the submission steps in this README expecting
> them to work end-to-end — they document a dormant process.
>
> **This directory is not dormant, though.** Parts of it are live code that the
> automated pipeline depends on:
>
> | Path | Status | Why it's live |
> |------|--------|---------------|
> | [`src/google-sheet-converter/`](src/google-sheet-converter/) | **Live** | Published as the npm package `@airbds/converter-tools` and consumed by the [`auto-airbds`](../../auto-airbds) website's server-side import route. It reads `metric/airbds_metric_v0.{3,4}.yaml` by relative path, so its location in the tree is load-bearing. |
> | [`review_template.yaml`](review_template.yaml) | **Live** | Not just a reviewer download — it is the **schema contract the converter emits against**. Changing it changes the converter's output spec. |
> | [`src/scripts/`](src/scripts/), [`testing/`](testing/), [`examples/`](examples/), [`docs/`](docs/), [`GUIDANCE.md`](GUIDANCE.md), [`archived_templates/`](archived_templates/) | Dormant | Manual-process material. Retained for reference and in case the process resumes. |
>
> So: don't delete or relocate this directory on the assumption that it's all
> archived. Treat the manual-process pieces as reference, and the converter and
> template as production dependencies.

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

> **Dormant — this no longer happens.** The `Review Check & Score` workflow that
> performed the steps below is disabled (it no longer runs on push or pull
> request; see `.github/workflows/review-check.yml`). The description is kept as
> a record of how the process worked, and of what would need re-enabling to
> revive it. To score a review today, run the processor by hand:
>
> ```bash
> pip install pyyaml
> python3 reviews/src/scripts/review_processor.py --files <your-review-file>
> ```

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
