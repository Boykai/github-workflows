# Research: Update Page Title to "Objects"

**Feature**: 005-update-page-title | **Date**: 2026-02-19  
**Purpose**: Resolve technical unknowns and document implementation approach

## Research Summary

This feature requires no significant research as it is a straightforward string replacement task. All technical context is already known from existing codebase exploration. The current application title "Agent Projects" appears in 28+ locations across the codebase. This document exists to satisfy the Phase 0 requirement from the plan template, but contains minimal content due to the feature's simplicity.

## Decision Areas

### 1. Title Replacement Strategy

**Decision**: Direct string replacement in all source files where "Agent Projects" appears as a user-facing title or configuration value

**Rationale**: 
- Application uses hardcoded title strings across ~10 files
- No existing centralized configuration or constant for the app title
- Feature scope is limited to this single update
- Adding configuration infrastructure would violate YAGNI principle

**Alternatives Considered**:
- **Centralized constant in config file**: Rejected — overkill for single-use string. Would require import statements, additional files, and refactoring across frontend/backend.
- **Environment variable**: Rejected — title is not environment-dependent. Would require .env changes, build-time substitution, and documentation updates.
- **i18n/localization system**: Rejected — no existing i18n infrastructure found; adding one would violate YAGNI.

**Implementation**: Replace `"Agent Projects"` with `"Objects"` in all relevant locations:
1. `frontend/index.html` line 7 (`<title>` tag)
2. `frontend/src/App.tsx` lines 72, 89 (`<h1>` headings)
3. `backend/src/main.py` lines 75, 77, 85, 86 (FastAPI config and log messages)
4. `frontend/e2e/auth.spec.ts` — title assertions
5. `frontend/e2e/ui.spec.ts` — title assertions
6. `frontend/e2e/integration.spec.ts` — title assertions
7. `.devcontainer/devcontainer.json` line 2 (container name)
8. `.devcontainer/post-create.sh` line 7 (setup echo)
9. `.env.example` line 2 (comment header)
10. `README.md` line 1 (project heading)
11. `backend/README.md` line 1 (backend heading)
12. `backend/pyproject.toml` line 4 (project description)
13. `frontend/src/services/api.ts` line 2 (JSDoc comment)
14. `frontend/src/types/index.ts` line 2 (JSDoc comment)
15. `backend/tests/test_api_e2e.py` line 2 (module docstring)

---

### 2. Scope of Changes

**Decision**: Update all occurrences of "Agent Projects" to "Objects" across the entire codebase, including user-facing UI, backend API metadata, tests, configuration, and documentation.

**Rationale**:
- Spec FR-001 through FR-007 mandate consistency across all surfaces
- The spec assumption states: "The current application title is 'Agent Projects' based on the existing codebase"
- Leaving any reference to the old title creates inconsistency (violates User Story 2)

**Alternatives Considered**:
- **Frontend-only changes**: Rejected — spec FR-007 requires backend configuration updates; FR-006 requires test assertion updates; spec edge cases require all metadata to be updated.
- **UI-only changes (skip docs/config)**: Rejected — spec User Story 2 requires "every location where the page/app title previously appeared" to be updated.

**Implementation**: Comprehensive find-and-replace with context-aware modifications (e.g., "Agent Projects API" → "Objects API", "Agent Projects — Backend" → "Objects — Backend").

---

### 3. Testing Strategy

**Decision**: Update existing E2E test assertions; no new tests needed

**Rationale**:
- Feature is visual change with no programmatic logic
- Constitution Principle IV (Test Optionality): Tests are optional by default
- Spec FR-006 mandates: "All automated tests that assert on the page title MUST be updated to expect 'Objects'"
- Existing E2E tests (`auth.spec.ts`, `ui.spec.ts`, `integration.spec.ts`) hardcode "Agent Projects" in assertions

**Alternatives Considered**:
- **New unit tests**: Rejected — no business logic to test. React Testing Library tests would only verify string literals.
- **Automated visual regression**: Rejected — overkill for single text change.
- **Skip test updates**: Rejected — spec FR-006 explicitly requires test assertions to be updated.

**Implementation**: 
1. Update all E2E test assertions from "Agent Projects" to "Objects"
2. Run existing test suite to verify no regressions

---

### 4. Package Name and Internal Identifiers

**Decision**: Update `frontend/package.json` name from `"agent-projects-frontend"` to `"objects-frontend"` for consistency

**Rationale**:
- The npm package name directly references the old app title
- While not user-facing, it appears in build outputs, logs, and developer tooling
- Spec requirement for consistency extends to "configuration files"

**Alternatives Considered**:
- **Keep old package name**: Considered — package name is an internal identifier. However, it would create confusion for developers seeing "agent-projects" in their tooling while the app is called "Objects".

**Implementation**: Update `name` field in `frontend/package.json`

---

### 5. Accessibility Impact

**Decision**: No accessibility changes required

**Rationale**:
- HTML `<title>` is already screen-reader accessible (WCAG 2.4.2)
- React headers are semantic `<h1>` elements (screen reader compatible)
- Text change from "Agent Projects" to "Objects" maintains same semantic meaning (application identifier)
- No ARIA attributes, roles, or labels require updates

**Implementation**: Direct string replacement preserves existing accessibility properties

---

### 6. Rollback Strategy

**Decision**: Standard git revert

**Rationale**:
- Changes are simple string replacements
- No database migrations, API contract changes, or state management involved
- Git commit revert immediately restores previous title
- No deployment coordination required

**Implementation**: Single atomic commit with clear message enables instant rollback if needed

---

## Implementation Risks

**Risk Level**: MINIMAL

- **Technical Risk**: None — simple string replacements in well-understood files
- **User Impact**: Positive — improves branding clarity
- **Testing Risk**: Low — existing test assertions are updated; manual verification sufficient
- **Rollback Risk**: None — instant git revert available

## Best Practices Applied

1. **YAGNI (You Aren't Gonna Need It)**: No configuration infrastructure for single string
2. **KISS (Keep It Simple)**: Direct replacement over abstraction
3. **DRY (Don't Repeat Yourself)**: Acceptable — multiple instances across files is not harmful duplication given context
4. **Semantic HTML**: Preserved existing accessible structure
5. **Atomic Commits**: Single commit for related changes

## Phase 0 Completion Checklist

- [x] All NEEDS CLARIFICATION items from Technical Context resolved
- [x] Technology choices documented with rationale
- [x] Alternatives evaluated for key decisions
- [x] Implementation approach clear and justified
- [x] Risks identified and assessed
- [x] No hidden dependencies discovered

**Status**: ✅ **PHASE 0 COMPLETE** - Ready for Phase 1 design artifacts
