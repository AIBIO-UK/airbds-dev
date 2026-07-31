#!/usr/bin/env bash
#
# Publish one version of the AIRBDS metric to the publication repository.
#
# Takes a metric version from this development repository, copies
# metric/airbds_metric_v<VERSION>.yaml to the root of AIBIO-UK/airbds-core as the
# unversioned airbds_metric.yaml, commits it on a release branch, pushes, and
# opens a pull request. The PR is left open for working-group review — this
# script never merges and never tags.
#
# The publication repo is cloned into a temporary directory each run and removed
# afterwards, so nothing here touches a local airbds-core checkout.
#
#   ./metric/src/scripts/release_metric_to_core.sh 0.5
#   ./metric/src/scripts/release_metric_to_core.sh v0.5 --dry-run
#
# Needs: git, and the GitHub CLI (gh, authenticated) unless --dry-run.
# See metric/src/README.md for the full workflow.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

# The published filename is deliberately unversioned: downstream consumers pin a
# git tag or release in airbds-core, not a filename.
DEST_FILE="airbds_metric.yaml"

CORE_REPO="${AIRBDS_CORE_REPO:-AIBIO-UK/airbds-core}"
CORE_REMOTE="${AIRBDS_CORE_REMOTE:-}"
BASE_BRANCH="main"
BRANCH=""
DRY_RUN=0
DRAFT=0

usage() {
  cat <<EOF
Usage: $(basename "$0") <version> [options]

Publish metric/airbds_metric_v<version>.yaml to the root of the publication
repository as ${DEST_FILE}, on a release branch, and open a pull request.

Arguments:
  <version>          Metric version to publish, e.g. 0.5 or v0.5

Options:
  --branch <name>    Release branch name       (default: release/metric-v<version>)
  --base <name>      Branch to open the PR against          (default: ${BASE_BRANCH})
  --repo <owner/rep> Publication repository                 (default: ${CORE_REPO})
  --remote <url>     Clone/push URL      (default: git@github.com:<owner/repo>.git)
  --draft            Open the pull request as a draft
  --dry-run          Commit locally only — no push, no PR. Keeps the temporary
                     clone and prints its path so the result can be inspected.
  -h, --help         Show this help

Environment:
  AIRBDS_CORE_REPO, AIRBDS_CORE_REMOTE   Defaults for --repo / --remote
EOF
}

die() { echo "error: $*" >&2; exit 1; }

VERSION=""
while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --branch)  BRANCH="${2:-}";      [ -n "$BRANCH" ]      || die "--branch needs a value"; shift 2 ;;
    --base)    BASE_BRANCH="${2:-}"; [ -n "$BASE_BRANCH" ] || die "--base needs a value";   shift 2 ;;
    --repo)    CORE_REPO="${2:-}";   [ -n "$CORE_REPO" ]   || die "--repo needs a value";   shift 2 ;;
    --remote)  CORE_REMOTE="${2:-}"; [ -n "$CORE_REMOTE" ] || die "--remote needs a value"; shift 2 ;;
    --draft)   DRAFT=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
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
[ -n "$CORE_REMOTE" ] || CORE_REMOTE="git@github.com:${CORE_REPO}.git"
# A bare local path clones without honouring --depth; file:// makes it shallow.
if [ -d "$CORE_REMOTE" ]; then CORE_REMOTE="file://$(cd "$CORE_REMOTE" && pwd)"; fi

command -v git >/dev/null 2>&1 || die "git is required"
if [ "$DRY_RUN" = 0 ]; then
  command -v gh >/dev/null 2>&1 || die "the GitHub CLI (gh) is required; install it or use --dry-run"
fi

# Provenance for the PR body: which commit of this repo the YAML came from, and
# whether it was clean at the time.
SRC_COMMIT="$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
SRC_DIRTY=""
if ! git -C "$REPO_ROOT" diff --quiet -- "$SRC_FILE" 2>/dev/null ||
   ! git -C "$REPO_ROOT" diff --cached --quiet -- "$SRC_FILE" 2>/dev/null; then
  SRC_DIRTY="yes"
  echo "warning: metric/airbds_metric_v${VERSION}.yaml has uncommitted changes — publishing the working-tree version" >&2
fi

WORK="$(mktemp -d)"
cleanup() {
  if [ "$DRY_RUN" = 1 ]; then
    echo "dry run: temporary clone left at ${WORK}"
  else
    rm -rf "$WORK"
  fi
}
trap cleanup EXIT

echo "==> cloning ${CORE_REPO} (${BASE_BRANCH})"
git clone --quiet --depth 1 --branch "$BASE_BRANCH" "$CORE_REMOTE" "$WORK/core"
CLONE="$WORK/core"

if git -C "$CLONE" ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1; then
  die "branch ${BRANCH} already exists on ${CORE_REPO} — delete it or pass --branch"
fi

# git needs an identity to commit; fall back to a bot one only if none resolves.
if [ -z "$(git -C "$CLONE" config user.email || true)" ]; then
  git -C "$CLONE" config user.name "airbds-release"
  git -C "$CLONE" config user.email "airbds-release@users.noreply.github.com"
fi

git -C "$CLONE" checkout --quiet -b "$BRANCH"
cp "$SRC_FILE" "$CLONE/$DEST_FILE"

# Stage first, then compare against HEAD — a plain worktree diff reports no
# change when the destination does not exist in the base branch yet.
git -C "$CLONE" add "$DEST_FILE"
if git -C "$CLONE" diff --cached --quiet; then
  echo "==> ${CORE_REPO}:${DEST_FILE} already matches metric v${VERSION} — nothing to release"
  exit 0
fi

git -C "$CLONE" commit --quiet -m "release: publish AIRBDS metric v${VERSION}

Copies metric/airbds_metric_v${VERSION}.yaml from AIBIO-UK/airbds-dev@${SRC_COMMIT}
to ${DEST_FILE} in the repository root."
echo "==> committed ${DEST_FILE} (metric v${VERSION}) on ${BRANCH}"

if [ "$DRY_RUN" = 1 ]; then
  git -C "$CLONE" --no-pager show --stat --oneline HEAD
  echo "dry run: not pushing, not opening a pull request"
  exit 0
fi

echo "==> pushing ${BRANCH} to ${CORE_REPO}"
git -C "$CLONE" push --quiet -u origin "$BRANCH"

PR_BODY="Publishes **AIRBDS metric v${VERSION}** to the repository root as \`${DEST_FILE}\`.

| | |
|---|---|
| Metric version | v${VERSION} |
| Source | [\`metric/airbds_metric_v${VERSION}.yaml\`](https://github.com/AIBIO-UK/airbds-dev/blob/${SRC_COMMIT}/metric/airbds_metric_v${VERSION}.yaml) |
| Source commit | AIBIO-UK/airbds-dev@${SRC_COMMIT}${SRC_DIRTY:+ (plus uncommitted working-tree changes)} |

The published filename is unversioned — pin a tag or release in this repository
to depend on a specific metric version.

Opened by \`metric/src/scripts/release_metric_to_core.sh\`."

PR_ARGS=(
  --repo "$CORE_REPO"
  --base "$BASE_BRANCH"
  --head "$BRANCH"
  --title "Release AIRBDS metric v${VERSION}"
  --body "$PR_BODY"
)
if [ "$DRAFT" = 1 ]; then PR_ARGS+=(--draft); fi

echo "==> opening pull request"
gh pr create "${PR_ARGS[@]}"
