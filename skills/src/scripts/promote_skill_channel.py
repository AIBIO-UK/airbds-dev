#!/usr/bin/env python3
"""Promote the assessment skill from one channel's source directory to another.

`development` -> `testing` was a manual directory copy plus a hand-edit of the
channel token in `SKILL.md`. Both halves are easy to get subtly wrong: a copy
that dereferences the symlinked metric and template into real files (so the
bundle silently stops tracking them), a missed mention of the old channel in the
update-check prose, or a promotion that leaves `skills/versions.json` describing
the bundle that used to be there.

This does the same job in one step and says exactly what it changed:

    ./skills/src/scripts/promote_skill_channel.py --dry-run   # rehearse
    ./skills/src/scripts/promote_skill_channel.py             # do it

A bundle carries its channel *inside* it — `metadata.channel` in `SKILL.md`, plus
the prose telling the skill which `channels.<name>` entry of the update manifest
to read — so the token substitution is the whole difference between two channels'
sources. It reuses `rechannel_skill_zip.rewrite_text`, which refuses any
substitution it cannot prove reversible, so the same guarantee applies here as
when the production zip is derived at release time: only the channel changed.

Symlinks are recreated as symlinks pointing at the same relative target, never
followed. That is what keeps a channel tracking the current metric and review
template instead of freezing a copy of them; the build workflow dereferences them
when it zips, which is the right and only place for that to happen.

`skills/versions.json` is updated for the destination channel to describe what
was just promoted — the `skill_version` from the promoted `SKILL.md` and the
`metric_version` from the metric its symlink resolves to. Skipping that would
leave the manifest advertising the previous bundle, which
validate_skills_versions.py would then reject.

  --check   report whether the destination is already the promotion of the source
            without writing anything. Channels are allowed to differ — `testing`
            is a snapshot of `development` taken at promotion time, not a mirror
            — so a difference is information, not an error, and --check exits 0
            either way unless something is actually broken.

Needs only the standard library. See skills/docs/MAINTENANCE.md.
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rechannel_skill_zip import (  # noqa: E402  (sibling module, after sys.path tweak)
    RechannelError,
    rewrite_text,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR_NAME = "airbds-assessment-skill"
MANIFEST_REL = "skills/versions.json"

# Build artefacts and editor droppings that live under a channel but are not part
# of the bundle. Never copied, and never deleted from the destination either.
IGNORED_NAMES = {"__pycache__", ".DS_Store", ".pytest_cache"}


def channel_dir(repo_root: Path, channel: str) -> Path:
    return repo_root / "skills" / channel / SKILL_DIR_NAME


def bundle_entries(root: Path):
    """Every path in a bundle, relative to it, skipping ignored names.

    Symlinks are yielded as entries in their own right and never descended into,
    so a symlinked directory would be recreated as a link rather than walked.
    """
    out = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames if d not in IGNORED_NAMES)
        here = Path(dirpath)
        for name in sorted(dirnames) + sorted(filenames):
            if name in IGNORED_NAMES:
                continue
            out.append((here / name).relative_to(root))
    return sorted(set(out))


def read_skill_version(skill_md: Path):
    """`metadata.version` from the front matter, without needing PyYAML."""
    in_metadata = False
    for line in skill_md.read_text(encoding="utf-8").splitlines():
        if line.strip() == "---" and in_metadata:
            break
        if line.rstrip() == "metadata:":
            in_metadata = True
            continue
        if in_metadata and not line.startswith((" ", "\t")):
            in_metadata = False
        if in_metadata and line.strip().startswith("version:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return None


def read_bundled_metric_version(bundle: Path):
    """`schema_version` of the metric the bundle's assets symlink resolves to."""
    path = bundle / "assets" / "airbds_metric.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("schema_version")
    except json.JSONDecodeError:
        return None


def plan(src_root: Path, dst_root: Path, src_channel: str, dst_channel: str):
    """What promoting would do, as (action, relative-path) pairs.

    Actions: 'rechannel' (SKILL.md, token substituted), 'link', 'copy', 'mkdir',
    'delete'. Raises RechannelError if SKILL.md cannot be rewritten verifiably.
    """
    src_entries = bundle_entries(src_root)
    dst_entries = bundle_entries(dst_root) if dst_root.exists() else []
    actions = []

    for rel in src_entries:
        src = src_root / rel
        dst = dst_root / rel
        if src.is_symlink():
            target = os.readlink(src)
            current = os.readlink(dst) if dst.is_symlink() else None
            if current != target:
                actions.append(("link", rel, target))
        elif src.is_dir():
            if not dst.is_dir():
                actions.append(("mkdir", rel, None))
        elif rel == Path("SKILL.md"):
            new_text, changed = rewrite_text(
                src.read_text(encoding="utf-8"), src_channel, dst_channel
            )
            existing = dst.read_text(encoding="utf-8") if dst.is_file() else None
            if existing != new_text:
                actions.append(("rechannel", rel, changed))
        else:
            same = (
                dst.is_file()
                and not dst.is_symlink()
                and dst.read_bytes() == src.read_bytes()
            )
            if not same:
                actions.append(("copy", rel, None))

    for rel in dst_entries:
        if rel not in src_entries:
            actions.append(("delete", rel, None))

    return actions


