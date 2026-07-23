#!/usr/bin/env python3
"""Generate the blank review template pair from a canonical metric YAML.

`reviews/review_template.{yaml,csv}` are the blank forms a reviewer fills in.
They must list exactly the current metric's questions (ids, scopes, weights,
text, guidance) and carry a `not_applicable` slot for each Ethics question.
Hand-maintaining two parallel files invites silent drift, so this script derives
both from `metric/airbds_metric_v<version>.yaml` — the single source of truth —
guaranteeing the YAML and CSV always agree.

It reuses the review processor's `load_metric_profile` so the question metadata
(order, scope, weight, ethics flags, text, guidance) is read exactly as the
scorer reads it.

Usage:
    # Regenerate reviews/review_template.{yaml,csv} for the current metric
    python3 reviews/src/scripts/build_review_template.py --version 0.5

    # Verify the committed pair still matches the metric (suitable for CI)
    python3 reviews/src/scripts/build_review_template.py --version 0.5 --check

Exit codes:
    0 — wrote the files (default), or --check found both already in sync
    1 — --check found a committed file differs from the metric
"""

import argparse
import csv
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from review_processor import (  # noqa: E402  (sibling module, after sys.path tweak)
    CSV_SECTION_A_FIELDS,
    load_metric_profile,
)

# Repo root is four levels up: <root>/reviews/src/scripts/<this file>.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_METRIC_DIR = REPO_ROOT / "metric"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "reviews"

# Reviewer/dataset field comments, mirrored from the established template.
REVIEWER_COMMENTS = {
    "name": "# Full name",
    "initials": "# e.g. GF",
    "orcid": "# e.g. 0000-0000-0000-0000",
    "review_date": "# ISO 8601, e.g. 2025-01-15",
}

ETHICS_NOTE = '# Ethics questions — answer "Yes" if dataset has no human/animal subjects'


def _yaml_header(version: str) -> list[str]:
    return [
        f"# Review template — AIRBDS AI-Readiness Dataset Scoring Metric v{version}",
        '# Fill in all fields. For each question, set answer to "Yes" or "No".',
        f"# This YAML lists answer slots by question id; see airbds_metric_v{version}.yaml (or",
        "# review_template.csv) for the full question text and guidance. Generic",
        f"# reviewer instructions are in that metric's `instructions:` block.",
        "# See reviews/GUIDANCE.md and the metric YAML's grading block for grading details.",
        "#",
        "# Scoring is NOT automated: automated scoring on pull request is disabled. Score",
        "# the completed file yourself with:",
        "#   python3 reviews/src/scripts/review_processor.py --files <file-list>",
        "# This validates the review, fills in the result block, and renames the file.",
        "# To submit, open a PR at https://github.com/AIBIO-UK/airbds-dev",
    ]


def _pad_slot(inline: str, comment: str) -> str:
    """Right-pad an inline value so its trailing comment aligns at column 22."""
    return f"{inline}{comment}" if not comment else f"{inline.ljust(22)}{comment}"


def render_yaml(profile: dict, version: str) -> str:
    out = _yaml_header(version)
    out.append("")
    out.append(f'schema_version: "{version}"')
    out.append("")

    out.append("reviewer:")
    for field in ("name", "initials", "orcid", "affiliation", "review_date"):
        out.append(_pad_slot(f'  {field}: ""', REVIEWER_COMMENTS.get(field, "")))
    out.append("")

    out.append("dataset:")
    for field in ("name", "url", "hosting_resource", "accession", "comments"):
        out.append(f'  {field}: ""')
    out.append("")

    out.append('process_comments: ""')
    out.append("")

    out.append("answers:")
    ethics_ids = profile["ethics_ids"]
    first_ethics_seen = False
    for qid in profile["question_ids"]:
        if qid in ethics_ids and not first_ethics_seen:
            out.append(f"  {ETHICS_NOTE}")
            first_ethics_seen = True
        if qid in ethics_ids:
            out.append(f'  {qid}: {{ answer: "", comments: "", not_applicable: false }}')
        else:
            out.append(f'  {qid}: {{ answer: "", comments: "" }}')
    out.append("")

    out.append("# Calculated fields — complete after scoring")
    out.append("result:")
    out.append("  weighted_score: null")
    out.append('  grade: ""   # Caution / Bronze / Silver / Gold')
    return "\n".join(out) + "\n"


def render_csv(profile: dict) -> str:
    question_meta = profile["question_meta"]
    has_theme = profile["has_theme"]

    rows = [["field", "value"]]
    for field in CSV_SECTION_A_FIELDS:
        rows.append([field, profile["schema_version"] if field == "schema_version" else ""])
    rows.append([])  # blank separator row

    header = ["question_id", "scope"]
    if has_theme:
        header.append("theme")
    header += ["weight", "question", "guidance", "answer", "not_applicable", "comments"]
    rows.append(header)

    for qid in profile["question_ids"]:
        qm = question_meta.get(qid, {})
        row = [qid, qm.get("scope", "")]
        if has_theme:
            row.append(qm.get("theme") or "")
        row += [
            qm.get("weight", ""),
            qm.get("question", ""),
            qm.get("guidance", ""),
            "",        # answer (blank)
            "FALSE",   # not_applicable
            "",        # comments (blank)
        ]
        rows.append(row)

    buf = io.StringIO()
    # LF line endings: the blank template uses LF (the processor's write_csv
    # emits CRLF for processed reviews, but the committed template is LF).
    csv.writer(buf, lineterminator="\n").writerows(rows)
    return buf.getvalue()


def main() -> None:
    ap = argparse.ArgumentParser(description="Build the blank review template pair from the metric YAML.")
    ap.add_argument("--version", required=True, help="metric version to build for, e.g. 0.5")
    ap.add_argument("--metric-dir", type=Path, default=DEFAULT_METRIC_DIR, help="dir holding airbds_metric_v<version>.yaml")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="dir to write review_template.{yaml,csv}")
    ap.add_argument("--check", action="store_true",
                    help="do not write; exit 1 if a committed file differs from the metric")
    args = ap.parse_args()

    metric_path = args.metric_dir / f"airbds_metric_v{args.version}.yaml"
    if not metric_path.exists():
        sys.exit(f"ERROR: metric not found: {metric_path}")
    profile = load_metric_profile(str(metric_path))
    if profile["schema_version"] != args.version:
        sys.exit(f"ERROR: {metric_path} has schema_version {profile['schema_version']!r}, "
                 f"expected {args.version!r}")

    yaml_text = render_yaml(profile, args.version)
    csv_text = render_csv(profile)
    targets = {
        args.output_dir / "review_template.yaml": yaml_text,
        args.output_dir / "review_template.csv": csv_text,
    }

    if args.check:
        drifted = [p for p, text in targets.items()
                   if (p.read_text(encoding="utf-8") if p.exists() else "") != text]
        if not drifted:
            print(f"OK: review_template.{{yaml,csv}} are in sync with {metric_path.name} "
                  f"({len(profile['question_ids'])} questions)")
            sys.exit(0)
        for p in drifted:
            print(f"DRIFT: {p} differs from {metric_path.name}.", file=sys.stderr)
        print(f"Regenerate with: python3 reviews/src/scripts/build_review_template.py "
              f"--version {args.version}", file=sys.stderr)
        sys.exit(1)

    for p, text in targets.items():
        p.write_text(text, encoding="utf-8")
        print(f"Wrote: {p}")
    print(f"{len(profile['question_ids'])} questions "
          f"({len(profile['ethics_ids'])} ethics) from {metric_path.name}")


if __name__ == "__main__":
    main()
