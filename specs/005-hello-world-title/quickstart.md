# Quickstart: Update App Title to "Hello World"

**Feature**: 005-hello-world-title  
**Date**: 2026-02-19

## Prerequisites

- Node.js (for frontend build/test)
- Python 3.11+ (for backend)
- Access to the repository on the feature branch

## Implementation Summary

This feature is a global find-and-replace of "Agent Projects" → "Hello World" across the codebase. No new files, dependencies, or architectural changes are required.

## Step-by-Step Implementation

### Step 1: Update User-Facing Display (P1)

**Files to modify:**

1. **`frontend/index.html`** — Change `<title>Agent Projects</title>` to `<title>Hello World</title>`
2. **`frontend/src/App.tsx`** — Change both `<h1>Agent Projects</h1>` occurrences to `<h1>Hello World</h1>`

**Verify:** Run the frontend dev server (`npm run dev` in `frontend/`) and confirm:
- Browser tab shows "Hello World"
- Login page header shows "Hello World"
- App header shows "Hello World"

### Step 2: Update Backend Metadata (P2)

**Files to modify:**

1. **`backend/src/main.py`** — Update FastAPI app title, description, and log messages
2. **`backend/pyproject.toml`** — Update package description
3. **`backend/README.md`** — Update headings and descriptions

**Verify:** Run the backend (`uvicorn backend.src.main:app`) and check `/docs` shows "Hello World API"

### Step 3: Update Tests and Config (P3)

**Files to modify:**

1. **`frontend/e2e/auth.spec.ts`** — Update all `'Agent Projects'` assertions to `'Hello World'`
2. **`frontend/e2e/ui.spec.ts`** — Update all `'Agent Projects'` assertions to `'Hello World'`
3. **`frontend/e2e/integration.spec.ts`** — Update assertion to `'Hello World'`
4. **`frontend/src/types/index.ts`** — Update JSDoc comment
5. **`frontend/src/services/api.ts`** — Update JSDoc comment
6. **`.devcontainer/devcontainer.json`** — Update container name
7. **`.env.example`** — Update header comment

### Step 4: Verify No Remaining References

Run a global search to confirm no "Agent Projects" references remain:

```bash
grep -r "Agent Projects" --include="*.ts" --include="*.tsx" --include="*.html" --include="*.json" --include="*.py" --include="*.toml" --include="*.md" --include="*.example" .
```

Expected result: Only matches in `specs/` directory (which documents the old title for context).

## Testing

### Unit Tests
No new unit tests required — this is a text replacement with no logic changes.

### E2E Tests
Existing E2E tests will be updated to assert "Hello World" instead of "Agent Projects". Run:

```bash
cd frontend && npx playwright test
```

### Manual Verification
1. Start the application (`docker-compose up` or run frontend/backend individually)
2. Open browser → verify tab title is "Hello World"
3. Verify login page header shows "Hello World"
4. Log in → verify app header shows "Hello World"
5. Open `/docs` → verify API docs title is "Hello World API"
