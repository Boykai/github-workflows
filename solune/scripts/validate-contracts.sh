#!/usr/bin/env bash
set -euo pipefail

# Contract Validation: Export OpenAPI schema and generate TypeScript types
# to detect drift between backend models and frontend type definitions.
#
# Usage: bash solune/scripts/validate-contracts.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="$REPO_ROOT/solune/backend"
FRONTEND_DIR="$REPO_ROOT/solune/frontend"
OPENAPI_JSON="$BACKEND_DIR/openapi.json"
GENERATED_TYPES="$FRONTEND_DIR/src/types/openapi-generated.d.ts"
BACKEND_PYTHON="$BACKEND_DIR/.venv/bin/python"

if [[ -x "$BACKEND_PYTHON" ]]; then
  PYTHON_BIN="$BACKEND_PYTHON"
else
  PYTHON_BIN="python3"
fi

echo "=== Step 1: Export OpenAPI schema ==="
"$PYTHON_BIN" "$SCRIPT_DIR/export-openapi.py" --output "$OPENAPI_JSON"

if [[ ! -f "$OPENAPI_JSON" ]]; then
  echo "ERROR: OpenAPI schema not generated at $OPENAPI_JSON"
  exit 1
fi

echo "=== Step 2: Generate TypeScript types from OpenAPI schema ==="
cd "$FRONTEND_DIR"
npx openapi-typescript "$OPENAPI_JSON" --output "$GENERATED_TYPES"

echo "=== Step 3: Type-check generated types ==="
npx tsc --noEmit

echo "=== Contract validation passed ==="
