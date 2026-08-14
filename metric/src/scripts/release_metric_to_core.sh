#!/usr/bin/env bash
#
# Publish one version of the AIRBDS metric to the publication repository.
#
# Takes a metric version from this development repository and publishes
# metric/airbds_metric_v<VERSION>.{yaml,json} to the root of AIBIO-UK/airbds-core
# as the unversioned airbds_metric.yaml and airbds_metric.json, on a release
# branch, with a pull request left open for working-group review. It never merges
# and never tags: airbds-core carries the current metric and only the current
# one, while every version — superseded ones included — stays here under its own
# name, which is what anyone depending on a specific version references.
#
# Both renderings go in one commit. They are the same metric in two formats —
# the YAML for readers, the JSON for consumers that must parse it without a YAML
# library, the assessment skill among them — so publishing one without the other
# would leave the publication repo asserting two different metrics at once. A
# preflight confirms the pair actually matches before anything is cloned; see
# check_metric_renderings_match.py.
#
# The same commit restamps the metric version quoted in that repo's
# skills/README.md: the published YAML is unversioned, so that sentence is where
# a reader learns which metric is current, and it has to move with the file.
# The skill version there is left alone — that one belongs to the skill release.
# See scripts/stamp_core_versions.py.
#
#   ./metric/src/scripts/release_metric_to_core.sh 1.0.0
#   ./metric/src/scripts/release_metric_to_core.sh v1.0.0 --dry-run
#
# The clone/branch/commit/push/PR mechanics live in scripts/publish-to-core.sh;
# every option it takes (--dry-run, --draft, --base, --repo, --remote, --branch)
# is accepted here and forwarded. Needs git, and gh unless --dry-run.
# See metric/src/README.md for the full workflow.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PUBLISH="${REPO_ROOT}/scripts/publish-to-core.sh"
STAMP="${REPO_ROOT}/scripts/stamp_core_versions.py"
CHECK_PAIR="${REPO_ROOT}/metric/src/scripts/check_metric_renderings_match.py"

# The published filenames are deliberately unversioned: airbds-core answers "what
# is the current AIRBDS metric?", and airbds-dev answers "what was v1.0.0?".
DEST_YAML="airbds_metric.yaml"
DEST_JSON="airbds_metric.json"

# The JSON rendering arrived with v1.0.0. The retained v0.3 and v0.4 metrics
# predate it and are YAML-only; anything from 1.0.0 on must ship both, and a
# missing JSON there means the generator was not rerun rather than that the
# version is exempt.
JSON_FROM_MAJOR=1

die() { echo "error: $*" >&2; exit 1; }

