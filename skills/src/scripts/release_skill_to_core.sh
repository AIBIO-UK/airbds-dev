#!/usr/bin/env bash
#
# Publish the current testing assessment-skill zip to the publication repository.
#
# This is the push to production. It promotes the exact artifact the testing
# channel's build workflow produced — the zip people have actually been testing —
# rather than rebuilding it here, so what ships is byte-for-byte what was tested.
# The zip is downloaded from the airbds-dev release, checked against its
# published digest and against skills/versions.json, then committed to
# AIBIO-UK/airbds-core as skills/airbds-assessment-skill.zip on a release branch,
# with a pull request left open for review.
#
#   ./skills/src/scripts/release_skill_to_core.sh
#   ./skills/src/scripts/release_skill_to_core.sh --dry-run
#   ./skills/src/scripts/release_skill_to_core.sh --zip /path/to/some.zip
#
# The published filename carries neither channel nor version: the testing channel
# is this repo's staging area, and what lands in airbds-core is simply "the
# skill". Pin a tag or release there to depend on a specific build.
#
# The clone/branch/commit/push/PR mechanics live in scripts/publish-to-core.sh.
# Needs git, unzip, and gh (authenticated) — gh is required even for --dry-run
# unless --zip supplies the artifact locally.
# See skills/src/README.md for the full workflow.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PUBLISH="${REPO_ROOT}/scripts/publish-to-core.sh"
MANIFEST="${REPO_ROOT}/skills/versions.json"

CHANNEL="testing"
RELEASE_TAG="assessment-skill-${CHANNEL}"
ASSET_NAME="airbds-assessment-skill-${CHANNEL}.zip"
SOURCE_REPO="AIBIO-UK/airbds-dev"

# Neither channel nor version — see the header note.
DEST_FILE="skills/airbds-assessment-skill.zip"

die() { echo "error: $*" >&2; exit 1; }

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Promote the current ${CHANNEL} assessment-skill zip to the publication
repository as ${DEST_FILE}, on a release branch, and open a pull request.

The artifact is downloaded from the ${SOURCE_REPO} '${RELEASE_TAG}' release,
so what ships is exactly what was tested.

Options:
  --zip <file>       Publish this local zip instead of downloading the release.
                     Skips the digest check; the manifest checks still run
  --branch <name>    Release branch name (default: release/skill-v<version>)
  --dry-run          Commit locally only — no push, no PR
  --draft            Open the pull request as a draft
  --force            Publish even if the zip disagrees with skills/versions.json
  -h, --help         Show this help

