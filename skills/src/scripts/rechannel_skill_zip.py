#!/usr/bin/env python3
"""Rewrite an assessment-skill zip's release channel, verifiably.

A skill bundle carries its channel *inside* it — `metadata.channel` in
`SKILL.md`, plus the prose that tells the skill which `channels.<name>` entry of
the update manifest to read. So the tested `testing` zip cannot simply be
shipped as production: every production user, and the runtime update check,
would be told they are on `testing`.

Rebuilding the bundle from a separate `production/` source directory would solve
that by introducing a third copy of `SKILL.md` to keep in step. This script takes
the other route: derive production from the artifact that was actually tested by
substituting the channel token, and *prove* that is all that happened.

The proof has two halves:

  1. Reversibility. Replacing the new channel with the old one in the rewritten
     `SKILL.md` must reproduce the original byte for byte. That fails loudly if
     the source already contained the target token, which is the one case where
     a blind substitution could not be undone — and so the one case where "only
     the channel changed" could not be checked.
  2. Everything else is copied verbatim: same members, same order, same
     modification times, same permissions, same compression method, same bytes.

`--check` runs the same verification against an already-published zip, so a
reviewer of the airbds-core pull request can confirm the claim without trusting
this script's output:

    rechannel_skill_zip.py --in tested.zip --check published.zip

Used by skills/src/scripts/release_skill_to_core.sh. Needs only the standard
library.
"""

import argparse
import hashlib
import sys
import zipfile

# `( cd <skill-dir> && zip -r - . )` writes flat names, but a bundle zipped a
# different way can carry the `./` prefix — accept either rather than fail
# confusingly on a zip that is otherwise fine.
SKILL_MD_NAMES = ("SKILL.md", "./SKILL.md")

# Copied member-by-member so the rewritten zip differs from its source in file
# content alone. `flag_bits` and `extra` are deliberately not copied: both
# describe how the entry is *stored* (data descriptors, zip64 sizes, timestamp
# extras) and are rewritten by zipfile as it writes, so carrying the source's
# values over would describe the new entry incorrectly.
COPIED_FIELDS = (
    "date_time",
    "compress_type",
    "external_attr",
    "internal_attr",
    "create_system",
    "comment",
)


class RechannelError(Exception):
    """Something about the bundle makes a verifiable rewrite impossible."""


def find_skill_md(zf):
    """The bundle's root SKILL.md, which is the only member ever rewritten."""
    by_name = {info.filename: info for info in zf.infolist()}
    for name in SKILL_MD_NAMES:
        if name in by_name:
            return by_name[name]
    raise RechannelError(
        "zip has no SKILL.md at its root — is this an assessment-skill build?"
    )


def rewrite_text(text, src, dst):
    """Substitute the channel token, refusing anything unverifiable.

    Returns (new_text, [1-based line numbers that changed]).
    """
    if src == dst:
        raise RechannelError(f"source and target channel are both '{src}'")
    if src not in text:
        raise RechannelError(
            f"SKILL.md never mentions the '{src}' channel — is it from that channel?"
        )
    # Plain substring substitution, which is what promoting a channel by hand
    # does. Every occurrence goes, so the result cannot mention the old channel.
    new_text = text.replace(src, dst)
    if new_text.replace(dst, src) != text:
        raise RechannelError(
            f"the rewrite is not reversible: SKILL.md already mentions '{dst}' "
            f"before the rewrite, so 'only the channel changed' cannot be "
            f"verified. Reword that mention, or promote the bundle by hand."
        )
    changed = [
        n
        for n, (before, after) in enumerate(
            zip(text.splitlines(), new_text.splitlines()), start=1
        )
        if before != after
    ]
    return new_text, changed


