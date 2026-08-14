#!/usr/bin/env python3
"""Offline tests for the metric release script.

These exercise release_metric_to_core.sh end to end against a throwaway local
bare repository standing in for AIBIO-UK/airbds-core, with `gh` replaced by a
stub that records its arguments. Nothing touches the network or the real
publication repository.

Run directly:
    python3 metric/src/tests/test_release_metric_to_core.py
or under pytest:
    pytest metric/src/tests/test_release_metric_to_core.py
"""

import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent.parent.parent
SCRIPT_REL = "metric/src/scripts/release_metric_to_core.sh"
SCRIPT = REPO_ROOT / SCRIPT_REL
VERSION = "1.0.0"
SRC_YAML = REPO_ROOT / "metric" / f"airbds_metric_v{VERSION}.yaml"
SRC_JSON = REPO_ROOT / "metric" / f"airbds_metric_v{VERSION}.json"
DEST_YAML = "airbds_metric.yaml"
DEST_JSON = "airbds_metric.json"

# A retained metric from before the JSON rendering existed, used to check that
# those versions still publish as YAML alone.
LEGACY_VERSION = "0.4"

# Everything release_metric_to_core.sh reaches for through its own REPO_ROOT.
# Copied into a throwaway tree by _fake_repo when a test needs the *sources* to
# be wrong — a missing or mismatched JSON — which cannot be staged in the real
# repository.
SCRIPT_FILES = (
    "scripts/publish-to-core.sh",
    "scripts/stamp_core_versions.py",
    SCRIPT_REL,
    "metric/src/scripts/check_metric_renderings_match.py",
)

# Records its arguments NUL-separated, then prints a plausible PR URL. NUL and
# not newline: the PR body is multi-line, and splitting on newlines would
# silently truncate it to its first line.
GH_STUB = """#!/usr/bin/env bash
printf '%s\\0' "$@" >> "$GH_CALLS"
echo "https://github.com/fake/core/pull/1"
"""

# The publication repo's skills/README.md, as the release script expects to find
# it: version numbers wrapped in comment markers. The skill version is seeded
# with a real-looking value because a metric release must leave it untouched.
CORE_SKILLS_README = """# AIRBDS assessment skills

There is currently one skill at [`skills/airbds-assessment-skill.zip`](x),
currently at version <!--skill-version-->0.8.0<!--/skill-version--> and assessing
against [AIRBDS metric](y) v<!--metric-version-->0.0.1<!--/metric-version-->.
"""

CORE_SKILLS_README_PATH = "skills/README.md"


def _read_gh_calls(path):
    if not path.exists():
        return []
    raw = path.read_bytes()
    return [a.decode() for a in raw.split(b"\0")[:-1]] if raw else []


def _git(*args, cwd):
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout


def _make_origin(
    tmp_path, seed_metric=None, seed_metric_json=None, seed_readme=CORE_SKILLS_README
):
    """A bare repo with a main branch, standing in for airbds-core."""
    seed = tmp_path / "seed"
    seed.mkdir()
    _git("init", "--quiet", "--initial-branch=main", cwd=seed)
    _git("config", "user.name", "test", cwd=seed)
    _git("config", "user.email", "test@example.com", cwd=seed)
    (seed / "README.md").write_text("# airbds-core\n", encoding="utf-8")
    if seed_readme is not None:
        readme = seed / CORE_SKILLS_README_PATH
        readme.parent.mkdir(parents=True, exist_ok=True)
        readme.write_text(seed_readme, encoding="utf-8")
    if seed_metric is not None:
        (seed / DEST_YAML).write_text(seed_metric, encoding="utf-8")
    if seed_metric_json is not None:
        (seed / DEST_JSON).write_text(seed_metric_json, encoding="utf-8")
    _git("add", "-A", cwd=seed)
    _git("commit", "--quiet", "-m", "seed", cwd=seed)

    origin = tmp_path / "core.git"
    _git("clone", "--quiet", "--bare", str(seed), str(origin), cwd=tmp_path)
    return origin


def _fake_repo(tmp_path, version, yaml_text, json_text=None):
    """A minimal copy of this repository whose metric sources the test controls.

    The release script finds its sources relative to its own location, so the
    only way to exercise a broken source pair — JSON missing, JSON disagreeing
    with the YAML — is to run a copy of the script from a tree where that is
    true. Returns the path to the copied script.
    """
    root = tmp_path / "fake-repo"
    for rel in SCRIPT_FILES:
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / rel, dst)
    metric = root / "metric"
    metric.mkdir(exist_ok=True)
    (metric / f"airbds_metric_v{version}.yaml").write_text(yaml_text, encoding="utf-8")
    if json_text is not None:
        (metric / f"airbds_metric_v{version}.json").write_text(
            json_text, encoding="utf-8"
        )
    return root / SCRIPT_REL


