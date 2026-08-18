#!/usr/bin/env python3
"""Build an installable AIRBDS assessment-skill zip locally, for one channel.

The release zips are produced in CI (`.github/workflows/build-assessment-skill-*`),
which zip a channel's skill directory with its symlinks **dereferenced**: the
bundled metric, review template, and scorer are symlinks in the repo, and an
installable skill needs their real contents, not dangling links. This script does
the same thing locally, so a channel can be built and test-installed before it is
promoted or published — the interactive check in `RELEASING.md` Stage 5.

It is for local testing only. The production release promotes the CI-built
`testing` zip (see `release_skill_to_core.sh`); it never uses a locally built one.

Usage:
    python3 skills/src/scripts/build_skill_zip.py development
    python3 skills/src/scripts/build_skill_zip.py testing -o /tmp/skill.zip

The archive root is the skill directory's contents (`SKILL.md`, `assets/`,
`scripts/`), matching the CI build, so it installs the same way.
"""

import argparse
import os
import sys
import zipfile
from pathlib import Path

# Repo root is four levels up: <root>/skills/src/scripts/<this file>.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SKILL_SUBPATH = "airbds-assessment-skill"


def channel_skill_dir(repo_root: Path, channel: str) -> Path:
    return repo_root / "skills" / channel / SKILL_SUBPATH


def available_channels(repo_root: Path) -> list:
    skills = repo_root / "skills"
    if not skills.is_dir():
        return []
    return sorted(d.name for d in skills.iterdir()
                  if (d / SKILL_SUBPATH).is_dir())


def build_zip(repo_root: Path, channel: str, out_path: Path) -> int:
    """Write an installable zip of the channel's skill to `out_path`.

    Symlinked members are dereferenced — their target bytes are stored as a
    regular file — exactly as the CI `zip` (run without `-y`) does. Returns the
    number of files written.
    """
    src = channel_skill_dir(repo_root, channel)
    if not src.is_dir():
        avail = available_channels(repo_root)
        hint = f" (available: {', '.join(avail)})" if avail else ""
        raise SystemExit(f"ERROR: no skill bundle for channel {channel!r} at {src}{hint}")

    members = []
    for dirpath, dirnames, filenames in os.walk(src, followlinks=True):
        dirnames.sort()
        for name in sorted(filenames):
            members.append(Path(dirpath) / name)
    members.sort()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in members:
            arcname = path.relative_to(src).as_posix()
            try:
                data = path.read_bytes()  # follows symlinks -> real content
            except OSError as exc:
                raise SystemExit(
                    f"ERROR: cannot read bundled file {arcname} ({exc}); "
                    "a symlink in the skill may be dangling."
                )
            zf.writestr(arcname, data)
    return len(members)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Build an installable AIRBDS assessment-skill zip for one "
                    "channel, with bundled symlinks dereferenced (as CI does).")
    ap.add_argument("channel", help="channel to build, e.g. development or testing")
    ap.add_argument("-o", "--output", type=Path, default=None,
                    help="output zip path "
                         "(default: ./airbds-assessment-skill-<channel>.zip)")
    ap.add_argument("--repo-root", type=Path, default=REPO_ROOT,
                    help="repo root (default: inferred from this script's location)")
    args = ap.parse_args()

    repo_root = args.repo_root.resolve()
    out = args.output or Path.cwd() / f"airbds-assessment-skill-{args.channel}.zip"
    count = build_zip(repo_root, args.channel, out)
    print(f"Wrote {out} ({count} files; symlinks dereferenced).")


if __name__ == "__main__":
    main()