All other options are passed through to scripts/publish-to-core.sh — run
\`scripts/publish-to-core.sh --help\` for --base, --repo, and --remote.
EOF
}

ZIP_OVERRIDE=""
BRANCH=""
FORCE=0
PASSTHROUGH=()
while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --zip)     ZIP_OVERRIDE="${2:-}"; [ -n "$ZIP_OVERRIDE" ] || die "--zip needs a value";  shift 2 ;;
    --branch)  BRANCH="${2:-}";       [ -n "$BRANCH" ]       || die "--branch needs a value"; shift 2 ;;
    --force)   FORCE=1; shift ;;
    --dry-run|--draft) PASSTHROUGH+=("$1"); shift ;;
    --base|--repo|--remote) PASSTHROUGH+=("$1" "${2:-}"); shift 2 ;;
    *)         die "unknown option: $1" ;;
  esac
done

command -v unzip >/dev/null 2>&1 || die "unzip is required"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# ---------------------------------------------------------------- the artifact
if [ -n "$ZIP_OVERRIDE" ]; then
  [ -f "$ZIP_OVERRIDE" ] || die "zip not found: ${ZIP_OVERRIDE}"
  ZIP="$ZIP_OVERRIDE"
  RELEASE_NOTE="local file \`$(basename "$ZIP_OVERRIDE")\` (not the published release)"
  echo "==> using local zip ${ZIP_OVERRIDE}"
else
  command -v gh >/dev/null 2>&1 || die "the GitHub CLI (gh) is required to download the release; install it or pass --zip"

  echo "==> downloading ${ASSET_NAME} from ${SOURCE_REPO} (${RELEASE_TAG})"
  gh release download "$RELEASE_TAG" --repo "$SOURCE_REPO" \
     --pattern "$ASSET_NAME" --dir "$WORK" ||
    die "could not download ${ASSET_NAME} from the ${RELEASE_TAG} release"
  ZIP="${WORK}/${ASSET_NAME}"

  # The release metadata carries the digest GitHub recorded at upload, so the
  # download can be checked rather than trusted.
  PUBLISHED_AT="$(gh release view "$RELEASE_TAG" --repo "$SOURCE_REPO" --json publishedAt --jq .publishedAt)"
  EXPECTED_DIGEST="$(gh release view "$RELEASE_TAG" --repo "$SOURCE_REPO" \
      --json assets --jq ".assets[] | select(.name==\"${ASSET_NAME}\") | .digest")"
  ACTUAL_DIGEST="sha256:$(sha256sum "$ZIP" | cut -d' ' -f1)"
  if [ -n "$EXPECTED_DIGEST" ] && [ "$EXPECTED_DIGEST" != "$ACTUAL_DIGEST" ]; then
    die "downloaded zip does not match the published digest
  expected: ${EXPECTED_DIGEST}
  actual:   ${ACTUAL_DIGEST}"
  fi
  echo "==> digest verified: ${ACTUAL_DIGEST}"
  RELEASE_NOTE="[\`${ASSET_NAME}\`](https://github.com/${SOURCE_REPO}/releases/download/${RELEASE_TAG}/${ASSET_NAME}), built ${PUBLISHED_AT}"
fi

ZIP_SHA256="$(sha256sum "$ZIP" | cut -d' ' -f1)"

# ------------------------------------------------- what is actually in the zip
unzip -q -o "$ZIP" SKILL.md -d "$WORK/inspect" 2>/dev/null ||
  die "zip has no SKILL.md at its root — is this an assessment-skill build?"
SKILL_MD="${WORK}/inspect/SKILL.md"

# Read the frontmatter fields without a YAML parser: they are flat, quoted
# scalars under metadata:, and this must run with nothing but coreutils.
zip_version="$(sed -n 's/^  version: *"\{0,1\}\([^"]*\)"\{0,1\} *$/\1/p' "$SKILL_MD" | head -1)"
zip_channel="$(sed -n 's/^  channel: *"\{0,1\}\([^"]*\)"\{0,1\} *$/\1/p' "$SKILL_MD" | head -1)"

[ -n "$zip_version" ] || die "could not read metadata.version from the zip's SKILL.md"
[ -n "$zip_channel" ] || die "could not read metadata.channel from the zip's SKILL.md"

echo "==> zip contains skill v${zip_version} (channel: ${zip_channel})"

problems=()
[ "$zip_channel" = "$CHANNEL" ] ||
  problems+=("zip is from the '${zip_channel}' channel, expected '${CHANNEL}'")

# skills/versions.json is what the published skills poll for updates, so a zip
# that disagrees with it would ship users a version the manifest never announces.
manifest_version=""
manifest_metric=""
if [ -f "$MANIFEST" ]; then
  # One read, two fields: skill_version gates the release, metric_version is
  # reported in the PR body so a reviewer sees what the skill scores against.
  read -r manifest_version manifest_metric <<<"$(python3 -c "
import json, sys
c = json.load(open(sys.argv[1]))['channels'].get(sys.argv[2], {})
print(c.get('skill_version', '-'), c.get('metric_version', '-'))
" "$MANIFEST" "$CHANNEL" 2>/dev/null || echo '- -')"
  if [ "$manifest_version" = "-" ]; then manifest_version=""; fi
  if [ "$manifest_metric" = "-" ]; then manifest_metric=""; fi

  [ -n "$manifest_version" ] ||
    problems+=("skills/versions.json has no skill_version for the '${CHANNEL}' channel")
  if [ -n "$manifest_version" ] && [ "$manifest_version" != "$zip_version" ]; then
    problems+=("zip is skill v${zip_version} but skills/versions.json advertises v${manifest_version} for '${CHANNEL}' — the manifest is what installed skills poll, so publishing this would ship a version nothing announces")
  fi
else
  problems+=("skills/versions.json not found at ${MANIFEST}")
fi

if [ ${#problems[@]} -gt 0 ]; then
  echo "error: the artifact disagrees with this repository:" >&2
  for p in "${problems[@]}"; do echo "  - ${p}" >&2; done
  # A version mismatch usually means skills/versions.json was not bumped when the
  # skill was, or the release predates the bump — check both before overriding.
  if [ "$FORCE" = 0 ]; then
    echo "refusing to publish — fix the mismatch, or pass --force to override" >&2
    exit 1
  fi
  echo "warning: --force given, publishing anyway" >&2
fi

[ -n "$BRANCH" ] || BRANCH="release/skill-v${zip_version}"

SRC_COMMIT="$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"

BODY="Promotes the **${CHANNEL}** AIRBDS assessment skill to production as \`${DEST_FILE}\`.

| | |
|---|---|
| Skill version | ${zip_version} |
| Metric version | ${manifest_metric:-unknown} |
| Built from channel | ${zip_channel} |
| Artifact | ${RELEASE_NOTE} |
| sha256 | \`${ZIP_SHA256}\` |
| Released from | AIBIO-UK/airbds-dev@${SRC_COMMIT} |

This is the artifact the testing channel's build workflow produced — it is
promoted as built, not rebuilt here, so what ships is byte-for-byte what was
tested. Verify by comparing the sha256 above against the release asset.

The published filename carries neither channel nor version; pin a tag or release
in this repository to depend on a specific build.

Opened by \`skills/src/scripts/release_skill_to_core.sh\`."

# Called rather than exec'd: the zip lives in $WORK, so the cleanup trap has to
# survive until publish-to-core.sh has copied it.
"$PUBLISH" \
  --src "$ZIP" \
  --dest "$DEST_FILE" \
  --branch "$BRANCH" \
  --title "Release AIRBDS assessment skill v${zip_version}" \
  --body "$BODY" \
  --commit-message "release: publish AIRBDS assessment skill v${zip_version}

Promotes the ${CHANNEL} channel build from AIBIO-UK/airbds-dev@${SRC_COMMIT}
to ${DEST_FILE}.

sha256: ${ZIP_SHA256}" \
  ${PASSTHROUGH[@]+"${PASSTHROUGH[@]}"}
