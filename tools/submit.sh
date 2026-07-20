#!/usr/bin/env bash
#
# submit: branch, commit, push, and open a self-merging pull request.
#
# This is the whole contribution flow in one command. It opens a PR (pull
# request — a proposal to merge your work into `main`) and turns on GitHub's
# "auto-merge", which means the PR merges itself the moment CI goes green.
# Nobody has to review or click anything.
#
# Usage:
#     tools/submit.sh -m "feat: add fianchetto-bot (league L1)"
#     tools/submit.sh -m "fix: arena time limit off by one" --dry-run
#
# Diagnostics go to stderr; the PR URL goes to stdout (so you can pipe it).

set -euo pipefail

TOOL="submit"
MSG=""
DRY_RUN=0

usage() {
    cat <<'EOF'
Usage: tools/submit.sh -m MESSAGE [--dry-run]

Branch, commit, push, and open a pull request that merges itself once CI passes.

Options:
  -m, --message MSG   Commit message. Also used to name the branch.
  -n, --dry-run       Print what would happen; change nothing.
  -h, --help          Show this help and exit.

Run from anywhere inside the repo. If you are on `main`, a new branch is
created for you; if you are already on a branch, that branch is used.

Next: after this prints a PR URL, you are done — CI runs and the PR merges
itself. Watch it with `gh pr checks --watch`.
EOF
}

die() {
    echo "$TOOL: error: $*" >&2
    exit 1
}

say() { echo "$TOOL: $*" >&2; }

while [ $# -gt 0 ]; do
    case "$1" in
        -m|--message) MSG="${2:-}"; shift 2 ;;
        -n|--dry-run) DRY_RUN=1; shift ;;
        -h|--help)    usage; exit 0 ;;
        *)            die "unknown argument: $1 (try --help)" ;;
    esac
done

[ -n "$MSG" ] || die "a commit message is required (-m). Try --help."

command -v gh >/dev/null || die "the GitHub CLI (gh) is not installed: https://cli.github.com"
gh auth status >/dev/null 2>&1 || die "not logged in to GitHub. Run: gh auth login"

# Work from the repo root so the checks below find their paths.
ROOT="$(git rev-parse --show-toplevel)" || die "not inside a git repository"
cd "$ROOT"

if [ -z "$(git status --porcelain)" ]; then
    die "nothing to submit — no changed files."
fi

# Branch name: slugify the commit message, drop any conventional-commit prefix.
BRANCH="$(printf '%s' "$MSG" \
    | sed -E 's/^[a-z]+(\([^)]*\))?!?: *//' \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g' \
    | cut -c1-40)"
[ -n "$BRANCH" ] || BRANCH="submit"

CURRENT="$(git rev-parse --abbrev-ref HEAD)"
if [ "$CURRENT" = "main" ]; then
    TARGET_BRANCH="$BRANCH"
    say "on main — will create branch '$TARGET_BRANCH'"
else
    TARGET_BRANCH="$CURRENT"
    say "already on branch '$TARGET_BRANCH' — using it"
fi

if [ "$DRY_RUN" -eq 1 ]; then
    say "dry run; nothing was changed. Would have:"
    {
        echo "  - checked out branch: $TARGET_BRANCH"
        echo "  - committed: $MSG"
        echo "  - pushed to origin and opened a self-merging PR"
        echo "  - files:"
        git status --porcelain | sed 's/^/      /'
    } >&2
    exit 0
fi

# Run the same gates CI runs, so a red PR is caught here in seconds rather
# than in CI minutes later. Not fatal: a draft PR on broken code is fine and
# is explicitly encouraged for questions.
say "running local checks (same as CI)..."
CHECKS_OK=1
python tools/check_imports.py engines || CHECKS_OK=0
pytest -q || CHECKS_OK=0
if [ "$CHECKS_OK" -eq 0 ]; then
    say "warning: local checks failed — submitting anyway, but CI will block the"
    say "warning: auto-merge until they pass. That is fine; push fixes to this"
    say "warning: same branch and it will merge itself when green."
fi

[ "$CURRENT" = "main" ] && git checkout -b "$TARGET_BRANCH"

git add -A
git commit -m "$MSG"
git push -u origin "$TARGET_BRANCH"

# --fill reuses the commit message as the PR title/body.
gh pr create --fill
gh pr merge --auto --squash

say "done — this PR merges itself when CI passes."
say "Next: watch it with 'gh pr checks --watch', or just walk away."
gh pr view --json url --jq .url
