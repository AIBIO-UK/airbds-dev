#!/usr/bin/env python3
"""Offline tests for the assessment-skill release script.

These drive release_skill_to_core.sh end to end against a throwaway local bare
repository standing in for AIBIO-UK/airbds-core, with `gh` replaced by a stub.
The artifact is supplied via --zip, so nothing reaches the network or the real
publication repository.

Run directly:
    python3 skills/src/tests/test_release_skill_to_core.py
or under pytest:
    pytest skills/src/tests/test_release_skill_to_core.py
"""

import hashlib
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent.parent.parent
SCRIPT = REPO_ROOT / "skills" / "src" / "scripts" / "release_skill_to_core.sh"
MANIFEST = REPO_ROOT / "skills" / "versions.json"
DEST_FILE = "skills/airbds-assessment-skill.zip"

# NUL-separated, not newline: the PR body is multi-line, and splitting on
# newlines would silently truncate it to its first line.
GH_STUB = """#!/usr/bin/env bash
printf '%s\\0' "$@" >> "$GH_CALLS"
echo "https://github.com/fake/core/pull/1"
"""


def _read_gh_calls(path):
    if not path.exists():
        return []
    raw = path.read_bytes()
    return [a.decode() for a in raw.split(b"\0")[:-1]] if raw else []


def _manifest_skill_version(channel="production"):
    """The gate is the *target* channel's entry — what production skills poll."""
    return json.loads(MANIFEST.read_text())["channels"][channel]["skill_version"]


def _git(*args, cwd):
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout


def _make_zip(tmp_path, version=None, channel="testing", name="skill.zip", body=""):
    """A minimal skill bundle: SKILL.md frontmatter is all the script reads."""
    if version is None:
        version = _manifest_skill_version()
    skill_md = (
        "---\n"
        "name: airbds-assessment-skill\n"
        "description: Test bundle.\n"
        "metadata:\n"
        f'  version: "{version}"\n'
        f"  channel: {channel}\n"
        "---\n\n# AIRBDS assessment skill\n"
        f"\nLook up `channels.{channel}` in the manifest.\n{body}"
    )
    path = tmp_path / name
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("SKILL.md", skill_md)
        z.writestr("assets/airbds_metric.json", '{"schema_version": "0.5"}')
        z.writestr("scripts/score.py", "# scorer\n")
    return path


def _rechannel(zip_path, out_path, src="testing", dst="production"):
    """What the release script publishes, produced the same way it produces it."""
    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "skills" / "src" / "scripts" / "rechannel_skill_zip.py"),
            "--in", str(zip_path),
            "--out", str(out_path),
            "--from", src,
            "--to", dst,
        ],
        check=True,
        capture_output=True,
    )
    return out_path


def _make_origin(tmp_path, seed_zip=None):
    seed = tmp_path / "seed"
    seed.mkdir()
    _git("init", "--quiet", "--initial-branch=main", cwd=seed)
    _git("config", "user.name", "test", cwd=seed)
    _git("config", "user.email", "test@example.com", cwd=seed)
    (seed / "README.md").write_text("# airbds-core\n", encoding="utf-8")
    if seed_zip is not None:
        dest = seed / DEST_FILE
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(seed_zip.read_bytes())
    _git("add", "-A", cwd=seed)
    _git("commit", "--quiet", "-m", "seed", cwd=seed)

    origin = tmp_path / "core.git"
    _git("clone", "--quiet", "--bare", str(seed), str(origin), cwd=tmp_path)
    return origin