def rechannel_zip(in_path, out_path, src, dst):
    """Write out_path: in_path with SKILL.md's channel token substituted."""
    with zipfile.ZipFile(in_path) as zin:
        skill_name = find_skill_md(zin).filename
        text = zin.read(skill_name).decode("utf-8")
        new_text, changed = rewrite_text(text, src, dst)
        new_bytes = new_text.encode("utf-8")

        with zipfile.ZipFile(out_path, "w") as zout:
            for info in zin.infolist():
                data = (
                    new_bytes
                    if info.filename == skill_name
                    else zin.read(info.filename)
                )
                out_info = zipfile.ZipInfo(info.filename)
                for field in COPIED_FIELDS:
                    setattr(out_info, field, getattr(info, field))
                zout.writestr(out_info, data)

    return {"changed_lines": changed, "substitutions": text.count(src)}


def verify(in_path, out_path, src, dst):
    """Confirm out_path is in_path with nothing but the channel substituted.

    Raises RechannelError listing every difference that is not the rewrite.
    """
    problems = []
    with zipfile.ZipFile(in_path) as zin, zipfile.ZipFile(out_path) as zout:
        src_infos = zin.infolist()
        out_infos = zout.infolist()

        src_names = [i.filename for i in src_infos]
        out_names = [i.filename for i in out_infos]
        if src_names != out_names:
            raise RechannelError(
                "member lists differ:\n"
                f"  source:    {src_names}\n"
                f"  published: {out_names}"
            )

        skill_name = find_skill_md(zin).filename
        for src_info, out_info in zip(src_infos, out_infos):
            for field in COPIED_FIELDS:
                a, b = getattr(src_info, field), getattr(out_info, field)
                if a != b:
                    problems.append(f"{src_info.filename}: {field} {a!r} -> {b!r}")

            src_data = zin.read(src_info.filename)
            out_data = zout.read(out_info.filename)
            if src_info.filename == skill_name:
                out_text = out_data.decode("utf-8")
                if out_text.replace(dst, src).encode("utf-8") != src_data:
                    problems.append(
                        f"{skill_name}: undoing the channel rewrite does not "
                        f"reproduce the source — it differs by more than the "
                        f"'{src}' -> '{dst}' substitution"
                    )
                elif src in out_text:
                    # Reversible but unchanged, e.g. the source zip republished
                    # as-is: production users would still be told they are on
                    # the old channel.
                    problems.append(f"{skill_name}: still mentions the '{src}' channel")
            elif src_data != out_data:
                problems.append(f"{src_info.filename}: content differs")

    if problems:
        raise RechannelError(
            "the published zip is not the source with only its channel "
            "rewritten:\n" + "\n".join(f"  - {p}" for p in problems)
        )


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Rewrite an assessment-skill zip's release channel, or check that a "
            "published zip is exactly such a rewrite."
        )
    )
    parser.add_argument("--in", dest="src_zip", required=True,
                        help="the source bundle (the tested artifact)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--out", help="write the rewritten bundle here")
    group.add_argument("--check", help="verify this existing bundle instead of writing one")
    parser.add_argument("--from", dest="src_channel", default="testing",
                        help="channel the source is on (default: testing)")
    parser.add_argument("--to", dest="dst_channel", default="production",
                        help="channel to rewrite it to (default: production)")
    args = parser.parse_args(argv)

    target = args.out or args.check
    try:
        if args.out:
            result = rechannel_zip(
                args.src_zip, args.out, args.src_channel, args.dst_channel
            )
            lines = ", ".join(str(n) for n in result["changed_lines"])
            print(
                f"==> SKILL.md: {result['substitutions']} occurrence(s) of "
                f"'{args.src_channel}' -> '{args.dst_channel}' on line(s) {lines}"
            )
        verify(args.src_zip, target, args.src_channel, args.dst_channel)
    except RechannelError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except (OSError, zipfile.BadZipFile) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(
        f"==> verified: {target} is {args.src_zip} with only the channel "
        f"rewritten (every other member byte-identical)"
    )
    print(f"    source    sha256: {sha256(args.src_zip)}")
    print(f"    published sha256: {sha256(target)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
