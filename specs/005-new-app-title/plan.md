# Implementation Plan: Update App Title to "New App"

**Branch**: `005-new-app-title` | **Date**: 2026-02-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-new-app-title/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Update the application title from "Agent Projects" to "New App" across all user-facing locations: HTML page title (browser tab), application headers (login and authenticated views), backend API metadata and log messages, configuration files, E2E test assertions, and documentation. This is a straightforward search-and-replace task requiring no architectural changes, new dependencies, or data model updates.

## Technical Context

**Language/Version**: TypeScript 5.4, Python 3.12, HTML5  
**Primary Dependencies**: React 18.3, Vite 5.4, FastAPI  
**Storage**: N/A (static content changes only)  
**Testing**: Vitest (unit), Playwright (E2E), pytest (backend)  
**Target Platform**: Modern web browsers (Chrome, Firefox, Safari, Edge)  
**Project Type**: Web (frontend React SPA + backend Python API)  
**Performance Goals**: N/A (no performance impact from string changes)  
**Constraints**: Must maintain existing browser title and header functionality  
**Scale/Scope**: ~15 file changes across frontend, backend, config, tests, and documentation; no database, API endpoint, or state management changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Evaluation (Before Phase 0)

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Specification-First** | ✅ PASS | Complete spec.md with 3 prioritized user stories (P1: Browser tab, P2: App header, P3: Consistency), Given-When-Then scenarios, and clear scope boundaries |
| **II. Template-Driven** | ✅ PASS | Following plan-template.md structure. All sections populated per template requirements. No custom sections added. |
| **III. Agent-Orchestrated** | ✅ PASS | Single speckit.plan agent execution. Clear input (spec.md) and outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md). Handoff to speckit.tasks next. |
| **IV. Test Optionality** | ✅ PASS | No new tests required. Existing E2E tests need title assertion updates to match new title. No TDD approach needed for string replacements. |
| **V. Simplicity & DRY** | ✅ PASS | Minimal complexity: direct string replacements across known files. No abstractions, no new patterns. Matches YAGNI principle. |

**Pre-Design Gate Status**: ✅ **PASSED** - All principles satisfied. No violations requiring justification.

### Post-Design Evaluation (After Phase 1)

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Specification-First** | ✅ PASS | Design artifacts (research.md, data-model.md, contracts/) align with spec requirements. No scope expansion. |
| **II. Template-Driven** | ✅ PASS | All Phase 0-1 artifacts follow prescribed templates. No deviations introduced. |
| **III. Agent-Orchestrated** | ✅ PASS | Phase 0-1 completed by single agent. Clean handoff state achieved. Ready for speckit.tasks. |
| **IV. Test Optionality** | ✅ PASS | Design confirms existing E2E test assertions must be updated to match new title. No new test infrastructure needed. |
| **V. Simplicity & DRY** | ✅ PASS | Final design maintains simplicity: literal string replacements only. No complexity introduced. |

**Post-Design Gate Status**: ✅ **PASSED** - Design maintains constitutional compliance. No complexity tracking required.

## Project Structure

### Documentation (this feature)

```text
specs/005-new-app-title/
├── spec.md              # Feature specification (completed)
├── checklists/
│   └── requirements.md  # Spec validation checklist (completed)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (generated below)
├── data-model.md        # Phase 1 output (generated below)
├── quickstart.md        # Phase 1 output (generated below)
├── contracts/           # Phase 1 output (generated below)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── index.html           # HTML page title (browser tab display)
├── src/
│   ├── App.tsx          # Application headers (login + authenticated)
│   ├── types/index.ts   # Type definition file header comment
│   └── services/api.ts  # API client file header comment
├── e2e/
│   ├── auth.spec.ts     # Title/heading assertions (5 locations)
│   ├── ui.spec.ts       # Heading assertions (2 locations)
│   └── integration.spec.ts  # Heading assertion (1 location)
└── package.json         # No changes required (internal package name)

backend/
├── src/
│   └── main.py          # FastAPI title, description, log messages
├── pyproject.toml       # Package description
├── README.md            # Backend documentation header
└── tests/
    └── test_api_e2e.py  # Test file header comment

.devcontainer/
├── devcontainer.json    # Dev container name
└── post-create.sh       # Setup script message

README.md                # Root documentation header
```

**Structure Decision**: Web application with React frontend + Python backend. Changes span both frontend presentation layer and backend metadata/configuration. All changes are string literal replacements with no structural modifications.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations detected. This section intentionally left minimal per constitution principle V (Simplicity).
