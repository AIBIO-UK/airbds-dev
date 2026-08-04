#!/usr/bin/env python3
"""Tests for airbds_scoring.py — the shared scorer.

These run against the committed v1.0.0 metric, so they exercise the real grading
thresholds rather than a fixture's. The parity test is the important one: it
asserts the JSON path (what the assessment skill runs) and the YAML path (what
review_processor.py runs on submitted reviews) produce identical results, which
is the property that lets the skill's score be trusted.

Run under pytest:
    pytest reviews/src/tests/test_airbds_scoring.py
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "reviews" / "src" / "scripts"
METRIC_JSON = REPO_ROOT / "metric" / "airbds_metric_v1.0.0.json"
METRIC_YAML = REPO_ROOT / "metric" / "airbds_metric_v1.0.0.yaml"
SCORE_PY = SCRIPTS_DIR / "airbds_scoring.py"

sys.path.insert(0, str(SCRIPTS_DIR))
import airbds_scoring as scoring  # noqa: E402


@pytest.fixture(scope="module")
def profile():
    return scoring.load_metric_profile_json(METRIC_JSON)


@pytest.fixture(scope="module")
def metric():
    return json.loads(METRIC_JSON.read_text(encoding="utf-8"))


def answers_all(metric, value="Yes"):
    return {qid: value for qid in metric["questions"]}


def ids_with_grade(metric, grade):
    return [q for q, v in metric["questions"].items() if v["grade"] == grade]


# ── Scoring and grading ───────────────────────────────────────────────────────

def test_all_yes_scores_every_point_and_earns_gold(metric, profile):
    result = scoring.score_payload(answers_all(metric), profile)
    expected = sum(
        metric["grade_points"][q["grade"]] for q in metric["questions"].values()
    )
    assert result["final_score"] == expected
    assert result["grade"] == "Gold"
    assert result["errors"] == []


def test_all_no_scores_zero_and_falls_to_caution(metric, profile):
    result = scoring.score_payload(answers_all(metric, "No"), profile)
    assert result["final_score"] == 0
    assert result["grade"] == "Caution"


def test_a_no_deducts_exactly_that_question_s_points(metric, profile):
    answers = answers_all(metric)
    target = ids_with_grade(metric, "Important")[0]
    answers[target] = "No"
    full = scoring.score_payload(answers_all(metric), profile)["final_score"]
    result = scoring.score_payload(answers, profile)
    assert full - result["final_score"] == metric["grade_points"]["Important"]


def test_tier_counts_reflect_the_answers(metric, profile):
    answers = answers_all(metric)
    optional = ids_with_grade(metric, "Optional")
    for qid in optional[:2]:
        answers[qid] = "No"
    tiers = scoring.score_payload(answers, profile)["tiers"]
    assert tiers["Optional"]["total"] == len(optional)
    assert tiers["Optional"]["yes"] == len(optional) - 2
    assert tiers["Critical"]["proportion"] == 1.0


def test_gold_is_lost_when_an_important_question_fails(metric, profile):
    """Gold demands every Important question; the score alone is not enough."""
    answers = answers_all(metric)
    answers[ids_with_grade(metric, "Important")[0]] = "No"
    result = scoring.score_payload(answers, profile)
    assert result["grade"] != "Gold"
    assert result["tiers"]["Important"]["proportion"] < 1.0


def test_the_highest_qualifying_grade_wins(metric, profile):
    """Half the Optional questions failing still leaves Silver, not Bronze."""
    answers = answers_all(metric)
    for qid in ids_with_grade(metric, "Optional")[:4]:
        answers[qid] = "No"
    assert scoring.score_payload(answers, profile)["grade"] == "Silver"


# ── Validation ────────────────────────────────────────────────────────────────

def test_a_missing_question_is_refused_rather_than_scored(metric, profile):
    answers = answers_all(metric)
    dropped = next(iter(answers))
    del answers[dropped]
    result = scoring.score_payload(answers, profile)
    assert "final_score" not in result
    assert any(dropped in e and "missing" in e for e in result["errors"])


def test_an_unknown_question_id_is_reported(metric, profile):
    answers = answers_all(metric)
    answers["ABC-99"] = "Yes"
    result = scoring.score_payload(answers, profile)
    assert any("ABC-99" in e for e in result["errors"])


@pytest.mark.parametrize("bad", ["yes", "Y", "true", True, None, ""])
def test_only_exactly_yes_or_no_is_accepted(metric, profile, bad):
    answers = answers_all(metric)
    target = next(iter(answers))
    answers[target] = bad
    result = scoring.score_payload(answers, profile)
    assert any(target in e for e in result["errors"])


def test_a_non_object_answers_document_is_rejected(profile):
    result = scoring.score_payload(["ABC-01"], profile)
    assert result["errors"]


# ── Parity with the YAML path used by review_processor.py ─────────────────────

def test_json_and_yaml_metric_paths_score_identically(metric):
    """The skill (JSON) and review_processor.py (YAML) must never disagree."""
    import review_processor  # imports yaml; available wherever CI runs

    yaml_profile = review_processor.load_metric_profile(str(METRIC_YAML))
    json_profile = scoring.load_metric_profile_json(METRIC_JSON)

    assert yaml_profile["schema_version"] == json_profile["schema_version"]

    cases = [answers_all(metric), answers_all(metric, "No")]
    mixed = answers_all(metric)
    for qid in list(mixed)[::3]:
        mixed[qid] = "No"
    cases.append(mixed)

    for flat in cases:
        nested = {qid: {"answer": value} for qid, value in flat.items()}
        from_yaml = scoring.score_review(
            nested, yaml_profile["question_meta"], yaml_profile["grading"]
        )
        from_json = scoring.score_review(
            nested, json_profile["question_meta"], json_profile["grading"]
        )
        assert from_yaml == from_json


# ── Command-line behaviour ────────────────────────────────────────────────────

def run_cli(args, stdin=None):
    return subprocess.run(
        [sys.executable, str(SCORE_PY), *args],
        input=stdin, capture_output=True, text=True,
    )

def test_cli_scores_a_file_and_exits_zero(metric, tmp_path):
    path = tmp_path / "answers.json"
    path.write_text(json.dumps(answers_all(metric)))
    proc = run_cli([str(path), "--metric", str(METRIC_JSON)])
    assert proc.returncode == 0
    assert json.loads(proc.stdout)["grade"] == "Gold"


def test_cli_reads_stdin(metric):
    proc = run_cli(["-", "--metric", str(METRIC_JSON)],
                   stdin=json.dumps(answers_all(metric, "No")))
    assert proc.returncode == 0
    assert json.loads(proc.stdout)["final_score"] == 0


def test_cli_exits_one_on_invalid_answers(tmp_path):
    path = tmp_path / "answers.json"
    path.write_text(json.dumps({"ABC-01": "Yes"}))
    proc = run_cli([str(path), "--metric", str(METRIC_JSON)])
    assert proc.returncode == 1
    assert json.loads(proc.stdout)["errors"]


def test_cli_exits_two_when_the_metric_is_missing(metric, tmp_path):
    path = tmp_path / "answers.json"
    path.write_text(json.dumps(answers_all(metric)))
    proc = run_cli([str(path), "--metric", str(tmp_path / "nope.json")])
    assert proc.returncode == 2
    assert "manually" in proc.stderr


def test_the_bundled_symlink_resolves_and_finds_its_metric(metric, tmp_path):
    """The skill invokes scripts/score.py; its default metric must resolve there."""
    bundled = REPO_ROOT / "skills" / "development" / "airbds-assessment-skill" / "scripts" / "score.py"
    path = tmp_path / "answers.json"
    path.write_text(json.dumps(answers_all(metric)))
    proc = subprocess.run([sys.executable, str(bundled), str(path)],
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["grade"] == "Gold"
