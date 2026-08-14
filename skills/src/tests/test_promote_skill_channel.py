#!/usr/bin/env python3
"""Tests for the channel-promotion script.

Each test builds a synthetic skills tree — two channel bundles with symlinked
assets and a manifest — and drives the script against it with --repo-root, so
nothing touches the real tree.

Run directly:
    python3 skills/src/tests/test_promote_skill_channel.py
or under pytest:
    pytest skills/src/tests/test_promote_skill_channel.py
"""

import json
import os
import subprocess
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent.parent.parent
SCRIPT = REPO_ROOT / "skills" / "src" / "scripts" / "promote_skill_channel.py"

SKILL_MD = """---
name: airbds-assessment-skill
description: test bundle
metadata:
  version: "{skill_version}"
  channel: {channel}
---

# Test skill

Look up channels.{channel} in the manifest. Only the {channel} channel matters.
"""


def _run(root, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(root), *args],
        capture_output=True, text=True,
    )


def _bundle(root, channel, skill_version="0.8.1", metric_version="1.0.0"):
    """A channel bundle: SKILL.md, a symlinked metric, a symlinked score script."""
    d = root / "skills" / channel / "airbds-assessment-skill"
    (d / "assets").mkdir(parents=True)
    (d / "scripts").mkdir(parents=True)
    (d / "SKILL.md").write_text(
        SKILL_MD.format(skill_version=skill_version, channel=channel),
        encoding="utf-8",
    )
    # A metric file to point at, and the symlink into it (relative, four up).
    metric = root / "metric" / f"airbds_metric_v{metric_version}.json"
    metric.parent.mkdir(exist_ok=True)
    metric.write_text(json.dumps({"schema_version": metric_version}) + "\n")
    os.symlink(f"../../../../metric/airbds_metric_v{metric_version}.json",
               d / "assets" / "airbds_metric.json")
    os.symlink("../../../../reviews/src/scripts/airbds_scoring.py",
               d / "scripts" / "score.py")
    return d


def _manifest(root, channels):
    (root / "skills").mkdir(exist_ok=True)
    (root / "skills" / "versions.json").write_text(
        json.dumps({"channels": {
            name: {
                "metric_version": mv,
                "skill_version": sv,
                "skill_update_url": f"https://example.invalid/{name}.zip",
            } for name, (sv, mv) in channels.items()
        }}, indent=2) + "\n", encoding="utf-8"
    )


def _build(tmp_path, dev=("0.9.0", "1.0.1"), testing=("0.8.1", "1.0.0")):
    """Dev ahead of testing by default: a promotion is pending."""
    root = tmp_path / "repo"
    root.mkdir()
    _bundle(root, "development", *dev)
    _bundle(root, "testing", *testing)
    _manifest(root, {
        "production": ("0.8.1", "1.0.0"),
        "testing": testing,
        "development": dev,
    })
    return root


def _read(root, channel, rel):
    return (root / "skills" / channel / "airbds-assessment-skill" / rel).read_text()


def test_dry_run_writes_nothing(tmp_path):
    root = _build(tmp_path)
    before = _read(root, "testing", "SKILL.md")
    proc = _run(root, "--dry-run")
    assert proc.returncode == 0, proc.stderr
    assert "dry run: nothing written" in proc.stdout
    assert _read(root, "testing", "SKILL.md") == before  # untouched


def test_promotion_rechannels_and_copies(tmp_path):
    root = _build(tmp_path)
    proc = _run(root)
    assert proc.returncode == 0, proc.stderr + proc.stdout

    testing_md = _read(root, "testing", "SKILL.md")
    # The dev SKILL.md, but on the testing channel — no 'development' left.
    assert 'channel: testing' in testing_md
    assert "development" not in testing_md
    assert 'version: "0.9.0"' in testing_md
    assert "channels.testing" in testing_md


def test_symlinks_stay_symlinks(tmp_path):
    """The promoted metric must remain a link, not a dereferenced copy."""
    root = _build(tmp_path)
    _run(root)
    link = root / "skills/testing/airbds-assessment-skill/assets/airbds_metric.json"
    assert link.is_symlink()
    # Repointed at dev's metric (v1.0.1), by relative target.
    assert os.readlink(link) == "../../../../metric/airbds_metric_v1.0.1.json"


