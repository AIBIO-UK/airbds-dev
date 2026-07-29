#!/usr/bin/env python3
"""AIRBDS scoring — the single implementation of "answers in, score and grade out".

Two callers share this module:

  * `review_processor.py` imports `score_review` (and `WEIGHT_POINTS`) after
    loading a metric from YAML. It is the authority for committed review files.
  * The assessment skill runs this file as a script, against the metric JSON
    bundled beside it, to score an assessment the model has just produced.

The two paths must agree, so the scoring lives here once rather than being
restated in the skill's instructions. That is the whole point: a model asked to
sum weighted points and evaluate four grading thresholds by hand may get it
wrong, quietly, and weaker models more often. Here the arithmetic is fixed.

This module imports **only the standard library** — deliberately. The skill runs
wherever the user's assistant runs, and PyYAML cannot be assumed there, so the
skill-facing path reads `airbds_metric.json` (generated beside the canonical
YAML by the metric build script) rather than the YAML itself.

Usage as a script:

    # answers.json maps every question id to exactly "Yes" or "No":
    #   {"ABC-01": "Yes", "ABC-02": "No", ...}
    python3 score.py answers.json
    cat answers.json | python3 score.py -

    # In an environment with no shell, import it instead:
    #   import score; print(score.score_from_files("answers.json"))

The metric defaults to the bundled `assets/airbds_metric.json` (the skill puts
executables in `scripts/` and data in `assets/`); override with --metric.

Exit codes:
    0 — scored; the result is on stdout as JSON
    1 — the answers failed validation; the problems are in `errors` on stdout
    2 — the metric file could not be read
"""

import argparse
import json
import sys
from pathlib import Path

# Fallback grade points, used only if a metric omits grade_points for a grade.
WEIGHT_POINTS = {"Critical": 80, "Important": 5, "Optional": 2}

VALID_ANSWERS = ("Yes", "No")


# ── Scoring ───────────────────────────────────────────────────────────────────

def score_review(answers: dict, question_meta: dict, grading: list) -> tuple:
    """Return (weighted_score: int, grade: str).

    Grades identically to the auto-airbds frontend: the dataset earns the
    highest grade for which the proportion of "Yes" answers in every grade tier
    is at least the tier minimum AND the total weighted score is at least the
    grade's min_score. Proportions use the metric's full per-tier question
    counts as denominators, so a missing answer counts against the proportion.
    """
    score = 0
    for qid, qm in question_meta.items():
        if answers.get(qid, {}).get("answer") == "Yes":
            score += qm.get("weight_points", 0)

    proportions = tier_proportions(answers, question_meta)

    grade = ""
    for g in grading:
        proportions_met = all(
            proportions.get(tier, {}).get("proportion", 1.0) >= minimum
            for tier, minimum in g["min_proportion_yes"].items()
        )
        if proportions_met and score >= g["min_score"]:
            grade = g["name"]
            break

    return score, grade


def tier_proportions(answers: dict, question_meta: dict) -> dict:
    """Return {tier: {"yes": n, "total": n, "proportion": float}}.

    Split out of `score_review` because the skill reports these alongside the
    grade: with the counts in front of it the model can say *why* a grade was
    missed without recomputing anything. A tier with no questions imposes no
    constraint, so its proportion is 1.0.
    """
    totals: dict = {}
    yeses: dict = {}
    for qid, qm in question_meta.items():
        tier = qm["weight"]
        totals[tier] = totals.get(tier, 0) + 1
        if answers.get(qid, {}).get("answer") == "Yes":
            yeses[tier] = yeses.get(tier, 0) + 1

    return {
        tier: {
            "yes": yeses.get(tier, 0),
            "total": total,
            "proportion": 1.0 if total == 0 else yeses.get(tier, 0) / total,
        }
        for tier, total in totals.items()
    }


# ── Metric loading (JSON — the YAML path lives in review_processor.py) ────────

def load_metric_profile_json(metric_path) -> dict:
    """Load the scoring facts from a metric JSON file.

    Returns the same `question_meta` / `grading` shapes `review_processor.py`'s
    `load_metric_profile` builds from the YAML, so `score_review` is fed
    identical input by both callers.
    """
    data = json.loads(Path(metric_path).read_text(encoding="utf-8"))
    grade_points = data.get("grade_points", {})

    question_meta = {}
    for qid, q in (data.get("questions") or {}).items():
        grade = q["grade"]
        question_meta[qid] = {
            "weight": grade,
            "weight_points": grade_points.get(grade, WEIGHT_POINTS.get(grade, 0)),
        }

    grading = [
        {
            "name": entry["name"],
            "min_proportion_yes": dict(entry.get("min_proportion_yes", {})),
            "min_score": entry.get("min_score", 0),
        }
        for entry in data.get("grading", [])
    ]

    return {
        "schema_version": str(data.get("schema_version", "")).strip(),
        "question_meta": question_meta,
        "grading": grading,
    }


