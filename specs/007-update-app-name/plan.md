# Implementation Plan: Update App Name to "Robot"

**Branch**: `007-update-app-name` | **Date**: 2026-02-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-update-app-name/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Rename the application display name from "Agent Projects" to "Robot" across all user-facing surfaces: browser tab title (HTML), application headers (React), backend API metadata and startup logs (FastAPI), developer environment name (devcontainer), configuration files (pyproject.toml, .env.example), documentation (README files), startup scripts, and E2E test assertions. This is a straightforward find-and-replace task requiring no architectural changes, new dependencies, or data model updates.

## Technical Context

**Language/Version**: TypeScript 5.x (frontend), Python 3.11+ (backend), HTML5  
**Primary Dependencies**: React 18, Vite 5, FastAPI 0.109+, Playwright (E2E)  
**Storage**: N/A (static content changes only)  
**Testing**: Playwright (frontend E2E), pytest (backend)  
**Target Platform**: Modern web browsers (Chrome, Firefox, Safari, Edge), Linux server (backend)  
**Project Type**: Web (frontend React SPA + backend Python FastAPI API)  
**Performance Goals**: N/A (no performance impact from string changes)  
**Constraints**: Must maintain existing functionality; all instances of "Agent Projects" replaced with "Robot"  
**Scale/Scope**: ~12 file changes across frontend, backend, config, docs, and tests; no database, API contract, or state management changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Evaluation (Before Phase 0)

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Specification-First** | ✅ PASS | Complete spec.md with 4 prioritized user stories (P1: Browser tab, P1: UI headers, P2: Backend/developer surfaces, P2: No old references), Given-When-Then acceptance scenarios, clear scope (display name only, no package/directory renames), and assumptions documented. |
| **II. Template-Driven** | ✅ PASS | Following plan-template.md structure. All sections populated per template requirements. No custom sections added. |
| **III. Agent-Orchestrated** | ✅ PASS | Single speckit.plan agent execution. Clear input (spec.md) and outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md). Handoff to speckit.tasks next. |
| **IV. Test Optionality** | ✅ PASS | No new tests required. Existing E2E test assertions that check for "Agent Projects" must be updated to "Robot" per FR-008. No TDD mandated. |
| **V. Simplicity & DRY** | ✅ PASS | Minimal complexity: string replacements across ~12 files. No abstractions, no new patterns. Direct implementation matches YAGNI principle. |

**Pre-Design Gate Status**: ✅ **PASSED** — All principles satisfied. No violations requiring justification.

### Post-Design Evaluation (After Phase 1)

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Specification-First** | ✅ PASS | Design artifacts (research.md, data-model.md, contracts/) align with spec requirements. No scope expansion. All 9 functional requirements addressed. |
| **II. Template-Driven** | ✅ PASS | All Phase 0–1 artifacts follow prescribed templates. No deviations introduced. |
| **III. Agent-Orchestrated** | ✅ PASS | Phase 0–1 completed by single agent. Clean handoff state achieved. Ready for speckit.tasks. |
| **IV. Test Optionality** | ✅ PASS | Design confirms no new test infrastructure needed. Existing E2E assertions updated as required by FR-008. |
| **V. Simplicity & DRY** | ✅ PASS | Final design maintains simplicity: literal string replacements only. No complexity introduced. |

**Post-Design Gate Status**: ✅ **PASSED** — Design maintains constitutional compliance. No complexity tracking required.

## Project Structure

### Documentation (this feature)

```text
specs/007-update-app-name/
├── spec.md              # Feature specification (completed)
├── checklists/
│   └── requirements.md  # Spec validation checklist (completed)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (generated below)
├── data-model.md        # Phase 1 output (generated below)
├── quickstart.md        # Phase 1 output (generated below)
├── contracts/           # Phase 1 output (generated below)
│   └── file-changes.md  # Exact file modification contract
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── index.html           # HTML page title (Browser tab display) — FR-001
├── src/
│   └── App.tsx          # Application headers (login + authenticated) — FR-002
└── e2e/
    ├── auth.spec.ts     # E2E test assertions on app name — FR-008
    ├── ui.spec.ts       # E2E test assertions on app name — FR-008
    └── integration.spec.ts  # E2E test assertions on app name — FR-008

backend/
├── src/
│   └── main.py          # FastAPI title, description, startup logs — FR-003, FR-004
├── pyproject.toml       # Project description — FR-005
└── README.md            # Backend documentation — FR-007

.devcontainer/
├── devcontainer.json    # Dev environment name — FR-006
└── post-create.sh       # Setup script log message — FR-006

.env.example             # Environment file header — FR-005
README.md                # Main project documentation — FR-007
```

**Structure Decision**: Web application with React frontend and FastAPI backend. Changes span both frontend and backend presentation/configuration layers but involve no logic, API contract, or state management changes. This is a cross-cutting display name update.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations detected. This section intentionally left minimal per constitution principle V (Simplicity).
