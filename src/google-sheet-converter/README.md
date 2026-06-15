# `google-sheet-converter/`

The reusable AIRBDS review-converter library — turns an assessment spreadsheet
into a review YAML conforming to
[`metric/review_template.yaml`](../../metric/review_template.yaml). It is the
shared core used by the CLI
(`../scripts/convert_review_google_sheet_to_yaml_v0.3.mts`) and, later, by
a website's server-side code.

This is its own npm package — `package.json`, dependencies, and `tsconfig.json`
live here. For how to *run* the converter, see the
[workspace README](../README.md); this file is for working on the library itself.

## Develop

Run from this directory (`src/google-sheet-converter`):

```bash
bun install      # one-time
bun test         # node:test suite over *.test.ts
bun run typecheck # tsc --noEmit
```
