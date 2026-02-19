# Implementation Plan: Update App Title to "Goodbye"

**Branch**: `005-goodbye-app-title` | **Date**: 2026-02-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-goodbye-app-title/spec.md`

## Summary

Replace the application display title from "Agent Projects" to "Goodbye" across all user-facing surfaces — the HTML `<title>` tag, two `<h1>` heading elements in `App.tsx`, and all E2E test assertions that reference the current title. No functional logic, routing, or API behavior depends on the title string; this is a display-only change. No manifest files, i18n resources, or meta tags beyond the `<title>` tag exist in the project.

## Technical Context

**Language/Version**: TypeScript ~5.4 (frontend), Python 3.12 (backend — no changes needed)
**Primary Dependencies**: React 18.3, Vite (build), Playwright (E2E tests), Vitest (unit tests)
**Storage**: N/A — no data persistence involved
**Testing**: Vitest (unit), Playwright (E2E) — E2E tests assert the title/heading text
**Target Platform**: Web browser (Vite dev server / production build)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: N/A — text-only change
**Constraints**: None — no functional behavior depends on the title string
**Scale/Scope**: 3 source files + 3 E2E test files affected

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | spec.md complete with 2 prioritized user stories, acceptance scenarios, edge cases |
| II. Template-Driven | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated | ✅ PASS | specify → plan → tasks → implement phase sequence followed |
| IV. Test Optionality | ✅ PASS | Tests not mandated in spec; existing E2E test assertions must be updated to avoid regressions but no new test files required |
| V. Simplicity/DRY | ✅ PASS | Direct string replacement in 3 source files + 3 test files. No abstraction introduced. Title is currently hardcoded in multiple locations (login page h1, app header h1, HTML title tag) — each instance is updated directly as no centralized config exists, per spec scope. |

## Project Structure

### Documentation (this feature)

```text
specs/005-goodbye-app-title/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (empty — no API changes)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
frontend/
├── index.html                    # <title> tag — "Agent Projects" → "Goodbye"
├── src/
│   └── App.tsx                   # Two <h1> elements — "Agent Projects" → "Goodbye"
└── e2e/
    ├── auth.spec.ts              # Title/heading assertions — update to "Goodbye"
    ├── ui.spec.ts                # Heading assertions — update to "Goodbye"
    └── integration.spec.ts       # Heading assertion — update to "Goodbye"
```

**Structure Decision**: Existing web application layout (frontend/ + backend/). Only frontend files are modified. Backend requires zero changes — the title is purely a frontend display concern.

## Files Requiring Changes

| File | Change | Requirement |
|------|--------|-------------|
| `frontend/index.html` (line 7) | `<title>Agent Projects</title>` → `<title>Goodbye</title>` | FR-001 |
| `frontend/src/App.tsx` (line 72) | `<h1>Agent Projects</h1>` → `<h1>Goodbye</h1>` (login page) | FR-002 |
| `frontend/src/App.tsx` (line 89) | `<h1>Agent Projects</h1>` → `<h1>Goodbye</h1>` (app header) | FR-003 |
| `frontend/e2e/auth.spec.ts` | Update all `'Agent Projects'` assertions to `'Goodbye'` | FR-004 |
| `frontend/e2e/ui.spec.ts` | Update all `'Agent Projects'` assertions to `'Goodbye'` | FR-004 |
| `frontend/e2e/integration.spec.ts` | Update `'Agent Projects'` assertion to `'Goodbye'` | FR-004 |

### Files NOT Requiring Changes

| File | Reason |
|------|--------|
| `frontend/src/types/index.ts` | Comment only — "TypeScript types for Agent Projects API" — not user-facing |
| `frontend/src/services/api.ts` | Comment only — "API client service for Agent Projects" — not user-facing |
| Any manifest.json / site.webmanifest | None exists in the project |
| Any i18n / localization files | No i18n framework is configured |
| Backend files | Title is not referenced in backend code |

## Complexity Tracking

> No Constitution Check violations — this section is intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
