// Shared types for the AIRBDS review converter.
// The converter turns an AIRBDS assessment spreadsheet into a review document
// conforming to metric/review_template.yaml.

/** A single answered question in a review. */
export interface ReviewAnswer {
  /** "Yes" | "No" | "" — empty means unanswered (a draft, not yet submittable). */
  answer: string;
  comments: string;
  /** Present only for Ethics-scope questions (ACM-24…28). */
  not_applicable?: boolean;
}

export interface Reviewer {
  name: string;
  initials: string;
  orcid: string;
  affiliation: string;
  review_date: string;
}

export interface Dataset {
  name: string;
  url: string;
  hosting_resource: string;
  accession: string;
  comments: string;
}

export interface Review {
  schema_version: string;
  reviewer: Reviewer;
  dataset: Dataset;
  process_comments: string;
  answers: Record<string, ReviewAnswer>;
  /** Left blank by the converter — review_processor.py / CI compute it. */
  result: { weighted_score: number | null; grade: string };
}

/**
 * The slice of the canonical metric the converter needs: the ordered question
 * ids and which of them are Ethics-scope. Parsed from the single source of
 * truth, metric/airbds_metric_v0.3.yaml — never hardcoded or copied here.
 */
export interface Metric {
  questionIds: string[];
  ethicsIds: Set<string>;
}

export interface ConvertResult {
  yaml: string;
  review: Review;
  warnings: string[];
}

/** The two CSV tabs a converter run needs. */
export interface SheetCsvs {
  reviewCsv: string;
  questionsCsv: string;
}

export const SCHEMA_VERSION = "0.3";
