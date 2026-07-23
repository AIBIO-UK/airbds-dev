#!/usr/bin/env python3
"""Offline tests for the v0.5 metric build script.

These run against committed fixture CSVs (the three source tabs exported from the
canonical Google Sheet), so they need no network. They cover the v0.5-specific
behaviour — the restructured grade-points pivot and the new Instructions capture —
plus a byte-for-byte check that the committed metric YAML still regenerates.

Run directly:
    python3 metric/src/tests/test_build_metric_yaml_v0.5.py
or under pytest:
    pytest metric/src/tests/test_build_metric_yaml_v0.5.py
"""

import importlib.util
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
FIXTURES = TESTS_DIR / "fixtures"
REPO_ROOT = TESTS_DIR.parent.parent.parent
SCRIPT = REPO_ROOT / "metric" / "src" / "scripts" / "build_metric_yaml_from_google_sheet_v0.5.py"
COMMITTED_YAML = REPO_ROOT / "metric" / "airbds_metric_v0.5.yaml"


def _load_build_module():
    """Import the build script by path (its filename contains a dot: v0.5)."""
    spec = importlib.util.spec_from_file_location("build_v05", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bm = _load_build_module()


def _worksheets():
    scoring = (FIXTURES / "scoring-v0.5.csv").read_text(encoding="utf-8")
    lookups = (FIXTURES / "config-v0.5.csv").read_text(encoding="utf-8")
    instructions = (FIXTURES / "instructions-v0.5.csv").read_text(encoding="utf-8")
    return (bm.CsvWorksheet(scoring), bm.CsvWorksheet(lookups),
            bm.CsvWorksheet(instructions), scoring, lookups, instructions)


def test_read_questions():
    scoring_ws, *_ = _worksheets()
    qs = bm.read_questions(scoring_ws)
    assert len(qs) == 25, f"expected 25 questions, got {len(qs)}"
    assert [q["id"] for q in qs] == [f"ABC-{n:02d}" for n in range(1, 26)]
    by_scope = {}
    for q in qs:
        by_scope[q["scope"]] = by_scope.get(q["scope"], 0) + 1
    assert by_scope == {"Infrastructure": 10, "Metadata": 6, "Content": 6, "Ethics": 3}, by_scope
    by_grade = {}
    for q in qs:
        by_grade[q["grade"]] = by_grade.get(q["grade"], 0) + 1
    assert by_grade == {"Critical": 9, "Important": 10, "Optional": 6}, by_grade
    # Ethics questions are the ones that will carry not_applicable_default.
    assert {q["id"] for q in qs if q["scope"] == "Ethics"} == {"ABC-23", "ABC-24", "ABC-25"}


def test_read_grade_points_from_pivot():
    _, lookups_ws, *_ = _worksheets()
    pts = bm.read_grade_points(lookups_ws)
    # v0.5 reads these from the 'Points per Question' column of the pivot.
    assert pts == {"Critical": 80, "Important": 5, "Optional": 2}, pts


def test_read_grading():
    _, lookups_ws, *_ = _worksheets()
    grading = bm.read_grading(lookups_ws)
    assert [g["name"] for g in grading] == ["Gold", "Silver", "Bronze", "Caution"]
    gold, silver, bronze, caution = grading
    assert gold["min_score"] == 776
    assert gold["min_proportion_yes"] == {"Critical": 1.0, "Important": 1.0, "Optional": 0.5}
    assert silver["min_score"] == 745
    assert bronze["min_score"] == 640
    assert abs(bronze["min_proportion_yes"]["Critical"] - 0.8888888889) < 1e-9
    assert caution["min_score"] == 0
    assert caution["min_proportion_yes"] == {"Critical": 0.0, "Important": 0.0, "Optional": 0.0}


def test_read_instructions():
    *_, instructions_ws, _, _, _ = _worksheets()
    text = bm.read_instructions(instructions_ws)
    assert text, "instructions should not be empty"
    # Captures the generic guidance…
    assert "AI-readiness of a dataset" in text
    assert "out of scope for this metric" in text
    # …preserves paragraph breaks…
    assert "\n\n" in text
    # …and excludes the per-review data-entry section below it.
    assert "Reviewer name" not in text
    assert "Accession number" not in text


def test_committed_yaml_regenerates_byte_for_byte():
    scoring_ws, lookups_ws, instructions_ws, scoring, lookups, instructions = _worksheets()
    qs = bm.read_questions(scoring_ws)
    pts = bm.read_grade_points(lookups_ws)
    grading = bm.read_grading(lookups_ws)
    instr = bm.read_instructions(instructions_ws)
    bm.validate(qs, pts, grading)
    sha = bm.source_sha256(scoring, lookups, instructions)
    generated = bm.render_yaml(qs, pts, grading, instr, bm.DEFAULT_SHEET, sha)

    import yaml
    doc = yaml.safe_load(generated)  # must be valid YAML
    assert doc["schema_version"] == "0.5"
    assert doc["instructions"].strip().endswith("specific questions.")
    assert len(doc["questions"]) == 25
    assert doc["grade_points"] == {"Critical": 80, "Important": 5, "Optional": 2}
    assert doc["questions"]["ABC-23"]["not_applicable_default"] == "Yes"

    committed = COMMITTED_YAML.read_text(encoding="utf-8")
    assert generated == committed, (
        "committed metric/airbds_metric_v0.5.yaml is out of sync with the fixtures; "
        "regenerate it from the sheet (or fixtures) and commit the result."
    )


def _run_all():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"FAIL {t.__name__}: {e}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return failures


if __name__ == "__main__":
    import sys
    sys.exit(1 if _run_all() else 0)
