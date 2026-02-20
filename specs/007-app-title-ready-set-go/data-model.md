# Data Model: Update App Title to "Ready Set Go"

**Feature**: 007-app-title-ready-set-go | **Date**: 2026-02-20

---

## Overview

This feature involves no data model changes. It is a pure text-replacement operation — changing the display title from "Agent Projects" to "Ready Set Go" across all files. No entities are created, modified, or removed. No database migrations, API contract changes, or type definition changes are needed.

## File Change Inventory

The following table provides the complete inventory of files and occurrences to be modified. Each row represents a single file with the exact lines, old text, and new text.

### Frontend Files

| File | Line | Old Value | New Value | Type |
|------|------|-----------|-----------|------|
| `frontend/index.html` | 7 | `<title>Agent Projects</title>` | `<title>Ready Set Go</title>` | HTML title tag |
| `frontend/src/App.tsx` | 72 | `<h1>Agent Projects</h1>` | `<h1>Ready Set Go</h1>` | React heading (unauthenticated) |
| `frontend/src/App.tsx` | 89 | `<h1>Agent Projects</h1>` | `<h1>Ready Set Go</h1>` | React heading (authenticated) |
| `frontend/src/services/api.ts` | 2 | `API client service for Agent Projects.` | `API client service for Ready Set Go.` | Docstring comment |
| `frontend/src/types/index.ts` | 2 | `TypeScript types for Agent Projects API.` | `TypeScript types for Ready Set Go API.` | Docstring comment |

### Frontend E2E Test Files

| File | Line | Old Value | New Value | Type |
|------|------|-----------|-----------|------|
| `frontend/e2e/auth.spec.ts` | 12 | `'Agent Projects'` | `'Ready Set Go'` | `toContainText` assertion |
| `frontend/e2e/auth.spec.ts` | 24 | `'Agent Projects'` | `'Ready Set Go'` | `toContainText` assertion |
| `frontend/e2e/auth.spec.ts` | 38 | `'Agent Projects'` | `'Ready Set Go'` | `toContainText` assertion |
| `frontend/e2e/auth.spec.ts` | 62 | `/Agent Projects/i` | `/Ready Set Go/i` | `toHaveTitle` regex assertion |
| `frontend/e2e/auth.spec.ts` | 99 | `'Agent Projects'` | `'Ready Set Go'` | `toContainText` assertion |
| `frontend/e2e/ui.spec.ts` | 43 | `'Agent Projects'` | `'Ready Set Go'` | `toContainText` assertion |
| `frontend/e2e/ui.spec.ts` | 67 | `'Agent Projects'` | `'Ready Set Go'` | `toContainText` assertion |
| `frontend/e2e/integration.spec.ts` | 69 | `'Agent Projects'` | `'Ready Set Go'` | `toContainText` assertion |

### Backend Files

| File | Line | Old Value | New Value | Type |
|------|------|-----------|-----------|------|
| `backend/src/main.py` | 75 | `"Starting Agent Projects API"` | `"Starting Ready Set Go API"` | Logger info message |
| `backend/src/main.py` | 77 | `"Shutting down Agent Projects API"` | `"Shutting down Ready Set Go API"` | Logger info message |
| `backend/src/main.py` | 85 | `title="Agent Projects API"` | `title="Ready Set Go API"` | FastAPI app title |
| `backend/src/main.py` | 86 | `description="REST API for Agent Projects"` | `description="REST API for Ready Set Go"` | FastAPI app description |
| `backend/pyproject.toml` | 4 | `description = "FastAPI backend for Agent Projects"` | `description = "FastAPI backend for Ready Set Go"` | Project metadata |
| `backend/tests/test_api_e2e.py` | 2 | `Agent Projects Backend` | `Ready Set Go Backend` | Module docstring |
| `backend/README.md` | 1 | `# Agent Projects — Backend` | `# Ready Set Go — Backend` | Documentation heading |
| `backend/README.md` | 3 | `...powers Agent Projects and...` | `...powers Ready Set Go and...` | Documentation paragraph |

### Configuration & Documentation Files

| File | Line | Old Value | New Value | Type |
|------|------|-----------|-----------|------|
| `.devcontainer/devcontainer.json` | 2 | `"name": "Agent Projects"` | `"name": "Ready Set Go"` | Container name |
| `.devcontainer/post-create.sh` | 7 | `Setting up Agent Projects development` | `Setting up Ready Set Go development` | Echo message |
| `.env.example` | 2 | `# Agent Projects - Environment Configuration` | `# Ready Set Go - Environment Configuration` | Header comment |
| `README.md` | 1 | `# Agent Projects` | `# Ready Set Go` | Project heading |

## Totals

- **Files to modify**: 15
- **Total occurrences**: 25
- **New entities**: 0
- **Modified entities**: 0
- **Deleted entities**: 0
- **Database migrations**: 0

## Validation Rules

- **FR-008 compliance**: Every replacement MUST use exact casing "Ready Set Go" — no variations
- **Completeness check**: After all replacements, `grep -rn "Agent Projects"` (excluding `specs/` and `.git/`) MUST return zero results
