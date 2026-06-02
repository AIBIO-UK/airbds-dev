#!/usr/bin/env python3
"""AIRBDS Review Processor — validates, converts, and scores review files.

Usage:
    python3 scripts/review_processor.py \
        --files /tmp/changed_files.txt \
        --metric metric/airbds_metric_v0.3.yaml

Each line in --files should be a path to a .yaml or .csv review file.
The script validates, scores, writes the result block, generates the companion
format, and renames each file to include the score and grade as a postfix.

Exit codes:
    0 — all files passed validation
    1 — one or more files failed validation
"""

import argparse
import csv
import io
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

import yaml

# ── Constants ──────────────────────────────────────────────────────────────────

SCHEMA_VERSION = "0.3"
ETHICS_QUESTIONS = {"ACM-24", "ACM-25", "ACM-26", "ACM-27", "ACM-28"}
ALL_QUESTION_IDS = [f"ACM-{i}" for i in range(1, 29)]
WEIGHT_POINTS = {"Critical": 80, "Important": 5, "Optional": 2}

# YAML 1.1 strings that are misread as booleans — must be quoted on output
YAML11_BOOL_STRINGS = {
    "y", "Y", "yes", "Yes", "YES",
    "n", "N", "no", "No", "NO",
    "true", "True", "TRUE", "false", "False", "FALSE",
    "on", "On", "ON", "off", "Off", "OFF",
}

# Regex to detect strings that YAML would parse as numbers (e.g. "0.3", "123")
_NUMERIC_RE = re.compile(r"^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$")

# Filename regex: <token>_<INITIALS>_<N>[_<score>_<grade>].<ext>
# Group 1 = base stem (everything before optional score postfix)
# Group 2 = grade (if scored), Group 3 = extension
SCORED_SUFFIX_RE = re.compile(
    r"^(.+_[A-Z]{1,6}_\d+)(?:_\d+_(Caution|Bronze|Silver|Gold))?\.(yaml|csv)$"
)
FILENAME_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]*_[A-Z]{2,6}_\d+"
    r"(?:_\d+_(?:Caution|Bronze|Silver|Gold))?\.(yaml|csv)$"
)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Strict match for a *fully scored* filename: requires both score AND grade components.
# Groups: (1) base stem, (2) score as string, (3) grade, (4) extension
FULL_SCORED_FILENAME_RE = re.compile(
    r"^(.+_[A-Z]{1,6}_\d+)_(\d+)_(Caution|Bronze|Silver|Gold)\.(yaml|csv)$"
)

CSV_SECTION_A_FIELDS = [
    "schema_version", "reviewer_name", "reviewer_initials", "reviewer_orcid",
    "reviewer_affiliation", "review_date", "dataset_name", "dataset_url",
    "dataset_accession", "hosting_resource", "process_comments",
]


# ── Custom YAML Dumper (forces quotes on bool-like strings) ───────────────────

class ReviewDumper(yaml.Dumper):
    pass


def _bool_safe_str(dumper: yaml.Dumper, data: str) -> yaml.ScalarNode:
    needs_quoting = (
        data in YAML11_BOOL_STRINGS
        or data == ""
        or _NUMERIC_RE.match(data) is not None
    )
    if needs_quoting:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


ReviewDumper.add_representer(str, _bool_safe_str)


# ── Metric loading ─────────────────────────────────────────────────────────────

