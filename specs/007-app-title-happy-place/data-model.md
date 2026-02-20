# Data Model: Update App Title to "Happy Place"

**Feature**: 007-app-title-happy-place
**Date**: 2026-02-20
**Source**: [spec.md](spec.md), [research.md](research.md)

## Entities

This feature does not introduce, modify, or remove any data entities, database schemas, API models, or TypeScript interfaces. The change is a pure string replacement of the application display name.

## String Inventory

The following is the complete inventory of all occurrences of the current title "Agent Projects" that must be replaced with "Happy Place".

### Category 1: User-Visible (Browser & UI)

| # | File | Line | Current Value | New Value |
|---|------|------|---------------|-----------|
| 1 | `frontend/index.html` | 7 | `<title>Agent Projects</title>` | `<title>Happy Place</title>` |
| 2 | `frontend/src/App.tsx` | 72 | `<h1>Agent Projects</h1>` | `<h1>Happy Place</h1>` |
| 3 | `frontend/src/App.tsx` | 89 | `<h1>Agent Projects</h1>` | `<h1>Happy Place</h1>` |

### Category 2: API & Backend Metadata

| # | File | Line | Current Value | New Value |
|---|------|------|---------------|-----------|
| 4 | `backend/src/main.py` | 85 | `title="Agent Projects API"` | `title="Happy Place API"` |
| 5 | `backend/src/main.py` | 86 | `description="REST API for Agent Projects"` | `description="REST API for Happy Place"` |
| 6 | `backend/src/main.py` | 75 | `logger.info("Starting Agent Projects API")` | `logger.info("Starting Happy Place API")` |
| 7 | `backend/src/main.py` | 77 | `logger.info("Shutting down Agent Projects API")` | `logger.info("Shutting down Happy Place API")` |

### Category 3: Developer Configuration

| # | File | Line | Current Value | New Value |
|---|------|------|---------------|-----------|
| 8 | `.devcontainer/devcontainer.json` | 2 | `"name": "Agent Projects"` | `"name": "Happy Place"` |
| 9 | `.devcontainer/post-create.sh` | 7 | `echo "🚀 Setting up Agent Projects development environment..."` | `echo "🚀 Setting up Happy Place development environment..."` |
| 10 | `.env.example` | 2 | `# Agent Projects - Environment Configuration` | `# Happy Place - Environment Configuration` |
| 11 | `backend/pyproject.toml` | 4 | `description = "FastAPI backend for Agent Projects"` | `description = "FastAPI backend for Happy Place"` |

### Category 4: Documentation

| # | File | Line | Current Value | New Value |
|---|------|------|---------------|-----------|
| 12 | `README.md` | 1 | `# Agent Projects` | `# Happy Place` |
| 13 | `backend/README.md` | 1 | `# Agent Projects — Backend` | `# Happy Place — Backend` |
| 14 | `backend/README.md` | 3 | `...powers Agent Projects and the...` | `...powers Happy Place and the...` |

### Category 5: Code Comments

| # | File | Line | Current Value | New Value |
|---|------|------|---------------|-----------|
| 15 | `frontend/src/services/api.ts` | 2 | `* API client service for Agent Projects.` | `* API client service for Happy Place.` |
| 16 | `frontend/src/types/index.ts` | 2 | `* TypeScript types for Agent Projects API.` | `* TypeScript types for Happy Place API.` |
| 17 | `backend/tests/test_api_e2e.py` | 2 | `End-to-end API tests for the Agent Projects Backend.` | `End-to-end API tests for the Happy Place Backend.` |

### Category 6: E2E Test Assertions

| # | File | Line | Current Value | New Value |
|---|------|------|---------------|-----------|
| 18 | `frontend/e2e/auth.spec.ts` | 12 | `toContainText('Agent Projects')` | `toContainText('Happy Place')` |
| 19 | `frontend/e2e/auth.spec.ts` | 24 | `toContainText('Agent Projects', { timeout: 5000 })` | `toContainText('Happy Place', { timeout: 5000 })` |
| 20 | `frontend/e2e/auth.spec.ts` | 38 | `toContainText('Agent Projects')` | `toContainText('Happy Place')` |
| 21 | `frontend/e2e/auth.spec.ts` | 62 | `toHaveTitle(/Agent Projects/i)` | `toHaveTitle(/Happy Place/i)` |
| 22 | `frontend/e2e/auth.spec.ts` | 99 | `toContainText('Agent Projects')` | `toContainText('Happy Place')` |
| 23 | `frontend/e2e/ui.spec.ts` | 43 | `toContainText('Agent Projects')` | `toContainText('Happy Place')` |
| 24 | `frontend/e2e/ui.spec.ts` | 67 | `toContainText('Agent Projects')` | `toContainText('Happy Place')` |
| 25 | `frontend/e2e/integration.spec.ts` | 69 | `toContainText('Agent Projects')` | `toContainText('Happy Place')` |

## Validation Rules

- The replacement string MUST be exactly `"Happy Place"` (title case, single space)
- No partial replacements (e.g., replacing only "Agent" or only "Projects")
- After replacement, a codebase-wide search for "Agent Projects" must return zero results (excluding the `specs/` directory which documents the change)

## State Transitions

N/A — no state machines, workflows, or entity lifecycle changes.

## Relationships

N/A — no entity relationships affected.
