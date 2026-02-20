# Data Model: Update App Title to "Happy Place"

**Feature**: 007-app-title-happy-place  
**Date**: 2026-02-20  
**Source**: [spec.md](spec.md), [research.md](research.md)

## Overview

This feature involves no data model changes — no new entities, fields, relationships, or state transitions. The change is a pure string replacement of the application display title from `"Agent Projects"` to `"Happy Place"` across all locations in the codebase.

This document serves as the **complete file inventory** of all changes required.

## File Change Inventory

### Category 1: User-Visible Title (Priority: P1)

These files directly affect what end users see in the browser.

| # | File | Line | Current Value | New Value | Type |
|---|------|------|---------------|-----------|------|
| 1 | `frontend/index.html` | 7 | `<title>Agent Projects</title>` | `<title>Happy Place</title>` | HTML title tag |
| 2 | `frontend/src/App.tsx` | 72 | `<h1>Agent Projects</h1>` | `<h1>Happy Place</h1>` | Login view heading |
| 3 | `frontend/src/App.tsx` | 89 | `<h1>Agent Projects</h1>` | `<h1>Happy Place</h1>` | Main header heading |

### Category 2: Backend API Metadata (Priority: P1)

These files affect the API documentation and server logs.

| # | File | Line | Current Value | New Value | Type |
|---|------|------|---------------|-----------|------|
| 4 | `backend/src/main.py` | 75 | `"Starting Agent Projects API"` | `"Starting Happy Place API"` | Log message |
| 5 | `backend/src/main.py` | 77 | `"Shutting down Agent Projects API"` | `"Shutting down Happy Place API"` | Log message |
| 6 | `backend/src/main.py` | 85 | `title="Agent Projects API"` | `title="Happy Place API"` | FastAPI title |
| 7 | `backend/src/main.py` | 86 | `description="REST API for Agent Projects"` | `description="REST API for Happy Place"` | FastAPI description |

### Category 3: E2E Test Assertions (Priority: P1)

These test assertions must be updated to match the new title.

| # | File | Line | Current Value | New Value |
|---|------|------|---------------|-----------|
| 8 | `frontend/e2e/auth.spec.ts` | 12 | `toContainText('Agent Projects')` | `toContainText('Happy Place')` |
| 9 | `frontend/e2e/auth.spec.ts` | 24 | `toContainText('Agent Projects')` | `toContainText('Happy Place')` |
| 10 | `frontend/e2e/auth.spec.ts` | 38 | `toContainText('Agent Projects')` | `toContainText('Happy Place')` |
| 11 | `frontend/e2e/auth.spec.ts` | 62 | `toHaveTitle(/Agent Projects/i)` | `toHaveTitle(/Happy Place/i)` |
| 12 | `frontend/e2e/auth.spec.ts` | 99 | `toContainText('Agent Projects')` | `toContainText('Happy Place')` |
| 13 | `frontend/e2e/ui.spec.ts` | 43 | `toContainText('Agent Projects')` | `toContainText('Happy Place')` |
| 14 | `frontend/e2e/ui.spec.ts` | 67 | `toContainText('Agent Projects')` | `toContainText('Happy Place')` |
| 15 | `frontend/e2e/integration.spec.ts` | 69 | `toContainText('Agent Projects')` | `toContainText('Happy Place')` |

### Category 4: Developer Configuration & Documentation (Priority: P2)

These files affect developer experience and project metadata.

| # | File | Line | Current Value | New Value | Type |
|---|------|------|---------------|-----------|------|
| 16 | `.devcontainer/devcontainer.json` | 2 | `"name": "Agent Projects"` | `"name": "Happy Place"` | Dev container name |
| 17 | `.devcontainer/post-create.sh` | 7 | `Setting up Agent Projects development environment` | `Setting up Happy Place development environment` | Setup message |
| 18 | `.env.example` | 2 | `# Agent Projects - Environment Configuration` | `# Happy Place - Environment Configuration` | Config header |
| 19 | `backend/pyproject.toml` | 4 | `description = "FastAPI backend for Agent Projects"` | `description = "FastAPI backend for Happy Place"` | Package description |
| 20 | `README.md` | 1 | `# Agent Projects` | `# Happy Place` | Project heading |
| 21 | `backend/README.md` | 1 | `# Agent Projects — Backend` | `# Happy Place — Backend` | Backend heading |
| 22 | `backend/README.md` | 3 | `...powers Agent Projects and...` | `...powers Happy Place and...` | Backend description |

### Category 5: Code Comments & Docstrings (Priority: P2)

These are developer-facing comments that reference the app name.

| # | File | Line | Current Value | New Value | Type |
|---|------|------|---------------|-----------|------|
| 23 | `frontend/src/services/api.ts` | 2 | `API client service for Agent Projects.` | `API client service for Happy Place.` | JSDoc comment |
| 24 | `frontend/src/types/index.ts` | 2 | `TypeScript types for Agent Projects API.` | `TypeScript types for Happy Place API.` | JSDoc comment |
| 25 | `backend/tests/test_api_e2e.py` | 2 | `End-to-end API tests for the Agent Projects Backend.` | `End-to-end API tests for the Happy Place Backend.` | Python docstring |

## Validation Rules

- **Casing**: Must be exactly `"Happy Place"` (title case with space) in all display contexts
- **No partial matches**: The string `"Agent Projects"` must not appear anywhere in the codebase after the change (verified by `grep -r "Agent Projects" . --include="*.{ts,tsx,py,html,json,toml,sh,md,yaml,yml}"`)
- **Context preservation**: Surrounding text structure must be preserved (e.g., `"FastAPI backend for Happy Place"` not `"FastAPI backend for Happy Place API"`)

## Entities

No new entities are introduced by this feature. The change is purely cosmetic/branding.

## Relationships

No relationship changes. The title string is independent and not referenced by any data model, database, or API schema.

## State Transitions

N/A — no state changes involved.
