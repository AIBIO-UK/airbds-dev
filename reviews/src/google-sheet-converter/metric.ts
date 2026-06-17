import { parse as parseYaml } from "yaml";
import type { Metric } from "./types.ts";

/**
 * Extract the ordered question ids and the Ethics-scope set from the canonical
 * metric YAML (metric/airbds_metric_v0.3.yaml). The metric is the single source
 * of truth for which questions exist and which are Ethics — the converter never
 * hardcodes the ACM ids, so a future metric version flows through automatically.
 */
export function parseMetric(metricYaml: string): Metric {
  const data = parseYaml(metricYaml) as
    | { questions?: Record<string, { scope?: string }> }
    | null;
  const questions = data?.questions ?? {};
  const questionIds = Object.keys(questions)
    .filter((id) => /^ACM-\d+$/.test(id))
    .sort((a, b) => Number(a.slice(4)) - Number(b.slice(4)));
  if (questionIds.length === 0) {
    throw new Error(
      "No ACM-* questions found in the metric YAML — is this metric/airbds_metric_v0.3.yaml?",
    );
  }
  const ethicsIds = new Set(
    questionIds.filter((id) => questions[id]?.scope === "Ethics"),
  );
  return { questionIds, ethicsIds };
}
