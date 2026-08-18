#!/usr/bin/env python3
"""Tests for build_skill_zip.py — the local channel-zip builder.

Each test builds a synthetic skills tree — a channel bundle whose metric and
scorer are symlinks — and drives the script against it with --repo-root, so
nothing touches the real tree. The property that matters is that the symlinked
members are DEREFERENCED into real files in the zip, the way the CI build (and an
installable skill) needs.

Run directly:
    python3 skills/src/tests/test_build_skill_zip.py
or under pytest:
    pytest skills/src/tests/test_build_skill_zip.py
"""

import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent.parent.parent
SCRIPT = REPO_ROOT / "skills" / "src" / "scripts" / "build_skill_zip.py"

SKILL_MD = """---
name: airbds-assessment-skill
description: test bundle
metadata:
  version: "0.9.0"
  channel: development
---

# Test skill
"""

METRIC_JSON = json.dumps({"schema_version": "1.0.1", "questions": {}}) + "\n"
SCORE_PY = "# fake scorer\nprint('ok')\n"


def _bundle(root, channel="development"):
    """A channel bundle: SKILL.md, a symlinked metric, a symlinked scorer."""
    d = root / "skills" / channel / "airbds-assessment-skill"
    (d / "assets").mkdir(parents=True)
    (d / "scripts").mkdir(parents=True)
    (d / "SKILL.md").write_text(SKILL_MD, encoding="utf-8")
    # Real targets outside the bundle, reached by relative symlinks (four up).
    metric = root / "metric" / "airbds_metric_v1.0.1.json"
    metric.parent.mkdir(exist_ok=True)
    metric.write_text(METRIC_JSON, encoding="utf-8")
    scorer = root / "reviews" / "src" / "scripts" / "airbds_scoring.py"
    scorer.parent.mkdir(parents=True)
    scorer.write_text(SCORE_PY, encoding="utf-8")
    os.symlink("../../../../metric/airbds_metric_v1.0.1.json",
               d / "assets" / "airbds_metric.json")
    os.symlink("../../../../reviews/src/scripts/airbds_scoring.py",
               d / "scripts" / "score.py")
    return d


def _run(root, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(root), *args],
        capture_output=True, text=True,
    )


def test_builds_zip_with_expected_members(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _bundle(root)
    out = tmp_path / "dev.zip"
    proc = _run(root, "development", "-o", str(out))
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert out.exists()
    with zipfile.ZipFile(out) as zf:
        names = set(zf.namelist())
    assert {"SKILL.md", "assets/airbds_metric.json", "scripts/score.py"} <= names


def test_symlinked_members_are_dereferenced(tmp_path):
    """The bundled metric/scorer symlinks must land as real file content."""
    root = tmp_path / "repo"
    root.mkdir()
    _bundle(root)
    out = tmp_path / "dev.zip"
    assert _run(root, "development", "-o", str(out)).returncode == 0
    with zipfile.ZipFile(out) as zf:
        # Real content, not a symlink target path.
        assert json.loads(zf.read("assets/airbds_metric.json"))["schema_version"] == "1.0.1"
        assert zf.read("scripts/score.py").decode() == SCORE_PY
        # A dereferenced entry is a regular file: the symlink mode bit is unset.
        info = zf.getinfo("assets/airbds_metric.json")
        mode = (info.external_attr >> 16) & 0o170000
        assert mode != 0o120000, "metric was stored as a symlink, not dereferenced"


def test_default_output_name(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _bundle(root, "testing")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(root), "testing"],
        capture_output=True, text=True, cwd=str(tmp_path),
    )
    assert proc.returncode == 0, proc.stderr
    assert (tmp_path / "airbds-assessment-skill-testing.zip").exists()


def test_unknown_channel_errors(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _bundle(root, "development")
    proc = _run(root, "nope", "-o", str(tmp_path / "x.zip"))
    assert proc.returncode != 0
    combined = (proc.stderr + proc.stdout).lower()
    assert "no skill bundle" in combined
    assert "development" in combined  # names what is available


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
