import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { parse as parseYaml } from "yaml";
import { convert } from "./index.ts";
import { parseMetric } from "./metric.ts";

const here = (p: string) => fileURLToPath(new URL(p, import.meta.url));

// Reference the single source of truth, the same metric the CLI uses.
const metric = parseMetric(
  await readFile(here("../../../../../metric/airbds_metric_v0.3.yaml"), "utf8"),
);
const reviewCsv = await readFile(here("./fixtures/review-info.csv"), "utf8");
const questionsCsv = await readFile(here("./fixtures/questions.csv"), "utf8");

test("maps reviewer and dataset fields from the review-info tab", () => {
  const { review } = convert(reviewCsv, questionsCsv, metric);
  assert.equal(review.reviewer.name, "Justin Clark-Casey");
  assert.equal(review.reviewer.initials, ""); // never derived — reviewer fills it in
  assert.equal(review.reviewer.review_date, ""); // never guessed — reviewer fills it in
  assert.equal(
    review.dataset.name,
    "Flagship Dataset of Type 2 Diabetes from the AI-READI Project",
  );
  assert.equal(review.dataset.url, "https://fairhub.io/datasets/3");
  assert.equal(review.dataset.hosting_resource, "AI-READI");
  // Read despite the spreadsheet's "Accession numer" typo.
  assert.equal(review.dataset.accession, "https://doi.org/10.60775/fairhub.3");
  assert.match(review.process_comments, /AI-ready/);
});

test("maps all 28 answers with their comments", () => {
  const { review } = convert(reviewCsv, questionsCsv, metric);
  assert.equal(Object.keys(review.answers).length, 28);
  assert.equal(review.answers["ACM-1"].answer, "Yes");
  assert.equal(review.answers["ACM-5"].answer, "No"); // custom (non-standard) licence
  assert.match(review.answers["ACM-5"].comments, /[Cc]ustom licen/);
});

test("ethics questions carry not_applicable and stay blank in this draft", () => {
  const { review, warnings } = convert(reviewCsv, questionsCsv, metric);
  for (const id of ["ACM-24", "ACM-25", "ACM-26", "ACM-27", "ACM-28"]) {
    assert.equal(review.answers[id].not_applicable, false);
    assert.equal(review.answers[id].answer, ""); // unanswered in the example sheet
  }
  assert.ok(warnings.some((w) => /Unanswered/.test(w)));
});

test("result is left null for the processor / CI to compute", () => {
  const { review } = convert(reviewCsv, questionsCsv, metric);
  assert.equal(review.result.weighted_score, null);
  assert.equal(review.result.grade, "");
});

test("emitted YAML quotes Yes/No and round-trips to the same answers", () => {
  const { yaml } = convert(reviewCsv, questionsCsv, metric);
  assert.match(yaml, /answer: "Yes"/);
  const parsed = parseYaml(yaml) as {
    schema_version: unknown;
    answers: Record<string, { answer: unknown }>;
  };
  // schema_version and answers must stay strings, not bool/number coercions.
  assert.equal(parsed.schema_version, "0.3");
  assert.equal(typeof parsed.schema_version, "string");
  assert.equal(parsed.answers["ACM-1"].answer, "Yes");
  assert.equal(typeof parsed.answers["ACM-1"].answer, "string");
});
