#!/usr/bin/env python3
"""Build the canonical v0.5 metric YAML from the AIRBDS Google Sheet.

Like v0.4, v0.5 is authored in a public Google Sheet (the working group's live
doc). This script pulls the Scoring, Lookups, and Instructions tabs via the
public CSV export (the sheet's own export format, not this script's output
format) and regenerates the metric YAML from them.

Usage:
    # Regenerate metric/airbds_metric_v0.5.yaml from the live sheet
    python3 metric/src/scripts/build_metric_yaml_from_google_sheet_v0.5.py

    # Verify the committed file still matches the live sheet (the drift check)
    python3 metric/src/scripts/build_metric_yaml_from_google_sheet_v0.5.py --check

    # Work offline from exported CSVs instead of fetching
    python3 metric/src/scripts/build_metric_yaml_from_google_sheet_v0.5.py \
        --scoring-csv scoring.csv --lookups-csv lookups.csv \
        --instructions-csv instructions.csv

Schema notes (v0.5 vs v0.4):
  * The metric is 25 questions (was 27). Ids remain ABC-NN; scopes and grades
    are unchanged (Infrastructure/Metadata/Content/Ethics; Critical/Important/
    Optional).
  * The Lookups tab was restructured: per-question points now live in a
    'COUNTA of Grade' pivot's 'Points per Question' column (was a flat
    'Grade / Points' table). The 'Required proportions' grading table is
    unchanged.
  * NEW: the sheet's Instructions tab is captured verbatim into a top-level
    `instructions:` block, so downstream reviewers (human and AI) read the same
    generic guidance the sheet shows. The per-review data-entry section on that
    tab is excluded.
  * Document-level metadata (license, description, scope descriptions) is NOT in
    the sheet — it is held in the CONFIG block below; edit it there.

Exit codes:
    0 — wrote the files (default), or --check found both already in sync
    1 — --check found a committed file differs from the sheet
    2 — the sheet failed a sanity check (e.g. an unexpected scope)
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sheet_source import (  # noqa: E402  (sibling module, after sys.path tweak)
    CsvWorksheet,
    extract_spreadsheet_id,
    fetch_named_tabs,
)

# Repo root is four levels up: <root>/metric/src/scripts/<this file>.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCRIPT_PATH = f"metric/src/scripts/{Path(__file__).name}"

# ── Editorial config (NOT in the sheet — edit here) ──────────────────────────

VERSION = "0.5"

DEFAULT_SHEET = "https://docs.google.com/spreadsheets/d/13w-MiUQc2sLzRFqRQD_YT6BisE3Orv5Oj3i0YBw7r_M/edit"
DEFAULT_OUTPUT = REPO_ROOT / "metric" / "airbds_metric_v0.5.yaml"

METADATA = {
    "metric_name": "AIRBDS AI-Readiness Dataset Scoring Metric",
    "schema_version": VERSION,
    "release_date": "2026",
    "license": "CC-BY-4.0",
    "repository": "https://github.com/AIBIO-UK/airbds-metric",
    "contact": "info@aibio.ac.uk",
}

DESCRIPTION_LINES = [
    "A structured checklist for evaluating the AI-readiness of bioscience datasets.",
    "Questions are grouped into four scopes (Infrastructure, Metadata, Content, Ethics)",
    "and graded as Optional, Important, or Critical to produce a composite score",
    "and grade (Caution / Bronze / Silver / Gold).",
]

SCOPES = [
    ("Infrastructure", "Questions about how the dataset is hosted, accessed, and identified."),
    ("Metadata", "Questions about the dataset's descriptive and contextual metadata."),
    ("Content", "Questions about the quality, format, and consistency of the data itself."),
    ("Ethics", "Questions about ethical, privacy, and security considerations. Applicable primarily to datasets containing human or animal subject data."),
]

# Scopes whose questions carry not_applicable_default: "Yes".
NA_DEFAULT_SCOPES = {"Ethics"}

QID_RE = re.compile(r"^ABC-\d+$")

HEADER_COMMENT = f"""\
# =============================================================================
# {METADATA["metric_name"]} — v{VERSION}
# AI-Ready Bioscience Datasets Working Group (AIRBDS), AIBIO-UK
# https://aibio.ac.uk/about/working-groups/airbds/
# License: {METADATA["license"]}
# =============================================================================
#
# *** GENERATED FILE — DO NOT EDIT BY HAND. ***
#
# This file is generated from the AIRBDS scoring Google Sheet by the metric
# build script (see metric/README.md). Any manual edit will be lost the next
# time the file is regenerated. To change this file's contents — or the way it
# is generated — edit the sheet (and/or that script) and re-run it.
# Never edit this file directly.
# =============================================================================
#
# Question definitions for a given metric version. For a version the scope and
# grade of each question are fixed, so they are defined here as the source of
# truth rather than trusted from uploaded assessments.
#
# This is a language-neutral data file: the question definitions can be read by
# any tool (the review processor, the auto-airbds web frontend, etc.). The
# `guidance` field explains how each question should be answered; it is guidance
# for humans/LLMs."""

