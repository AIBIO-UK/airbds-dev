#!/usr/bin/env python3
"""Tests for the publication-repo version stamper.

These run scripts/stamp_core_versions.py against throwaway files. Nothing
touches git, the network, or the real publication repository — the release
scripts' own tests cover the stamper in its actual setting.

Run directly:
    python3 scripts/tests/test_stamp_core_versions.py
or under pytest:
    pytest scripts/tests/test_stamp_core_versions.py
"""

import subprocess
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "stamp_core_versions.py"

README = """# AIRBDS assessment skills

There is currently one skill at [`skills/airbds-assessment-skill.zip`](x),
currently at version <!--skill-version-->0.8.0<!--/skill-version--> and assessing
against [AIRBDS metric](y) v<!--metric-version-->1.0.0<!--/metric-version-->.
"""


def _write(tmp_path, text=README, name="README.md"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def _run(path, *args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--file", str(path), *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )


def test_stamps_both_versions(tmp_path):
    path = _write(tmp_path)
    proc = _run(path, "--skill-version", "0.9.0", "--metric-version", "1.1.0")

    assert proc.returncode == 0, proc.stderr
    text = path.read_text(encoding="utf-8")
    assert "<!--skill-version-->0.9.0<!--/skill-version-->" in text
    assert "<!--metric-version-->1.1.0<!--/metric-version-->" in text
    assert "0.8.0 -> 0.9.0" in proc.stdout or "0.8.0" in proc.stdout


def test_leaves_the_version_it_was_not_given(tmp_path):
    """What lets a metric release run without touching the skill's number."""
    path = _write(tmp_path)
    proc = _run(path, "--metric-version", "1.1.0")

    assert proc.returncode == 0, proc.stderr
    text = path.read_text(encoding="utf-8")
    assert "<!--skill-version-->0.8.0<!--/skill-version-->" in text
    assert "<!--metric-version-->1.1.0<!--/metric-version-->" in text


def test_is_idempotent(tmp_path):
    path = _write(tmp_path)
    first = _run(path, "--skill-version", "0.9.0")
    after_first = path.read_text(encoding="utf-8")
    second = _run(path, "--skill-version", "0.9.0")

    assert first.returncode == 0 and second.returncode == 0
    assert path.read_text(encoding="utf-8") == after_first
    assert "already 0.9.0" in second.stdout


def test_stamps_every_occurrence(tmp_path):
    """A version quoted twice must not end up quoted two different ways."""
    text = README + "\nInstall v<!--skill-version-->0.8.0<!--/skill-version--> today.\n"
    path = _write(tmp_path, text)
    proc = _run(path, "--skill-version", "0.9.0")

    assert proc.returncode == 0, proc.stderr
    assert path.read_text(encoding="utf-8").count("0.9.0") == 2
    assert "0.8.0" not in path.read_text(encoding="utf-8")


def test_check_reports_a_mismatch_without_writing(tmp_path):
    path = _write(tmp_path)
    before = path.read_text(encoding="utf-8")
    proc = _run(path, "--skill-version", "0.9.0", "--check")

    assert proc.returncode == 1
    assert "skill-version is 0.8.0, expected 0.9.0" in proc.stderr
    assert path.read_text(encoding="utf-8") == before


def test_check_passes_when_current(tmp_path):
    path = _write(tmp_path)
    proc = _run(path, "--skill-version", "0.8.0", "--metric-version", "1.0.0", "--check")

    assert proc.returncode == 0, proc.stderr
    assert "up to date" in proc.stdout


def test_missing_marker_is_an_error(tmp_path):
    path = _write(tmp_path, "# skills\n\nVersion 0.8.0, metric v1.0.0.\n")
    proc = _run(path, "--skill-version", "0.9.0")

    assert proc.returncode == 2
    assert "no <!--skill-version-->" in proc.stderr


def test_unclosed_marker_is_treated_as_missing(tmp_path):
    """A span must stay on one line — a runaway match would eat the document."""
    text = "# skills\n\nVersion <!--skill-version-->0.8.0\n\nmore prose <!--/skill-version-->\n"
    path = _write(tmp_path, text)
    proc = _run(path, "--skill-version", "0.9.0")

    assert proc.returncode == 2
    assert "no <!--skill-version-->" in proc.stderr


def test_missing_file_is_an_error(tmp_path):
    proc = _run(tmp_path / "nope.md", "--skill-version", "0.9.0")

    assert proc.returncode == 2
    assert "file not found" in proc.stderr


def test_rejects_a_malformed_version(tmp_path):
    path = _write(tmp_path)
    proc = _run(path, "--skill-version", "latest")

    assert proc.returncode == 2
    assert "must look like" in proc.stderr


def test_requires_something_to_stamp(tmp_path):
    path = _write(tmp_path)
    proc = _run(path)

    assert proc.returncode == 2
    assert "nothing to stamp" in proc.stderr


def test_defaults_to_the_skills_readme(tmp_path):
    """Release scripts rely on the default path when run from the clone root."""
    (tmp_path / "skills").mkdir()
    (tmp_path / "skills" / "README.md").write_text(README, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--skill-version", "0.9.0"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0, proc.stderr
    assert "0.9.0" in (tmp_path / "skills" / "README.md").read_text(encoding="utf-8")


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