def load_metric(metric_path: str) -> dict:
    """Load question metadata from the canonical metric YAML.

    Returns {question_id: {weight, weight_points, scope, theme, question, guidance}}.

    Questions are stored as a map keyed by question id. Each question's grade
    lives in a `grade` field and the per-grade point values in a top-level
    `grade_points` map. The processor's internal vocabulary is
    "weight"/"weight_points", so the grade is surfaced as the weight and its
    points looked up from grade_points.
    """
    with open(metric_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    grade_points = data.get("grade_points", {})
    meta = {}
    for qid, q in (data.get("questions") or {}).items():
        grade = q["grade"]
        meta[qid] = {
            "weight": grade,
            "weight_points": grade_points.get(grade, WEIGHT_POINTS.get(grade, 0)),
            "scope": q["scope"],
            "theme": q["theme"],
            "question": q["question"].strip(),
            "guidance": q["guidance"].strip(),
        }
    return meta


def load_grading(metric_path: str) -> list:
    """Load grade thresholds from the metric YAML, highest grade first.

    Returns a list of {name, min_proportion_yes: {tier: float}, min_score: float}.
    A dataset earns the highest grade whose per-tier "Yes" proportions and total
    weighted score all meet the listed minima — mirroring the auto-airbds
    frontend so the two grade identically.
    """
    with open(metric_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    grading = []
    for entry in data.get("grading", []):
        grading.append({
            "name": entry["name"],
            "min_proportion_yes": dict(entry.get("min_proportion_yes", {})),
            "min_score": entry.get("min_score", 0),
        })
    return grading


# ── Filename helpers ───────────────────────────────────────────────────────────

def validate_filename(path: str) -> list:
    """Return list of error strings; empty list means valid."""
    errors = []
    basename = os.path.basename(path)
    ext = os.path.splitext(basename)[1].lower()

    if ext not in (".yaml", ".csv"):
        errors.append(
            f"Extension `{ext}` is not supported — use `.yaml` or `.csv`"
        )
        return errors

    if not FILENAME_RE.match(basename):
        errors.append(
            f"Filename `{basename}` does not match naming convention "
            f"`<accession>_<INITIALS>_<n>.yaml` — "
            f"initials must be 2–6 uppercase letters (A-Z only, no digits or lowercase). "
            f"Example: `E-MTAB-1234_GF_1.yaml`"
        )
    return errors


def extract_base_stem(path: str) -> str:
    """Strip any score postfix and return base stem (e.g. 'E-MTAB-1234_CH_1')."""
    basename = os.path.basename(path)
    m = SCORED_SUFFIX_RE.match(basename)
    if m:
        return m.group(1)
    return os.path.splitext(basename)[0]


def extract_initials_from_filename(path: str) -> str | None:
    """Return reviewer initials from filename (penultimate underscore segment)."""
    stem = extract_base_stem(path)
    parts = stem.rsplit("_", 2)
    if len(parts) >= 2:
        candidate = parts[-2]
        if re.match(r"^[A-Z]{1,6}$", candidate):
            return candidate
    return None


# ── YAML parsing & validation ─────────────────────────────────────────────────

def parse_yaml(path: str) -> tuple:
    """Return (data_dict, errors). data_dict is None on parse failure."""
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            return None, ["File does not contain a YAML mapping at the top level"]
        return data, []
    except yaml.YAMLError as exc:
        return None, [f"YAML parse error: {exc}"]
    except OSError as exc:
        return None, [f"Cannot read file: {exc}"]


def validate_content(data: dict, filename_initials: str | None, question_meta: dict) -> list:
    """Validate parsed review data (works for both YAML and normalised CSV)."""
    errors = []

    # schema_version
    sv = data.get("schema_version")
    if sv is None:
        errors.append("`schema_version` field is missing")
    elif str(sv) != SCHEMA_VERSION:
        errors.append(
            f"`schema_version` must be `\"{SCHEMA_VERSION}\"` (string, not float) — got `{sv!r}`"
        )

    # reviewer block
    reviewer = data.get("reviewer")
    if not isinstance(reviewer, dict):
        errors.append("`reviewer` block is missing or malformed")
    else:
        for field in ("name", "initials", "affiliation", "review_date"):
            v = reviewer.get(field)
            if not v or not str(v).strip():
                errors.append(f"`reviewer.{field}`: required field is empty")

        initials = str(reviewer.get("initials") or "").strip()
        if initials and not re.match(r"^[A-Z]{1,6}$", initials):
            errors.append(
                f"`reviewer.initials`: `{initials}` — must be uppercase letters only (A-Z), 1–6 chars"
            )
        if initials and filename_initials and initials != filename_initials:
            errors.append(
                f"`reviewer.initials` (`{initials}`) does not match initials in filename (`{filename_initials}`)"
            )

        rd = str(reviewer.get("review_date") or "").strip()
        if rd:
            _validate_date(rd, "reviewer.review_date", errors)

    # dataset block
    dataset = data.get("dataset")
    if not isinstance(dataset, dict):
        errors.append("`dataset` block is missing or malformed")
    else:
        for field in ("name", "url", "hosting_resource"):
            v = dataset.get(field)
            if not v or not str(v).strip():
                errors.append(f"`dataset.{field}`: required field is empty")
        url = str(dataset.get("url") or "").strip()
        if url and not url.startswith(("http://", "https://")):
            errors.append(
                f"`dataset.url`: must start with `http://` or `https://` — got `{url}` "
                f"(hint: add `https://` at the beginning)"
            )

    # answers block
    answers = data.get("answers")
    if not isinstance(answers, dict):
        errors.append("`answers` block is missing or malformed")
        return errors

    missing_ids = [qid for qid in ALL_QUESTION_IDS if qid not in answers]
    if missing_ids:
        errors.append(f"Missing question block(s): {', '.join(missing_ids)}")

    for qid in ALL_QUESTION_IDS:
        if qid not in answers:
            continue
        ans_block = answers[qid]
        if not isinstance(ans_block, dict):
            errors.append(f"`answers.{qid}`: expected a mapping, got `{ans_block!r}`")
            continue

        answer = ans_block.get("answer")
        if isinstance(answer, bool):
            errors.append(
                f"`answers.{qid}.answer`: got YAML boolean `{answer}` — "
                f"wrap in quotes: `answer: \"{'Yes' if answer else 'No'}\"`"
            )
        elif answer not in ("Yes", "No"):
            errors.append(
                f"`answers.{qid}.answer`: `{answer!r}` — must be exactly `\"Yes\"` or `\"No\"` "
                f"(case-sensitive, quoted string)"
            )

        if qid in ETHICS_QUESTIONS:
            na = ans_block.get("not_applicable")
            if not isinstance(na, bool):
                errors.append(
                    f"`answers.{qid}.not_applicable`: must be boolean `true` or `false` — got `{na!r}`"
                )

    # result block must exist (values can be null — will be filled in)
    if "result" not in data:
        errors.append(
            "`result` block is missing — add these lines at the end of your file:\n"
            "  result:\n    weighted_score: null\n    grade: \"\""
        )

    return errors


def _validate_date(value: str, field: str, errors: list) -> None:
    if not DATE_RE.match(value):
        errors.append(
            f"`{field}`: `{value}` does not match YYYY-MM-DD format "
            f"(use zero-padded month and day, e.g. `2025-06-01`)"
        )
        return
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
        if parsed.year < 2024:
            errors.append(
                f"`{field}`: `{value}` is before 2024 — check if this is correct"
            )
    except ValueError:
        errors.append(f"`{field}`: `{value}` is not a valid calendar date")


# ── CSV parsing ───────────────────────────────────────────────────────────────

def parse_csv(path: str) -> tuple:
    """Parse a CSV review file into the same dict structure as YAML."""
    try:
        with open(path, newline="", encoding="utf-8") as f:
            raw = f.read()
    except OSError as exc:
        return None, [f"Cannot read file: {exc}"]

    reader = csv.reader(io.StringIO(raw))
    rows = list(reader)

    # Section A: row 0 is "field,value" header, rows 1-11 are data pairs
    section_a: dict = {}
    for row in rows[1:12]:
        if len(row) >= 1 and row[0].strip():
            section_a[row[0].strip()] = row[1].strip() if len(row) > 1 else ""

    # Find Section B header row (first cell == "question_id")
    header_row_idx = None
    for i, row in enumerate(rows):
        if row and row[0].strip() == "question_id":
            header_row_idx = i
            break

    if header_row_idx is None:
        return None, [
            "CSV Section B header row not found — expected a row starting with `question_id`"
        ]

    header = [h.strip() for h in rows[header_row_idx]]
    answers: dict = {}
    for row in rows[header_row_idx + 1:]:
        if not row or not row[0].strip():
            continue
        row_dict = {header[i]: row[i].strip() if i < len(row) else "" for i in range(len(header))}
        qid = row_dict.get("question_id", "").strip()
        if not qid:
            continue
        answers[qid] = {
            "answer": row_dict.get("answer", ""),
            "comments": row_dict.get("comments", ""),
            "not_applicable": _parse_csv_bool(row_dict.get("not_applicable", "FALSE")),
        }

    data = {
        "schema_version": section_a.get("schema_version", ""),
        "reviewer": {
            "name": section_a.get("reviewer_name", ""),
            "initials": section_a.get("reviewer_initials", ""),
            "orcid": section_a.get("reviewer_orcid", ""),
            "affiliation": section_a.get("reviewer_affiliation", ""),
            "review_date": section_a.get("review_date", ""),
        },
        "dataset": {
            "name": section_a.get("dataset_name", ""),
            "url": section_a.get("dataset_url", ""),
            "hosting_resource": section_a.get("hosting_resource", ""),
            "accession": section_a.get("dataset_accession", ""),
            "comments": "",
        },
        "process_comments": section_a.get("process_comments", ""),
        "answers": answers,
        "result": {"weighted_score": None, "grade": ""},
    }
    return data, []


def _parse_csv_bool(value: str) -> bool:
    return str(value).strip().upper() == "TRUE"


# ── Scoring ───────────────────────────────────────────────────────────────────

def score_review(answers: dict, question_meta: dict, grading: list) -> tuple:
    """Return (weighted_score: int, grade: str).

    Grades identically to the auto-airbds frontend: the dataset earns the
    highest grade for which the proportion of "Yes" answers in every grade tier
    is at least the tier minimum AND the total weighted score is at least the
    grade's min_score. Proportions use the metric's full per-tier question
    counts as denominators, so a missing answer counts against the proportion.
    """
    total_by_tier: dict = {}
    yes_by_tier: dict = {}
    score = 0

    for qid, qm in question_meta.items():
        tier = qm["weight"]
        total_by_tier[tier] = total_by_tier.get(tier, 0) + 1
        if answers.get(qid, {}).get("answer") == "Yes":
            yes_by_tier[tier] = yes_by_tier.get(tier, 0) + 1
            score += qm.get("weight_points", 0)

    def proportion(tier: str) -> float:
        total = total_by_tier.get(tier, 0)
        # A tier with no questions imposes no constraint.
        return 1.0 if total == 0 else yes_by_tier.get(tier, 0) / total

    grade = ""
    for g in grading:
        proportions_met = all(
            proportion(tier) >= minimum
            for tier, minimum in g["min_proportion_yes"].items()
        )
        if proportions_met and score >= g["min_score"]:
            grade = g["name"]
            break

    return score, grade


# ── File writing ──────────────────────────────────────────────────────────────

def write_yaml(path: str, data: dict) -> None:
    """Write review data as YAML, ensuring answer strings are quoted."""
    out: dict = {
        "schema_version": data.get("schema_version", SCHEMA_VERSION),
        "reviewer": data.get("reviewer", {}),
        "dataset": data.get("dataset", {}),
        "process_comments": data.get("process_comments", ""),
        "answers": {},
        "result": data.get("result", {"weighted_score": None, "grade": ""}),
    }

    for qid in ALL_QUESTION_IDS:
        ans = (data.get("answers") or {}).get(qid, {})
        entry: dict = {
            "answer": ans.get("answer", ""),
            "comments": ans.get("comments", ""),
        }
        if qid in ETHICS_QUESTIONS:
            entry["not_applicable"] = bool(ans.get("not_applicable", False))
        out["answers"][qid] = entry

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Review — AIRBDS AI-Readiness Dataset Scoring Metric v{SCHEMA_VERSION}\n")
        f.write("# Auto-processed by AIRBDS Review Processor\n\n")
        yaml.dump(out, f, Dumper=ReviewDumper, default_flow_style=False,
                  allow_unicode=True, sort_keys=False)


def write_csv(path: str, data: dict, question_meta: dict) -> None:
    """Write review data as CSV matching review_template.csv layout."""
    reviewer = data.get("reviewer") or {}
    dataset = data.get("dataset") or {}
    result = data.get("result") or {}
    answers = data.get("answers") or {}

    rows = [
        ["field", "value"],
        ["schema_version", data.get("schema_version", SCHEMA_VERSION)],
        ["reviewer_name", reviewer.get("name", "")],
        ["reviewer_initials", reviewer.get("initials", "")],
        ["reviewer_orcid", reviewer.get("orcid", "")],
        ["reviewer_affiliation", reviewer.get("affiliation", "")],
        ["review_date", reviewer.get("review_date", "")],
        ["dataset_name", dataset.get("name", "")],
        ["dataset_url", dataset.get("url", "")],
        ["dataset_accession", dataset.get("accession", "")],
        ["hosting_resource", dataset.get("hosting_resource", "")],
        ["process_comments", data.get("process_comments", "")],
        ["weighted_score", result.get("weighted_score", "")],
        ["grade", result.get("grade", "")],
        [],  # blank separator row
        ["question_id", "scope", "theme", "weight", "question", "guidance",
         "answer", "not_applicable", "comments"],
    ]

    for qid in ALL_QUESTION_IDS:
        qm = question_meta.get(qid, {})
        ans = answers.get(qid, {})
        na_val = bool(ans.get("not_applicable", False))
        rows.append([
            qid,
            qm.get("scope", ""),
            qm.get("theme", ""),
            qm.get("weight", ""),
            qm.get("question", ""),
            qm.get("guidance", ""),
            ans.get("answer", ""),
            "TRUE" if na_val else "FALSE",
            ans.get("comments", ""),
        ])

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


# ── Rename helper ─────────────────────────────────────────────────────────────

def compute_scored_path(path: str, score: int, grade: str) -> str:
    """Return path with score+grade postfix inserted before extension."""
    dirpath = os.path.dirname(path)
    basename = os.path.basename(path)
    m = SCORED_SUFFIX_RE.match(basename)
    if m:
        stem = m.group(1)
        ext = "." + m.group(3)
    else:
        stem, ext = os.path.splitext(basename)
    new_name = f"{stem}_{score}_{grade}{ext}"
    return os.path.join(dirpath, new_name) if dirpath else new_name


# ── File grouping ──────────────────────────────────────────────────────────────

def group_by_stem(file_list: list) -> dict:
    """Group file paths by their base stem (directory + name without score/ext).

    Returns {stem_key: {"yaml": path, "csv": path}} — either key may be absent.
    """
    groups: dict = {}
    for fpath in file_list:
        basename = os.path.basename(fpath)
        dirpath = os.path.dirname(fpath)
        m = SCORED_SUFFIX_RE.match(basename)
        if m:
            stem = m.group(1)
            ext = m.group(3)
        else:
            root, ext_with_dot = os.path.splitext(basename)
            stem = root
            ext = ext_with_dot.lstrip(".")

        key = os.path.join(dirpath, stem) if dirpath else stem
        if key not in groups:
            groups[key] = {}
        groups[key][ext] = fpath
    return groups


# ── Compliance check ──────────────────────────────────────────────────────────


def is_already_compliant(path: str) -> tuple:
    """Return (compliant, score, grade) if the file is already fully scored.

    A file is compliant when:
    1. Its filename already contains score AND grade components
       (matches FULL_SCORED_FILENAME_RE).
    2. The internal result.weighted_score matches the filename score.

    Returns (False, None, None) if either condition fails or if the file
    cannot be parsed, allowing normal processing to proceed.
    """
    basename = os.path.basename(path)
    m = FULL_SCORED_FILENAME_RE.match(basename)
    if not m:
        return False, None, None

    try:
        filename_score = int(m.group(2))
    except (ValueError, IndexError):
        return False, None, None

    filename_grade = m.group(3)
    ext = m.group(4)

    try:
        if ext == "yaml":
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                return False, None, None
            result_block = data.get("result")
            if not isinstance(result_block, dict):
                return False, None, None
            internal_score = result_block.get("weighted_score")
            if internal_score is None:
                return False, None, None
            if int(internal_score) == filename_score:
                return True, filename_score, filename_grade
            return False, None, None

        else:  # csv
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2 and row[0].strip() == "weighted_score":
                        try:
                            internal_score = int(row[1].strip())
                        except ValueError:
                            return False, None, None
                        if internal_score == filename_score:
                            return True, filename_score, filename_grade
                        return False, None, None
            return False, None, None

    except Exception:
        return False, None, None


# ── GitHub helpers ─────────────────────────────────────────────────────────────

def emit_annotation(path: str, message: str) -> None:
    safe = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    print(f"::error file={path},line=1::{safe}", flush=True)


def write_step_summary(results: list) -> None:
    lines = ["## AIRBDS Review Processor\n"]
    lines.append("| File | Status | Score | Grade | Notes |")
    lines.append("|------|--------|-------|-------|-------|")

    error_sections = []
    for r in results:
        fname = os.path.basename(r["path"])
        if r["status"] == "pass":
            status = "✅ Pass"
        elif r["status"] == "skip":
            status = "⏭ Skip"
        else:
            status = "❌ Fail"
        score = str(r["score"]) if r["score"] is not None else "—"
        grade = r["grade"] or "—"
        notes = "; ".join(r["notes"]) if r["notes"] else ""
        lines.append(f"| `{fname}` | {status} | {score} | {grade} | {notes} |")

        if r["errors"]:
            section = [f"\n### Errors in `{r['path']}`"]
            for err in r["errors"]:
                section.append(f"- {err}")
            error_sections.append("\n".join(section))

    lines.append("")
    lines.extend(error_sections)
    summary = "\n".join(lines) + "\n"

    print(summary)

    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as f:
            f.write(summary)


def write_outputs(has_changes: bool, has_errors: bool) -> None:
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"has_changes={str(has_changes).lower()}\n")
            f.write(f"has_errors={str(has_errors).lower()}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Validate, convert, and score AIRBDS review files.")
    parser.add_argument("--files", required=True,
                        help="Path to a text file listing review paths (one per line)")
    parser.add_argument("--metric", required=True,
                        help="Path to airbds_metric_v0.3.yaml")
    args = parser.parse_args()

    question_meta = load_metric(args.metric)
    grading = load_grading(args.metric)

    if not os.path.exists(args.files):
        write_outputs(False, False)
        sys.exit(0)

    with open(args.files, encoding="utf-8") as f:
        raw_paths = [line.strip() for line in f if line.strip()]

    # Exclude anything under reviews/examples/ from automated scoring
    # (examples are reference fixtures, not real submissions)
    file_list = [p for p in raw_paths if "reviews/examples" not in p.replace("\\", "/")]

    if not file_list:
        write_outputs(False, False)
        sys.exit(0)

    groups = group_by_stem(file_list)
    results = []
    has_changes = False
    has_errors = False

    for stem_key, formats in groups.items():
        # YAML is authoritative when both formats changed simultaneously
        if "yaml" in formats:
            primary_path = formats["yaml"]
            primary_fmt = "yaml"
        else:
            primary_path = formats["csv"]
            primary_fmt = "csv"

        # 0. Compliance shortcut — skip files that are already fully scored.
        # A file is compliant if its filename has the score+grade suffix AND
        # the internal result.weighted_score matches the filename score.
        # Skipped files do not set has_changes, so no auto-commit occurs.
        compliant, c_score, c_grade = is_already_compliant(primary_path)
        if compliant:
            print(f"[skip] already compliant: {os.path.basename(primary_path)}", flush=True)
            results.append({
                "path": primary_path,
                "fmt": primary_fmt,
                "status": "skip",
                "score": c_score,
                "grade": c_grade,
                "errors": [],
                "notes": ["Already compliant — skipped"],
            })
            continue

        result: dict = {
            "path": primary_path,
            "fmt": primary_fmt,
            "status": "fail",
            "score": None,
            "grade": None,
            "errors": [],
            "notes": [],
        }

        # 1. Filename validation
        fn_errors = validate_filename(primary_path)
        if fn_errors:
            result["errors"].extend(fn_errors)
            results.append(result)
            has_errors = True
            for e in fn_errors:
                emit_annotation(primary_path, e)
            continue

        filename_initials = extract_initials_from_filename(primary_path)

        # 2. Parse
        if primary_fmt == "yaml":
            data, parse_errors = parse_yaml(primary_path)
        else:
            data, parse_errors = parse_csv(primary_path)

        if parse_errors:
            result["errors"].extend(parse_errors)
            results.append(result)
            has_errors = True
            for e in parse_errors:
                emit_annotation(primary_path, e)
            continue

        # 3. Content validation
        content_errors = validate_content(data, filename_initials, question_meta)
        if content_errors:
            result["errors"].extend(content_errors)
            results.append(result)
            has_errors = True
            for e in content_errors:
                emit_annotation(primary_path, e)
            continue

        # 4. Score
        score, grade = score_review(data["answers"], question_meta, grading)
        data["result"] = {"weighted_score": score, "grade": grade}
        result["score"] = score
        result["grade"] = grade
        result["status"] = "pass"

        # 5. Write primary file at scored path
        scored_primary = compute_scored_path(primary_path, score, grade)
        if primary_fmt == "yaml":
            write_yaml(scored_primary, data)
        else:
            write_csv(scored_primary, data, question_meta)

        if os.path.abspath(primary_path) != os.path.abspath(scored_primary):
            os.remove(primary_path)
            result["notes"].append(f"Renamed → `{os.path.basename(scored_primary)}`")

        # 6. Generate companion format at scored path
        dirpath = os.path.dirname(scored_primary)
        scored_stem = os.path.splitext(os.path.basename(scored_primary))[0]
        companion_ext = "csv" if primary_fmt == "yaml" else "yaml"
        companion_path = (
            os.path.join(dirpath, f"{scored_stem}.{companion_ext}")
            if dirpath else f"{scored_stem}.{companion_ext}"
        )

        if companion_ext == "csv":
            write_csv(companion_path, data, question_meta)
        else:
            write_yaml(companion_path, data)

        companion_existed = companion_ext in formats
        result["notes"].append(
            f"{'Updated' if companion_existed else 'Generated'} {companion_ext.upper()} companion"
        )

        # Remove old unscored companion if a different path existed
        old_companion = formats.get(companion_ext)
        if old_companion and os.path.abspath(old_companion) != os.path.abspath(companion_path):
            if os.path.exists(old_companion):
                os.remove(old_companion)

        result["path"] = scored_primary
        results.append(result)
        has_changes = True

    write_step_summary(results)
    write_outputs(has_changes, has_errors)
    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