INSTRUCTIONS_COMMENT = """\
# Generic reviewer instructions, captured verbatim from the source sheet's
# Instructions tab. This is guidance for whoever assesses a dataset (human or
# AI agent) — how to interpret the metric and what is in/out of scope. It is
# informational and does not affect scoring."""

GRADE_POINTS_COMMENT = """\
# Full points awarded for a question when its answer is "Yes", keyed by the
# question's grade. A "No" answer always scores 0. A question's score is
# therefore fixed by its grade and answer, not taken from the assessment."""

GRADING_COMMENT = """\
# Grading thresholds, highest grade first. A dataset earns the highest grade for
# which every requirement holds: the proportion of "Yes" answers within each
# grade category must be at least min_proportion_yes (compared with >=), and the
# total score must be at least min_score. The final entry is the floor (all-zero
# requirements). Editing these values re-grades without any code change."""

SCOPES_COMMENT = "# Top-level groupings of the questions."

QUESTIONS_COMMENT = """\
# Every question is a boolean "Yes"/"No". Ethics questions carry a
# not_applicable_default of "Yes" — they are marked "Yes" for datasets with no
# human or animal subject data."""


# ── Tab classifiers ──────────────────────────────────────────────────────────

def _first_cell(csv_text: str) -> str:
    for line in csv_text.splitlines():
        cell = line.split(",")[0].strip().strip('"')
        if cell:
            return cell
    return ""


