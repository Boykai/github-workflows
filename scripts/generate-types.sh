#!/usr/bin/env bash
# scripts/generate-types.sh — Generate TypeScript types from backend OpenAPI schema and constants.
#
# Usage:
#   bash scripts/generate-types.sh              # fetch from running backend
#   OPENAPI_FILE=openapi.json bash scripts/generate-types.sh  # use local file

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend/src"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

mkdir -p "$FRONTEND_DIR/types" "$FRONTEND_DIR/constants"

# ── Step 1: Generate TypeScript types from OpenAPI schema ──────────────────

if [[ -n "${OPENAPI_FILE:-}" ]]; then
    echo "Using local OpenAPI schema: $OPENAPI_FILE"
    SCHEMA_SOURCE="$OPENAPI_FILE"
else
    echo "Fetching OpenAPI schema from $BACKEND_URL/openapi.json ..."
    SCHEMA_SOURCE="$BACKEND_URL/openapi.json"
fi

npx --prefix "$ROOT_DIR/frontend" openapi-typescript "$SCHEMA_SOURCE" \
    --output "$FRONTEND_DIR/types/generated.ts"

echo "✓ Generated $FRONTEND_DIR/types/generated.ts"

# ── Step 2: Generate constants from Python source ──────────────────────────

python3 "$SCRIPT_DIR/generate-constants.py" \
    --input "$ROOT_DIR/backend/src/constants.py" \
    --output "$FRONTEND_DIR/constants/generated.ts"

echo "✓ Generated $FRONTEND_DIR/constants/generated.ts"

echo "Type generation complete."
