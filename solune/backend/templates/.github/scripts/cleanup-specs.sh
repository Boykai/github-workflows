#!/usr/bin/env bash
set -euo pipefail

# Removes the specs/ directory from the working tree and stages the deletion.
# Intended to run as a final step in the Linter agent after all checks pass.

REPO_ROOT="$(git rev-parse --show-toplevel)"
SPECS_DIR="$REPO_ROOT/specs"

if [ -d "$SPECS_DIR" ]; then
  git rm -rf "$SPECS_DIR"
  echo "specs/ directory removed and staged for commit."
else
  echo "specs/ directory does not exist — nothing to clean up."
fi