def test_manifest_is_updated_for_the_target_channel_only(tmp_path):
    root = _build(tmp_path)
    _run(root)
    m = json.loads((root / "skills" / "versions.json").read_text())["channels"]
    assert m["testing"] == {
        "metric_version": "1.0.1", "skill_version": "0.9.0",
        "skill_update_url": "https://example.invalid/testing.zip",
    }
    # development and production untouched
    assert m["development"]["skill_version"] == "0.9.0"
    assert m["production"]["metric_version"] == "1.0.0"


def test_already_promoted_is_a_no_op(tmp_path):
    root = _build(tmp_path, dev=("0.8.1", "1.0.0"), testing=("0.8.1", "1.0.0"))
    proc = _run(root)
    assert proc.returncode == 0, proc.stderr
    assert "already the promotion" in proc.stdout


def test_check_reports_a_pending_promotion_without_writing(tmp_path):
    root = _build(tmp_path)
    before = _read(root, "testing", "SKILL.md")
    proc = _run(root, "--check")
    assert proc.returncode == 0, proc.stderr
    assert "is not currently the promotion" in proc.stdout
    assert _read(root, "testing", "SKILL.md") == before


def test_check_on_a_synced_pair_is_a_no_op(tmp_path):
    root = _build(tmp_path, dev=("0.8.1", "1.0.0"), testing=("0.8.1", "1.0.0"))
    proc = _run(root, "--check")
    assert proc.returncode == 0
    assert "already the promotion" in proc.stdout


def test_extra_file_in_target_is_deleted(tmp_path):
    root = _build(tmp_path)
    stray = root / "skills/testing/airbds-assessment-skill/assets/stale.txt"
    stray.write_text("left over from a previous version\n")
    proc = _run(root)
    assert proc.returncode == 0, proc.stderr
    assert not stray.exists()


def test_pycache_is_neither_copied_nor_deleted(tmp_path):
    root = _build(tmp_path)
    # a build artefact under testing that must survive
    keep = root / "skills/testing/airbds-assessment-skill/scripts/__pycache__"
    keep.mkdir()
    (keep / "score.cpython-312.pyc").write_bytes(b"\x00")
    # a build artefact under development that must NOT be copied across
    src_cache = root / "skills/development/airbds-assessment-skill/scripts/__pycache__"
    src_cache.mkdir()
    (src_cache / "x.pyc").write_bytes(b"\x00")

    proc = _run(root)
    assert proc.returncode == 0, proc.stderr
    assert keep.exists()
    assert not (root / "skills/testing/airbds-assessment-skill/scripts/"
                "__pycache__/x.pyc").exists()


def test_promoting_an_unchanged_metric_still_bumps_when_skill_differs(tmp_path):
    """Skill-only promotion: same metric, newer skill version."""
    root = _build(tmp_path, dev=("0.8.2", "1.0.0"), testing=("0.8.1", "1.0.0"))
    proc = _run(root)
    assert proc.returncode == 0, proc.stderr
    m = json.loads((root / "skills" / "versions.json").read_text())["channels"]
    assert m["testing"]["skill_version"] == "0.8.2"
    assert m["testing"]["metric_version"] == "1.0.0"


def test_missing_source_channel_errors(tmp_path):
    root = _build(tmp_path)
    proc = _run(root, "--from", "nope")
    assert proc.returncode == 1
    assert "no source bundle" in proc.stdout


def test_missing_target_channel_errors(tmp_path):
    root = _build(tmp_path)
    proc = _run(root, "--to", "nope")
    assert proc.returncode == 1
    assert "no target bundle" in proc.stdout


def test_custom_from_and_to(tmp_path):
    """The default is development->testing, but any pair of existing channels works."""
    root = _build(tmp_path)
    # Give production a source directory so it can be a promotion target.
    _bundle(root, "production", "0.5.0", "1.0.0")
    proc = _run(root, "--from", "testing", "--to", "production")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert 'channel: production' in _read(root, "production", "SKILL.md")


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
