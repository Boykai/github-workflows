# Data Model: Update App Title to "Happy Place"

**Feature**: 005-update-app-title | **Date**: 2026-02-20

---

## Entity Relationship Overview

This feature does not introduce, modify, or remove any data entities. It is a pure string-replacement change affecting display text, metadata, documentation, and test assertions.

```
No entity changes. Title is a hardcoded string literal, not a stored entity.
```

---

## Change Inventory

The "data model" for this feature is the **complete inventory of title string locations** — each represents a "record" that must be updated.

### User-Facing Locations (Priority: P1)

| # | File | Line | Current Value | New Value | Impact |
|---|------|------|---------------|-----------|--------|
| 1 | `frontend/index.html` | 7 | `<title>Agent Projects</title>` | `<title>Happy Place</title>` | Browser tab title |
| 2 | `frontend/src/App.tsx` | 72 | `<h1>Agent Projects</h1>` | `<h1>Happy Place</h1>` | Login page header |
| 3 | `frontend/src/App.tsx` | 89 | `<h1>Agent Projects</h1>` | `<h1>Happy Place</h1>` | Authenticated header |

### Backend Metadata (Priority: P1)

| # | File | Line | Current Value | New Value | Impact |
|---|------|------|---------------|-----------|--------|
| 4 | `backend/src/main.py` | 85 | `title="Agent Projects API"` | `title="Happy Place API"` | FastAPI OpenAPI title |
| 5 | `backend/src/main.py` | 86 | `description="REST API for Agent Projects"` | `description="REST API for Happy Place"` | FastAPI OpenAPI description |
| 6 | `backend/src/main.py` | 75 | `"Starting Agent Projects API"` | `"Starting Happy Place API"` | Startup log message |
| 7 | `backend/src/main.py` | 77 | `"Shutting down Agent Projects API"` | `"Shutting down Happy Place API"` | Shutdown log message |

### E2E Test Assertions (Priority: P1)

| # | File | Line | Current Value | New Value | Impact |
|---|------|------|---------------|-----------|--------|
| 8 | `frontend/e2e/auth.spec.ts` | 12 | `toContainText('Agent Projects')` | `toContainText('Happy Place')` | Test assertion |
| 9 | `frontend/e2e/auth.spec.ts` | 24 | `toContainText('Agent Projects'` | `toContainText('Happy Place'` | Test assertion |
| 10 | `frontend/e2e/auth.spec.ts` | 38 | `toContainText('Agent Projects')` | `toContainText('Happy Place')` | Test assertion |
| 11 | `frontend/e2e/auth.spec.ts` | 62 | `toHaveTitle(/Agent Projects/i)` | `toHaveTitle(/Happy Place/i)` | Test assertion (regex) |
| 12 | `frontend/e2e/auth.spec.ts` | 99 | `toContainText('Agent Projects')` | `toContainText('Happy Place')` | Test assertion |
| 13 | `frontend/e2e/ui.spec.ts` | 43 | `toContainText('Agent Projects')` | `toContainText('Happy Place')` | Test assertion |
| 14 | `frontend/e2e/ui.spec.ts` | 67 | `toContainText('Agent Projects')` | `toContainText('Happy Place')` | Test assertion |
| 15 | `frontend/e2e/integration.spec.ts` | 69 | `toContainText('Agent Projects')` | `toContainText('Happy Place')` | Test assertion |

### Configuration & Documentation (Priority: P2)

| # | File | Line | Current Value | New Value | Impact |
|---|------|------|---------------|-----------|--------|
| 16 | `.devcontainer/devcontainer.json` | 2 | `"name": "Agent Projects"` | `"name": "Happy Place"` | DevContainer display name |
| 17 | `.devcontainer/post-create.sh` | 7 | `Setting up Agent Projects` | `Setting up Happy Place` | Setup script message |
| 18 | `.env.example` | 2 | `# Agent Projects` | `# Happy Place` | Config file header comment |
| 19 | `backend/pyproject.toml` | 4 | `"FastAPI backend for Agent Projects"` | `"FastAPI backend for Happy Place"` | Python package description |
| 20 | `README.md` | 1 | `# Agent Projects` | `# Happy Place` | Root documentation header |
| 21 | `backend/README.md` | 1 | `# Agent Projects — Backend` | `# Happy Place — Backend` | Backend documentation header |
| 22 | `backend/README.md` | 3 | `...powers Agent Projects...` | `...powers Happy Place...` | Backend documentation body |

### Code Comments (Priority: P2)

| # | File | Line | Current Value | New Value | Impact |
|---|------|------|---------------|-----------|--------|
| 23 | `frontend/src/types/index.ts` | 2 | `TypeScript types for Agent Projects API.` | `TypeScript types for Happy Place API.` | Module docstring |
| 24 | `frontend/src/services/api.ts` | 2 | `API client service for Agent Projects.` | `API client service for Happy Place.` | Module docstring |
| 25 | `backend/tests/test_api_e2e.py` | 2 | `...for the Agent Projects Backend.` | `...for the Happy Place Backend.` | Test module docstring |

---

## Validation Rules

- **Casing**: Must be exactly "Happy Place" (title case, capital H and P) in all locations
- **No partial matches**: Entire "Agent Projects" string must be replaced, not substrings
- **Pattern preservation**: Where "Agent Projects API" exists, replace with "Happy Place API" (preserve the "API" suffix)

## State Transitions

N/A — No stateful entities are affected by this change.
