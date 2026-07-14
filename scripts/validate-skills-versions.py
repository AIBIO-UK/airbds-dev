#!/usr/bin/env python3
"""Validate skills/versions.json — the per-channel skill update manifest.

The assessment skills fetch this manifest at runtime to tell a user when a newer
skill (one targeting a newer AIRBDS metric version) is available for their
channel. A stale manifest would either suppress a needed update prompt or nag
users who are already current, so it is checked in CI.

Checks:
  1. skills/versions.json is present and valid JSON.
  2. It has a non-empty `channels` map; each channel entry has non-empty string
     `metric_version`, `skill_version`, and `skill_update_url` fields.
  3. Every advertised `metric_version` has a matching
     `metric/airbds_metric_v<version>.yaml` file in the repo.

Exits 0 when the manifest is valid, 1 (listing every problem) otherwise.

Run locally:  python3 scripts/validate-skills-versions.py
Run in CI:    .github/workflows/validate-skills-versions.yml
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "skills" / "versions.json"
REQUIRED_CHANNEL_FIELDS = ("metric_version", "skill_version", "skill_update_url")


def main() -> int:
    rel = MANIFEST.relative_to(REPO_ROOT)

    if not MANIFEST.exists():
        print(f"ERROR: manifest not found at {rel}")
        return 1

    try:
        data = json.loads(MANIFEST.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: {rel} is not valid JSON: {e}")
        return 1

    channels = data.get("channels")
    if not isinstance(channels, dict) or not channels:
        print(f"ERROR: {rel} has no non-empty 'channels' object.")
        return 1

    errors = []
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
            metric_file = REPO_ROOT / "metric" / f"airbds_metric_v{version}.yaml"
            if not metric_file.exists():
                errors.append(
                    f"channel '{name}': advertises metric_version '{version}' but "
                    f"{metric_file.relative_to(REPO_ROOT)} does not exist"
                )

    if errors:
        print(f"{rel} validation FAILED ({len(errors)} problem(s)):")
        for e in errors:
            print(f"  - {e}")
        return 1

    versions = sorted({c["metric_version"] for c in channels.values()})
    print(
        f"{rel} OK — {len(channels)} channel(s); advertised metric "
        f"versions {versions} all have matching metric files."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
