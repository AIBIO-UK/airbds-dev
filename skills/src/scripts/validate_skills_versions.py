#!/usr/bin/env python3
"""Validate skills/versions.json — the per-channel skill update manifest.

The assessment skills fetch this manifest at runtime to tell a user when a newer
skill (one targeting a newer AIRBDS metric version) is available for their
channel. A stale manifest would either suppress a needed update prompt or nag
users who are already current, so it is checked in CI.

The manifest restates facts that also live in the skill bundles themselves — a
channel's skill version is in its `SKILL.md`, and the metric it scores against is
whatever its `assets/airbds_metric.json` symlink resolves to. Both copies are
maintained by hand, so the useful checks here are the cross-checks: a channel
that says one thing and ships another is the failure this catches.

Checks:
  1. skills/versions.json is present and valid JSON.
  2. It has a non-empty `channels` map; each channel entry has non-empty string
     `metric_version`, `skill_version`, and `skill_update_url` fields.
  3. Every advertised `metric_version` has a matching
     `metric/airbds_metric_v<version>.yaml` file in the repo.

  For channels with a source directory in this repo (`development`, `testing` —
  `production` has none, being derived from `testing` at release time and gated
  by release_skill_to_core.sh):

  4. `skill_version` matches that channel's SKILL.md `metadata.version`.
  5. `metric_version` matches the `schema_version` of the metric the channel's
     `assets/airbds_metric.json` symlink actually resolves to. This is what
     catches a repointed symlink with an unbumped manifest, or the reverse.
  6. SKILL.md `metadata.channel` matches the directory the skill sits in.

  With --since <git-ref>, additionally:

  7. Any channel whose `metric_version` changed since that ref has had its
     `skill_version` raised by at least a MINOR. A new metric changes what the
     bundle contains and what it scores against, so it is not a patch-level
     change to the skill.

Exits 0 when the manifest is valid, 1 (listing every problem) otherwise.

Run locally:  python3 skills/src/scripts/validate_skills_versions.py
              python3 skills/src/scripts/validate_skills_versions.py --since HEAD
Run in CI:    .github/workflows/validate-skills-versions.yml
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[3]
REQUIRED_CHANNEL_FIELDS = ("metric_version", "skill_version", "skill_update_url")
SKILL_DIR_NAME = "airbds-assessment-skill"
MANIFEST_REL = "skills/versions.json"


def skill_md_path(repo_root: Path, channel: str) -> Path:
    return repo_root / "skills" / channel / SKILL_DIR_NAME / "SKILL.md"


def read_front_matter(path: Path) -> dict:
    """The SKILL.md YAML front matter, without requiring PyYAML.

    Only two scalar fields are needed (`metadata.version`, `metadata.channel`),
    and this script is otherwise stdlib-only — worth keeping it that way so CI
    needs no install step.
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    block = text[3:end] if end != -1 else text[3:]
    out, in_metadata = {}, False
    for line in block.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if re.match(r"^metadata:\s*$", line):
            in_metadata = True
            continue
        if not line.startswith((" ", "\t")):
            in_metadata = False
        if in_metadata:
            m = re.match(r"^\s+(\w+):\s*(.+?)\s*$", line)
            if m:
                out[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return out


def parse_version(value: str):
    """('1', '0', '1') -> (1, 0, 1); None if it is not a numeric X.Y[.Z]."""
    m = re.fullmatch(r"(\d+)\.(\d+)(?:\.(\d+))?", value.strip())
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))


def git_show(repo_root: Path, ref: str, rel_path: str):
    """A file's content at a git ref, or None if it cannot be read there."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "show", f"{ref}:{rel_path}"],
            capture_output=True, text=True, check=False,
        )
    except OSError:
        return None
    return proc.stdout if proc.returncode == 0 else None


def check_against_sources(repo_root: Path, name: str, entry: dict, errors: list):
    """Cross-check one channel's manifest entry against its skill bundle."""
    skill_md = skill_md_path(repo_root, name)
    if not skill_md.exists():
        return False  # no source directory — production; nothing to cross-check

    fm = read_front_matter(skill_md)
    rel_md = skill_md.relative_to(repo_root)

    declared = fm.get("version")
    if declared is None:
        errors.append(f"channel '{name}': {rel_md} has no metadata.version")
    elif declared != entry.get("skill_version"):
        errors.append(
            f"channel '{name}': manifest skill_version '{entry.get('skill_version')}' "
            f"but {rel_md} declares metadata.version '{declared}'"
        )

    if fm.get("channel") not in (None, name):
        errors.append(
            f"channel '{name}': {rel_md} declares metadata.channel "
            f"'{fm.get('channel')}' but sits in the '{name}' directory"
        )

    bundled = repo_root / "skills" / name / SKILL_DIR_NAME / "assets" / "airbds_metric.json"
    rel_bundled = bundled.relative_to(repo_root)
    if not bundled.exists():
        errors.append(
            f"channel '{name}': {rel_bundled} is missing or its symlink is broken"
        )
        return True
    try:
        schema_version = json.loads(bundled.read_text(encoding="utf-8")).get(
            "schema_version"
        )
    except json.JSONDecodeError as exc:
        errors.append(f"channel '{name}': {rel_bundled} is not valid JSON: {exc}")
        return True
    if schema_version != entry.get("metric_version"):
        target = bundled.resolve().name if bundled.is_symlink() else rel_bundled.name
        errors.append(
            f"channel '{name}': manifest metric_version "
            f"'{entry.get('metric_version')}' but the bundled metric "
            f"({target}) is schema_version '{schema_version}' — repoint the "
            f"symlink or fix the manifest so the skill scores against what it "
            f"advertises"
        )
    return True


