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

*Completed after Phase 1 design artifacts (research.md, data-model.md, contracts/, quickstart.md)*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts directly map to spec.md user stories and functional requirements |
| **II. Template-Driven Workflow** | ✅ PASS | research.md, data-model.md, contracts/file-changes.md, quickstart.md all follow canonical templates |
| **III. Agent-Orchestrated** | ✅ PASS | Phase 0 (research) and Phase 1 (design) completed successfully; clear handoff to implementation phase |
| **IV. Test Optionality** | ✅ PASS | No new tests required; existing E2E tests will verify changes naturally (may need expectation updates) |
| **V. Simplicity and DRY** | ✅ PASS | Simple 3-line string modification; no abstractions, no complexity added |

**Post-Design Result**: ✅ ALL GATES PASSED - Ready for Phase 2 (Tasks)

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

**Status**: No violations - No complexity tracking required

All constitution principles passed in both pre-design and post-design evaluations. This is a straightforward string modification feature with no architectural complexity, no new dependencies, and no violations of simplicity principles.

---

## Phase Completion Summary

### Phase 0: Outline & Research ✅

**Output**: `research.md`  
**Status**: Complete  
**Key Decisions**:
1. Dollar sign placement: Prefix position (before title text)
2. Styling approach: Plain text with CSS inheritance
3. Accessibility: Native screen reader support, no ARIA needed
4. Responsive design: No special handling required
5. Browser compatibility: Universal $ character support
6. Testing strategy: Existing E2E tests will validate
7. Font rendering: System font default rendering
8. Character encoding: Literal $ in UTF-8 source files
9. SEO impact: Neutral impact, optimal title length maintained
10. Change scope: 3 frontend locations only (HTML + 2 React headers)

### Phase 1: Design & Contracts ✅

**Output**: `data-model.md`, `contracts/file-changes.md`, `quickstart.md`  
**Status**: Complete  
**Key Artifacts**:
- **data-model.md**: Defined ApplicationTitle entity with 3 attributes (htmlTitle, loginHeaderTitle, authHeaderTitle)
- **contracts/file-changes.md**: Specified exact changes to 2 files (frontend/index.html, frontend/src/App.tsx)
- **quickstart.md**: Created 10-step implementation guide with 30-40 minute time estimate
- **Agent context**: Updated `.github/agents/copilot-instructions.md` with TypeScript/React/Vite stack information

**Constitution Re-evaluation**: All gates passed post-design

### Phase 2: Tasks

**Output**: `tasks.md` (NOT generated by this command)  
**Status**: Pending - Next step is to run `/speckit.tasks` command  
**Purpose**: Generate dependency-ordered task list for implementation

**Note**: This planning phase stops here. Implementation planning is complete. The `/speckit.tasks` command will decompose the design artifacts into executable tasks for the implementation phase.

---

## References

- **Feature Specification**: [spec.md](spec.md)
- **Constitution**: [.specify/memory/constitution.md](../../.specify/memory/constitution.md)
- **Plan Template**: [.specify/templates/artifacts/plan-template.md](../../.specify/templates/artifacts/plan-template.md)
- **Research Findings**: [research.md](research.md)
- **Data Model**: [data-model.md](data-model.md)
- **File Contracts**: [contracts/file-changes.md](contracts/file-changes.md)
- **Implementation Guide**: [quickstart.md](quickstart.md)

---

## Handoff to Implementation

### Ready for Next Phase: ✅ YES

This feature is ready for task generation and implementation:

1. **Specification complete**: All requirements, acceptance criteria, and edge cases documented
2. **Research complete**: All technology decisions made and documented
3. **Design complete**: Data model, contracts, and implementation guide created
4. **Constitution compliance**: All principles satisfied with no violations
5. **Agent context updated**: Copilot context file synchronized with current stack

### Next Command

```bash
# Generate tasks.md with dependency-ordered implementation tasks
/speckit.tasks
```

### Implementation Notes

- **Estimated Implementation Time**: 30-40 minutes (per quickstart.md)
- **Risk Level**: Low (simple string replacements)
- **Breaking Changes**: None
- **Testing Updates**: May need to update E2E test expectations
- **Deployment Impact**: Zero (client-side only, no backend/database changes)

---

**Plan Status**: ✅ COMPLETE  
**Generated**: 2026-02-16  
**Feature Branch**: `copilot/add-dollar-sign-to-header`  
**Spec Reference**: `specs/003-dollar-app-title/spec.md`
