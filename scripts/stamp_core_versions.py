#!/usr/bin/env python3
"""Stamp released version numbers into marked spans of a publication-repo file.

The publication repository's prose quotes the versions it ships — "currently at
version 0.8.0 and assessing against AIRBDS metric v1.0.0" — and prose does not
get updated by a release that only replaces a zip. That sentence went stale the
moment a release landed without someone remembering to edit it by hand.

So the numbers live inside HTML comment markers, and a release stamps them:

    currently at version <!--skill-version-->0.8.0<!--/skill-version--> and
    assessing against v<!--metric-version-->1.0.0<!--/metric-version-->

Markers are comments, so they render as nothing: the published page reads
exactly as it did before, and only the source carries the machinery. The `v` and
any other surrounding prose stay outside the span — a marker holds a bare
version number and nothing else, which is what makes the rewrite mechanical.

Only the versions passed are touched, which is what lets a metric release leave
the skill version alone and vice versa. Rewriting is idempotent: stamping a
value that is already there changes nothing and reports so.

    scripts/stamp_core_versions.py --skill-version 0.8.0 --metric-version 1.0.0
    scripts/stamp_core_versions.py --metric-version 1.0.0 --check

Run from a checkout of the publication repository (or pass --file). Release
scripts invoke it through publish-to-core.sh's --post-copy hook, which runs it
with the clone as its working directory.

Exit status: 0 stamped or already correct, 1 --check found a mismatch,
2 the file or a requested marker is missing.
"""

import argparse
import re
import sys
from pathlib import Path

DEFAULT_FILE = "skills/README.md"

# What a marker may hold: a bare version, two or three components. The retained
# v0.3/v0.4 metrics predate three-component versions, so the patch is optional —
# the same rule release_metric_to_core.sh applies to its argument.
VERSION_RE = re.compile(r"^\d+\.\d+(\.\d+)?$")

# Whitespace is tolerated inside the comment so a reflowed or prettier-formatted
# README still matches, but the span itself must be a single line: a marker that
# swallowed a paragraph break would be a silent corruption, not a stamp.
SPANS = {
    "skill-version": "--skill-version",
    "metric-version": "--metric-version",
}


def span_re(name):
    return re.compile(
        r"(<!--\s*" + re.escape(name) + r"\s*-->)([^\n]*?)(<!--\s*/" + re.escape(name) + r"\s*-->)"
    )


def die(msg, code=2):
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(code)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Stamp version numbers into marked spans of a publication-repo file.",
        epilog="With no --check, the file is rewritten in place.",
    )
    parser.add_argument(
        "--file",
        default=DEFAULT_FILE,
        help=f"file to stamp, relative to the working directory (default: {DEFAULT_FILE})",
    )
    parser.add_argument("--skill-version", help="version to stamp into the skill-version span")
    parser.add_argument("--metric-version", help="version to stamp into the metric-version span")
    parser.add_argument(
        "--check",
        action="store_true",
        help="report whether the spans already hold these versions; write nothing",
    )
    args = parser.parse_args(argv)

    wanted = {
        "skill-version": args.skill_version,
        "metric-version": args.metric_version,
    }
    if not any(wanted.values()):
        die("nothing to stamp — pass --skill-version and/or --metric-version")

    for name, value in wanted.items():
        if value is not None and not VERSION_RE.match(value):
            die(f"{SPANS[name]} must look like 1.0.0, got: {value}")

    path = Path(args.file)
    if not path.is_file():
        die(f"file not found: {path} (run this from a checkout of the publication repo, or pass --file)")

    original = path.read_text(encoding="utf-8")
    text = original
    mismatches = []
    stamped = []

    for name, value in wanted.items():
        if value is None:
            continue
        pattern = span_re(name)
        found = pattern.findall(text)
        if not found:
            # Loud rather than silent: a release that quietly skipped the stamp
            # would publish the stale sentence this script exists to prevent.
            die(
                f"no <!--{name}--> ... <!--/{name}--> span in {path} — "
                f"add the markers around the version number before releasing"
            )
        current = {m[1] for m in found}
        if current != {value}:
            mismatches.append((name, sorted(current), value))
        text = pattern.sub(lambda m: f"{m.group(1)}{value}{m.group(3)}", text)
        stamped.append((name, value, len(found)))

    if args.check:
        if mismatches:
            for name, current, value in mismatches:
                print(
                    f"{path}: {name} is {', '.join(current) or '(empty)'}, expected {value}",
                    file=sys.stderr,
                )
            return 1
        for name, value, count in stamped:
            print(f"{path}: {name} is {value} ({count} occurrence(s)) — up to date")
        return 0

    if text == original:
        for name, value, count in stamped:
            print(f"==> {path}: {name} already {value} ({count} occurrence(s))")
        return 0

    path.write_text(text, encoding="utf-8")
    for name, current, value in mismatches:
        print(f"==> {path}: {name} {', '.join(current) or '(empty)'} -> {value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
