# Quickstart: App Title Update to "Hello World"

**Feature**: 005-app-title-update
**Date**: 2026-02-19

## Prerequisites

- Repository cloned and on the feature branch
- Node.js installed (for frontend)
- Python 3.11+ installed (for backend, optional)

## Implementation Steps

### Step 1: Update Browser Tab Title (FR-001)

**File**: `frontend/index.html`

Change the `<title>` tag from `Agent Projects` to `Hello World`:

```html
<!-- Before -->
<title>Agent Projects</title>

<!-- After -->
<title>Hello World</title>
```

### Step 2: Update Application Header (FR-002)

**File**: `frontend/src/App.tsx`

Replace both `<h1>` elements that display the application title:

1. **Login screen** (approx. line 72):
```tsx
// Before
<h1>Agent Projects</h1>

// After
<h1>Hello World</h1>
```

2. **App header** (approx. line 89):
```tsx
// Before
<h1>Agent Projects</h1>

// After
<h1>Hello World</h1>
```

### Step 3: Update E2E Test Assertions (FR-006)

Replace all test assertions that reference the old title:

**File**: `frontend/e2e/auth.spec.ts` — 5 assertions
**File**: `frontend/e2e/ui.spec.ts` — 2 assertions
**File**: `frontend/e2e/integration.spec.ts` — 1 assertion

In each file, replace `'Agent Projects'` with `'Hello World'` in all `toContainText()` and `toHaveTitle()` calls.

### Step 4: Update Backend API Metadata (Optional)

**File**: `backend/src/main.py`

Update the FastAPI application metadata:

```python
# Before
title="Agent Projects API",
description="REST API for Agent Projects",

# After
title="Hello World API",
description="REST API for Hello World",
```

Also update logger messages for consistency:

```python
# Before
logger.info("Starting Agent Projects API")
logger.info("Shutting down Agent Projects API")

# After
logger.info("Starting Hello World API")
logger.info("Shutting down Hello World API")
```

## Verification

### Manual Verification

1. Start the frontend dev server: `cd frontend && npm run dev`
2. Open the application in a browser
3. Verify the browser tab shows "Hello World"
4. Verify the login page header shows "Hello World"
5. After authentication, verify the app header shows "Hello World"

### Automated Verification

1. Run frontend unit tests: `cd frontend && npm test`
2. Run e2e tests (requires running app): `cd frontend && npm run test:e2e`
3. Run backend tests: `cd backend && pytest`

## Scope Boundaries

**In scope**: All files listed above containing user-facing title text and their test assertions.

**Out of scope** (optional, non-user-facing):
- `README.md`, `backend/README.md` — project documentation
- `.devcontainer/devcontainer.json` — dev container name
- `.env.example` — comment text
- `backend/pyproject.toml` — package description
- Source code JSDoc comments — not rendered to users