def _run(tmp_path, origin, *args, expect_ok=True, version=VERSION, script=SCRIPT):
    """Run the release script with a stubbed gh on PATH."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    gh = bindir / "gh"
    gh.write_text(GH_STUB, encoding="utf-8")
    gh.chmod(0o755)
    calls = tmp_path / "gh-calls.txt"

    env = {
        **os.environ,
        "PATH": f"{bindir}{os.pathsep}{os.environ['PATH']}",
        "GH_CALLS": str(calls),
    }
    proc = subprocess.run(
        [str(script), version, "--repo", "fake/core", "--remote", str(origin), *args],
        env=env,
        capture_output=True,
        text=True,
    )
    if expect_ok:
        assert proc.returncode == 0, f"script failed:\n{proc.stdout}\n{proc.stderr}"
    return proc, _read_gh_calls(calls)


def _remote_branches(origin):
    out = _git("for-each-ref", "--format=%(refname:short)", "refs/heads", cwd=origin)
    return out.split()


def _file_at(origin, branch, path):
    return _git("show", f"{branch}:{path}", cwd=origin)


def test_publishes_unversioned_yaml_and_json_and_opens_pr(tmp_path):
    """The happy path: both renderings land unversioned, in one commit."""
    origin = _make_origin(tmp_path)
    proc, gh_args = _run(tmp_path, origin)

    assert "release/metric-v1.0.0" in _remote_branches(origin)
    assert _file_at(origin, "release/metric-v1.0.0", DEST_YAML) == SRC_YAML.read_text(
        encoding="utf-8"
    )
    assert _file_at(origin, "release/metric-v1.0.0", DEST_JSON) == SRC_JSON.read_text(
        encoding="utf-8"
    )

    # The versioned names must not follow the files across.
    tree = _git("ls-tree", "--name-only", "release/metric-v1.0.0", cwd=origin)
    assert DEST_YAML in tree.split() and DEST_JSON in tree.split()
    assert f"airbds_metric_v{VERSION}" not in tree

    assert "pr" in gh_args and "create" in gh_args
    assert "--base" in gh_args and gh_args[gh_args.index("--base") + 1] == "main"
    assert gh_args[gh_args.index("--head") + 1] == "release/metric-v1.0.0"
    assert gh_args[gh_args.index("--repo") + 1] == "fake/core"
    assert f"v{VERSION}" in gh_args[gh_args.index("--title") + 1]
    assert "--draft" not in gh_args
    assert "https://github.com/fake/core/pull/1" in proc.stdout


def test_both_renderings_land_in_a_single_commit(tmp_path):
    """Not two commits and not two PRs — core must never hold a half release."""
    origin = _make_origin(tmp_path)
    _run(tmp_path, origin)

    branch = f"release/metric-v{VERSION}"
    commits = _git("rev-list", "main.." + branch, cwd=origin).split()
    assert len(commits) == 1
    changed = _git(
        "show", "--name-only", "--format=", commits[0], cwd=origin
    ).split()
    assert DEST_YAML in changed and DEST_JSON in changed


def test_pr_body_names_both_published_files(tmp_path):
    origin = _make_origin(tmp_path)
    _, gh_args = _run(tmp_path, origin)

    body = gh_args[gh_args.index("--body") + 1]
    assert DEST_YAML in body and DEST_JSON in body
    assert f"metric/airbds_metric_v{VERSION}.yaml" in body
    assert f"metric/airbds_metric_v{VERSION}.json" in body


def test_dry_run_pushes_nothing(tmp_path):
    origin = _make_origin(tmp_path)
    proc, gh_args = _run(tmp_path, origin, "--dry-run")

    assert _remote_branches(origin) == ["main"]
    assert gh_args == []
    assert "not pushing" in proc.stdout


def test_stamps_metric_version_and_leaves_the_skill_version_alone(tmp_path):
    """The published YAML is unversioned, so the README sentence carries the version."""
    origin = _make_origin(tmp_path)
    _run(tmp_path, origin)

    readme = _file_at(origin, f"release/metric-v{VERSION}", CORE_SKILLS_README_PATH)
    assert f"<!--metric-version-->{VERSION}<!--/metric-version-->" in readme
    # Not this release's number to set: a metric release that moved it would
    # announce a skill version that was never published.
    assert "<!--skill-version-->0.8.0<!--/skill-version-->" in readme


def test_stale_readme_alone_is_still_a_release(tmp_path):
    """Metric unchanged but the prose stale: the stamp is reason enough to publish."""
    origin = _make_origin(
        tmp_path,
        seed_metric=SRC_YAML.read_text(encoding="utf-8"),
        seed_metric_json=SRC_JSON.read_text(encoding="utf-8"),
    )
    proc, gh_args = _run(tmp_path, origin)

    assert f"release/metric-v{VERSION}" in _remote_branches(origin)
    assert "nothing to release" not in proc.stdout
    assert gh_args != []


def test_refuses_a_readme_without_markers(tmp_path):
    """An unconverted README fails the release rather than silently skipping it."""
    origin = _make_origin(tmp_path, seed_readme="# AIRBDS assessment skills\n\nv0.0.1.\n")
    proc, gh_args = _run(tmp_path, origin, expect_ok=False)

    assert proc.returncode != 0
    assert "no <!--metric-version-->" in proc.stderr
    assert "post-copy hook failed" in proc.stderr
    assert _remote_branches(origin) == ["main"]
    assert gh_args == []


def _current_readme():
    """The core README already stamped with this release's metric version."""
    return CORE_SKILLS_README.replace(
        ">0.0.1<!--/metric-version", f">{VERSION}<!--/metric-version"
    )


