# Quickstart: Update App Title to "Happy Place"

**Feature**: 007-app-title-happy-place
**Date**: 2026-02-20

## Overview

This feature renames the application from "Agent Projects" to "Happy Place" across all locations in the codebase. It is a pure string-replacement change with no logic, schema, or dependency modifications.

| What Changes | Count | Impact |
|-------------|-------|--------|
| User-visible title (browser tab, headers) | 3 | Immediate branding update |
| API metadata (FastAPI title/description) | 4 | OpenAPI docs show new name |
| Developer config & docs | 6 | DevContainer, README, env config |
| Code comments | 3 | JSDoc and docstring updates |
| E2E test assertions | 8 | Tests expect new title |
| Build config (pyproject.toml) | 1 | Package description updated |
| **Total** | **25** | **Zero functional impact** |

## Prerequisites

1. Repository cloned and checked out to the feature branch
2. No additional dependencies, tools, or environment setup needed

## Implementation Steps

### Step 1: Update User-Visible Frontend (3 changes)

Update the browser tab title and both header elements:

1. **`frontend/index.html`** line 7 — Change `<title>` content
2. **`frontend/src/App.tsx`** line 72 — Change login page `<h1>`
3. **`frontend/src/App.tsx`** line 89 — Change authenticated page `<h1>`

**Verify**: Open the app in a browser. The tab should read "Happy Place" and the header should display "Happy Place" on both login and authenticated views.

### Step 2: Update Backend API Metadata (4 changes)

Update FastAPI application config and log messages:

1. **`backend/src/main.py`** line 75 — Startup log message
2. **`backend/src/main.py`** line 77 — Shutdown log message
3. **`backend/src/main.py`** line 85 — FastAPI `title` parameter
4. **`backend/src/main.py`** line 86 — FastAPI `description` parameter

**Verify**: Start the backend and visit `/api/docs` (debug mode). The Swagger UI should show "Happy Place API" as the title.

### Step 3: Update Developer Configuration (3 changes)

1. **`.devcontainer/devcontainer.json`** line 2 — Container name
2. **`.devcontainer/post-create.sh`** line 7 — Setup message
3. **`.env.example`** line 2 — Header comment

**Verify**: Open the project in a devcontainer. The container name should show "Happy Place".

### Step 4: Update Documentation (3 changes)

1. **`README.md`** line 1 — Project heading
2. **`backend/README.md`** line 1 — Backend heading
3. **`backend/README.md`** line 3 — Backend description

**Verify**: Open README files and confirm headings read "Happy Place".

### Step 5: Update Code Comments (3 changes)

1. **`frontend/src/services/api.ts`** line 2 — JSDoc comment
2. **`frontend/src/types/index.ts`** line 2 — JSDoc comment
3. **`backend/tests/test_api_e2e.py`** line 2 — Docstring comment

### Step 6: Update Build Config (1 change)

1. **`backend/pyproject.toml`** line 4 — Package description

### Step 7: Update E2E Test Assertions (8 changes)

1. **`frontend/e2e/auth.spec.ts`** — 5 assertion strings (lines 12, 24, 38, 62, 99)
2. **`frontend/e2e/ui.spec.ts`** — 2 assertion strings (lines 43, 67)
3. **`frontend/e2e/integration.spec.ts`** — 1 assertion string (line 69)

**Verify**: Run `npx playwright test` from the `frontend/` directory to confirm all E2E tests pass.

### Step 8: Final Verification

Run a codebase-wide search to confirm zero remaining occurrences:

```bash
grep -rn "Agent Projects" --include="*.py" --include="*.ts" --include="*.tsx" \
  --include="*.html" --include="*.json" --include="*.toml" --include="*.sh" \
  --include="*.md" --include="*.env*" . | grep -v 'specs/'
```

Expected result: **no output** (zero matches outside the specs directory).

## Error Handling

| Scenario | Resolution |
|----------|-----------|
| Missed occurrence found by search | Update the missed file and re-run search |
| E2E test fails after update | Verify the assertion string matches "Happy Place" exactly |
| Browser cache shows old title | Hard refresh (Ctrl+Shift+R) to clear cache |

## Key Files Modified

| File | Change Type |
|------|-------------|
| `frontend/index.html` | Title tag update |
| `frontend/src/App.tsx` | H1 heading updates (×2) |
| `backend/src/main.py` | FastAPI metadata + log messages (×4) |
| `.devcontainer/devcontainer.json` | Container name |
| `.devcontainer/post-create.sh` | Setup message |
| `.env.example` | Comment header |
| `README.md` | Project heading |
| `backend/README.md` | Heading + description |
| `backend/pyproject.toml` | Package description |
| `frontend/src/services/api.ts` | JSDoc comment |
| `frontend/src/types/index.ts` | JSDoc comment |
| `backend/tests/test_api_e2e.py` | Docstring comment |
| `frontend/e2e/auth.spec.ts` | Test assertions (×5) |
| `frontend/e2e/ui.spec.ts` | Test assertions (×2) |
| `frontend/e2e/integration.spec.ts` | Test assertion (×1) |
