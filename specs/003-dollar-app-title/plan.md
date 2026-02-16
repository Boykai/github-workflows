# Implementation Plan: Add Dollar Sign to Application Title

**Branch**: `copilot/add-dollar-sign-to-header` | **Date**: 2026-02-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-dollar-app-title/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Add a dollar sign ($) prefix to the application title "Welcome to Tech Connect 2026!" in the header to make the app's financial focus clearer and more visually aligned with its purpose. This is a straightforward string modification requiring updates to 3 locations: HTML page title (browser tab), authenticated application header, and login page header. The dollar sign will maintain consistent styling with existing title text to ensure proper accessibility and responsive design across desktop and mobile layouts.

## Technical Context

**Language/Version**: TypeScript 5.4, HTML5  
**Primary Dependencies**: React 18.3, Vite 5.4, CSS3  
**Storage**: N/A (static content changes only)  
**Testing**: Vitest (unit), Playwright (E2E)  
**Target Platform**: Modern web browsers (Chrome, Firefox, Safari, Edge)  
**Project Type**: Web (frontend React SPA + backend Python API)  
**Performance Goals**: N/A (no performance impact from text changes)  
**Constraints**: Must maintain existing styling, accessibility (screen reader), and responsive layouts  
**Scale/Scope**: 3 file changes (index.html, App.tsx x2); no database, API, or state management changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Evaluation

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | Feature has complete spec.md with prioritized user stories (P1/P2), Given-When-Then scenarios, and clear scope boundaries |
| **II. Template-Driven Workflow** | ✅ PASS | Following canonical plan template structure; all artifacts will use templates |
| **III. Agent-Orchestrated** | ✅ PASS | This is a speckit.plan agent execution with well-defined inputs (spec.md) and outputs (plan.md, research.md, etc.) |
| **IV. Test Optionality** | ✅ PASS | Tests not explicitly required by spec; existing E2E tests will verify title changes naturally |
| **V. Simplicity and DRY** | ✅ PASS | Simple string modification; no new abstractions or complex logic required |

**Pre-Design Result**: ✅ ALL GATES PASSED - Proceed to Phase 0

### Post-Design Evaluation

*To be completed after Phase 1 design artifacts*

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Web application (frontend + backend)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── index.html           # Browser tab title (line 7)
├── src/
│   ├── App.tsx          # Main application headers (lines 69, 85)
│   ├── components/
│   └── services/
└── e2e/
    └── ui.spec.ts       # E2E tests for title verification
```

**Structure Decision**: This is a web application with a React frontend and Python backend. The feature only affects the frontend (HTML + React component). No backend changes required as titles are static frontend content.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
