#!/usr/bin/env python3
"""Tests for the skills/versions.json validator.

Each test builds a synthetic repository — a manifest, a metric file, and one or
two skill bundles — and points the validator at it with --repo-root, so nothing
depends on the real tree's current versions.

Run directly:
    python3 skills/src/tests/test_validate_skills_versions.py
or under pytest:
    pytest skills/src/tests/test_validate_skills_versions.py
"""

import json
import subprocess
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent.parent.parent
SCRIPT = REPO_ROOT / "skills" / "src" / "scripts" / "validate_skills_versions.py"

SKILL_MD = """---
name: airbds-assessment-skill
description: test bundle
metadata:
  version: "{skill_version}"
  channel: {channel}
---

# Test skill
"""


def _run(root, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(root), *args],
        capture_output=True, text=True,
    )


def _build(tmp_path, channels, bundles=None, metric_versions=("1.0.0",)):
    """A synthetic repo.

    channels: {name: (skill_version, metric_version)} for the manifest.
    bundles:  {name: (skill_version, metric_version, channel_label)} for the
              on-disk skills. Defaults to mirroring `channels` for every channel
              except `production`, which has no source directory.
    """
    root = tmp_path / "repo"
    (root / "metric").mkdir(parents=True)
    for mv in metric_versions:
        (root / "metric" / f"airbds_metric_v{mv}.yaml").write_text(
            f'schema_version: "{mv}"\n', encoding="utf-8"
        )

    if bundles is None:
        bundles = {
            name: (sv, mv, name)
            for name, (sv, mv) in channels.items()
            if name != "production"
        }
    for name, (sv, mv, label) in bundles.items():
        d = root / "skills" / name / "airbds-assessment-skill" / "assets"
        d.mkdir(parents=True)
        (d.parent / "SKILL.md").write_text(
            SKILL_MD.format(skill_version=sv, channel=label), encoding="utf-8"
        )
        (d / "airbds_metric.json").write_text(
            json.dumps({"schema_version": mv}) + "\n", encoding="utf-8"
        )

    manifest = {
        "channels": {
            name: {
                "metric_version": mv,
                "skill_version": sv,
                "skill_update_url": f"https://example.invalid/{name}.zip",
            }
            for name, (sv, mv) in channels.items()
        }
    }
    (root / "skills").mkdir(exist_ok=True)
    (root / "skills" / "versions.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return root


def _commit(root, message="seed"):
    """Make the synthetic repo a git repo (or add a commit), for --since."""
    if not (root / ".git").exists():
        subprocess.run(["git", "init", "--quiet", "-b", "main"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "t@t"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "--quiet", "-m", message], cwd=root, check=True)


def _set_manifest(root, channels):
    data = json.loads((root / "skills" / "versions.json").read_text())
    for name, (sv, mv) in channels.items():
        data["channels"][name]["skill_version"] = sv
        data["channels"][name]["metric_version"] = mv
    (root / "skills" / "versions.json").write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8"
    )


CURRENT = {
    "production": ("0.8.1", "1.0.0"),
    "testing": ("0.8.1", "1.0.0"),
    "development": ("0.8.1", "1.0.0"),
}


# ── the pre-existing checks still hold ───────────────────────────────────────

def test_valid_manifest_passes(tmp_path):
    proc = _run(_build(tmp_path, dict(CURRENT)))
    assert proc.returncode == 0, proc.stdout
    assert "OK" in proc.stdout
    # production has no source directory, so it is not cross-checked
    assert "development, testing" in proc.stdout


def test_metric_version_without_a_metric_file_fails(tmp_path):
    root = _build(tmp_path, {"development": ("0.8.1", "9.9.9")},
                  metric_versions=("1.0.0", "9.9.9"))
    (root / "metric" / "airbds_metric_v9.9.9.yaml").unlink()
    proc = _run(root)
    assert proc.returncode == 1
    assert "does not exist" in proc.stdout


def test_missing_required_field_fails(tmp_path):
    root = _build(tmp_path, dict(CURRENT))
    data = json.loads((root / "skills" / "versions.json").read_text())
    del data["channels"]["testing"]["skill_update_url"]
    (root / "skills" / "versions.json").write_text(json.dumps(data), encoding="utf-8")
    proc = _run(root)
    assert proc.returncode == 1
    assert "skill_update_url" in proc.stdout


# ── check 4: skill_version vs SKILL.md ───────────────────────────────────────

def test_skill_version_disagreeing_with_skill_md_fails(tmp_path):
    root = _build(
        tmp_path,
        {"development": ("0.9.0", "1.0.0")},
        bundles={"development": ("0.8.1", "1.0.0", "development")},
    )
    proc = _run(root)
    assert proc.returncode == 1
    assert "metadata.version '0.8.1'" in proc.stdout


# ── check 5: metric_version vs the bundled metric ────────────────────────────

def test_repointed_symlink_without_a_manifest_bump_fails(tmp_path):
    """The Stage 5 mistake: the bundle moved to the new metric, the manifest did not."""
    root = _build(
        tmp_path,
        {"development": ("0.8.1", "1.0.0")},
        bundles={"development": ("0.8.1", "1.0.1", "development")},
        metric_versions=("1.0.0", "1.0.1"),
    )
    proc = _run(root)
    assert proc.returncode == 1
    assert "schema_version '1.0.1'" in proc.stdout