def test_no_op_when_already_published(tmp_path):
    """Re-releasing an unchanged metric succeeds without creating a branch or PR."""
    origin = _make_origin(
        tmp_path,
        seed_metric=SRC_YAML.read_text(encoding="utf-8"),
        seed_metric_json=SRC_JSON.read_text(encoding="utf-8"),
        # Current README too, or the stamp alone would make this a release.
        seed_readme=_current_readme(),
    )
    proc, gh_args = _run(tmp_path, origin)

    assert _remote_branches(origin) == ["main"]
    assert gh_args == []
    assert "nothing to release" in proc.stdout


def test_a_stale_json_alone_is_still_a_release(tmp_path):
    """The YAML already current is not enough — core must not keep an old JSON.

    This is the case that made a single-file release unsafe: publishing only the
    YAML would leave the two files in core describing different metrics.
    """
    stale = json.loads(SRC_JSON.read_text(encoding="utf-8"))
    stale["schema_version"] = "0.0.1"
    origin = _make_origin(
        tmp_path,
        seed_metric=SRC_YAML.read_text(encoding="utf-8"),
        seed_metric_json=json.dumps(stale, indent=2) + "\n",
        seed_readme=_current_readme(),
    )
    proc, gh_args = _run(tmp_path, origin)

    assert f"release/metric-v{VERSION}" in _remote_branches(origin)
    assert "nothing to release" not in proc.stdout
    assert _file_at(origin, f"release/metric-v{VERSION}", DEST_JSON) == SRC_JSON.read_text(
        encoding="utf-8"
    )


def test_refuses_a_version_whose_json_is_missing(tmp_path):
    """From v1.0.0 a missing JSON means the generator was not rerun."""
    origin = _make_origin(tmp_path)
    script = _fake_repo(tmp_path, VERSION, SRC_YAML.read_text(encoding="utf-8"))
    proc, gh_args = _run(tmp_path, origin, expect_ok=False, script=script)

    assert proc.returncode != 0
    assert "no JSON rendering" in proc.stderr
    assert _remote_branches(origin) == ["main"]
    assert gh_args == []


def test_refuses_a_json_that_disagrees_with_the_yaml(tmp_path):
    """A source pair that is not the same metric fails before anything is cloned."""
    drifted = json.loads(SRC_JSON.read_text(encoding="utf-8"))
    drifted["grade_points"]["Critical"] = 1
    origin = _make_origin(tmp_path)
    script = _fake_repo(
        tmp_path,
        VERSION,
        SRC_YAML.read_text(encoding="utf-8"),
        json.dumps(drifted, indent=2) + "\n",
    )
    proc, gh_args = _run(tmp_path, origin, expect_ok=False, script=script)

    assert proc.returncode != 0
    assert "grade_points" in proc.stderr
    assert "renderings disagree" in proc.stderr
    assert _remote_branches(origin) == ["main"]
    assert gh_args == []


def test_pre_1_0_versions_publish_the_yaml_alone(tmp_path):
    """v0.3 and v0.4 predate the JSON rendering and are exempt, not broken."""
    origin = _make_origin(tmp_path)
    proc, gh_args = _run(tmp_path, origin, version=LEGACY_VERSION)

    branch = f"release/metric-v{LEGACY_VERSION}"
    tree = _git("ls-tree", "--name-only", branch, cwd=origin).split()
    assert DEST_YAML in tree
    assert DEST_JSON not in tree
    assert "predates the JSON rendering" in proc.stderr
    assert gh_args != []


def test_custom_branch_base_and_draft(tmp_path):
    origin = _make_origin(tmp_path)
    _, gh_args = _run(
        tmp_path, origin, "--branch", "publish/v1.0.0", "--base", "main", "--draft"
    )

    assert "publish/v1.0.0" in _remote_branches(origin)
    assert gh_args[gh_args.index("--head") + 1] == "publish/v1.0.0"
    assert "--draft" in gh_args


def test_refuses_existing_release_branch(tmp_path):
    origin = _make_origin(tmp_path)
    _run(tmp_path, origin)  # first release creates the branch
    proc, _ = _run(tmp_path, origin, expect_ok=False)

    assert proc.returncode != 0
    assert "already exists" in proc.stderr


def test_rejects_unknown_version(tmp_path):
    origin = _make_origin(tmp_path)
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    proc = subprocess.run(
        [str(SCRIPT), "9.9", "--remote", str(origin)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "no metric file for v9.9" in proc.stderr


def test_rejects_malformed_version(tmp_path):
    proc = subprocess.run([str(SCRIPT), "latest"], capture_output=True, text=True)
    assert proc.returncode != 0
    assert "version must look like" in proc.stderr


if __name__ == "__main__":
    import sys
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
