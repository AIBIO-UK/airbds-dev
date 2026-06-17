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

export interface SheetAnswer {
  answer: string;
  comments: string;
}

/**
 * The questions tab has a header row beginning with "Q ID". Maps each ACM-N row
 * to its Answer and Comments, locating columns by header name so a reordered
 * sheet still parses. Footer rows (TOTAL, etc.) are ignored.
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
    if (!/^ACM-\d+$/.test(id)) continue;
    answers.set(id, {
      answer: (row[answerCol] ?? "").trim(),
      comments: commentsCol === -1 ? "" : (row[commentsCol] ?? "").trim(),
    });
  }
  return answers;
}
