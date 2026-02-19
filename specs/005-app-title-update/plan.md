# Implementation Plan: App Title Update to "Hello World"

**Branch**: `005-app-title-update` | **Date**: 2026-02-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-app-title-update/spec.md`

## Summary

Update all occurrences of the application title from "Agent Projects" to "Hello World" across the frontend HTML, React components, e2e test assertions, and backend API metadata. This is a text-only change with no structural, data model, or API contract modifications.

## Technical Context

**Language/Version**: TypeScript ~5.4.0 (frontend), Python 3.11+ (backend)
**Primary Dependencies**: React 18.3, Vite 5.4, FastAPI 0.109+
**Storage**: N/A (no data model changes)
**Testing**: Playwright (e2e), Vitest (unit — frontend), pytest (backend)
**Target Platform**: Web — modern browsers (Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: N/A (text-only change, no performance implications)
**Constraints**: N/A
**Scale/Scope**: Minimal — affects only static title strings across a known set of files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | `spec.md` exists with prioritized user stories (P1–P3), acceptance scenarios, and edge cases |
| II. Template-Driven Workflow | ✅ PASS | Following plan-template.md structure; all artifacts placed in canonical `specs/005-app-title-update/` directory |
| III. Agent-Orchestrated Execution | ✅ PASS | Executing via speckit.plan workflow with clear phase outputs |
| IV. Test Optionality with Clarity | ✅ PASS | Tests required — FR-006 in spec mandates updating e2e test assertions. Existing Playwright tests reference "Agent Projects" and must be updated |
| V. Simplicity and DRY | ✅ PASS | Minimal text replacement across known files; no abstraction or refactoring needed |

**Gate Result**: ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/005-app-title-update/
├── spec.md              # Feature specification (exists)
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (minimal — no schema changes)
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (no API contract changes)
│   └── README.md        # Explanation of why no contracts needed
└── checklists/
    └── requirements.md  # Specification quality checklist (exists)
```

### Source Code (repository root)

```text
frontend/
├── index.html                    # <title> tag — "Agent Projects" → "Hello World"
├── src/
│   └── App.tsx                   # Two <h1> elements — "Agent Projects" → "Hello World"
└── e2e/
    ├── auth.spec.ts              # 5 test assertions referencing "Agent Projects"
    ├── ui.spec.ts                # 2 test assertions referencing "Agent Projects"
    └── integration.spec.ts       # 1 test assertion referencing "Agent Projects"

backend/
└── src/
    └── main.py                   # FastAPI title/description metadata (non-user-facing, optional)
```

**Structure Decision**: Existing web application structure (frontend + backend). No new files or directories needed. Changes are limited to string replacements in existing files.

## Files Requiring Changes

### User-Facing (Required — per FR-001 through FR-006)

| File | Location | Current Value | New Value | Requirement |
|------|----------|---------------|-----------|-------------|
| `frontend/index.html` | `<title>` tag (line 7) | `Agent Projects` | `Hello World` | FR-001 |
| `frontend/src/App.tsx` | Login `<h1>` (line 72) | `Agent Projects` | `Hello World` | FR-002, FR-004 |
| `frontend/src/App.tsx` | Header `<h1>` (line 89) | `Agent Projects` | `Hello World` | FR-002, FR-004 |
| `frontend/e2e/auth.spec.ts` | Lines 12, 24, 38, 62, 99 | `Agent Projects` | `Hello World` | FR-006 |
| `frontend/e2e/ui.spec.ts` | Lines 43, 67 | `Agent Projects` | `Hello World` | FR-006 |
| `frontend/e2e/integration.spec.ts` | Line 69 | `Agent Projects` | `Hello World` | FR-006 |

### Non-User-Facing (Optional — per spec Assumptions)

| File | Location | Current Value | Decision |
|------|----------|---------------|----------|
| `backend/src/main.py` | FastAPI `title` (line 85) | `Agent Projects API` | Update for consistency |
| `backend/src/main.py` | FastAPI `description` (line 86) | `REST API for Agent Projects` | Update for consistency |
| `backend/src/main.py` | Logger messages (lines 75, 77) | `Agent Projects API` | Update for consistency |
| `README.md` | Heading (line 1) | `# Agent Projects` | Optional — project-level doc |
| `backend/README.md` | Heading/description | `Agent Projects` | Optional — project-level doc |
| `.devcontainer/devcontainer.json` | `name` field | `Agent Projects` | Optional — dev env config |
| `.env.example` | Comment (line 2) | `Agent Projects` | Optional — comment only |
| `backend/pyproject.toml` | `description` (line 4) | `FastAPI backend for Agent Projects` | Optional — build metadata |
| `frontend/src/services/api.ts` | JSDoc comment (line 2) | `Agent Projects` | Optional — code comment |
| `frontend/src/types/index.ts` | JSDoc comment (line 2) | `Agent Projects` | Optional — code comment |

## Complexity Tracking

> No violations to justify. All Constitution Check gates pass.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *None* | — | — |

## Post-Design Constitution Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | Design aligns with spec requirements FR-001 through FR-006 |
| II. Template-Driven | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated | ✅ PASS | Clean handoff to speckit.tasks phase |
| IV. Test Optionality | ✅ PASS | E2e test updates included per spec mandate |
| V. Simplicity and DRY | ✅ PASS | Direct string replacement — no abstraction, no new code |

**Post-Design Gate Result**: ALL PASS — ready for Phase 2 (speckit.tasks).