usage() {
  cat <<EOF
Usage: $(basename "$0") <version> [options]

Publish metric/airbds_metric_v<version>.{yaml,json} to the root of the
publication repository as ${DEST_YAML} and ${DEST_JSON}, in one commit
on a release branch, and open a pull request.

Arguments:
  <version>          Metric version to publish, e.g. 1.0.0 or v1.0.0

Options:
  --branch <name>    Release branch name (default: release/metric-v<version>)
  --dry-run          Commit locally only — no push, no PR
  --draft            Open the pull request as a draft
  -h, --help         Show this help

All other options are passed through to scripts/publish-to-core.sh — run
\`scripts/publish-to-core.sh --help\` for --base, --repo, and --remote.
EOF
}

VERSION=""
BRANCH=""
PASSTHROUGH=()
while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --branch)  BRANCH="${2:-}"; [ -n "$BRANCH" ] || die "--branch needs a value"; shift 2 ;;
    --dry-run|--draft) PASSTHROUGH+=("$1"); shift ;;
    --base|--repo|--remote) PASSTHROUGH+=("$1" "${2:-}"); shift 2 ;;
    -*)        die "unknown option: $1" ;;
    *)         [ -z "$VERSION" ] || die "unexpected argument: $1"; VERSION="$1"; shift ;;
  esac
done

[ -n "$VERSION" ] || { usage >&2; die "a metric version is required"; }

# Accept 1.0.0 or v1.0.0; carry the bare number around and add the v where
# needed. The patch component is optional: the retained v0.3 and v0.4 metrics
# predate the move to three-component versions and keep their two-part names.
VERSION="${VERSION#v}"
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+(\.[0-9]+)?$ ]] ||
  die "version must look like 1.0.0 or v1.0.0, got: ${VERSION}"

SRC_YAML="${REPO_ROOT}/metric/airbds_metric_v${VERSION}.yaml"
SRC_JSON="${REPO_ROOT}/metric/airbds_metric_v${VERSION}.json"
[ -f "$SRC_YAML" ] || die "no metric file for v${VERSION} at ${SRC_YAML#"$REPO_ROOT"/}"

# Sources and destinations paired in order for publish-to-core.sh. The JSON is
# only absent legitimately for the pre-1.0 metrics.
SRC_FILES=("$SRC_YAML")
DEST_FILES=("$DEST_YAML")
if [ -f "$SRC_JSON" ]; then
  SRC_FILES+=("$SRC_JSON")
  DEST_FILES+=("$DEST_JSON")
  echo "==> checking the YAML and JSON renderings match"
  python3 "$CHECK_PAIR" "$SRC_YAML" "$SRC_JSON" ||
    die "v${VERSION}'s renderings disagree — nothing published"
elif [ "${VERSION%%.*}" -ge "$JSON_FROM_MAJOR" ]; then
  die "no JSON rendering for v${VERSION} at ${SRC_JSON#"$REPO_ROOT"/} — rerun the generator so the YAML and JSON are written together"
else
  echo "note: v${VERSION} predates the JSON rendering — publishing ${DEST_YAML} only" >&2
fi

[ -n "$BRANCH" ] || BRANCH="release/metric-v${VERSION}"

# Provenance for the PR body: which commit of this repo the files came from, and
# whether they were clean at the time.
SRC_COMMIT="$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
SRC_DIRTY=""
for f in "${SRC_FILES[@]}"; do
  if ! git -C "$REPO_ROOT" diff --quiet -- "$f" 2>/dev/null ||
     ! git -C "$REPO_ROOT" diff --cached --quiet -- "$f" 2>/dev/null; then
    SRC_DIRTY="yes"
    echo "warning: ${f#"$REPO_ROOT"/} has uncommitted changes — publishing the working-tree version" >&2
  fi
done

# Runs inside the publication clone — absolute path, values quoted for the shell
# that re-parses this string. Only the metric version: the skill version in that
# README is the skill release's to set.
printf -v POST_COPY 'python3 %q --metric-version %q' "$STAMP" "$VERSION"

# One "Published" row per file, each linking the source it was copied from.
PUBLISHED_ROWS=""
for i in "${!SRC_FILES[@]}"; do
  src_rel="${SRC_FILES[$i]#"$REPO_ROOT"/}"
  PUBLISHED_ROWS+="| \`${DEST_FILES[$i]}\` | [\`${src_rel}\`](https://github.com/AIBIO-UK/airbds-dev/blob/${SRC_COMMIT}/${src_rel}) |
"
done

# Only worth explaining when both are going over.
RENDERINGS_NOTE=""
if [ "${#SRC_FILES[@]}" -gt 1 ]; then
  RENDERINGS_NOTE="
Both renderings are published together and carry the same data: the generator
writes the JSON from the object it parsed the YAML into, rather than making a
second pass over the sheet, and the release re-checks the pair before publishing.
The JSON is there for consumers that parse the metric without a YAML library —
the assessment skill bundles it as \`assets/airbds_metric.json\`.
"
fi

BODY="Publishes **AIRBDS metric v${VERSION}** to the repository root.

| Published as | Source |
|---|---|
${PUBLISHED_ROWS}
Metric version v${VERSION}, from AIBIO-UK/airbds-dev@${SRC_COMMIT}${SRC_DIRTY:+ (plus uncommitted working-tree changes)}.
${RENDERINGS_NOTE}
\`skills/README.md\` is restamped in the same commit so the metric version it
quotes reads v${VERSION}. That number sits inside HTML comment markers, so the
diff touches the source and not how the page reads.

The published filenames are unversioned: this repository carries the *current*
metric. To depend on a specific version, reference it in
[AIBIO-UK/airbds-dev](https://github.com/AIBIO-UK/airbds-dev), where every
version keeps its own name and superseded versions are retained.

Opened by \`metric/src/scripts/release_metric_to_core.sh\`."

FILE_ARGS=()
COPIED=""
for i in "${!SRC_FILES[@]}"; do
  FILE_ARGS+=(--src "${SRC_FILES[$i]}" --dest "${DEST_FILES[$i]}")
  COPIED+="  metric/airbds_metric_v${VERSION}.${SRC_FILES[$i]##*.} -> ${DEST_FILES[$i]}
"
done

exec "$PUBLISH" \
  "${FILE_ARGS[@]}" \
  --branch "$BRANCH" \
  --title "Release AIRBDS metric v${VERSION}" \
  --body "$BODY" \
  --post-copy "$POST_COPY" \
  --commit-message "release: publish AIRBDS metric v${VERSION}

Copies from AIBIO-UK/airbds-dev@${SRC_COMMIT} into the repository root:

${COPIED}
and restamps the metric version quoted in skills/README.md." \
  ${PASSTHROUGH[@]+"${PASSTHROUGH[@]}"}
