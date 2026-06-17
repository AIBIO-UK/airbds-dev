import type { SheetCsvs } from "./types.ts";

const BASE = "https://docs.google.com/spreadsheets/d";

/** Pull the spreadsheet id out of a full URL, or accept a bare id. */
export function extractSpreadsheetId(input: string): string {
  const m = input.match(/\/spreadsheets\/d\/([a-zA-Z0-9-_]+)/);
  if (m) return m[1];
  if (/^[a-zA-Z0-9-_]+$/.test(input.trim())) return input.trim();
  throw new Error(`Could not extract a spreadsheet id from "${input}".`);
}

async function fetchText(url: string): Promise<string> {
  const res = await fetch(url, { redirect: "follow" });
  if (!res.ok) throw new Error(`GET ${url} → ${res.status} ${res.statusText}`);
  return res.text();
}

/** Discover tab gids from the spreadsheet's htmlview page. */
async function discoverGids(id: string): Promise<string[]> {
  const html = await fetchText(`${BASE}/${id}/htmlview`);
  const gids = new Set<string>();
  for (const m of html.matchAll(/[?&#]gid=(\d+)/g)) gids.add(m[1]);
  gids.add("0"); // always try the default tab
  return [...gids];
}

function firstNonEmptyCell(csv: string): string {
  for (const line of csv.split(/\r?\n/)) {
    const cell = line.split(",")[0]?.replace(/^"|"$/g, "").trim();
    if (cell) return cell;
  }
  return "";
}

/**
 * Fetch the two tabs the converter needs (review-info and questions) from a
 * sheet URL or id. Tabs are classified by content, not by hard-coded gid, so
 * template *copies* with different gids still work. The sheet must be shared
 * "anyone with the link" for the public CSV export endpoint to return data.
 */
export async function fetchSheet(input: string): Promise<SheetCsvs> {
  const id = extractSpreadsheetId(input);
  const gids = await discoverGids(id);

  let reviewCsv: string | undefined;
  let questionsCsv: string | undefined;
  for (const gid of gids) {
    const csv = await fetchText(`${BASE}/${id}/export?format=csv&gid=${gid}`);
    if (!questionsCsv && firstNonEmptyCell(csv) === "Q ID") questionsCsv = csv;
    else if (!reviewCsv && /reviewer name/i.test(csv)) reviewCsv = csv;
    if (reviewCsv && questionsCsv) break;
  }

  if (!reviewCsv || !questionsCsv) {
    const missing = [!reviewCsv && "review-info", !questionsCsv && "questions"]
      .filter(Boolean)
      .join(" and ");
    throw new Error(
      `Could not find the ${missing} tab(s). Ensure the sheet is shared ` +
        '"anyone with the link" and follows the AIRBDS scoring template.',
    );
  }
  return { reviewCsv, questionsCsv };
}
