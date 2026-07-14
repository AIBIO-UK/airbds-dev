# `google-sheet-converter/`

The reusable AIRBDS review-converter library — turns an assessment spreadsheet
into a review YAML conforming to
[`review_template.yaml`](../../review_template.yaml). It is the
shared, metric-version-agnostic core used by the CLI
(`../scripts/convert_review_google_sheet_to_yaml.mts`, which reads the metric
version from the sheet) and by the
[`auto-airbds`](../../../../../auto-airbds) website's server-side import route, which
depends on it as the published npm package **`@airbds/converter-tools`**.

This is its own npm package — `package.json`, dependencies, and `tsconfig.json`
live here. For how to *run* the converter, see the
[workspace README](../README.md); this file is for working on the library itself.

The public surface is [`index.ts`](./index.ts) (`fetchSheet`, `convert`,
`buildReview`, `parseCsv`, `extractReviewInfo`, `extractAnswers`,
`detectSchemaVersion`, `emitYaml`, `parseMetric`, and the shared types). `fetchSheet`/`convert` use only the global
`fetch`, `csv-parse`, and `yaml`, so they run server-side in a Cloudflare Pages
Function (which needs the `nodejs_compat` flag for `csv-parse`'s `Buffer`/`stream`
usage).

## Develop

Run from this directory (`reviews/src/google-sheet-converter`):

```bash
bun install       # one-time
bun run test      # node:test suite over *.test.ts
bun run typecheck # tsc --noEmit
bun run build     # emit dist/ (JS + .d.ts) via tsconfig.build.json
```

## Publish

The library ships compiled output from `dist/` (built by `tsc` with
`rewriteRelativeImportExtensions`, so the `.ts` import specifiers in source are
rewritten to `.js` in the emitted JS). `dist/` is git-ignored and rebuilt by the
`prepublishOnly` script.

```bash
bun pm pack                  # inspect the tarball (dist/ + package.json + README)
bun publish --access public  # runs prepublishOnly (build + test), then publishes
```

Publishing needs an npm auth token. Bun has no `bun login`; it reads the token
from `~/.npmrc` / `bunfig.toml` / `$NPM_CONFIG_TOKEN`. Get one with `npm login`
(writes `~/.npmrc`, which Bun reads) or create a granular access token on
npmjs.com. The `@airbds` scope must exist on npm (create a free org, or rename to
an owned scope). Bump `version` before publishing.
