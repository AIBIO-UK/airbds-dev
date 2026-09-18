import { parse as parseCsvSync } from "csv-parse/sync";

/** Parse CSV text into rows of string cells (no header coupling). */
export function parseCsv(text: string): string[][] {
  return parseCsvSync(text, {
    relax_column_count: true,
    skip_empty_lines: true,
    bom: true,
  }) as string[][];
}

function normalizeLabel(label: string): string {
  return label.trim().replace(/:$/, "").trim().toLowerCase();
}

/**
 * The review-information tab is a set of label/value rows (a label cell followed
 * by its value cell). Returns a map from normalized label → value. The first
 * non-empty cell in a row is treated as the label and the next cell as its value.
 */
export function extractReviewInfo(rows: string[][]): Map<string, string> {
  const info = new Map<string, string>();
  for (const row of rows) {
    for (let i = 0; i < row.length - 1; i++) {
      const label = (row[i] ?? "").trim();
      if (!label) continue;
      const key = normalizeLabel(label);
      if (!info.has(key)) info.set(key, (row[i + 1] ?? "").trim());
      break;
    }
  }
  return info;
}

/**
 * Matches an AIRBDS metric version wherever a single cell declares it, in either
 * form the template has shipped: an old title cell ("AIRBDS … Metric v1.0.0") or
 * an inline label ("Version: 1.0.2"). The `\b` anchors keep it from firing on
 * words like "conversion". The patch component is optional but captured when
 * present, so "v1.0.2" is never truncated to "1.0" (retained v0.3/v0.4 sheets
 * carry two-part labels, so it cannot be required).
 */
const METRIC_VERSION =
  /(?:\bmetric\s+v\.?\s*|\bversion\b\s*:?\s*v?\.?\s*)(\d+\.\d+(?:\.\d+)?)/i;
/** A cell holding only a version number — the value beside a "Version:" label. */
const VERSION_NUMBER = /^v?\.?\s*(\d+\.\d+(?:\.\d+)?)\s*$/i;

/**
 * Read the metric version the sheet declares for itself, from the review-info
 * (Instructions) tab. The sheet is trusted for the version (it is only ever
 * distrusted for the score), so the right metric/airbds_metric_v<version>.yaml
 * can be selected without a flag. Handles every form the template has used:
 *
 *   - a "Version:" label cell with the number in the next cell   (current)
 *   - a single "Version: 1.0.2" cell                             (inline)
 *   - a "AIRBDS … Metric v1.0.0" title cell                      (older sheets)
 *
 * Returns the version string (e.g. "1.0.2") or null if none is found.
 */
export function detectSchemaVersion(reviewCsv: string): string | null {
  const rows = parseCsv(reviewCsv);

  // Current templates carry a labelled "Version:" field; the label/value reader
  // picks up its value cell regardless of which column the label sits in.
  const labelled = extractReviewInfo(rows).get("version");
  if (labelled) {
    const m = labelled.match(VERSION_NUMBER);
    if (m) return m[1];
  }

  // Older templates carry the version inline in a title cell (this also catches
  // a "Version: 1.0.2" written as a single cell rather than a label + value).
  for (const row of rows) {
    for (const cell of row) {
      const m = (cell ?? "").match(METRIC_VERSION);
      if (m) return m[1];
    }
  }
  return null;
}

export interface SheetAnswer {
  answer: string;
  comments: string;
}

/**
 * The questions tab has a header row beginning with "Q ID". Maps each
 * question-id row (ACM-1, ABC-01, …) to its Answer and Comments, locating
 * columns by header name so a reordered sheet still parses. Footer rows
 * (TOTAL, etc.) are ignored.
 */
export function extractAnswers(rows: string[][]): Map<string, SheetAnswer> {
  const headerIdx = rows.findIndex((r) => (r[0] ?? "").trim() === "Q ID");
  if (headerIdx === -1) {
    throw new Error(
      'Questions tab header not found (expected a row starting with "Q ID").',
    );
  }
  const header = rows[headerIdx].map((h) => (h ?? "").trim().toLowerCase());
  const idCol = header.indexOf("q id");
  const answerCol = header.indexOf("answer");
  const commentsCol = header.indexOf("comments");
  if (answerCol === -1) {
    throw new Error('Questions tab has no "Answer" column.');
  }

  const answers = new Map<string, SheetAnswer>();
  for (const row of rows.slice(headerIdx + 1)) {
    const id = (row[idCol] ?? "").trim();
    if (!/^[A-Za-z]+-\d+$/.test(id)) continue;
    answers.set(id, {
      answer: (row[answerCol] ?? "").trim(),
      comments: commentsCol === -1 ? "" : (row[commentsCol] ?? "").trim(),
    });
  }
  return answers;
}
