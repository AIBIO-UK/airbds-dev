import { parse as parseYaml } from "yaml";
import type { Metric } from "./types.ts";

/** A metric question id: a letter prefix, a dash, and a number (ACM-1, ABC-01). */
const QUESTION_ID = /^[A-Za-z]+-(\d+)$/;

/**
 * Extract the schema version, the ordered question ids, and the not-applicable
 * set (the Ethics questions) from the canonical metric YAML — the versioned
 * metric/airbds_metric_v*.yaml. The metric is the single source of truth: the
 * converter never hardcodes the ids, the schema version, or which questions are
 * Ethics, so a new metric version (v0.3 ACM-1…28 → v0.4 ABC-01…27 → v0.5
 * ABC-01…25) flows through with no converter edits.
 */
export function parseMetric(metricYaml: string): Metric {
  const data = parseYaml(metricYaml) as
    | {
        schema_version?: string | number;
        questions?: Record<string, { not_applicable_default?: unknown }>;
      }
    | null;
  const questions = data?.questions ?? {};
  const questionIds = Object.keys(questions)
    .filter((id) => QUESTION_ID.test(id))
    .sort(
      (a, b) =>
        Number(a.match(QUESTION_ID)![1]) - Number(b.match(QUESTION_ID)![1]),
    );
  if (questionIds.length === 0) {
    throw new Error(
      "No questions found in the metric YAML — is this a metric/airbds_metric_v*.yaml?",
    );
  }
  // A question needs a not_applicable flag in reviews iff the metric gives it a
  // not_applicable_default — the Ethics questions, and the same rule
  // review_processor.py applies on the way back in.
  const ethicsIds = new Set(
    questionIds.filter((id) => questions[id]?.not_applicable_default != null),
  );
  const schemaVersion = String(data?.schema_version ?? "").trim();
  if (!schemaVersion) {
    throw new Error("Metric YAML has no schema_version.");
  }
  return { schemaVersion, questionIds, ethicsIds };
}
