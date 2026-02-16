# Implementation Plan: Black Background Theme

**Branch**: `003-black-background-theme` | **Date**: 2026-02-16 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/003-black-background-theme/spec.md`

## Summary

Implement a solid black (#000000) background theme across the entire application interface to reduce eye strain in low-light environments. The feature will update CSS custom properties to replace the current dark gray background (#0d1117) with true black while maintaining WCAG AA accessibility standards for text contrast. The implementation uses pure CSS changes with minimal TypeScript modifications to set black as the default theme, requiring no new dependencies or infrastructure changes.

## Technical Context

**Language/Version**: TypeScript 5.4, CSS3 (CSS Custom Properties)  
**Primary Dependencies**: React 18.3.1, Vite 5.4 (build tool), existing CSS framework  
**Storage**: N/A (no persistence - theme resets on reload per spec out-of-scope)  
**Testing**: Vitest (unit tests), Playwright (E2E tests), manual visual verification, browser DevTools contrast checker  
**Target Platform**: Modern web browsers (Chrome, Firefox, Safari, Edge) - 95%+ browser support for CSS custom properties  
**Project Type**: Web application (frontend + backend separation)  
**Performance Goals**: Instant theme application (<16ms paint time), no FOUC (flash of unstyled content), CSS-only approach for zero runtime overhead  
**Constraints**: WCAG 2.1 Level AA contrast requirements (4.5:1 for normal text, 3:1 for large text), maintain existing functionality, preserve light theme as toggle option  
**Scale/Scope**: Small feature scope - 3 file modifications (index.css, App.css, useAppTheme.tsx), ~50 lines of CSS changes, affects all UI components via CSS cascade

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Check (Before Phase 0)

| Principle | Compliant? | Evidence |
|-----------|------------|----------|
| **I. Specification-First Development** | ✅ YES | Complete spec.md exists with 3 prioritized user stories (P1: core screens, P2: readability, P3: navigation/modals), Given-When-Then acceptance scenarios, clear out-of-scope items |
| **II. Template-Driven Workflow** | ✅ YES | Using canonical spec template, plan template being filled per workflow, all mandatory sections present |
| **III. Agent-Orchestrated Execution** | ✅ YES | Plan phase generating research.md, data-model.md, contracts/, quickstart.md as specified; clear handoff to tasks phase next |
| **IV. Test Optionality with Clarity** | ✅ YES | Spec does not mandate automated tests; manual visual testing + contrast checking sufficient for CSS-only changes; existing E2E tests will verify no regressions |
| **V. Simplicity and DRY** | ✅ YES | Reusing existing CSS custom property system; no new abstractions; modifying 3 existing variables rather than creating new theming system |

**Status**: ✅ **PASS** - All principles satisfied, proceeding to Phase 0 research

---

### Post-Design Check (After Phase 1)

| Principle | Compliant? | Evidence |
|-----------|------------|----------|
| **I. Specification-First Development** | ✅ YES | All user stories remain independently testable; design artifacts (research, data-model, contracts, quickstart) derive directly from spec requirements |
| **II. Template-Driven Workflow** | ✅ YES | Generated research.md (10 decisions), data-model.md (6 entities), contracts/css-changes.md (7 contracts), quickstart.md (11 steps) per template patterns |
| **III. Agent-Orchestrated Execution** | ✅ YES | Plan phase complete with all required artifacts; ready for /speckit.tasks handoff to generate task breakdown |
| **IV. Test Optionality with Clarity** | ✅ YES | Testing approach defined: manual visual verification + browser DevTools contrast checking + existing E2E regression tests; no new test infrastructure needed |
| **V. Simplicity and DRY** | ✅ YES | Design maintains simplicity: 3 CSS variable updates, 3 component-specific overrides, 1 TypeScript default value change; no architectural changes; reuses all existing patterns |

**Status**: ✅ **PASS** - Design phase maintains constitution compliance, ready for tasks phase

---

### Complexity Justification

**No violations to justify** - feature achieves goals through straightforward CSS variable modifications within existing theming system. All complexity deferred or avoided:

- ❌ No new theme system (reuse existing)
- ❌ No theme persistence (out of scope)
- ❌ No new React components (pure CSS)
- ❌ No API changes (frontend-only)
- ❌ No new dependencies (use built-in CSS)

## Project Structure

### Documentation (this feature)

```text
specs/003-black-background-theme/
├── spec.md              # Feature specification (completed by speckit.specify)
├── checklists/
│   └── requirements.md  # Specification validation (completed by speckit.specify)
├── plan.md              # This file (completed by speckit.plan)
├── research.md          # Phase 0 output - 10 technical decisions (completed)
├── data-model.md        # Phase 1 output - 6 entities (completed)
├── quickstart.md        # Phase 1 output - 11-step implementation guide (completed)
├── contracts/
│   └── css-changes.md   # Phase 1 output - 7 CSS contracts (completed)
└── tasks.md             # Phase 2 output (will be created by /speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/       # No changes (backend unaffected)
│   ├── services/     # No changes
│   └── api/          # No changes
└── tests/            # No changes

frontend/
├── src/
│   ├── index.css          # MODIFIED: Update CSS custom properties for black theme
│   ├── App.css            # MODIFIED: Add dark mode overrides for error components
│   ├── hooks/
│   │   └── useAppTheme.tsx  # MODIFIED: Change default isDarkMode to true
│   ├── components/        # No direct changes (inherit CSS variables)
│   └── services/          # No changes
├── e2e/                   # Existing E2E tests verify no regressions
└── tests/                 # Existing unit tests verify no regressions
```

**Structure Decision**: Web application (Option 2) - Frontend/backend separation detected. This feature is **frontend-only** with no backend modifications required. All changes localized to CSS styling and one theme hook default value. The existing CSS custom property cascade automatically applies theme to all components without requiring component-level changes.

## Complexity Tracking

> **No complexity violations to track** - this feature maintains strict simplicity

This section intentionally left empty. The black background theme implementation requires no architectural complexity, abstraction layers, or pattern violations. All changes achieved through:

1. **Direct CSS variable updates** (3 values in existing system)
2. **Component-specific overrides** (3 blocks for error/animation components)
3. **Single boolean default change** (1 line in existing hook)

No justification needed for:
- ❌ Additional projects/modules
- ❌ Repository patterns or abstraction layers
- ❌ Complex state management
- ❌ New dependencies or libraries
- ❌ Database schema changes
- ❌ API versioning or breaking changes

**Simplicity Score**: ✅ **Excellent** - Feature achieves requirements with minimal, surgical changes to existing codebase.
