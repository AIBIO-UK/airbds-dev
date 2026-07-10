import type { ConvertResult, Metric } from "./types.ts";
import { extractAnswers, extractReviewInfo, parseCsv } from "./parse-sheet.ts";
import { buildReview } from "./build-review.ts";
import { emitYaml } from "./emit-yaml.ts";

/**
 * Pure core: the two CSV tabs plus the parsed metric → review YAML. No IO, no
 * network — the CLI and the website both call this with already-fetched CSV
 * text and a Metric parsed from the canonical, versioned metric/airbds_metric_v*.yaml.
 */
export function convert(
  reviewCsv: string,
  questionsCsv: string,
  metric: Metric,
): ConvertResult {
  const info = extractReviewInfo(parseCsv(reviewCsv));
  const sheetAnswers = extractAnswers(parseCsv(questionsCsv));
  const { review, warnings } = buildReview(info, sheetAnswers, metric);
  return { yaml: emitYaml(review), review, warnings };
}