def test_manifest_bump_without_repointing_the_symlink_fails(tmp_path):
    """And the reverse: the manifest advertises a metric the bundle does not carry."""
    root = _build(
        tmp_path,
        {"development": ("0.9.0", "1.0.1")},
        bundles={"development": ("0.9.0", "1.0.0", "development")},
        metric_versions=("1.0.0", "1.0.1"),
    )
    proc = _run(root)
    assert proc.returncode == 1
    assert "metric_version '1.0.1'" in proc.stdout


def test_broken_bundled_metric_fails(tmp_path):
    root = _build(tmp_path, {"development": ("0.8.1", "1.0.0")})
    (root / "skills/development/airbds-assessment-skill/assets/airbds_metric.json").unlink()
    proc = _run(root)
    assert proc.returncode == 1
    assert "missing or its symlink is broken" in proc.stdout


# ── check 6: declared channel vs directory ───────────────────────────────────

def test_channel_label_disagreeing_with_directory_fails(tmp_path):
    root = _build(
        tmp_path,
        {"testing": ("0.8.1", "1.0.0")},
        bundles={"testing": ("0.8.1", "1.0.0", "development")},
    )
    proc = _run(root)
    assert proc.returncode == 1
    assert "metadata.channel" in proc.stdout


# ── check 7: --since, the minor-bump rule ────────────────────────────────────

def test_metric_bump_with_only_a_patch_skill_bump_fails(tmp_path):
    root = _build(tmp_path, dict(CURRENT), metric_versions=("1.0.0", "1.0.1"))
    _commit(root)
    _set_manifest(root, {"development": ("0.8.2", "1.0.1")})
    (root / "skills/development/airbds-assessment-skill/assets/airbds_metric.json"
     ).write_text(json.dumps({"schema_version": "1.0.1"}) + "\n", encoding="utf-8")
    _rewrite_skill_md(root, "development", "0.8.2")

    proc = _run(root, "--since", "HEAD")
    assert proc.returncode == 1
    assert "MINOR skill bump, not a patch" in proc.stdout
    assert "'0.8.1' -> '0.8.2'" in proc.stdout


def test_metric_bump_with_a_minor_skill_bump_passes(tmp_path):
    root = _build(tmp_path, dict(CURRENT), metric_versions=("1.0.0", "1.0.1"))
    _commit(root)
    _set_manifest(root, {"development": ("0.9.0", "1.0.1")})
    (root / "skills/development/airbds-assessment-skill/assets/airbds_metric.json"
     ).write_text(json.dumps({"schema_version": "1.0.1"}) + "\n", encoding="utf-8")
    _rewrite_skill_md(root, "development", "0.9.0")

    proc = _run(root, "--since", "HEAD")
    assert proc.returncode == 0, proc.stdout
    assert "bumps checked since HEAD" in proc.stdout


def test_major_skill_bump_also_satisfies_the_rule(tmp_path):
    root = _build(tmp_path, dict(CURRENT), metric_versions=("1.0.0", "1.0.1"))
    _commit(root)
    _set_manifest(root, {"development": ("1.0.0", "1.0.1")})
    (root / "skills/development/airbds-assessment-skill/assets/airbds_metric.json"
     ).write_text(json.dumps({"schema_version": "1.0.1"}) + "\n", encoding="utf-8")
    _rewrite_skill_md(root, "development", "1.0.0")

    proc = _run(root, "--since", "HEAD")
    assert proc.returncode == 0, proc.stdout


def test_unchanged_metric_needs_no_skill_bump(tmp_path):
    """A skill-only change is still allowed to be a patch."""
    root = _build(tmp_path, dict(CURRENT))
    _commit(root)
    _set_manifest(root, {"development": ("0.8.2", "1.0.0")})
    _rewrite_skill_md(root, "development", "0.8.2")

    proc = _run(root, "--since", "HEAD")
    assert proc.returncode == 0, proc.stdout


def test_unreadable_since_ref_is_an_error(tmp_path):
    root = _build(tmp_path, dict(CURRENT))
    _commit(root)
    proc = _run(root, "--since", "no-such-ref")
    assert proc.returncode == 1
    assert "cannot read" in proc.stdout


def test_without_since_the_bump_rule_is_not_checked(tmp_path):
    """The default run stays stateless — no git, no history."""
    root = _build(tmp_path, dict(CURRENT), metric_versions=("1.0.0", "1.0.1"))
    _commit(root)
    _set_manifest(root, {"development": ("0.8.2", "1.0.1")})
    (root / "skills/development/airbds-assessment-skill/assets/airbds_metric.json"
     ).write_text(json.dumps({"schema_version": "1.0.1"}) + "\n", encoding="utf-8")
    _rewrite_skill_md(root, "development", "0.8.2")

    proc = _run(root)
    assert proc.returncode == 0, proc.stdout
    assert "bumps checked" not in proc.stdout


def _rewrite_skill_md(root, channel, skill_version):
    p = root / "skills" / channel / "airbds-assessment-skill" / "SKILL.md"
    p.write_text(
        SKILL_MD.format(skill_version=skill_version, channel=channel), encoding="utf-8"
    )


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