def apply(actions, src_root: Path, dst_root: Path, src_channel: str, dst_channel: str):
    for action, rel, extra in actions:
        dst = dst_root / rel
        if action == "delete":
            if dst.is_symlink() or dst.is_file():
                dst.unlink()
            elif dst.is_dir():
                shutil.rmtree(dst)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if action == "mkdir":
            dst.mkdir(exist_ok=True)
        elif action == "link":
            if dst.is_symlink() or dst.exists():
                dst.unlink()
            os.symlink(extra, dst)
        elif action == "rechannel":
            src_text = (src_root / rel).read_text(encoding="utf-8")
            new_text, _ = rewrite_text(src_text, src_channel, dst_channel)
            dst.write_text(new_text, encoding="utf-8")
        elif action == "copy":
            shutil.copy2(src_root / rel, dst, follow_symlinks=False)


def manifest_update(repo_root: Path, dst_channel: str, skill_version, metric_version):
    """The destination channel's entry, and what it should become. None if same."""
    path = repo_root / MANIFEST_REL
    data = json.loads(path.read_text(encoding="utf-8"))
    entry = (data.get("channels") or {}).get(dst_channel)
    if entry is None:
        raise RechannelError(f"{MANIFEST_REL} has no '{dst_channel}' channel")
    changes = {}
    if skill_version and entry.get("skill_version") != skill_version:
        changes["skill_version"] = (entry.get("skill_version"), skill_version)
    if metric_version and entry.get("metric_version") != metric_version:
        changes["metric_version"] = (entry.get("metric_version"), metric_version)
    return path, data, changes


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--from", dest="source", default="development",
                    help="channel to promote from (default: development)")
    ap.add_argument("--to", dest="target", default="testing",
                    help="channel to promote to (default: testing)")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change; write nothing")
    ap.add_argument("--check", action="store_true",
                    help="report whether the target is already this promotion")
    ap.add_argument("--repo-root", type=Path, default=REPO_ROOT,
                    help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    repo_root = args.repo_root.resolve()
    src_root = channel_dir(repo_root, args.source)
    dst_root = channel_dir(repo_root, args.target)

    if not src_root.is_dir():
        print(f"ERROR: no source bundle at {src_root.relative_to(repo_root)}")
        return 1
    if not dst_root.exists():
        print(f"ERROR: no target bundle at {dst_root.relative_to(repo_root)} — "
              f"this promotes between existing channels, it does not create one")
        return 1
    # Symlink targets are relative and are copied verbatim, so the two bundles
    # must sit at the same depth or every link would resolve somewhere else.
    if len(src_root.relative_to(repo_root).parts) != len(
        dst_root.relative_to(repo_root).parts
    ):
        print("ERROR: the two channel directories are at different depths, so "
              "their relative symlinks are not interchangeable")
        return 1

    try:
        actions = plan(src_root, dst_root, args.source, args.target)
        skill_version = read_skill_version(src_root / "SKILL.md")
        metric_version = read_bundled_metric_version(src_root)
        manifest_path, manifest_data, manifest_changes = manifest_update(
            repo_root, args.target, skill_version, metric_version
        )
    except RechannelError as exc:
        print(f"ERROR: {exc}")
        return 1

    if not actions and not manifest_changes:
        print(f"'{args.target}' is already the promotion of '{args.source}' — "
              f"nothing to do.")
        return 0

    verb = "would" if (args.dry_run or args.check) else "will"
    print(f"Promoting '{args.source}' -> '{args.target}':")
    for action, rel, extra in actions:
        if action == "rechannel":
            lines = ", ".join(str(n) for n in extra)
            print(f"  {verb} rewrite  {rel} (channel token; lines {lines})")
        elif action == "link":
            print(f"  {verb} link     {rel} -> {extra}")
        else:
            print(f"  {verb} {action:8} {rel}")
    for field, (old, new) in manifest_changes.items():
        print(f"  {verb} set      {MANIFEST_REL}: {args.target}.{field} "
              f"{old} -> {new}")

    if args.check:
        print(f"\n--check: '{args.target}' is not currently the promotion of "
              f"'{args.source}'. That is allowed — a channel is a snapshot taken "
              f"at promotion time, not a mirror.")
        return 0
    if args.dry_run:
        print("\ndry run: nothing written")
        return 0

    apply(actions, src_root, dst_root, args.source, args.target)
    if manifest_changes:
        for field, (_, new) in manifest_changes.items():
            manifest_data["channels"][args.target][field] = new
        manifest_path.write_text(
            json.dumps(manifest_data, indent=2) + "\n", encoding="utf-8"
        )

    print(f"\nPromoted. Next: review the diff, run "
          f"`python3 skills/src/scripts/validate_skills_versions.py`, and commit "
          f"— pushing to main rebuilds the '{args.target}' release.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
