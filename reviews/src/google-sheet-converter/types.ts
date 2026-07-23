// Shared types for the AIRBDS review converter.
// The converter turns an AIRBDS assessment spreadsheet into a review document
// conforming to reviews/review_template.yaml.

/** A single answered question in a review. */
export interface ReviewAnswer {
  /** "Yes" | "No" | "" — empty means unanswered (a draft, not yet submittable). */
  answer: string;
  comments: string;
  /** Present only for Ethics-scope questions (those with a not_applicable_default). */
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
 * The slice of the canonical metric the converter needs: the schema version, the
 * ordered question ids, and which of them are Ethics-scope (carry a
 * not_applicable flag). Parsed from the single source of truth — the versioned
 * metric/airbds_metric_v*.yaml — never hardcoded or copied here, so a new metric
 * version (e.g. v0.3's ACM-1…28 → v0.4's ABC-01…27 → v0.5's ABC-01…25) flows
 * through automatically.
 */
export interface Metric {
  schemaVersion: string;
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
