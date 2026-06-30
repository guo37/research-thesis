#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || -z "${1:-}" ]]; then
  echo "Usage: bash scripts/sync_finish.sh \"commit message\" [--no-push]" >&2
  exit 1
fi

message="$1"
no_push=0
if [[ "${2:-}" == "--no-push" ]]; then
  no_push=1
fi

cd "$(dirname "$0")/.."

if [[ ! -d ".git" ]]; then
  echo "This folder is not a Git repository yet. Run: git init" >&2
  exit 1
fi

sensitive="$(find . -path ./.git -prune -o -type f \( -name "*.pem" -o -name "*.key" -o -name ".env" -o -name ".env.*" \) -print)"
if [[ -n "$sensitive" ]]; then
  echo "Sensitive local files found. They are ignored and will not be committed:"
  echo "$sensitive" | sed 's#^\./# - #'
fi

git lfs install --local >/dev/null 2>&1 || true
git add .

if [[ -z "$(git diff --cached --name-only)" ]]; then
  echo "No staged changes to commit."
  git status --short --branch
  exit 0
fi

git commit -m "$message"

if [[ "$no_push" -eq 0 ]]; then
  if [[ -n "$(git remote)" ]]; then
    git push
  else
    echo "No Git remote configured; commit created locally. Add a remote before multi-device sync."
  fi
fi

git status --short --branch

