# Research: App Title Update to "Hello World"

**Feature**: 005-app-title-update
**Date**: 2026-02-19
**Status**: Complete

## Research Tasks

### R1: Current Title Location Audit

**Task**: Identify all locations where the application title "Agent Projects" is currently defined.

**Decision**: The title appears in 3 categories of files: user-facing source (3 files), test assertions (3 files), and non-user-facing metadata/comments (8 files).

**Rationale**: A comprehensive grep for "Agent Projects" across the repository revealed all instances. User-facing locations are mandatory changes per the spec; non-user-facing locations are optional per the spec Assumptions section.

**Findings**:

| Category | File | Line(s) | Context |
|----------|------|---------|---------|
| User-facing source | `frontend/index.html` | 7 | `<title>Agent Projects</title>` |
| User-facing source | `frontend/src/App.tsx` | 72 | `<h1>Agent Projects</h1>` (login screen) |
| User-facing source | `frontend/src/App.tsx` | 89 | `<h1>Agent Projects</h1>` (app header) |
| Test assertion | `frontend/e2e/auth.spec.ts` | 12, 24, 38, 62, 99 | Playwright `toContainText` / `toHaveTitle` assertions |
| Test assertion | `frontend/e2e/ui.spec.ts` | 43, 67 | Playwright `toContainText` assertions |
| Test assertion | `frontend/e2e/integration.spec.ts` | 69 | Playwright `toContainText` assertion |
| Non-user-facing | `backend/src/main.py` | 75, 77, 85, 86 | FastAPI metadata and logger messages |
| Non-user-facing | `README.md` | 1 | Project heading |
| Non-user-facing | `backend/README.md` | 1, 3 | Backend project heading and description |
| Non-user-facing | `.devcontainer/devcontainer.json` | 2 | Dev container name |
| Non-user-facing | `.env.example` | 2 | Comment |
| Non-user-facing | `backend/pyproject.toml` | 4 | Package description |
| Non-user-facing | `frontend/src/services/api.ts` | 2 | JSDoc comment |
| Non-user-facing | `frontend/src/types/index.ts` | 2 | JSDoc comment |

**Alternatives considered**: None — this is a factual audit, not a design decision.

### R2: Best Practices for Title Consistency in React + Vite Applications

**Task**: Determine the standard approach for managing application titles in a React + Vite web application.

**Decision**: The current approach (static `<title>` in `index.html` plus `<h1>` elements in React components) is the standard pattern for React + Vite applications without dynamic page titles.

**Rationale**: The application does not use React Router or a head management library (e.g., react-helmet). The title is static across all views, so modifying the `<title>` tag directly in `index.html` and the `<h1>` elements in `App.tsx` is the simplest and most correct approach. No additional library or abstraction is needed.

**Alternatives considered**:
- **react-helmet / react-helmet-async**: Overkill for a single static title. Would add unnecessary dependency.
- **Vite configuration (vite.config.ts)**: Vite does not natively manage HTML `<title>` beyond the `index.html` template. No benefit over direct editing.
- **Environment variable**: Could use `VITE_APP_TITLE` for configurability, but spec does not require environment-specific titles. YAGNI applies.

### R3: E2E Test Update Strategy

**Task**: Determine the safest approach to updating Playwright e2e test assertions.

**Decision**: Direct string replacement of `'Agent Projects'` with `'Hello World'` in all Playwright test assertions. No structural test changes needed.

**Rationale**: All test assertions use simple string matching (`toContainText('Agent Projects')` or `toHaveTitle(/Agent Projects/i)`). The replacement is a 1:1 text swap with no logic changes. The tests will continue to validate the same behavior — only the expected string changes.

**Alternatives considered**:
- **Shared test constant**: Could extract title to a constant file used by tests. However, this adds indirection for a value that appears in only 8 assertions across 3 files. YAGNI and Simplicity principles apply.
- **Data-driven tests**: Unnecessary complexity for static string assertions.

### R4: Backend API Metadata Update Scope

**Task**: Determine whether backend FastAPI title/description metadata should be updated.

**Decision**: Update for consistency. The FastAPI `title` and `description` fields in `main.py` should be changed from "Agent Projects API" to "Hello World API" and the description updated accordingly.

**Rationale**: While these are not directly user-facing in the browser (they appear in the auto-generated OpenAPI docs at `/docs`), they represent the application's identity in API documentation. Updating them maintains consistency and is a trivial change with no risk.

**Alternatives considered**:
- **Skip backend changes**: Technically acceptable per spec (which focuses on user-facing text), but inconsistency between frontend branding and API docs would be confusing for developers.

## Summary

All NEEDS CLARIFICATION items resolved. The feature is a straightforward text replacement across a known, bounded set of files. No new dependencies, patterns, or infrastructure are needed.
