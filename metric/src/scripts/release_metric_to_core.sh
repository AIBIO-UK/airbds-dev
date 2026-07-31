#!/usr/bin/env bash
#
# Publish one version of the AIRBDS metric to the publication repository.
#
# Takes a metric version from this development repository and publishes
# metric/airbds_metric_v<VERSION>.yaml to the root of AIBIO-UK/airbds-core as the
# unversioned airbds_metric.yaml, on a release branch, with a pull request left
# open for working-group review. It never merges and never tags — because the
# published filename carries no version, a tag or release in airbds-core is what
# downstream consumers pin to, so tagging stays a deliberate step.
#
#   ./metric/src/scripts/release_metric_to_core.sh 0.5
#   ./metric/src/scripts/release_metric_to_core.sh v0.5 --dry-run
#
# The clone/branch/commit/push/PR mechanics live in scripts/publish-to-core.sh;
# every option it takes (--dry-run, --draft, --base, --repo, --remote, --branch)
# is accepted here and forwarded. Needs git, and gh unless --dry-run.
# See metric/src/README.md for the full workflow.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PUBLISH="${REPO_ROOT}/scripts/publish-to-core.sh"

# The published filename is deliberately unversioned: downstream consumers pin a
# git tag or release in airbds-core, not a filename.
DEST_FILE="airbds_metric.yaml"

die() { echo "error: $*" >&2; exit 1; }

usage() {
  cat <<EOF
Usage: $(basename "$0") <version> [options]

Publish metric/airbds_metric_v<version>.yaml to the root of the publication
repository as ${DEST_FILE}, on a release branch, and open a pull request.

Arguments:
  <version>          Metric version to publish, e.g. 0.5 or v0.5

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

# Accept 0.5 or v0.5; carry the bare number around and add the v where needed.
VERSION="${VERSION#v}"
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+$ ]] || die "version must look like 0.5 or v0.5, got: ${VERSION}"

SRC_FILE="${REPO_ROOT}/metric/airbds_metric_v${VERSION}.yaml"
[ -f "$SRC_FILE" ] || die "no metric file for v${VERSION} at ${SRC_FILE#"$REPO_ROOT"/}"

[ -n "$BRANCH" ] || BRANCH="release/metric-v${VERSION}"

# Provenance for the PR body: which commit of this repo the YAML came from, and
# whether it was clean at the time.
SRC_COMMIT="$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
SRC_DIRTY=""
if ! git -C "$REPO_ROOT" diff --quiet -- "$SRC_FILE" 2>/dev/null ||
   ! git -C "$REPO_ROOT" diff --cached --quiet -- "$SRC_FILE" 2>/dev/null; then
  SRC_DIRTY="yes"
  echo "warning: metric/airbds_metric_v${VERSION}.yaml has uncommitted changes — publishing the working-tree version" >&2
fi

BODY="Publishes **AIRBDS metric v${VERSION}** to the repository root as \`${DEST_FILE}\`.

| | |
|---|---|
| Metric version | v${VERSION} |
| Source | [\`metric/airbds_metric_v${VERSION}.yaml\`](https://github.com/AIBIO-UK/airbds-dev/blob/${SRC_COMMIT}/metric/airbds_metric_v${VERSION}.yaml) |
| Source commit | AIBIO-UK/airbds-dev@${SRC_COMMIT}${SRC_DIRTY:+ (plus uncommitted working-tree changes)} |

The published filename is unversioned — pin a tag or release in this repository
to depend on a specific metric version.

Opened by \`metric/src/scripts/release_metric_to_core.sh\`."

exec "$PUBLISH" \
  --src "$SRC_FILE" \
  --dest "$DEST_FILE" \
  --branch "$BRANCH" \
  --title "Release AIRBDS metric v${VERSION}" \
  --body "$BODY" \
  --commit-message "release: publish AIRBDS metric v${VERSION}

Copies metric/airbds_metric_v${VERSION}.yaml from AIBIO-UK/airbds-dev@${SRC_COMMIT}
to ${DEST_FILE} in the repository root." \
  ${PASSTHROUGH[@]+"${PASSTHROUGH[@]}"}
