# Implementation Plan: Update App Title to "Hello World"

**Branch**: `005-hello-world-title` | **Date**: 2026-02-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-hello-world-title/spec.md`

## Summary

Replace the application title "Agent Projects" with "Hello World" across all user-facing display locations (HTML title, React headers), backend API metadata (FastAPI OpenAPI config, logs), E2E test assertions, and supporting configuration files (devcontainer, env example, JSDoc comments, README). This is a pure text replacement with no architectural or functional changes.

## Technical Context

**Language/Version**: TypeScript 5.4.0 (frontend), Python 3.11+ (backend)  
**Primary Dependencies**: React 18.3.1, Vite 5.4.0, FastAPI ≥0.109.0  
**Storage**: N/A (no data changes)  
**Testing**: Vitest (unit), Playwright 1.58.1 (E2E) — existing tests need assertion updates  
**Target Platform**: Web application (modern browsers: Chrome, Firefox, Safari, Edge)  
**Project Type**: Web (frontend + backend)  
**Performance Goals**: N/A (no performance impact — static text change)  
**Constraints**: N/A  
**Scale/Scope**: 24 string replacements across ~14 files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | `spec.md` created with prioritized user stories (P1-P3), acceptance scenarios, and scope boundaries |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase produces well-defined outputs for task generation |
| IV. Test Optionality with Clarity | ✅ PASS | No new tests required; existing E2E tests updated to match new expected behavior. Tests not explicitly requested in spec. |
| V. Simplicity and DRY | ✅ PASS | Direct string replacement is the simplest approach. No new abstractions, libraries, or configuration layers introduced. |

**Gate Result**: ✅ ALL PASS — No violations to justify.

### Post-Phase 1 Re-evaluation

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | Research and data model align with spec requirements |
| II. Template-Driven | ✅ PASS | All Phase 0/1 artifacts generated per template structure |
| III. Agent-Orchestrated | ✅ PASS | Clear handoff artifacts for task generation phase |
| IV. Test Optionality | ✅ PASS | Existing test updates documented; no new test infrastructure |
| V. Simplicity/DRY | ✅ PASS | No complexity introduced; all changes are direct replacements |

**Post-Design Gate Result**: ✅ ALL PASS

## Project Structure

### Documentation (this feature)

```text
specs/005-hello-world-title/
├── spec.md              # Feature specification (speckit.specify output)
├── plan.md              # This file (speckit.plan output)
├── research.md          # Phase 0 output (speckit.plan)
├── data-model.md        # Phase 1 output (speckit.plan)
├── quickstart.md        # Phase 1 output (speckit.plan)
├── contracts/           # Phase 1 output (speckit.plan)
│   └── README.md        # No API contracts needed for this feature
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Phase 2 output (speckit.tasks - NOT created by speckit.plan)
```

### Source Code (repository root)

```text
# Web application structure (frontend + backend)
backend/
├── src/
│   └── main.py          # FastAPI app title and log messages
├── pyproject.toml        # Package description
└── README.md             # Documentation heading

frontend/
├── index.html            # Browser tab <title> tag
├── src/
│   ├── App.tsx           # React <h1> headers (login + app)
│   ├── types/index.ts    # JSDoc comment
│   └── services/api.ts   # JSDoc comment
└── e2e/
    ├── auth.spec.ts      # E2E title assertions
    ├── ui.spec.ts         # E2E title assertions
    └── integration.spec.ts # E2E title assertion

# Configuration
.devcontainer/
└── devcontainer.json     # Container name
.env.example              # Header comment
```

**Structure Decision**: Existing web application structure (Option 2: frontend + backend). No new directories or files created in source code. All changes are in-place text replacements within existing files.

## Complexity Tracking

> No violations detected. No complexity justifications needed.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
