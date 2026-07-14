import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { parse as parseYaml } from "yaml";
import { convert, detectSchemaVersion } from "./index.ts";
import { parseMetric } from "./metric.ts";

const here = (p: string) => fileURLToPath(new URL(p, import.meta.url));

// Reference the single source of truth, the same v0.4 metric the CLI uses.
const metric = parseMetric(
  await readFile(here("../../../metric/airbds_metric_v0.4.yaml"), "utf8"),
);
const reviewCsv = await readFile(here("./fixtures/review-info-v0.4.csv"), "utf8");
const questionsCsv = await readFile(here("./fixtures/questions-v0.4.csv"), "utf8");

test("v0.4: maps reviewer and dataset fields from the review-info tab", () => {
  const { review } = convert(reviewCsv, questionsCsv, metric);
  assert.equal(review.schema_version, "0.4");
  assert.equal(review.reviewer.name, "Justin Clark-Casey");
  assert.equal(review.reviewer.initials, ""); // never derived — reviewer fills it in
  assert.equal(
    review.dataset.name,
    "Flagship Dataset of Type 2 Diabetes from the AI-READI Project",
  );
  assert.equal(review.dataset.url, "https://fairhub.io/datasets/3");
  assert.equal(review.dataset.hosting_resource, "AI-READI");
  // v0.4 fixed the v0.3 "Accession numer" typo to "Accession number".
  assert.equal(review.dataset.accession, "https://doi.org/10.60775/fairhub.3");
  assert.match(review.process_comments, /AI-ready/);
});

test("v0.4: maps all 27 answers with their comments", () => {
  const { review } = convert(reviewCsv, questionsCsv, metric);
  assert.equal(Object.keys(review.answers).length, 27);
  assert.equal(review.answers["ABC-01"].answer, "Yes");
  assert.equal(review.answers["ABC-05"].answer, "No"); // custom (non-standard) licence
  assert.match(review.answers["ABC-05"].comments, /[Cc]ustom licen/);
});

test("v0.4: the four ethics questions carry not_applicable; others do not", () => {
  const { review } = convert(reviewCsv, questionsCsv, metric);
  for (const id of ["ABC-24", "ABC-25", "ABC-26", "ABC-27"]) {
    assert.equal(review.answers[id].not_applicable, false);
  }
  assert.equal("not_applicable" in review.answers["ABC-01"], false);
});

test("v0.4: a fully-answered sheet produces no 'unanswered' warning", () => {
  const { warnings } = convert(reviewCsv, questionsCsv, metric);
  assert.ok(!warnings.some((w) => /Unanswered/.test(w)));
});

test("v0.4: result is left null for the processor / CI to compute", () => {
  const { review } = convert(reviewCsv, questionsCsv, metric);
  assert.equal(review.result.weighted_score, null);
  assert.equal(review.result.grade, "");
});

test("v0.4: emitted YAML quotes Yes/No and keeps schema_version a string", () => {
  const { yaml } = convert(reviewCsv, questionsCsv, metric);
  assert.match(yaml, /answer: "Yes"/);
  assert.match(yaml, /v0\.4/); // header tracks the metric version
  const parsed = parseYaml(yaml) as {
    schema_version: unknown;
    answers: Record<string, { answer: unknown }>;
  };
  // schema_version and answers must stay strings, not bool/number coercions.
  assert.equal(parsed.schema_version, "0.4");
  assert.equal(typeof parsed.schema_version, "string");
  assert.equal(parsed.answers["ABC-01"].answer, "Yes");
  assert.equal(typeof parsed.answers["ABC-01"].answer, "string");
});

test("v0.4: review_date is read from the sheet when present", () => {
  // The example fixture leaves the date blank; this confirms the new v0.4
  // "Review date:" row flows through to the review when the reviewer fills it in.
  const datedInfo = [
    "Review informaton,,",
    ",Reviewer name:,Test Reviewer",
    ",Review date:,2026-03-01",
    ",Dataset name:,Example dataset",
  ].join("\n");
  const { review, warnings } = convert(datedInfo, questionsCsv, metric);
  assert.equal(review.reviewer.review_date, "2026-03-01");
  assert.ok(!warnings.some((w) => /Review date is blank/.test(w)));
});

test("detectSchemaVersion reads the version from the Instructions tab", async () => {
  // The sheet is trusted for the version; it is read from the "Metric vX.Y"
  // label, not inferred from the ACM-/ABC- question-id prefix.
  const v03Info = await readFile(here("./fixtures/review-info.csv"), "utf8");
  assert.equal(detectSchemaVersion(v03Info), "0.3");
  assert.equal(detectSchemaVersion(reviewCsv), "0.4"); // the v0.4 fixture
  assert.equal(detectSchemaVersion("Reviewer name:,Someone\nDataset name:,X"), null);
});
