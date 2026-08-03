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

import os
import shlex
import subprocess
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent.parent.parent
SCRIPT = REPO_ROOT / "metric" / "src" / "scripts" / "release_metric_to_core.sh"
VERSION = "1.0"
SRC_YAML = REPO_ROOT / "metric" / f"airbds_metric_v{VERSION}.yaml"
DEST_FILE = "airbds_metric.yaml"

# Records its arguments NUL-separated, then prints a plausible PR URL. NUL and
# not newline: the PR body is multi-line, and splitting on newlines would
# silently truncate it to its first line.
GH_STUB = """#!/usr/bin/env bash
printf '%s\\0' "$@" >> "$GH_CALLS"
echo "https://github.com/fake/core/pull/1"
"""


def _read_gh_calls(path):
    if not path.exists():
        return []
    raw = path.read_bytes()
    return [a.decode() for a in raw.split(b"\0")[:-1]] if raw else []


def _git(*args, cwd):
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout


def _make_origin(tmp_path, seed_metric=None):
    """A bare repo with a main branch, standing in for airbds-core."""
    seed = tmp_path / "seed"
    seed.mkdir()
    _git("init", "--quiet", "--initial-branch=main", cwd=seed)
    _git("config", "user.name", "test", cwd=seed)
    _git("config", "user.email", "test@example.com", cwd=seed)
    (seed / "README.md").write_text("# airbds-core\n", encoding="utf-8")
    if seed_metric is not None:
        (seed / DEST_FILE).write_text(seed_metric, encoding="utf-8")
    _git("add", "-A", cwd=seed)
    _git("commit", "--quiet", "-m", "seed", cwd=seed)

    origin = tmp_path / "core.git"
    _git("clone", "--quiet", "--bare", str(seed), str(origin), cwd=tmp_path)
    return origin


def _run(tmp_path, origin, *args, expect_ok=True):
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
        [str(SCRIPT), VERSION, "--repo", "fake/core", "--remote", str(origin), *args],
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


def test_publishes_unversioned_yaml_and_opens_pr(tmp_path):
    """The happy path: versioned source lands as airbds_metric.yaml on a branch."""
    origin = _make_origin(tmp_path)
    proc, gh_args = _run(tmp_path, origin)

    assert "release/metric-v1.0" in _remote_branches(origin)
    published = _file_at(origin, "release/metric-v1.0", DEST_FILE)
    assert published == SRC_YAML.read_text(encoding="utf-8")

    # The versioned name must not follow the file across.
    assert DEST_FILE in _git(
        "ls-tree", "--name-only", "release/metric-v1.0", cwd=origin
    ).split()
    assert f"airbds_metric_v{VERSION}.yaml" not in _git(
        "ls-tree", "--name-only", "release/metric-v1.0", cwd=origin
    )

    assert "pr" in gh_args and "create" in gh_args
    assert "--base" in gh_args and gh_args[gh_args.index("--base") + 1] == "main"
    assert gh_args[gh_args.index("--head") + 1] == "release/metric-v1.0"
    assert gh_args[gh_args.index("--repo") + 1] == "fake/core"
    assert f"v{VERSION}" in gh_args[gh_args.index("--title") + 1]
    assert "--draft" not in gh_args
    assert "https://github.com/fake/core/pull/1" in proc.stdout


def test_dry_run_pushes_nothing(tmp_path):
    origin = _make_origin(tmp_path)
    proc, gh_args = _run(tmp_path, origin, "--dry-run")

    assert _remote_branches(origin) == ["main"]
    assert gh_args == []
    assert "not pushing" in proc.stdout


def test_no_op_when_already_published(tmp_path):
    """Re-releasing an unchanged metric succeeds without creating a branch or PR."""
    origin = _make_origin(tmp_path, seed_metric=SRC_YAML.read_text(encoding="utf-8"))
    proc, gh_args = _run(tmp_path, origin)

    assert _remote_branches(origin) == ["main"]
    assert gh_args == []
    assert "nothing to release" in proc.stdout


def test_custom_branch_base_and_draft(tmp_path):
    origin = _make_origin(tmp_path)
    _, gh_args = _run(
        tmp_path, origin, "--branch", "publish/v1.0", "--base", "main", "--draft"
    )

    assert "publish/v1.0" in _remote_branches(origin)
    assert gh_args[gh_args.index("--head") + 1] == "publish/v1.0"
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
