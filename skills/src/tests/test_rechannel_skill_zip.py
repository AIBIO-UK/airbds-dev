#!/usr/bin/env python3
"""Tests for the channel rewrite that turns the tested zip into the production one.

The rewrite is what replaces the old byte-for-byte promotion guarantee, so these
tests are mostly about what it refuses to do: change anything but the channel,
or make a change it cannot prove was only the channel.

Run directly:
    python3 skills/src/tests/test_rechannel_skill_zip.py
or under pytest:
    pytest skills/src/tests/test_rechannel_skill_zip.py
"""

import importlib.util
import subprocess
import sys
import zipfile
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent.parent.parent
SCRIPT = REPO_ROOT / "skills" / "src" / "scripts" / "rechannel_skill_zip.py"

_spec = importlib.util.spec_from_file_location("rechannel_skill_zip", SCRIPT)
rechannel = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rechannel)

# The channel references a real bundle carries: the frontmatter field the client
# reads, and the prose telling the skill which manifest entry is its own.
SKILL_MD = """---
name: airbds-assessment-skill
description: Test bundle.
metadata:
  version: "0.7.1"
  channel: {channel}
---

# AIRBDS assessment skill

Look up `channels.{channel}` in the manifest, matching this skill's own
`metadata.channel` (`{channel}`). Ignore every other channel.
"""

# Modes matter: score.py is executable in the bundle and must stay that way.
MEMBERS = {
    "assets/airbds_metric.json": (b'{"schema_version": "0.5"}', 0o644),
    "scripts/score.py": (b"#!/usr/bin/env python3\n", 0o755),
}


def _make_zip(path, channel="testing", skill_md=None):
    text = skill_md if skill_md is not None else SKILL_MD.format(channel=channel)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        info = zipfile.ZipInfo("SKILL.md", date_time=(2026, 7, 30, 12, 35, 22))
        info.external_attr = 0o644 << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info, text.encode("utf-8"))
        for name, (data, mode) in MEMBERS.items():
            info = zipfile.ZipInfo(name, date_time=(2026, 7, 30, 12, 35, 22))
            info.external_attr = mode << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)
    return path


def _run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *[str(a) for a in args]],
        capture_output=True,
        text=True,
    )


def _read(path, name):
    with zipfile.ZipFile(path) as z:
        return z.read(name)


def test_rewrites_only_the_channel(tmp_path):
    src = _make_zip(tmp_path / "testing.zip")
    out = tmp_path / "production.zip"
    proc = _run("--in", src, "--out", out)
    assert proc.returncode == 0, proc.stderr

    text = _read(out, "SKILL.md").decode()
    assert "channel: production" in text
    assert "channels.production" in text
    assert "testing" not in text
    # The one guarantee the PR body claims: undoing the swap gives back the
    # tested file exactly.
    assert text.replace("production", "testing").encode() == _read(src, "SKILL.md")

    for name, (data, _) in MEMBERS.items():
        assert _read(out, name) == data

    with zipfile.ZipFile(src) as a, zipfile.ZipFile(out) as b:
        before = {i.filename: i for i in a.infolist()}
        after = {i.filename: i for i in b.infolist()}
        assert list(before) == list(after)
        for name, info in before.items():
            assert after[name].external_attr == info.external_attr, name
            assert after[name].date_time == info.date_time, name
            assert after[name].compress_type == info.compress_type, name


def test_refuses_when_the_rewrite_is_not_reversible(tmp_path):
    """A source already mentioning the target channel cannot be checked."""
    md = SKILL_MD.format(channel="testing") + "\nNot for production use.\n"
    src = _make_zip(tmp_path / "testing.zip", skill_md=md)
    out = tmp_path / "production.zip"
    proc = _run("--in", src, "--out", out)

    assert proc.returncode != 0
    assert "not reversible" in proc.stderr


def test_refuses_a_bundle_from_another_channel(tmp_path):
    src = _make_zip(tmp_path / "development.zip", channel="development")
    proc = _run("--in", src, "--out", tmp_path / "production.zip")

    assert proc.returncode != 0
    assert "never mentions the 'testing' channel" in proc.stderr


def test_rejects_zip_without_skill_md(tmp_path):
    src = tmp_path / "bogus.zip"
    with zipfile.ZipFile(src, "w") as z:
        z.writestr("readme.txt", "not a skill")
    proc = _run("--in", src, "--out", tmp_path / "out.zip")

    assert proc.returncode != 0
    assert "no SKILL.md" in proc.stderr


def test_check_accepts_a_faithful_rewrite(tmp_path):
    """--check is how a reviewer of the airbds-core PR audits the artifact."""
    src = _make_zip(tmp_path / "testing.zip")
    out = tmp_path / "production.zip"
    assert _run("--in", src, "--out", out).returncode == 0

    proc = _run("--in", src, "--check", out)
    assert proc.returncode == 0, proc.stderr
    assert "verified" in proc.stdout


def test_check_rejects_a_tampered_member(tmp_path):
    src = _make_zip(tmp_path / "testing.zip")
    out = tmp_path / "production.zip"
    assert _run("--in", src, "--out", out).returncode == 0

    # Rebuild the "published" zip with a smuggled change to the scorer.
    tampered = tmp_path / "tampered.zip"
    with zipfile.ZipFile(out) as a, zipfile.ZipFile(tampered, "w") as b:
        for info in a.infolist():
            data = a.read(info.filename)
            if info.filename == "scripts/score.py":
                data += b"# smuggled\n"
            b.writestr(info, data)

    proc = _run("--in", src, "--check", tampered)
    assert proc.returncode != 0
    assert "scripts/score.py: content differs" in proc.stderr


def test_check_rejects_an_unrewritten_zip(tmp_path):
    """Publishing the tested zip as-is is the bug this whole step exists for."""
    src = _make_zip(tmp_path / "testing.zip")
    proc = _run("--in", src, "--check", src)

    assert proc.returncode != 0
    assert "still mentions the 'testing' channel" in proc.stderr


def test_check_rejects_a_zip_missing_a_member(tmp_path):
    src = _make_zip(tmp_path / "testing.zip")
    out = tmp_path / "production.zip"
    assert _run("--in", src, "--out", out).returncode == 0

    stripped = tmp_path / "stripped.zip"
    with zipfile.ZipFile(out) as a, zipfile.ZipFile(stripped, "w") as b:
        for info in a.infolist():
            if info.filename != "scripts/score.py":
                b.writestr(info, a.read(info.filename))

    proc = _run("--in", src, "--check", stripped)
    assert proc.returncode != 0
    assert "member lists differ" in proc.stderr


def test_rewrite_text_reports_the_lines_it_changed(tmp_path):
    text = SKILL_MD.format(channel="testing")
    new_text, changed = rechannel.rewrite_text(text, "testing", "production")

    assert "testing" not in new_text
    lines = text.splitlines()
    assert changed and all(
        "testing" in lines[n - 1] for n in changed
    ), (changed, lines)


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
