# Implementation Plan: Update App Title to "New App"

**Branch**: `005-new-app-title` | **Date**: 2026-02-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-new-app-title/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Update application title from "Agent Projects" to "New App" across all user-facing locations: HTML page title (browser tab), authenticated application header, login page header, backend API metadata, configuration files, documentation, devcontainer settings, and E2E test assertions. This is a comprehensive string replacement task requiring no architectural changes, new dependencies, or data model updates.

## Technical Context

**Language/Version**: TypeScript 5.4, Python ≥3.11, HTML5  
**Primary Dependencies**: React 18.3, Vite 5.4, FastAPI ≥0.109  
**Storage**: N/A (static content changes only)  
**Testing**: Vitest (unit), Playwright (E2E), pytest (backend)  
**Target Platform**: Modern web browsers (Chrome, Firefox, Safari, Edge)  
**Project Type**: Web (frontend React SPA + backend Python API)  
**Performance Goals**: N/A (no performance impact from string changes)  
**Constraints**: Must maintain existing browser title and header functionality  
**Scale/Scope**: ~10 file changes across frontend, backend, config, and docs; no database, API logic, or state management changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Evaluation (Before Phase 0)

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Specification-First** | ✅ PASS | Complete spec.md with 3 prioritized user stories (P1: Browser tab, P2: App header, P3: Consistency), Given-When-Then scenarios, and clear scope boundaries |
| **II. Template-Driven** | ✅ PASS | Following plan-template.md structure. All sections populated per template requirements. No custom sections added. |
| **III. Agent-Orchestrated** | ✅ PASS | Single speckit.plan agent execution. Clear input (spec.md) and outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md). Handoff to speckit.tasks next. |
| **IV. Test Optionality** | ✅ PASS | No new tests required. Feature is simple string replacement. Existing E2E tests need title/heading assertion updates to match new title. |
| **V. Simplicity & DRY** | ✅ PASS | Minimal complexity: string replacements across ~10 files. No abstractions, no new patterns. Direct implementation matches YAGNI principle. |

**Pre-Design Gate Status**: ✅ **PASSED** - All principles satisfied. No violations requiring justification.

### Post-Design Evaluation (After Phase 1)

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Specification-First** | ✅ PASS | Design artifacts (research.md, data-model.md, contracts/) align with spec requirements. No scope expansion. |
| **II. Template-Driven** | ✅ PASS | All Phase 0-1 artifacts follow prescribed templates. No deviations introduced. |
| **III. Agent-Orchestrated** | ✅ PASS | Phase 0-1 completed by single agent. Clean handoff state achieved. Ready for speckit.tasks. |
| **IV. Test Optionality** | ✅ PASS | Design confirms E2E test assertion updates needed (existing tests hardcode "Agent Projects"). No new test infrastructure required. |
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
├── index.html           # HTML page title (Browser tab display)
├── src/
│   ├── App.tsx          # Application headers (login + authenticated)
│   └── [other files unchanged]
├── e2e/
│   ├── auth.spec.ts     # Title and heading assertions
│   ├── ui.spec.ts       # Heading assertions
│   └── integration.spec.ts  # Heading assertions
└── package.json         # Package name (internal identifier)

backend/
├── src/
│   └── main.py          # FastAPI title and description metadata
├── pyproject.toml       # Package name and description
└── README.md            # Backend documentation heading

.devcontainer/
├── devcontainer.json    # Container name
└── post-create.sh       # Setup echo message

README.md                # Root documentation heading
.env.example             # Environment configuration header comment
```

**Structure Decision**: Web application with React frontend and FastAPI backend. Changes span both frontend presentation layer and backend metadata/configuration. All changes are string replacements in existing files — no new files, no structural changes.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations detected. This section intentionally left minimal per constitution principle V (Simplicity).