CLASSIFIERS = {
    "scoring": lambda t: _first_cell(t) == "Q ID",
    "lookups": lambda t: "Required proportions" in t and "Points per Question" in t,
    "instructions": lambda t: _first_cell(t) == "Instructions",
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def dq(text) -> str:
    """Render a value as a YAML double-quoted scalar."""
    escaped = str(text).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def norm(text) -> str:
    """Collapse internal whitespace runs and strip (fixes stray sheet spaces)."""
    return " ".join(str(text or "").split())


def normalize_newlines(text: str) -> str:
    """Canonicalize line endings to LF.

    A live fetch returns the sheet's CSV with CRLF, whereas an offline CSV read
    through `Path.read_text` has already been normalized to LF. `source_sha256`
    hashes this raw text, so without this the same sheet would hash differently
    online vs offline (breaking both `--check` and the offline byte-for-byte
    test). It also makes the hash independent of whether Google serves CRLF or
    LF on a given day.
    """
    return text.replace("\r\n", "\n").replace("\r", "\n")


def clean_multiline(text) -> str:
    """Tidy a multi-paragraph cell: collapse intra-line whitespace but keep
    paragraph breaks (blank lines). Runs of blank lines collapse to one, and
    leading/trailing blank lines are dropped. Returns '' for an empty cell."""
    if text is None:
        return ""
    lines = [" ".join(str(line).split()) for line in str(text).splitlines()]
    out = []
    for line in lines:
        if line or (out and out[-1]):  # collapse runs of blank lines to one
            out.append(line)
    while out and not out[-1]:
        out.pop()
    while out and not out[0]:
        out.pop(0)
    return "\n".join(out)


def fmt_prop(value) -> str:
    """Format a proportion the way the YAML does: 1.0, 0.5, 0.875, 0.0."""
    return str(float(value))


def fmt_score(value) -> str:
    """min_score: keep integers integral (560, 703) and fractions as-is (667.5)."""
    f = float(value)
    return str(int(f)) if f.is_integer() else str(f)


def source_sha256(scoring_csv: str, lookups_csv: str, instructions_csv: str) -> str:
    """Content hash of the exact source tabs — the content-addressed "revision".

    Deterministic given the source content, so it is safe to embed in the YAML
    (the --check byte comparison stays valid) and serves as the drift baseline.
    Covers all three source tabs, so an edit to the Instructions tab is detected
    too.
    """
    h = hashlib.sha256()
    h.update(scoring_csv.encode("utf-8"))
    h.update(b"\n--LOOKUPS--\n")
    h.update(lookups_csv.encode("utf-8"))
    h.update(b"\n--INSTRUCTIONS--\n")
    h.update(instructions_csv.encode("utf-8"))
    return h.hexdigest()


# ── Sheet readers (operate on a CsvWorksheet / openpyxl worksheet) ───────────

def read_questions(ws) -> list[dict]:
    """Read the question table from the Scoring tab, in sheet order."""
    header = {norm(ws.cell(1, c).value): c
              for c in range(1, ws.max_column + 1) if ws.cell(1, c).value}
    required = ["Q ID", "Scope", "Question", "Notes", "Grade"]
    missing = [h for h in required if h not in header]
    if missing:
        sys.exit(f"ERROR: Scoring tab is missing column(s): {missing}")

    questions = []
    for r in range(2, ws.max_row + 1):
        qid = norm(ws.cell(r, header["Q ID"]).value)
        if not QID_RE.match(qid):
            continue
        questions.append({
            "id": qid,
            "scope": norm(ws.cell(r, header["Scope"]).value),
            "grade": norm(ws.cell(r, header["Grade"]).value),
            "question": norm(ws.cell(r, header["Question"]).value),
            "guidance": norm(ws.cell(r, header["Notes"]).value),
        })
    return questions


def _find_row(ws, predicate):
    for r in range(1, ws.max_row + 1):
        if predicate(r):
            return r
    return None


def read_grade_points(ws) -> dict:
    """Read {grade: points} from the Lookups 'COUNTA of Grade' pivot.

    v0.5 restructured the Lookups tab: the flat 'Grade / Points' table became a
    pivot whose header row is `Grade | <scopes…> | Grand Total |
    Points per Question | Points available`. The per-question points live in the
    'Points per Question' column; the following rows are the three grades and a
    'Grand Total' row (which ends the table).
    """
    hdr = _find_row(ws, lambda r: norm(ws.cell(r, 1).value) == "Grade"
                    and any(norm(ws.cell(r, c).value) == "Points per Question"
                            for c in range(1, ws.max_column + 1)))
    if hdr is None:
        sys.exit("ERROR: could not locate the 'Grade / Points per Question' table in Lookups")
    points_col = next(c for c in range(1, ws.max_column + 1)
                      if norm(ws.cell(hdr, c).value) == "Points per Question")
    points = {}
    for r in range(hdr + 1, ws.max_row + 1):
        name = norm(ws.cell(r, 1).value)
        val = ws.cell(r, points_col).value
        if name in {"Optional", "Important", "Critical"} and isinstance(val, (int, float)):
            points[name] = int(val)
        elif name or val is not None:
            break  # 'Grand Total' row or the next table
    return points


def read_grading(ws) -> list[dict]:
    """Read the grading thresholds from the Lookups 'Required proportions' table."""
    hdr = _find_row(ws, lambda r: norm(ws.cell(r, 1).value) == "Optional"
                    and norm(ws.cell(r, 4).value) == "Threshold"
                    and norm(ws.cell(r, 5).value) == "Grade")
    if hdr is None:
        sys.exit("ERROR: could not locate the 'Required proportions' table in Lookups")
    rows = []
    for r in range(hdr + 1, ws.max_row + 1):
        grade = norm(ws.cell(r, 5).value)
        if not grade:
            break
        rows.append({
            "name": grade,
            "description": norm(ws.cell(r, 6).value),
            "min_proportion_yes": {
                "Critical": float(ws.cell(r, 3).value or 0),
                "Important": float(ws.cell(r, 2).value or 0),
                "Optional": float(ws.cell(r, 1).value or 0),
            },
            "min_score": float(ws.cell(r, 4).value or 0),  # may be fractional
        })
    rows.sort(key=lambda g: g["min_score"], reverse=True)  # highest grade first
    return rows


def read_instructions(ws) -> str:
    """Read the generic reviewer instructions from the Instructions tab.

    The tab opens with an 'Instructions' label in column 1 and the guidance
    prose in a content column to its right; a per-review data-entry section
    (headed e.g. 'Review informaton') follows below and is NOT part of the
    generic instructions. Everything from the header row down to that next
    labelled row is captured, with paragraph breaks preserved.
    """
    r0 = _find_row(ws, lambda r: norm(ws.cell(r, 1).value) == "Instructions")
    if r0 is None:
        sys.exit("ERROR: could not locate the 'Instructions' header in the Instructions tab")
    # Content column: the rightmost non-empty cell in the header row.
    content_col = max((c for c in range(1, ws.max_column + 1)
                       if norm(ws.cell(r0, c).value)), default=1)
    blocks = []
    for r in range(r0, ws.max_row + 1):
        if r > r0 and norm(ws.cell(r, 1).value):
            break  # next labelled section (e.g. the review data-entry block)
        text = clean_multiline(ws.cell(r, content_col).value)
        if text:
            blocks.append(text)
    instructions = "\n\n".join(blocks)
    if not instructions:
        sys.exit("ERROR: the Instructions tab yielded no text")
    return instructions


# ── YAML / CSV rendering ─────────────────────────────────────────────────────

def render_footer(questions: list[dict], grade_points: dict) -> str:
    def num(qid):
        return int(qid.split("-")[1])

    lines = [
        "# =============================================================================",
        "# QUESTION SUMMARY",
        f"# Total questions: {len(questions)}",
    ]
    for scope_id, _ in SCOPES:
        ids = [q["id"] for q in questions if q["scope"] == scope_id]
        if not ids:
            continue
        ids.sort(key=num)
        rng = f"({ids[0]} – {ids[-1]})"
        lines.append(f"# {(scope_id + ':').ljust(17)}{len(ids):>2}  {rng}")

    lines.append("#")
    lines.append(f"# Grade breakdown (all {len(questions)} questions):")
    total = 0
    for grade in ("Critical", "Important", "Optional"):
        count = sum(1 for q in questions if q["grade"] == grade)
        pts = grade_points[grade]
        subtotal = count * pts
        total += subtotal
        lines.append(
            f"#   {(grade + ':').ljust(10)}{count:>3}   × {str(pts):<2} pts = {str(subtotal):<3} pts maximum"
        )
    lines.append(f"#   TOTAL maximum (incl. Ethics): {total} pts")
    lines.append("# =============================================================================")
    return "\n".join(lines)


def render_yaml(questions, grade_points, grading, instructions,
                sheet_url, content_sha256) -> str:
    out = [HEADER_COMMENT, ""]
    out.append(f"# Source: {sheet_url}")
    out.append(f"# Source content sha256: {content_sha256}")
    out.append("")

    for key, val in METADATA.items():
        out.append(f"{key}: {dq(val)}")
    out.append("")

    out.append("description: >")
    out.extend(f"  {line}" for line in DESCRIPTION_LINES)
    out.append("")

    out.append(INSTRUCTIONS_COMMENT)
    out.append("instructions: |")
    for line in instructions.split("\n"):
        out.append(f"  {line}" if line else "")
    out.append("")

    out.append(GRADE_POINTS_COMMENT)
    out.append("grade_points:")
    for grade in sorted(grade_points, key=grade_points.get, reverse=True):
        out.append(f"  {grade}: {grade_points[grade]}")
    out.append("")

    out.append(GRADING_COMMENT)
    out.append("grading:")
    for g in grading:
        p = g["min_proportion_yes"]
        out.append(f"  - name: {g['name']}")
        out.append(f"    description: {dq(g['description'])}")
        out.append(
            "    min_proportion_yes: "
            f"{{ Critical: {fmt_prop(p['Critical'])}, "
            f"Important: {fmt_prop(p['Important'])}, "
            f"Optional: {fmt_prop(p['Optional'])} }}"
        )
        out.append(f"    min_score: {fmt_score(g['min_score'])}")
    out.append("")

    out.append(SCOPES_COMMENT)
    out.append("scopes:")
    for i, (scope_id, desc) in enumerate(SCOPES, start=1):
        out.append(f"  - id: {scope_id}")
        out.append(f"    sort_order: {i}")
        out.append(f"    description: {dq(desc)}")
    out.append("")

    out.append(QUESTIONS_COMMENT)
    out.append("questions:")
    for q in questions:
        out.append(f"  {q['id']}:")
        out.append(f"    scope: {q['scope']}")
        out.append(f"    grade: {q['grade']}")
        out.append(f"    question: {dq(q['question'])}")
        out.append(f"    guidance: {dq(q['guidance'])}")
        out.append('    answer: { type: boolean, options: ["Yes", "No"] }')
        if q["scope"] in NA_DEFAULT_SCOPES:
            out.append('    not_applicable_default: "Yes"')
    out.append("")

    out.append(render_footer(questions, grade_points))
    return "\n".join(out) + "\n"


# ── Validation ───────────────────────────────────────────────────────────────

def validate(questions, grade_points, grading) -> None:
    if not questions:
        sys.exit("ERROR: no questions (ABC-N rows) were found in the Scoring tab")
    configured_scopes = {s for s, _ in SCOPES}
    unknown = {q["scope"] for q in questions} - configured_scopes
    if unknown:
        sys.exit(f"ERROR: sheet uses scope(s) not in CONFIG.SCOPES: {sorted(unknown)}\n"
                 f"       Add them (with a description) to the SCOPES list.")
    for grade in {q["grade"] for q in questions}:
        if grade not in grade_points:
            sys.exit(f"ERROR: question grade {grade!r} has no entry in grade_points")
    if not grading:
        sys.exit("ERROR: no grading thresholds were read from the Lookups tab")


# ── Main ─────────────────────────────────────────────────────────────────────

def load_worksheets(args) -> tuple:
    """Return (scoring_ws, lookups_ws, instructions_ws, src) from files or the sheet.

    `src` carries the raw tab CSVs (for hashing) and provenance: the sheet id/url
    when fetched, or None/the files when working offline.
    """
    offline = args.scoring_csv or args.lookups_csv or args.instructions_csv
    if offline:
        if not (args.scoring_csv and args.lookups_csv and args.instructions_csv):
            sys.exit("ERROR: pass all of --scoring-csv, --lookups-csv, and "
                     "--instructions-csv, or none.")
        scoring = normalize_newlines(args.scoring_csv.read_text(encoding="utf-8"))
        lookups = normalize_newlines(args.lookups_csv.read_text(encoding="utf-8"))
        instructions = normalize_newlines(args.instructions_csv.read_text(encoding="utf-8"))
        src = {
            "label": f"{args.scoring_csv.name} + {args.lookups_csv.name} "
                     f"+ {args.instructions_csv.name}",
            "sheet_id": None,
            "sheet_url": args.sheet,
            "scoring_csv": scoring,
            "lookups_csv": lookups,
            "instructions_csv": instructions,
        }
        return (CsvWorksheet(scoring), CsvWorksheet(lookups),
                CsvWorksheet(instructions), src)

    sheet_id = extract_spreadsheet_id(args.sheet)
    tabs = fetch_named_tabs(sheet_id, CLASSIFIERS)
    scoring = normalize_newlines(tabs["scoring"])
    lookups = normalize_newlines(tabs["lookups"])
    instructions = normalize_newlines(tabs["instructions"])
    src = {
        "label": f"Google Sheet {sheet_id}",
        "sheet_id": sheet_id,
        "sheet_url": args.sheet,
        "scoring_csv": scoring,
        "lookups_csv": lookups,
        "instructions_csv": instructions,
    }
    return (CsvWorksheet(scoring), CsvWorksheet(lookups),
            CsvWorksheet(instructions), src)


def write_manifest(path: Path, src: dict, content_sha256: str, generated_at: str) -> None:
    """Write the provenance sidecar (JSON): which sheet and which revision (hash)."""
    manifest = {
        "metric_version": VERSION,
        "sheet_url": src["sheet_url"],
        "sheet_id": src["sheet_id"],
        "content_sha256": content_sha256,
        "generated_at": generated_at,
        "generator": SCRIPT_PATH,
    }
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Build the v0.5 metric YAML from the Google Sheet.")
    ap.add_argument("--sheet", default=DEFAULT_SHEET, help="sheet URL or id (default: the canonical sheet)")
    ap.add_argument("--scoring-csv", type=Path, help="local Scoring tab CSV (offline; with --lookups-csv/--instructions-csv)")
    ap.add_argument("--lookups-csv", type=Path, help="local Lookups tab CSV (offline)")
    ap.add_argument("--instructions-csv", type=Path, help="local Instructions tab CSV (offline)")
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="path to write the metric YAML")
    ap.add_argument("--check", action="store_true",
                    help="do not write; exit 1 if the output differs from what the sheet produces")
    args = ap.parse_args()

    scoring_ws, lookups_ws, instructions_ws, src = load_worksheets(args)
    questions = read_questions(scoring_ws)
    grade_points = read_grade_points(lookups_ws)
    grading = read_grading(lookups_ws)
    instructions = read_instructions(instructions_ws)
    validate(questions, grade_points, grading)

    content_sha256 = source_sha256(src["scoring_csv"], src["lookups_csv"],
                                   src["instructions_csv"])
    generated_yaml = render_yaml(questions, grade_points, grading, instructions,
                                 src["sheet_url"], content_sha256)
    yaml.safe_load(generated_yaml)  # confirm the YAML is valid before trusting it

    if args.check:
        # The source hash is embedded in the YAML breadcrumb, so a byte mismatch
        # also catches any change to the upstream source content.
        current = args.output.read_bytes() if args.output.exists() else b""
        if current == generated_yaml.encode("utf-8"):
            print(f"OK: {args.output.name} is in sync "
                  f"with {src['label']} (sha256 {content_sha256[:12]}, {len(questions)} questions)")
            sys.exit(0)
        print(f"DRIFT: {args.output} differs from {src['label']}.", file=sys.stderr)
        print(f"Regenerate with: python3 {SCRIPT_PATH}", file=sys.stderr)
        sys.exit(1)

    manifest_path = args.output.parent / f"{args.output.stem}.upstream.json"
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    write_manifest(manifest_path, src, content_sha256, generated_at)

    args.output.write_bytes(generated_yaml.encode("utf-8"))
    print(f"Wrote: {args.output}\n"
          f"Wrote: {manifest_path}\n"
          f"{len(questions)} questions, "
          f"{sum(q['scope'] in NA_DEFAULT_SCOPES for q in questions)} ethics, "
          f"instructions captured ({len(instructions)} chars)\n"
          f"Source: {src['label']} (sha256 {content_sha256[:12]})")


if __name__ == "__main__":
    main()
