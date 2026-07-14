# Tooling design

Why the review tooling under `reviews/src/` is built the way it is. Scope: the
Google-Sheet → review-YAML converter and how it relates to the existing Python
scripts.

## TypeScript, not Python (for the converter)

The converter will eventually run **server-side in a website** (Node) to parse
incoming spreadsheet links, as well as on the command line. The website runtime
is Node, so the real choice was *in-process TypeScript* vs. *calling Python
across a language boundary from Node*.

Writing it in Python would mean a permanent boundary on every request — either
spawning a Python subprocess (needs a Python runtime beside Node; awkward-to-
impossible on serverless/edge hosts) or running a separate Python microservice
(a second deployable + network hop). That is an ongoing operational tax to avoid
a one-time `npm install`. A server-side React app already runs npm, so adding two
libraries is idiomatic and free.

TypeScript also lets the CLI and the website share **one implementation, one set
of types, and one test suite**. So: TypeScript, with mature libraries —
`csv-parse` and `yaml` — rather than hand-rolled parsing.

`review_processor.py` and `build_metric_yaml_from_spreadsheet_v0.3.py`
**stay Python**: they are CI/local tools, not part of the website request path,
and rewriting them carries no benefit.

## Pure core + thin adapters

```
google-sheet-converter/convert.ts   convert(reviewCsv, questionsCsv, metric, opts) → { yaml, review, warnings }
                                    PURE: strings in, value out. No IO, no network.
google-sheet-converter/fetch-sheet.ts   fetchSheet(url) → { reviewCsv, questionsCsv }   (network, shared)
scripts/…_to_yaml.mts   CLI adapter: arg parsing + fs read/write; detects the sheet's version
(website, later)       HTTP adapter: request in, YAML/JSON out
```

All IO lives at the edges. The pure core is trivially unit-testable and runs
unchanged in Node, the browser, or an edge runtime. The CLI and the website are
each a thin shell over `convert()`.

## Single source of truth: the metric is referenced, never copied

The converter needs to know which questions exist (v0.3's ACM-1…28, v0.4's
ABC-01…27, …), the schema version, and which questions are Ethics-scope (they
carry `not_applicable`). All of that is **read from the canonical, versioned
`metric/airbds_metric_v*.yaml` in the repo root** — it is never hardcoded in the
converter and never copied into a bundled asset.

Mechanically, the metric is **injected**: `convert()` takes a parsed `Metric`
argument, the CLI reads the appropriate `metric/airbds_metric_v*.yaml` and passes
it in, and the website supplies the same metric it already has. The converter is
metric-version-agnostic — the question ids, schema version, and Ethics set all
come from the injected metric, so a new metric version flows through with no
converter code edits.

Which metric to inject is itself read from the sheet: the CLI calls
`detectSchemaVersion()` on the review-info (Instructions) tab — the
"AIRBDS … Metric vX.Y" label — and loads the matching `metric/airbds_metric_v*.yaml`.
The sheet is trusted for the *version* but never for the *score*; the version is
not inferred from the question-id prefix. Likewise, `review_template.yaml`
is not read or copied — the small wrapper shape (reviewer/dataset/result) is part
of the converter's output format, not metric data.

## No scoring in the converter

The converter fills `answers` and leaves `result` blank (`weighted_score: null`,
`grade: ""`). `review_processor.py` / CI are the **authoritative** scorer and
also rename the file to the scored convention. Duplicating scoring in the
converter would risk divergence from the canonical implementation, so it is
deliberately omitted.

## Correctness: YAML 1.1 boolean coercion

`answer` values are the strings `"Yes"` / `"No"` (or empty). Under YAML 1.1 an
unquoted `Yes`/`No`/`y`/`n`/`off`… is read as a **boolean**, which
`review_processor.py` rejects. `emit-yaml.ts` therefore force-quotes every string
scalar (`defaultStringType: "QUOTE_DOUBLE"`), so the output round-trips as
strings. The `schema_version` value (e.g. `"0.4"`) is quoted for the same reason
(otherwise read as a float).

## Sheet ingestion

`fetchSheet` discovers the tab gids from the spreadsheet's `htmlview` page, then
fetches each tab via the public `export?format=csv&gid=…` endpoint and
**classifies tabs by content** (questions = header cell `Q ID`; review-info =
contains `Reviewer name`). Classifying by content, not by hard-coded gid, means a
*copy* of the template — which gets fresh gids — still works. Private sheets are
handled by exporting the two tabs to CSV manually and passing `--review-csv` /
`--questions-csv`.

## Honest about gaps

The converter never fabricates data. Answers that are not exactly `Yes`/`No`
(e.g. the mid-review ethics rows in the example sheet) are left blank and
reported as warnings; the spreadsheet carries no reviewer initials/ORCID/
affiliation/date, so those are left blank with warnings rather than guessed
(initials in particular are never derived — Drive titles and names are
unreliable). The result is a clearly-incomplete *draft* the reviewer finishes,
not a misleading complete-looking file.

## Runtime

The converter is plain TypeScript with no build step, so any runtime that runs
`.ts` directly works. For a from-zero machine, **Bun** is the simplest (one
self-contained binary = runtime + package manager + TS execution, identical on
Ubuntu and macOS); **Node ≥ 23.6** also runs it via native type stripping
(22.6–23.5 needs `--experimental-strip-types`). The code is runtime-agnostic — it
uses only `node:`-prefixed builtins, global `fetch`, and the two npm deps, all
provided by both. `package-lock.json` is the single committed lockfile; Bun
migrates from it on `bun install`.

No transpile step is required to run or test. `tsconfig.json` is for type-checking
and editors. Because Node only *strips* types (no transform), type-only imports
use `import type` (enforced by `verbatimModuleSyntax`) and intra-package imports
carry explicit `.ts` extensions.
