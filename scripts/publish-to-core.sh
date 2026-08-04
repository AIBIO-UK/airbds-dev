#!/usr/bin/env bash
#
# Publish one file to the AIRBDS publication repository via a pull request.
#
# The shared engine behind the per-domain release scripts — it knows nothing
# about metrics or skills, only how to land a file in AIBIO-UK/airbds-core
# safely: clone to a temporary directory, branch, commit, push, open a PR, and
# leave it open for review. It never merges and never tags.
#
# A release is not always one file. The publication repo's prose quotes the
# versions it ships, and that prose goes stale unless the release updates it too.
# --post-copy runs an arbitrary command inside the clone for exactly that, and
# whatever it changes is committed alongside --src. The hook is why this stays
# generic: the engine still knows nothing about what is being released, it only
# knows that a caller may need a second edit in the same commit.
#
# Callers (they compute the file, destination, branch, PR text, and any hook):
#   metric/src/scripts/release_metric_to_core.sh
#   skills/src/scripts/release_skill_to_core.sh
#
# Every option after --src/--dest/--branch is forwarded verbatim by those
# wrappers, so an option added here is available to both.
set -euo pipefail

CORE_REPO="${AIRBDS_CORE_REPO:-AIBIO-UK/airbds-core}"
CORE_REMOTE="${AIRBDS_CORE_REMOTE:-}"
BASE_BRANCH="main"
SRC=""
DEST=""
BRANCH=""
TITLE=""
BODY=""
COMMIT_MSG=""
POST_COPY=""
DRY_RUN=0
DRAFT=0

usage() {
  cat <<EOF
Usage: $(basename "$0") --src <file> --dest <path> --branch <name> [options]

Publish one file to the root-relative <path> of the publication repository, on a
release branch, and open a pull request.

Required:
  --src <file>       File to publish, in this repository
  --dest <path>      Destination path within the publication repo, e.g.
                     airbds_metric.yaml or skills/airbds-assessment-skill.zip
  --branch <name>    Release branch to create

Options:
  --title <text>       Pull request title      (default: "Publish <dest>")
  --body <text>        Pull request body
  --commit-message <t> Commit message          (default: "release: publish <dest>")
  --post-copy <cmd>    Shell command run inside the clone after --src is copied
                       and before the commit, with the clone as its working
                       directory and AIRBDS_CORE_CLONE set to its path. Anything
                       it changes is committed too. A non-zero exit aborts the
                       release before anything is pushed
  --base <name>        Branch to open the PR against            (default: ${BASE_BRANCH})
  --repo <owner/repo>  Publication repository                   (default: ${CORE_REPO})
  --remote <url>       Clone/push URL      (default: git@github.com:<owner/repo>.git)
  --draft              Open the pull request as a draft
  --dry-run            Commit locally only — no push, no PR. Keeps the temporary
                       clone and prints its path so it can be inspected.
  -h, --help           Show this help

Environment:
  AIRBDS_CORE_REPO, AIRBDS_CORE_REMOTE   Defaults for --repo / --remote
EOF
}

die() { echo "error: $*" >&2; exit 1; }

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --src)            SRC="${2:-}";         [ -n "$SRC" ]         || die "--src needs a value";    shift 2 ;;
    --dest)           DEST="${2:-}";        [ -n "$DEST" ]        || die "--dest needs a value";   shift 2 ;;
    --branch)         BRANCH="${2:-}";      [ -n "$BRANCH" ]      || die "--branch needs a value"; shift 2 ;;
    --title)          TITLE="${2:-}";       shift 2 ;;
    --body)           BODY="${2:-}";        shift 2 ;;
    --commit-message) COMMIT_MSG="${2:-}";  shift 2 ;;
    --post-copy)      POST_COPY="${2:-}";   [ -n "$POST_COPY" ]   || die "--post-copy needs a value"; shift 2 ;;
    --base)           BASE_BRANCH="${2:-}"; [ -n "$BASE_BRANCH" ] || die "--base needs a value";   shift 2 ;;
    --repo)           CORE_REPO="${2:-}";   [ -n "$CORE_REPO" ]   || die "--repo needs a value";   shift 2 ;;
    --remote)         CORE_REMOTE="${2:-}"; [ -n "$CORE_REMOTE" ] || die "--remote needs a value"; shift 2 ;;
    --draft)          DRAFT=1; shift ;;
    --dry-run)        DRY_RUN=1; shift ;;
    *)                die "unknown option: $1" ;;
  esac
done

[ -n "$SRC" ]    || { usage >&2; die "--src is required"; }
[ -n "$DEST" ]   || { usage >&2; die "--dest is required"; }
[ -n "$BRANCH" ] || { usage >&2; die "--branch is required"; }
[ -f "$SRC" ]    || die "source file not found: ${SRC}"

case "$DEST" in
  /*|*..*) die "--dest must be a relative path inside the repo, got: ${DEST}" ;;
esac

[ -n "$TITLE" ]      || TITLE="Publish ${DEST}"
[ -n "$COMMIT_MSG" ] || COMMIT_MSG="release: publish ${DEST}"
[ -n "$CORE_REMOTE" ] || CORE_REMOTE="git@github.com:${CORE_REPO}.git"
# A bare local path clones without honouring --depth; file:// makes it shallow.
if [ -d "$CORE_REMOTE" ]; then CORE_REMOTE="file://$(cd "$CORE_REMOTE" && pwd)"; fi

command -v git >/dev/null 2>&1 || die "git is required"
if [ "$DRY_RUN" = 0 ]; then
  command -v gh >/dev/null 2>&1 || die "the GitHub CLI (gh) is required; install it or use --dry-run"
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
mkdir -p "$(dirname "$CLONE/$DEST")"
cp "$SRC" "$CLONE/$DEST"

# Stage first, then compare against HEAD — a plain worktree diff reports no
# change when the destination does not exist in the base branch yet.
git -C "$CLONE" add "$DEST"

if [ -n "$POST_COPY" ]; then
  echo "==> running post-copy hook"
  # Runs after the copy so the hook sees the released file in place, and before
  # the staging check so a release that only needs the hook's edit — the zip
  # unchanged, the prose stale — is still a release rather than a no-op.
  ( cd "$CLONE" && AIRBDS_CORE_CLONE="$CLONE" bash -c "$POST_COPY" ) ||
    die "post-copy hook failed — nothing committed, nothing published"
  git -C "$CLONE" add -A
fi

if git -C "$CLONE" diff --cached --quiet; then
  echo "==> ${CORE_REPO}:${DEST} is already identical${POST_COPY:+, and the post-copy hook changed nothing} — nothing to release"
  exit 0
fi

git -C "$CLONE" commit --quiet -m "$COMMIT_MSG"
echo "==> committed ${DEST} on ${BRANCH}"

if [ "$DRY_RUN" = 1 ]; then
  git -C "$CLONE" --no-pager show --stat --oneline HEAD
  echo "dry run: not pushing, not opening a pull request"
  exit 0
fi

echo "==> pushing ${BRANCH} to ${CORE_REPO}"
git -C "$CLONE" push --quiet -u origin "$BRANCH"

PR_ARGS=(
  --repo "$CORE_REPO"
  --base "$BASE_BRANCH"
  --head "$BRANCH"
  --title "$TITLE"
  --body "$BODY"
)
if [ "$DRAFT" = 1 ]; then PR_ARGS+=(--draft); fi

echo "==> opening pull request"
gh pr create "${PR_ARGS[@]}"
