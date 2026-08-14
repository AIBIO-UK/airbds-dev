#!/usr/bin/env python3
"""Confirm a metric's YAML and JSON renderings carry the same data.

The generator writes both files from one parsed object, so they cannot drift
when they are produced together. They can drift when they are not — a YAML
hand-corrected after the fact, a JSON copied in from somewhere else, a rebuild
that wrote one file and not the other. This is the check that stops such a pair
being published as though it were one metric.

Equality is structural, not textual: the two formats are compared as the objects
they parse to, so indentation, key quoting, and the YAML's comments are all
irrelevant. Only a difference a consumer could observe is a failure.

    python3 metric/src/scripts/check_metric_renderings_match.py \\
        metric/airbds_metric_v1.0.0.yaml metric/airbds_metric_v1.0.0.json

Exits 0 when they match, 1 with the differing top-level keys when they do not.
Used as a preflight by metric/src/scripts/release_metric_to_core.sh.
"""

import argparse
import json
import sys
from pathlib import Path

import yaml


def differing_keys(from_yaml, from_json):
    """Top-level keys that differ, including those present in only one file."""
    if not isinstance(from_yaml, dict) or not isinstance(from_json, dict):
        return ["<document>"]
    return sorted(
        k for k in set(from_yaml) | set(from_json)
        if k not in from_yaml or k not in from_json or from_yaml[k] != from_json[k]
    )


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("yaml_file", type=Path, help="the metric YAML")
    ap.add_argument("json_file", type=Path, help="its JSON rendering")
    args = ap.parse_args(argv)

    for path in (args.yaml_file, args.json_file):
        if not path.is_file():
            sys.exit(f"ERROR: no such file: {path}")

    try:
        from_yaml = yaml.safe_load(args.yaml_file.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        sys.exit(f"ERROR: {args.yaml_file} is not valid YAML: {exc}")
    try:
        from_json = json.loads(args.json_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"ERROR: {args.json_file} is not valid JSON: {exc}")

    if from_yaml == from_json:
        print(f"OK: {args.json_file.name} matches {args.yaml_file.name}")
        return 0

    keys = differing_keys(from_yaml, from_json)
    sys.exit(
        f"ERROR: {args.json_file.name} does not match {args.yaml_file.name} — "
        f"they differ in: {', '.join(keys)}\n"
        f"Regenerate both from the sheet so the pair is written in one pass."
    )


if __name__ == "__main__":
    sys.exit(main())
