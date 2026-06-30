#!/usr/bin/env bash
set -euo pipefail

no_pull=0
if [[ "${1:-}" == "--no-pull" ]]; then
  no_pull=1
fi

cd "$(dirname "$0")/.."

if [[ ! -d ".git" ]]; then
  echo "This folder is not a Git repository yet. Run: git init" >&2
  exit 1
fi

git lfs install --local >/dev/null 2>&1 || true

if [[ "$no_pull" -eq 0 ]]; then
  if [[ -n "$(git remote)" ]]; then
    git pull --rebase --autostash
  else
    echo "No Git remote configured; skipping pull."
  fi
fi

git status --short --branch

