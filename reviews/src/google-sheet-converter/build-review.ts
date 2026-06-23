import type { Metric, Review, ReviewAnswer } from "./types.ts";
import type { SheetAnswer } from "./parse-sheet.ts";

/** Return the first non-empty value among the given normalized labels. */
function pick(info: Map<string, string>, ...keys: string[]): string {
  for (const k of keys) {
    const v = info.get(k);
    if (v) return v;
  }
  return "";
}

/**
 * Assemble a Review from the parsed sheet tabs, driven by the canonical metric's
 * question list and schema version. Never fabricates answers: anything not
 * exactly "Yes"/"No" is left blank and reported as a warning, so a mid-review
 * sheet converts to a clearly-incomplete draft rather than a misleading "all No".
 */
export function buildReview(
  info: Map<string, string>,
  sheetAnswers: Map<string, SheetAnswer>,
  metric: Metric,
): { review: Review; warnings: string[] } {
  const warnings: string[] = [];

  const name = pick(info, "reviewer name");
  // The spreadsheet has no initials field; the reviewer adds them afterwards.
  warnings.push(
    "Reviewer initials are blank (not in the sheet) — add them before submitting.",
  );

  // v0.4 sheets carry a review date; v0.3 sheets do not. Read it when present,
  // and only warn when it is actually blank.
  const reviewDate = pick(info, "review date");
  if (!reviewDate) {
    warnings.push(
      "Review date is blank (not in the sheet) — add it before submitting.",
    );
  }

  // The spreadsheet carries no affiliation, but review_processor.py requires it.
  warnings.push(
    "Reviewer affiliation is blank (not in the sheet) — add it before submitting.",
  );

  const answers: Record<string, ReviewAnswer> = {};
  const unanswered: string[] = [];
  const unexpected: string[] = [];
  for (const id of metric.questionIds) {
    const sa = sheetAnswers.get(id);
    let answer = (sa?.answer ?? "").trim();
    if (answer !== "Yes" && answer !== "No") {
      if (answer) unexpected.push(`${id}="${answer}"`);
      else unanswered.push(id);
      answer = "";
    }
    const entry: ReviewAnswer = { answer, comments: sa?.comments ?? "" };
    if (metric.ethicsIds.has(id)) entry.not_applicable = false;
    answers[id] = entry;
  }

  for (const id of sheetAnswers.keys()) {
    if (!metric.questionIds.includes(id)) {
      warnings.push(`Sheet answers ${id}, which is not in the metric — ignored.`);
    }
  }
  if (unanswered.length) {
    warnings.push(
      `Unanswered question(s) left blank: ${unanswered.join(", ")}. ` +
        'The file is a draft until every question is "Yes" or "No".',
    );
  }
  if (unexpected.length) {
    warnings.push(
      `Answer(s) not "Yes"/"No" (cleared to blank): ${unexpected.join(", ")}.`,
    );
  }

  const review: Review = {
    schema_version: metric.schemaVersion,
    reviewer: {
      name,
      initials: "",
      orcid: "",
      affiliation: "",
      review_date: reviewDate,
    },
    dataset: {
      name: pick(info, "dataset name"),
      url: pick(info, "dataset link", "dataset url"),
      hosting_resource: pick(info, "resource name", "hosting resource"),
      // The template spreadsheet has a known typo: "Accession numer".
      accession: pick(info, "accession number", "accession numer", "accession"),
      comments: pick(info, "dataset comments"),
    },
    process_comments: pick(info, "process comments"),
    answers,
    result: { weighted_score: null, grade: "" },
  };

  return { review, warnings };
}
