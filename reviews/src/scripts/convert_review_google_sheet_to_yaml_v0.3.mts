#!/usr/bin/env node
/**
 * Convert an AIRBDS assessment Google Sheet (or its exported CSV tabs) into a
 * review YAML conforming to reviews/review_template.yaml.
 *
 *   # From a public Google Sheet (shared "anyone with the link"):
 *   node reviews/src/scripts/convert_review_google_sheet_to_yaml_v0.3.mts <url-or-id> review.yaml
 *
 *   # Offline / private sheet — supply the two exported CSV tabs:
 *   node reviews/src/scripts/convert_review_google_sheet_to_yaml_v0.3.mts \
 *       --review-csv review-info.csv --questions-csv questions.csv review.yaml
 *
 * Scoring is intentionally NOT done here: `result` is left blank and
 * reviews/src/scripts/review_processor.py / CI compute the score and grade.
 *
 * This is a thin adapter over the pure ../google-sheet-converter library.
 */
import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { convert, fetchSheet, parseMetric } from "../google-sheet-converter/index.ts";

// metric/airbds_metric_v0.3.yaml is the single source of truth, referenced from
// the repo root — never copied into the converter.
const DEFAULT_METRIC = fileURLToPath(
  new URL("../../../metric/airbds_metric_v0.3.yaml", import.meta.url),
);

interface Args {
  sheet?: string;
  reviewCsv?: string;
  questionsCsv?: string;
  out?: string;
  metric: string;
}

function parseArgs(argv: string[]): Args {
  const args: Args = { metric: DEFAULT_METRIC };
  const positionals: string[] = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const next = () => argv[++i];
    switch (a) {
      case "--review-csv": args.reviewCsv = next(); break;
      case "--questions-csv": args.questionsCsv = next(); break;
      case "--metric": args.metric = next(); break;
      case "--help":
      case "-h": printUsageAndExit(0);
      // falls through (printUsageAndExit never returns)
      default:
        if (a.startsWith("-")) throw new Error(`Unknown option: ${a}`);
        positionals.push(a);
    }
  }
  // Offline mode (CSV tabs supplied) takes no sheet, so the lone positional is
  // the output path; otherwise the positionals are <sheet> [output].
  if (args.reviewCsv || args.questionsCsv) {
    args.out = positionals[0];
  } else {
    args.sheet = positionals[0];
    args.out = positionals[1];
  }
  return args;
}

function printUsageAndExit(code: number): never {
  const text = `Convert an AIRBDS assessment Google Sheet to a review YAML.

Usage:
  convert_review_google_sheet_to_yaml_v0.3.mts <sheet-url-or-id> [output.yaml]
  convert_review_google_sheet_to_yaml_v0.3.mts --review-csv <f> --questions-csv <f> [output.yaml]

Arguments:
  <sheet-url-or-id>        Public Google Sheet — full URL or just the spreadsheet id
  [output.yaml]            Output path (optional; default: stdout)

Options:
  --review-csv <file>      Offline: the review-information tab as CSV
  --questions-csv <file>   Offline: the questions tab as CSV
  --metric <file>          Metric YAML (default: repo metric/airbds_metric_v0.3.yaml)
  --help, -h               Show this help

The sheet must be shared "anyone with the link".`;
  console.log(text);
  process.exit(code);
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));

  let reviewCsv: string;
  let questionsCsv: string;
  if (args.reviewCsv && args.questionsCsv) {
    [reviewCsv, questionsCsv] = await Promise.all([
      readFile(args.reviewCsv, "utf8"),
      readFile(args.questionsCsv, "utf8"),
    ]);
  } else if (args.sheet) {
    ({ reviewCsv, questionsCsv } = await fetchSheet(args.sheet));
  } else {
    console.error(
      "Error: provide a Google Sheet URL/id, or both --review-csv and --questions-csv.\n",
    );
    printUsageAndExit(1);
  }

  const metric = parseMetric(await readFile(args.metric, "utf8"));
  const { yaml, warnings } = convert(reviewCsv, questionsCsv, metric);

  if (args.out) {
    await writeFile(args.out, yaml, "utf8");
    console.error(`Wrote ${args.out}`);
  } else {
    process.stdout.write(yaml);
  }

  for (const w of warnings) console.error(`warning: ${w}`);
  if (warnings.length) {
    console.error(
      `\n${warnings.length} warning(s). Complete any blank answers, name the file ` +
        "per CONTRIBUTING.md (<accession>_<INITIALS>_<n>.yaml), then submit — CI scores it.",
    );
  }
}

main().catch((err: unknown) => {
  console.error(`error: ${err instanceof Error ? err.message : String(err)}`);
  process.exit(1);
});
