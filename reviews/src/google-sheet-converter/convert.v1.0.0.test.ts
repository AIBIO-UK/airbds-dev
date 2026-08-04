import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { parse as parseYaml } from "yaml";
import { convert, detectSchemaVersion } from "./index.ts";
import { parseMetric } from "./metric.ts";

const here = (p: string) => fileURLToPath(new URL(p, import.meta.url));

// Reference the single source of truth, the same v1.0.0 metric the CLI uses.
// No converter code is v1.0.0-specific; this suite guards that the version flows
// through end-to-end (25 questions, Ethics ABC-23…25) with no code change.
const metric = parseMetric(
  await readFile(here("../../../metric/airbds_metric_v1.0.0.yaml"), "utf8"),
);
const reviewCsv = await readFile(here("./fixtures/review-info-v1.0.0.csv"), "utf8");
const questionsCsv = await readFile(here("./fixtures/questions-v1.0.0.csv"), "utf8");

test("v1.0.0: maps reviewer and dataset fields from the review-info tab", () => {
  const { review } = convert(reviewCsv, questionsCsv, metric);
  assert.equal(review.schema_version, "1.0.0");
  assert.equal(review.reviewer.name, "Ada Lovelace");
  assert.equal(review.reviewer.initials, ""); // never derived — reviewer fills it in
  assert.equal(review.reviewer.review_date, "2026-07-23");
  assert.equal(review.dataset.name, "Example v1.0.0 Bioscience Dataset");
  assert.equal(review.dataset.url, "https://example.org/datasets/5");
  assert.equal(review.dataset.hosting_resource, "Zenodo");
  assert.equal(review.dataset.accession, "https://doi.org/10.5281/zenodo.99999");
  assert.match(review.process_comments, /v0\.5 converter/);
});

test("v1.0.0: maps all 25 answers with their comments", () => {
  const { review } = convert(reviewCsv, questionsCsv, metric);
  assert.equal(Object.keys(review.answers).length, 25);
  assert.equal(review.answers["ABC-01"].answer, "Yes");
  assert.equal(review.answers["ABC-05"].answer, "No"); // non-standard licence
  assert.match(review.answers["ABC-05"].comments, /[Cc]ustom licence/);
});

test("v1.0.0: the three ethics questions carry not_applicable; others do not", () => {
  const { review } = convert(reviewCsv, questionsCsv, metric);
  for (const id of ["ABC-23", "ABC-24", "ABC-25"]) {
    assert.equal(review.answers[id].not_applicable, false);
  }
  assert.equal("not_applicable" in review.answers["ABC-01"], false);
  // v0.4's fourth ethics id must not leak into a v1.0.0 review.
  assert.equal("ABC-27" in review.answers, false);
});

test("v1.0.0: a fully-answered sheet produces no 'unanswered' warning", () => {
  const { warnings } = convert(reviewCsv, questionsCsv, metric);
  assert.ok(!warnings.some((w) => /Unanswered/.test(w)));
});

test("v1.0.0: result is left null for the processor / CI to compute", () => {
  const { review } = convert(reviewCsv, questionsCsv, metric);
  assert.equal(review.result.weighted_score, null);
  assert.equal(review.result.grade, "");
});

test("v1.0.0: emitted YAML quotes Yes/No and keeps schema_version a string", () => {
  const { yaml } = convert(reviewCsv, questionsCsv, metric);
  assert.match(yaml, /answer: "Yes"/);
  assert.match(yaml, /v0\.5/); // header tracks the metric version
  const parsed = parseYaml(yaml) as {
    schema_version: unknown;
    answers: Record<string, { answer: unknown }>;
  };
  assert.equal(parsed.schema_version, "1.0.0");
  assert.equal(typeof parsed.schema_version, "string");
  assert.equal(parsed.answers["ABC-05"].answer, "No");
  assert.equal(typeof parsed.answers["ABC-05"].answer, "string");
});

test("v1.0.0: detectSchemaVersion reads 1.0.0 from the Instructions tab", () => {
  assert.equal(detectSchemaVersion(reviewCsv), "1.0.0");
});
