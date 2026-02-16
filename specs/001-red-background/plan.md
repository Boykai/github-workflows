# Implementation Plan: Red Background Interface

**Branch**: `copilot/apply-red-background-interface-again` | **Date**: 2026-02-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-red-background/spec.md`

## Summary

Apply a solid red (#FF0000) background to the main app container across all screens and responsive layouts. The implementation modifies CSS custom properties in the existing theming system to ensure the red background persists across navigation, page refreshes, and both light/dark theme modes while maintaining text contrast for accessibility.

## Technical Context

**Language/Version**: TypeScript 5.x (frontend), CSS3
**Primary Dependencies**: React 18.3, Vite (build tool), CSS custom properties
**Storage**: localStorage (theme mode persistence via useAppTheme hook)
**Testing**: Vitest (unit), Playwright (e2e)
**Target Platform**: Modern web browsers (Chrome, Firefox, Safari, Edge)
**Project Type**: Web application (frontend focus - CSS styling change)
**Performance Goals**: Background color applied within 100ms of page load, zero visual flicker
**Constraints**: Maintain WCAG AA contrast ratio (4.5:1) for text, preserve existing theme functionality
**Scale/Scope**: Single CSS variable change affecting all screens in the application

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Specification-First | ✅ PASS | Complete spec.md with 3 prioritized user stories (P1, P2, P3), Given-When-Then scenarios, clear scope boundaries |
| II. Template-Driven Workflow | ✅ PASS | Following canonical plan-template.md structure for all artifacts |
| III. Agent-Orchestrated Execution | ✅ PASS | Clear phase boundaries: specify → plan → tasks → implement |
| IV. Test Optionality | ✅ PASS | Tests not explicitly required for simple CSS change - visual verification sufficient |
| V. Simplicity and DRY | ✅ PASS | Minimal change: single CSS custom property modification, no new abstractions needed |

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
frontend/
├── src/
│   ├── index.css              # Global CSS with theme variables (MODIFIED)
│   ├── App.css                # App component styles
│   ├── App.tsx                # Main app component
│   ├── components/
│   │   └── chat/
│   │       └── ChatInterface.css
│   └── hooks/
│       └── useAppTheme.ts     # Theme mode persistence logic
└── tests/
    ├── unit/
    └── e2e/
```

**Structure Decision**: Web application structure (frontend-focused change). The feature only requires modifying CSS custom properties in `frontend/src/index.css` where the `--color-bg-secondary` variable controls the main page background color for both light and dark themes.

## Complexity Tracking

> No violations detected - Constitution Check passed for all principles.

---

## Post-Design Constitution Check

*Re-evaluation after Phase 1 design completion*

| Principle | Status | Post-Design Evidence |
|-----------|--------|---------------------|
| I. Specification-First | ✅ PASS | Design artifacts (research.md, data-model.md, contracts/, quickstart.md) directly implement spec requirements without scope creep |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates: research.md (10 questions), data-model.md (CSS variables), contracts/css-changes.md (change specification), quickstart.md (implementation guide) |
| III. Agent-Orchestrated Execution | ✅ PASS | Phase 0 (research) and Phase 1 (design) completed successfully. Ready for Phase 2 (tasks) hand-off via /speckit.tasks command |
| IV. Test Optionality | ✅ PASS | No automated tests added. Visual verification documented in quickstart.md sufficient for 2-line CSS change |
| V. Simplicity and DRY | ✅ PASS | Design confirmed minimal approach: 2 CSS custom property values changed in 1 file. Zero new abstractions, zero JavaScript changes, zero new dependencies |

### Design Validation

**Artifacts Generated**:
- ✅ research.md: 10 research questions resolved, all NEEDS CLARIFICATION items cleared
- ✅ data-model.md: CSS custom property definitions and state management documented
- ✅ contracts/css-changes.md: Exact 2-line CSS change specification with validation checklists
- ✅ quickstart.md: 15-20 minute implementation guide with troubleshooting
- ✅ Agent context updated: TypeScript, React, CSS custom properties added to copilot-instructions.md

**Constitution Compliance**:
- No complexity violations introduced during design
- No new abstractions or dependencies added
- Scope remains exactly as specified: CSS background color only
- Test optionality maintained: visual verification sufficient

**Ready for Phase 2**: All design artifacts complete. Implementation can proceed via /speckit.tasks command.

---

## Phase Summary

### Phase 0: Research (Completed)

**Duration**: Research phase  
**Deliverable**: `research.md` with 10 resolved questions  
**Outcome**: Confirmed approach - modify `--color-bg-secondary` in both theme modes

**Key Decisions**:
1. Target CSS variable: `--color-bg-secondary` in `:root` and `html.dark-mode-active`
2. Side effects acceptable: buttons/task previews inherit red background
3. Accessibility trade-off: light mode contrast documented as known issue
4. No JavaScript changes needed: existing theme system handles persistence

### Phase 1: Design (Completed)

**Duration**: Design phase  
**Deliverables**: 
- `data-model.md`: CSS variable definitions and theme state management
- `contracts/css-changes.md`: Exact 2-line change specification
- `quickstart.md`: 15-20 minute implementation guide
- Agent context updated

**Outcome**: Implementation contract defined - 2 lines in 1 file

**Key Artifacts**:
1. **Data Model**: Documents CSS custom property architecture and theme switching
2. **Contract**: Specifies exact before/after values, validation checklist, rollback plan
3. **Quickstart**: Step-by-step guide with troubleshooting and verification scenarios

### Next Phase: Tasks (Phase 2)

**Command**: `/speckit.tasks` (not executed by /speckit.plan)  
**Input**: This plan.md + all Phase 0/1 artifacts  
**Output**: `tasks.md` with executable implementation tasks  
**Executor**: Separate agent or human developer

---

## Notes

This plan was generated by the `/speckit.plan` command which executes Phase 0 (research) and Phase 1 (design) of the speckit workflow. The plan stops here as Phase 2 (tasks generation) is handled by a separate `/speckit.tasks` command per the constitution's agent-orchestrated execution principle.

All planning artifacts are now available in `specs/001-red-background/` for the implementation phase.
