#!/usr/bin/env node
/**
 * Convert an AIRBDS assessment Google Sheet (or its exported CSV tabs) into a
 * review YAML conforming to reviews/review_template.yaml.
 *
 * The metric version is read from the sheet itself — the "AIRBDS … Metric vX.Y"
 * label on the Instructions tab — and the matching metric/airbds_metric_vX.Y.yaml
 * is loaded automatically. The sheet is trusted for the version; it is only ever
 * distrusted for the score, which is left to review_processor.py / CI.
 *
 *   # From a public Google Sheet (shared "anyone with the link"):
 *   node reviews/src/scripts/convert_review_google_sheet_to_yaml.mts <url-or-id> review.yaml
 *
 *   # Offline / private sheet — supply the two exported CSV tabs:
 *   node reviews/src/scripts/convert_review_google_sheet_to_yaml.mts \
 *       --review-csv review-info.csv --questions-csv questions.csv review.yaml
 *
 * This is a thin adapter over the pure ../google-sheet-converter library.
 */
import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import {
  convert,
  detectSchemaVersion,
  fetchSheet,
  parseMetric,
} from "../google-sheet-converter/index.ts";

// The bundled metric for a given version, referenced from the repo root — the
// single source of truth, never copied into the converter.
const metricPathFor = (version: string): string =>
  fileURLToPath(
    new URL(`../../../metric/airbds_metric_v${version}.yaml`, import.meta.url),
  );

interface Args {
  sheet?: string;
  reviewCsv?: string;
  questionsCsv?: string;
  out?: string;
}

function parseArgs(argv: string[]): Args {
  const args: Args = {};
  const positionals: string[] = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const next = () => argv[++i];
    switch (a) {
      case "--review-csv": args.reviewCsv = next(); break;
      case "--questions-csv": args.questionsCsv = next(); break;
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

The metric version is detected from the sheet's Instructions tab ("AIRBDS … Metric
vX.Y") and the matching metric/airbds_metric_v<version>.yaml is loaded automatically.

Usage:
  convert_review_google_sheet_to_yaml.mts <sheet-url-or-id> [output.yaml]
  convert_review_google_sheet_to_yaml.mts --review-csv <f> --questions-csv <f> [output.yaml]

Arguments:
  <sheet-url-or-id>        Public Google Sheet — full URL or just the spreadsheet id
  [output.yaml]            Output path (optional; default: stdout)

Options:
  --review-csv <file>      Offline: the review-information (Instructions) tab as CSV
  --questions-csv <file>   Offline: the questions tab as CSV
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

  // The sheet declares its own metric version on the Instructions tab.
  const version = detectSchemaVersion(reviewCsv);
  if (!version) {
    throw new Error(
      "Could not determine the metric version from the sheet — expected an " +
        '"AIRBDS … Metric vX.Y" label on the Instructions tab.',
    );
  }

  let metricYaml: string;
  try {
    metricYaml = await readFile(metricPathFor(version), "utf8");
  } catch {
    throw new Error(
      `The sheet declares metric version v${version}, but ` +
        `metric/airbds_metric_v${version}.yaml was not found.`,
    );
  }
  const metric = parseMetric(metricYaml);
  const { yaml, warnings } = convert(reviewCsv, questionsCsv, metric);

  if (args.out) {
    await writeFile(args.out, yaml, "utf8");
    console.error(`Wrote ${args.out} (detected metric v${version})`);
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
