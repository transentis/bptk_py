#!/bin/bash
#
# publish_docs.sh
#
# Copies the rendered documentation into the bptk-docs repository, from where Vercel
# deploys it. Nothing is built here - `just docs-publish` renders first and this script
# refuses to run on anything but a complete, gate-approved render.
#
# Usage:
#   ./scripts/publish_docs.sh [--dry-run] [--allow-dirty] [--any-branch] [--yes]
#
# Environment:
#   DOCS_REPO  where bptk-docs is checked out (default: ../bptk-docs). CI clones it into
#              a working directory and points this at the clone, so the copy, the
#              exclusions and the guards stay in one place rather than being restated in
#              a workflow file.
#
# What it does:
#   1. Refuses unless this is `main`, the working tree is clean and the render is complete
#   2. Runs the documentation gate - a green `quarto render` says nothing about the pages
#   3. rsync --delete into ../bptk-docs (which mirrors `_output` one to one)
#   4. Shows the diff and asks before committing, and asks again before pushing
#
# Why rsync rather than the `cp -R` this replaces: `cp` never deletes, so a page removed
# from the site stayed online until someone remembered to add it to a hand-written list
# of directories to wipe first. That list had no entry for `marimo-islands/`, which the
# new site brings. `--delete` derives the removals instead of maintaining them.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INTERNAL_REPO="$(dirname "$SCRIPT_DIR")"
DOCS_REPO="${DOCS_REPO:-${INTERNAL_REPO}/../bptk-docs}"
OUTPUT="${INTERNAL_REPO}/docs/tutorial/_output"

DRY_RUN=""
ALLOW_DIRTY="no"
ANY_BRANCH="no"
ASSUME_YES="no"
for argument in "$@"; do
    case "$argument" in
        --dry-run)     DRY_RUN="--dry-run" ;;
        --allow-dirty) ALLOW_DIRTY="yes" ;;
        --any-branch)  ANY_BRANCH="yes" ;;
        --yes)         ASSUME_YES="yes" ;;
        *) echo "Unknown option: $argument"; exit 2 ;;
    esac
done
[[ -n "$DRY_RUN" ]] && echo "=== DRY RUN MODE ==="

cd "$INTERNAL_REPO"

# --- What must be true before the site can be published -----------------------------

if [[ ! -d "$DOCS_REPO/.git" ]]; then
    echo "Error: bptk-docs not found at $DOCS_REPO"
    exit 1
fi

# In CI the checkout is detached, so `git rev-parse --abbrev-ref HEAD` says "HEAD".
# GITHUB_REF_NAME carries the branch there, which keeps this guard meaningful in both
# places rather than being waved away with a flag.
BRANCH="${GITHUB_REF_NAME:-$(git rev-parse --abbrev-ref HEAD)}"
if [[ "$BRANCH" != "main" && "$ANY_BRANCH" != "yes" ]]; then
    echo "Error: on branch '$BRANCH'. The website is published from main."
    echo "       Merge first, or pass --any-branch if you know why you are doing this."
    exit 1
fi

if [[ -n "$(git status --porcelain)" && "$ALLOW_DIRTY" != "yes" ]]; then
    echo "Error: the working tree has uncommitted changes, so the published site could"
    echo "       not be traced back to a commit. Commit them, or pass --allow-dirty."
    exit 1
fi

# A half-built `_output` looks like a result: quarto writes page by page, so an aborted
# render leaves a directory that is part old and part missing.
for required in "index.html" "marimo-islands" "search.json"; do
    if [[ ! -e "$OUTPUT/$required" ]]; then
        echo "Error: $OUTPUT/$required is missing - the render is incomplete."
        echo "       Run 'just docs-render' (or 'just docs-publish', which does both)."
        exit 1
    fi
done

echo "Gate: checking what the render actually produced"
PYTHON="${INTERNAL_REPO}/.venv/bin/python"
[[ -x "$PYTHON" ]] || PYTHON="python3"
"$PYTHON" "${SCRIPT_DIR}/check_docs_render.py" "$OUTPUT" > /tmp/docs_gate.log 2>&1 || {
    echo "Error: the documentation gate failed. Nothing was published."
    tail -25 /tmp/docs_gate.log
    exit 1
}
grep -E "^(Pages with cells|Errors in total|Dead internal links|Own runtime|Pages still on the CDN)" /tmp/docs_gate.log | sed 's/^/  /'

# --- Copy ---------------------------------------------------------------------------

echo ""
echo "Publishing: $OUTPUT -> $DOCS_REPO"
echo ""

# `readme.md` belongs to bptk-docs and has no counterpart here, so it is protected from
# --delete rather than being republished on every run.
rsync -a --delete --stats $DRY_RUN \
    --exclude='.git' \
    --exclude='readme.md' \
    --exclude='.DS_Store' \
    "$OUTPUT/" \
    "$DOCS_REPO/"

if [[ -n "$DRY_RUN" ]]; then
    echo ""
    echo "=== DRY RUN COMPLETE - nothing was written ==="
    exit 0
fi

# --- Review, commit, push -----------------------------------------------------------

cd "$DOCS_REPO"
CHANGES="$(git status --porcelain)"
if [[ -z "$CHANGES" ]]; then
    echo "The published site is already up to date."
    exit 0
fi

echo ""
echo "=== Changes in bptk-docs ==="
# `sed -n` rather than `head`: head closes the pipe after 30 lines, git status keeps
# writing, and under `set -o pipefail` the SIGPIPE fails the whole script with 141. Which
# means this only ever worked for a publish of 30 paths or fewer - a normal one is 500.
git status --short | sed -n '1,30p'
TOTAL="$(git status --porcelain | wc -l | tr -d ' ')"
echo "  ($TOTAL paths changed)"
echo ""
git diff --stat | tail -5

SOURCE_COMMIT="$(git -C "$INTERNAL_REPO" rev-parse --short HEAD)"
MESSAGE="Update docs from bptk-py-internal $SOURCE_COMMIT"

if [[ "$ASSUME_YES" == "yes" ]]; then
    git add -A
    git commit -q -m "$MESSAGE"
    git push
    echo "Published: $(git log --oneline -1)"
    echo "Vercel deploys from here."
    exit 0
fi

echo ""
read -p "Commit this as the published site (from bptk-py-internal $SOURCE_COMMIT)? [y/N] " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted. The files are in $DOCS_REPO; 'git checkout .' there undoes them."
    exit 0
fi

read -p "Commit message [$MESSAGE]: " GIVEN
MESSAGE="${GIVEN:-$MESSAGE}"
git add -A
git commit -q -m "$MESSAGE"
echo "Committed locally: $(git log --oneline -1)"

echo ""
echo "The push is what deploys: Vercel builds bptk-docs on every push to main."
read -p "Push to origin? [y/N] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git push
    echo "Pushed. Vercel deploys from here."
else
    echo "Not pushed. Run 'git push' in $DOCS_REPO when ready."
fi