def check_bump_since(repo_root: Path, channels: dict, ref: str, errors: list):
    """A channel that moved to a new metric must have moved at least a minor."""
    raw = git_show(repo_root, ref, MANIFEST_REL)
    if raw is None:
        errors.append(f"--since: cannot read {MANIFEST_REL} at git ref '{ref}'")
        return
    try:
        before = json.loads(raw).get("channels") or {}
    except json.JSONDecodeError as exc:
        errors.append(f"--since: {MANIFEST_REL} at '{ref}' is not valid JSON: {exc}")
        return

    for name, entry in channels.items():
        old = before.get(name)
        if not isinstance(old, dict):
            continue  # new channel — nothing to compare against
        if old.get("metric_version") == entry.get("metric_version"):
            continue

        old_skill = parse_version(str(old.get("skill_version", "")))
        new_skill = parse_version(str(entry.get("skill_version", "")))
        if old_skill is None or new_skill is None:
            errors.append(
                f"channel '{name}': metric_version changed but skill_version "
                f"'{old.get('skill_version')}' -> '{entry.get('skill_version')}' "
                f"is not a numeric version, so the bump cannot be checked"
            )
            continue
        if new_skill[:2] <= old_skill[:2]:
            errors.append(
                f"channel '{name}': metric_version "
                f"'{old.get('metric_version')}' -> '{entry.get('metric_version')}' "
                f"but skill_version only went '{old.get('skill_version')}' -> "
                f"'{entry.get('skill_version')}'. A new metric changes what the "
                f"bundle contains and what it scores against — that is at least a "
                f"MINOR skill bump, not a patch"
            )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--since", metavar="REF",
        help="git ref to compare the manifest against, enabling the skill-version "
             "bump check (e.g. HEAD, origin/main, a base commit SHA)",
    )
    ap.add_argument(
        "--repo-root", type=Path, default=DEFAULT_REPO_ROOT,
        help=argparse.SUPPRESS,  # tests point this at a synthetic tree
    )
    args = ap.parse_args(argv)

    repo_root = args.repo_root.resolve()
    manifest = repo_root / MANIFEST_REL

    if not manifest.exists():
        print(f"ERROR: manifest not found at {MANIFEST_REL}")
        return 1

    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: {MANIFEST_REL} is not valid JSON: {e}")
        return 1

    channels = data.get("channels")
    if not isinstance(channels, dict) or not channels:
        print(f"ERROR: {MANIFEST_REL} has no non-empty 'channels' object.")
        return 1

    errors: list = []
    cross_checked = []
    for name, entry in channels.items():
        if not isinstance(entry, dict):
            errors.append(f"channel '{name}': entry must be an object")
            continue
        for field in REQUIRED_CHANNEL_FIELDS:
            value = entry.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(
                    f"channel '{name}': missing or empty string field '{field}'"
                )
        version = entry.get("metric_version")
        if isinstance(version, str) and version.strip():
            metric_file = repo_root / "metric" / f"airbds_metric_v{version}.yaml"
            if not metric_file.exists():
                errors.append(
                    f"channel '{name}': advertises metric_version '{version}' but "
                    f"metric/{metric_file.name} does not exist"
                )
        if check_against_sources(repo_root, name, entry, errors):
            cross_checked.append(name)

    if args.since:
        check_bump_since(repo_root, channels, args.since, errors)

    if errors:
        print(f"{MANIFEST_REL} validation FAILED ({len(errors)} problem(s)):")
        for e in errors:
            print(f"  - {e}")
        return 1

    versions = sorted({c["metric_version"] for c in channels.values()})
    print(
        f"{MANIFEST_REL} OK — {len(channels)} channel(s); advertised metric "
        f"versions {versions} all have matching metric files."
    )
    print(
        f"  cross-checked against the skill bundles: "
        f"{', '.join(sorted(cross_checked)) or 'none'}"
        + (f"; skill-version bumps checked since {args.since}" if args.since else "")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