# ── Answer validation ─────────────────────────────────────────────────────────

def validate_answers(raw: dict, question_meta: dict) -> list:
    """Return a list of problems with a flat {qid: "Yes"|"No"} mapping.

    The model still has to transcribe its own judgements into this file, so this
    is where the remaining risk sits. Refusing to score a set that is missing a
    question is deliberate: silently treating it as unanswered would understate
    the tier proportion and could hand back a lower grade that looks legitimate.
    """
    errors = []
    if not isinstance(raw, dict):
        return ["answers must be a JSON object mapping question id to \"Yes\" or \"No\""]

    expected = set(question_meta)
    given = set(raw)

    for qid in sorted(expected - given):
        errors.append(f"{qid}: missing — every question in the metric must be answered")
    for qid in sorted(given - expected):
        errors.append(f"{qid}: not a question in this metric version")
    for qid in sorted(given & expected):
        if raw[qid] not in VALID_ANSWERS:
            errors.append(
                f"{qid}: {raw[qid]!r} is not a valid answer — use exactly \"Yes\" or \"No\""
            )
    return errors


# ── Script entry point ────────────────────────────────────────────────────────

def default_metric_path() -> Path:
    """Locate the bundled metric JSON.

    In a skill bundle the executable lives in `scripts/` and its data in
    `assets/`, so `../assets/` is the normal case; alongside is checked first so
    the module still works if the two are kept together.

    Deliberately not `resolve()`d. In the repo this file is reached through
    `skills/*/airbds-assessment-skill/scripts/score.py`, a symlink; resolving it
    would search next to the *source* file rather than next to the symlink, so
    the skill could not be tested from a checkout. Callers running the module
    from its source location should pass --metric.
    """
    here = Path(__file__).parent
    for candidate in (here / "airbds_metric.json",
                      here.parent / "assets" / "airbds_metric.json"):
        if candidate.exists():
            return candidate
    return here.parent / "assets" / "airbds_metric.json"


def score_from_files(answers_path, metric_path=None) -> dict:
    """Score an answers file against a metric JSON; return the result payload.

    Importable for environments that can run Python but have no shell.
    """
    profile = load_metric_profile_json(metric_path or default_metric_path())
    text = sys.stdin.read() if str(answers_path) == "-" else Path(answers_path).read_text(encoding="utf-8")
    return score_payload(json.loads(text), profile)


def score_payload(raw_answers: dict, profile: dict) -> dict:
    """Build the result payload from raw flat answers and a loaded profile."""
    question_meta = profile["question_meta"]
    errors = validate_answers(raw_answers, question_meta)
    if errors:
        return {"schema_version": profile["schema_version"], "errors": errors}

    # score_review takes the review-file shape ({qid: {"answer": ...}}), which is
    # what review_processor.py passes; the skill's flat mapping is adapted here.
    answers = {qid: {"answer": value} for qid, value in raw_answers.items()}
    score, grade = score_review(answers, question_meta, profile["grading"])

    return {
        "schema_version": profile["schema_version"],
        "final_score": score,
        "grade": grade,
        "tiers": {
            tier: {
                "yes": t["yes"],
                "total": t["total"],
                "proportion": round(t["proportion"], 4),
            }
            for tier, t in tier_proportions(answers, question_meta).items()
        },
        "errors": [],
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Score AIRBDS assessment answers against the metric.",
        epilog='answers file: {"ABC-01": "Yes", "ABC-02": "No", ...} — every question id, '
               'answered exactly "Yes" or "No". Use - to read it from stdin.',
    )
    ap.add_argument("answers", help='path to the answers JSON, or - for stdin')
    ap.add_argument("--metric", type=Path, default=None,
                    help="metric JSON (default: airbds_metric.json beside this script)")
    args = ap.parse_args()

    metric_path = args.metric or default_metric_path()
    try:
        profile = load_metric_profile_json(metric_path)
    except (OSError, ValueError) as e:
        print(f"ERROR: could not read the metric at {metric_path}: {e}", file=sys.stderr)
        print("Score the assessment manually using the rules in SKILL.md.", file=sys.stderr)
        return 2

    try:
        text = sys.stdin.read() if args.answers == "-" else Path(args.answers).read_text(encoding="utf-8")
        raw_answers = json.loads(text)
    except (OSError, ValueError) as e:
        print(json.dumps({"schema_version": profile["schema_version"],
                          "errors": [f"could not read the answers: {e}"]}, indent=2))
        return 1

    result = score_payload(raw_answers, profile)
    print(json.dumps(result, indent=2))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
