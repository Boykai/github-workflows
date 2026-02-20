# Quickstart: Update App Title to "Happy Place"

**Feature**: 007-app-title-happy-place  
**Date**: 2026-02-20

## Overview

This feature updates the application display title from "Agent Projects" to "Happy Place" across all locations in the codebase. The change is a systematic string replacement affecting 15 files with ~25 occurrences.

| Category | Files | Occurrences | Priority |
|----------|-------|-------------|----------|
| User-visible title | 2 files | 3 | P1 |
| Backend API metadata | 1 file | 4 | P1 |
| E2E test assertions | 3 files | 8 | P1 |
| Developer config & docs | 6 files | 7 | P2 |
| Code comments & docstrings | 3 files | 3 | P2 |
| **Total** | **15 files** | **~25** | |

## Prerequisites

1. **Repository cloned** with the feature branch checked out
2. **Node.js** installed (for frontend verification)
3. **Python 3.12** installed (for backend verification)

## Implementation Steps

### Step 1: Frontend User-Visible Title (P1)

Update the browser tab title and application headings:

```bash
# frontend/index.html — line 7
# Change: <title>Agent Projects</title> → <title>Happy Place</title>

# frontend/src/App.tsx — lines 72, 89
# Change: <h1>Agent Projects</h1> → <h1>Happy Place</h1> (both occurrences)
```

**Verify**: Run `npm run dev` in the frontend directory, open the browser, and confirm:
- Browser tab shows "Happy Place"
- Login page header shows "Happy Place"

### Step 2: Backend API Metadata (P1)

Update the FastAPI application metadata and log messages:

```bash
# backend/src/main.py — lines 75, 77, 85, 86
# Change all "Agent Projects" → "Happy Place" in:
#   - logger.info("Starting Agent Projects API") → logger.info("Starting Happy Place API")
#   - logger.info("Shutting down Agent Projects API") → logger.info("Shutting down Happy Place API")
#   - title="Agent Projects API" → title="Happy Place API"
#   - description="REST API for Agent Projects" → description="REST API for Happy Place"
```

**Verify**: Run the backend and check `/api/docs` shows "Happy Place API".

### Step 3: E2E Test Assertions (P1)

Update all Playwright test assertions to match the new title:

```bash
# frontend/e2e/auth.spec.ts — lines 12, 24, 38, 62, 99
# frontend/e2e/ui.spec.ts — lines 43, 67
# frontend/e2e/integration.spec.ts — line 69
# Change all 'Agent Projects' → 'Happy Place' in test assertions
```

**Verify**: Tests compile without errors (`npx tsc --noEmit` in frontend/).

### Step 4: Developer Configuration (P2)

Update developer environment and project metadata:

```bash
# .devcontainer/devcontainer.json — line 2
# Change: "name": "Agent Projects" → "name": "Happy Place"

# .devcontainer/post-create.sh — line 7
# Change: "Setting up Agent Projects development environment" → "Setting up Happy Place development environment"

# .env.example — line 2
# Change: "# Agent Projects - Environment Configuration" → "# Happy Place - Environment Configuration"

# backend/pyproject.toml — line 4
# Change: description = "FastAPI backend for Agent Projects" → description = "FastAPI backend for Happy Place"
```

### Step 5: Documentation (P2)

Update README files:

```bash
# README.md — line 1
# Change: # Agent Projects → # Happy Place

# backend/README.md — lines 1, 3
# Change: "Agent Projects" → "Happy Place" (heading and description)
```

### Step 6: Code Comments (P2)

Update developer-facing comments and docstrings:

```bash
# frontend/src/services/api.ts — line 2
# frontend/src/types/index.ts — line 2
# backend/tests/test_api_e2e.py — line 2
# Change all "Agent Projects" → "Happy Place" in comments/docstrings
```

## Final Verification

After all changes:

```bash
# Verify no remaining references (from repo root, excluding specs/)
grep -rn "Agent Projects" . \
  --include="*.ts" --include="*.tsx" --include="*.py" \
  --include="*.html" --include="*.json" --include="*.toml" \
  --include="*.sh" --include="*.md" --include="*.yaml" --include="*.yml" \
  | grep -v specs/ | grep -v node_modules/ | grep -v .git/

# Expected: zero results
```

## Key Files Modified

| File | Change |
|------|--------|
| `frontend/index.html` | `<title>` tag |
| `frontend/src/App.tsx` | Two `<h1>` elements |
| `backend/src/main.py` | FastAPI title, description, log messages |
| `frontend/e2e/auth.spec.ts` | 5 test assertions |
| `frontend/e2e/ui.spec.ts` | 2 test assertions |
| `frontend/e2e/integration.spec.ts` | 1 test assertion |
| `.devcontainer/devcontainer.json` | Container name |
| `.devcontainer/post-create.sh` | Setup message |
| `.env.example` | Config header comment |
| `backend/pyproject.toml` | Package description |
| `README.md` | Project heading |
| `backend/README.md` | Heading and description |
| `frontend/src/services/api.ts` | JSDoc comment |
| `frontend/src/types/index.ts` | JSDoc comment |
| `backend/tests/test_api_e2e.py` | Docstring |
