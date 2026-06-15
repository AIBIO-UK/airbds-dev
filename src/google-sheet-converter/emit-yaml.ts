import { stringify } from "yaml";
import type { Review } from "./types.ts";

const HEADER = `# Review — AIRBDS AI-Readiness Dataset Scoring Metric v0.3
# Generated from a Google Sheet assessment by
# src/scripts/convert_review_google_sheet_to_yaml_v0.3.mts
# Answers are taken from the sheet; \`result\` is left blank for the review
# processor (src/scripts/review_processor.py) / CI to score, which also renames
# the file to the scored convention.
`;

/**
 * Emit a review as YAML. Every string scalar is double-quoted so a YAML 1.1
 * reader can never coerce "Yes"/"No"/"" into booleans — the exact trap
 * review_processor.py guards against on the way back in. Keys stay plain and
 * `result.weighted_score: null` is emitted unquoted.
 */
export function emitYaml(review: Review): string {
  const body = stringify(review, {
    defaultStringType: "QUOTE_DOUBLE",
    defaultKeyType: "PLAIN",
    lineWidth: 0,
  });
  return `${HEADER}\n${body}`;
}
