#!/usr/bin/env python3
"""Tests for the YAML/JSON rendering check.

Run directly:
    python3 metric/src/tests/test_check_metric_renderings_match.py
or under pytest:
    pytest metric/src/tests/test_check_metric_renderings_match.py
"""

import json
import subprocess
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent.parent.parent
SCRIPT = REPO_ROOT / "metric" / "src" / "scripts" / "check_metric_renderings_match.py"
COMMITTED_YAML = REPO_ROOT / "metric" / "airbds_metric_v1.0.0.yaml"
COMMITTED_JSON = REPO_ROOT / "metric" / "airbds_metric_v1.0.0.json"


def _run(yaml_path, json_path):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(yaml_path), str(json_path)],
        capture_output=True,
        text=True,
    )


def _pair(tmp_path, data, json_data=None, yaml_text=None):
    """Write a YAML/JSON pair, optionally making them disagree."""
    import yaml as _yaml

    yaml_path = tmp_path / "m.yaml"
    json_path = tmp_path / "m.json"
    yaml_path.write_text(
        yaml_text if yaml_text is not None else _yaml.safe_dump(data),
        encoding="utf-8",
    )
    json_path.write_text(
        json.dumps(data if json_data is None else json_data, indent=2) + "\n",
        encoding="utf-8",
    )
    return yaml_path, json_path


def test_committed_v100_pair_matches(tmp_path):
    """The real files: the check must agree with what we are about to publish."""
    proc = _run(COMMITTED_YAML, COMMITTED_JSON)
    assert proc.returncode == 0, proc.stderr
    assert "matches" in proc.stdout


def test_matching_pair_passes(tmp_path):
    y, j = _pair(tmp_path, {"schema_version": "1.0.0", "questions": [{"id": "A-1"}]})
    proc = _run(y, j)
    assert proc.returncode == 0, proc.stderr


def test_formatting_differences_are_not_a_mismatch(tmp_path):
    """Comments, indentation, and key order are not data."""
    y, j = _pair(
        tmp_path,
        {"schema_version": "1.0.0", "grade_points": {"Critical": 80}},
        yaml_text=(
            "# GENERATED FILE — DO NOT EDIT BY HAND\n"
            "grade_points:\n"
            "    Critical:   80\n"
            'schema_version: "1.0.0"\n'
        ),
    )
    proc = _run(y, j)
    assert proc.returncode == 0, proc.stderr


def test_differing_value_is_reported_by_key(tmp_path):
    y, j = _pair(
        tmp_path,
        {"schema_version": "1.0.0", "grade_points": {"Critical": 80}},
        json_data={"schema_version": "1.0.0", "grade_points": {"Critical": 1}},
    )
    proc = _run(y, j)
    assert proc.returncode != 0
    assert "grade_points" in proc.stderr
    assert "schema_version" not in proc.stderr


def test_key_present_in_only_one_file_is_reported(tmp_path):
    y, j = _pair(
        tmp_path,
        {"schema_version": "1.0.0"},
        json_data={"schema_version": "1.0.0", "source": {"sheet_url": "x"}},
    )
    proc = _run(y, j)
    assert proc.returncode != 0
    assert "source" in proc.stderr


def test_missing_file_is_an_error(tmp_path):
    y, j = _pair(tmp_path, {"schema_version": "1.0.0"})
    j.unlink()
    proc = _run(y, j)
    assert proc.returncode != 0
    assert "no such file" in proc.stderr


def test_malformed_json_is_an_error(tmp_path):
    y, j = _pair(tmp_path, {"schema_version": "1.0.0"})
    j.write_text("{not json", encoding="utf-8")
    proc = _run(y, j)
    assert proc.returncode != 0
    assert "not valid JSON" in proc.stderr


if __name__ == "__main__":
    import tempfile

    failures = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        with tempfile.TemporaryDirectory() as td:
            try:
                fn(Path(td))
                print(f"PASS {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {name}: {exc}")
    print(f"\n{'FAILED' if failures else 'OK'} ({failures} failure(s))")
    sys.exit(1 if failures else 0)