def _run(tmp_path, origin, zip_path, *args, expect_ok=True):
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
        [
            str(SCRIPT),
            "--zip", str(zip_path),
            "--repo", "fake/core",
            "--remote", str(origin),
            *args,
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    if expect_ok:
        assert proc.returncode == 0, f"script failed:\n{proc.stdout}\n{proc.stderr}"
    return proc, _read_gh_calls(calls)


def _remote_branches(origin):
    return _git(
        "for-each-ref", "--format=%(refname:short)", "refs/heads", cwd=origin
    ).split()


def test_publishes_zip_and_opens_pr(tmp_path):
    """The happy path: the zip lands at skills/airbds-assessment-skill.zip."""
    version = _manifest_skill_version()
    zip_path = _make_zip(tmp_path)
    origin = _make_origin(tmp_path)
    proc, gh_args = _run(tmp_path, origin, zip_path)

    branch = f"release/skill-v{version}"
    assert branch in _remote_branches(origin)

    # Compare bytes, not text — a corrupted binary commit is the failure mode.
    published_bytes = subprocess.run(
        ["git", "show", f"{branch}:{DEST_FILE}"],
        cwd=origin, check=True, capture_output=True,
    ).stdout
    published = tmp_path / "published.zip"
    published.write_bytes(published_bytes)
    assert zipfile.ZipFile(published).testzip() is None

    # What ships is the source with its channel rewritten — so not the source
    # bytes, but the bytes the same rewrite produces from them.
    assert published_bytes != zip_path.read_bytes()
    assert published_bytes == _rechannel(zip_path, tmp_path / "expected.zip").read_bytes()

    skill_md = zipfile.ZipFile(published).read("SKILL.md").decode()
    assert "channel: production" in skill_md
    assert "channels.production" in skill_md
    assert "testing" not in skill_md

    assert "pr" in gh_args and "create" in gh_args
    assert gh_args[gh_args.index("--head") + 1] == branch
    assert gh_args[gh_args.index("--base") + 1] == "main"
    assert version in gh_args[gh_args.index("--title") + 1]

    # The PR body must carry both digests: the source one a reviewer checks
    # against the release, and the published one they check against the commit.
    body = gh_args[gh_args.index("--body") + 1]
    assert hashlib.sha256(zip_path.read_bytes()).hexdigest() in body
    assert hashlib.sha256(published_bytes).hexdigest() in body
    assert "https://github.com/fake/core/pull/1" in proc.stdout


def test_refuses_version_mismatch_with_manifest(tmp_path):
    """A zip the manifest does not advertise would ship an unannounced version."""
    zip_path = _make_zip(tmp_path, version="9.9.9")
    origin = _make_origin(tmp_path)
    proc, gh_args = _run(tmp_path, origin, zip_path, expect_ok=False)

    assert proc.returncode != 0
    assert "skills/versions.json advertises" in proc.stderr
    assert _remote_branches(origin) == ["main"]
    assert gh_args == []


def test_force_overrides_version_mismatch(tmp_path):
    zip_path = _make_zip(tmp_path, version="9.9.9")
    origin = _make_origin(tmp_path)
    proc, _ = _run(tmp_path, origin, zip_path, "--force")

    assert "release/skill-v9.9.9" in _remote_branches(origin)
    assert "--force given" in proc.stderr


def test_refuses_wrong_channel(tmp_path):
    """Only a testing build is promoted — including one already marked production."""
    for channel in ("development", "production"):
        zip_path = _make_zip(tmp_path, channel=channel, name=f"{channel}.zip")
        sub = tmp_path / channel
        sub.mkdir()
        origin = _make_origin(sub)
        proc, _ = _run(tmp_path, origin, zip_path, expect_ok=False)

        assert proc.returncode != 0
        assert f"'{channel}' channel" in proc.stderr
        assert _remote_branches(origin) == ["main"]


def test_refuses_an_unverifiable_channel_rewrite(tmp_path):
    """A bundle already mentioning 'production' cannot be rewritten provably."""
    zip_path = _make_zip(tmp_path, body="\nNot for production use.\n")
    origin = _make_origin(tmp_path)
    proc, gh_args = _run(tmp_path, origin, zip_path, expect_ok=False)

    assert proc.returncode != 0
    assert "not reversible" in proc.stderr
    assert _remote_branches(origin) == ["main"]
    assert gh_args == []


def test_force_does_not_override_a_failed_rewrite(tmp_path):
    """--force covers a manifest disagreement, never an unprovable artifact."""
    zip_path = _make_zip(tmp_path, body="\nNot for production use.\n")
    origin = _make_origin(tmp_path)
    proc, _ = _run(tmp_path, origin, zip_path, "--force", expect_ok=False)

    assert proc.returncode != 0
    assert _remote_branches(origin) == ["main"]


def test_rejects_zip_without_skill_md(tmp_path):
    path = tmp_path / "bogus.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("readme.txt", "not a skill")
    origin = _make_origin(tmp_path)
    proc, _ = _run(tmp_path, origin, path, expect_ok=False)

    assert proc.returncode != 0
    assert "no SKILL.md" in proc.stderr


def test_dry_run_pushes_nothing(tmp_path):
    zip_path = _make_zip(tmp_path)
    origin = _make_origin(tmp_path)
    proc, gh_args = _run(tmp_path, origin, zip_path, "--dry-run")

    assert _remote_branches(origin) == ["main"]
    assert gh_args == []
    assert "not pushing" in proc.stdout


def test_no_op_when_already_published(tmp_path):
    """Already-published means the rewritten zip, since that is what is shipped."""
    zip_path = _make_zip(tmp_path)
    published = _rechannel(zip_path, tmp_path / "published.zip")
    origin = _make_origin(tmp_path, seed_zip=published)
    proc, gh_args = _run(tmp_path, origin, zip_path)

    assert _remote_branches(origin) == ["main"]
    assert gh_args == []
    assert "nothing to release" in proc.stdout


def test_refuses_existing_release_branch(tmp_path):
    zip_path = _make_zip(tmp_path)
    origin = _make_origin(tmp_path)
    _run(tmp_path, origin, zip_path)
    proc, _ = _run(tmp_path, origin, zip_path, expect_ok=False)

    assert proc.returncode != 0
    assert "already exists" in proc.stderr


def test_missing_zip_is_an_error(tmp_path):
    origin = _make_origin(tmp_path)
    proc, _ = _run(tmp_path, origin, tmp_path / "nope.zip", expect_ok=False)

    assert proc.returncode != 0
    assert "zip not found" in proc.stderr


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
