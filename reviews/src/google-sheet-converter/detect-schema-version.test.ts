import { test } from "node:test";
import assert from "node:assert/strict";
import { detectSchemaVersion } from "./index.ts";

// detectSchemaVersion must read the version from every form the AIRBDS
// spreadsheet template has shipped, so one import path serves old and new sheets.

test("reads the current 'Version:' labelled-cell template (as live sheets ship)", () => {
  // The v1.0.x review-info tab: an "AIRBDS Core metric" title, then a "Version:"
  // label with the number in the next cell.
  const csv = [
    ",AIRBDS Core metric",
    "Version:,1.0.2",
    'Instructions:,"Answer each question Yes or No."',
    ",Reviewer name:,Ada Lovelace",
  ].join("\n");
  assert.equal(detectSchemaVersion(csv), "1.0.2");
});

test("reads the older '… Metric vX.Y.Z' title cell without truncating the patch", () => {
  const csv = "Instructions,,AIRBDS Dataset Metric v1.0.0\n,Reviewer name:,X";
  assert.equal(detectSchemaVersion(csv), "1.0.0");
});

test("reads a two-component pre-1.0 title (v0.4)", () => {
  const csv = "Instructions,,AIRBDS Dataset Metric v0.4\n,Reviewer name:,X";
  assert.equal(detectSchemaVersion(csv), "0.4");
});

test("reads an inline 'Version: 1.0.1' cell", () => {
  const csv = "AIRBDS assessment,Version: 1.0.1\n,Reviewer name:,X";
  assert.equal(detectSchemaVersion(csv), "1.0.1");
});

test("returns null when no version is present", () => {
  assert.equal(detectSchemaVersion("Reviewer name:,Someone\nDataset name:,X"), null);
});

test("does not fire on words that merely contain 'version' or 'metric'", () => {
  const csv = "Notes,A conversion to 2.0 units and a parametric v3.1 model\n,Reviewer name:,X";
  assert.equal(detectSchemaVersion(csv), null);
});
