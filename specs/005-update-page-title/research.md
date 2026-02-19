# Research: Update Page Title to "Objects"

**Feature**: 005-update-page-title | **Date**: 2026-02-19  
**Purpose**: Resolve technical unknowns and document implementation approach

## Research Summary

This feature requires no significant research as it is a straightforward string replacement task. All technical context is already known from existing codebase exploration. This document exists to satisfy the Phase 0 requirement from the plan template, but contains minimal content due to the feature's simplicity.

## Decision Areas

### 1. Title Replacement Strategy

**Decision**: Direct string replacement in source files (HTML, JSX, Python, TOML, Markdown, Shell, JSON)

**Rationale**:
- Application uses hardcoded "Agent Projects" string in ~22 locations across ~15 files
- No existing centralized configuration or constant for the title
- Feature scope is limited to this single update
- Adding configuration infrastructure would violate YAGNI principle

**Alternatives Considered**:
- **Centralized constant in config file**: Rejected — overkill for single-use string. Would require import statements and additional files across both frontend and backend. Adds complexity without benefit.
- **Environment variable**: Rejected — title is not environment-dependent. Would require .env changes, build-time substitution, and documentation updates.
- **i18n/localization system**: Rejected — application currently has no i18n infrastructure and the spec does not require it.

**Implementation**: Replace `"Agent Projects"` with `"Objects"` in all identified locations:

#### Frontend (user-facing)
1. `frontend/index.html` line 7 — `<title>` tag
2. `frontend/src/App.tsx` line 72 — login page `<h1>`
3. `frontend/src/App.tsx` line 89 — authenticated header `<h1>`

#### Backend (API metadata and logs)
4. `backend/src/main.py` line 75 — startup log message
5. `backend/src/main.py` line 77 — shutdown log message
6. `backend/src/main.py` line 85 — FastAPI app title
7. `backend/src/main.py` line 86 — FastAPI app description

#### E2E Tests (assertions)
8. `frontend/e2e/auth.spec.ts` — 5 occurrences (title and h1 assertions)
9. `frontend/e2e/ui.spec.ts` — 2 occurrences (h1 assertions)
10. `frontend/e2e/integration.spec.ts` — 1 occurrence (h1 assertion)

#### Comments and Documentation
11. `frontend/src/services/api.ts` — comment header
12. `frontend/src/types/index.ts` — comment header
13. `backend/tests/test_api_e2e.py` — docstring
14. `backend/pyproject.toml` — package description
15. `backend/README.md` — heading and description
16. `README.md` — repository heading
17. `.devcontainer/devcontainer.json` — container name
18. `.devcontainer/post-create.sh` — setup message
19. `.env.example` — comment header

---

### 2. Scope of Changes

**Decision**: Update ALL occurrences of "Agent Projects" across the entire codebase, including user-facing UI, backend metadata, test assertions, documentation, and configuration files.

**Rationale**:
- Spec FR-001 through FR-007 require consistency across all UI elements, navigation, backend config, tests, and API metadata
- Leaving partial references creates confusion for developers and potentially inconsistent behavior
- The 001-app-title-update feature previously scoped changes to frontend only; this feature takes a comprehensive approach per spec requirements

**Alternatives Considered**:
- **Frontend-only changes**: Rejected — spec explicitly requires backend configuration and test updates (FR-006, FR-007)
- **UI-only changes (skip comments/docs)**: Rejected — leaving "Agent Projects" in comments and docs creates confusion when the app is called "Objects"

---

### 3. Testing Strategy

**Decision**: Update existing E2E test assertions; no new tests required

**Rationale**:
- Feature is a visual/textual change with no programmatic logic
- Constitution Principle IV (Test Optionality): Tests are optional by default
- Existing E2E tests already assert on the title; they will break without updates
- 8 test assertions across 3 files need updating to expect "Objects"

**Alternatives Considered**:
- **New unit tests**: Rejected — no business logic to test. Tests would only verify string literals match constants.
- **Automated visual regression**: Rejected — overkill for text change
- **Skip test updates**: Rejected — existing tests would fail, violating SC-003

**Implementation**:
1. Update all 8 E2E assertions to expect "Objects" instead of "Agent Projects"
2. Run existing E2E test suite to verify no regressions
3. Manual verification in browser

---

### 4. Accessibility Impact

**Decision**: No accessibility changes required

**Rationale**:
- HTML `<title>` is already screen-reader accessible (WCAG 2.4.2)
- React headers are semantic `<h1>` elements (screen reader compatible)
- Text change maintains same semantic meaning (application identifier)
- No ARIA attributes, roles, or labels require updates

---

### 5. Performance Considerations

**Decision**: No performance impact

**Rationale**:
- Shorter title string in some locations, longer in none
- No runtime performance change — titles are static strings loaded once
- React re-renders unaffected — title changes are in different render paths

---

## Implementation Risks

**Risk Level**: MINIMAL

- **Technical Risk**: None — simple string replacements in well-understood files
- **User Impact**: Positive — UI accurately reflects content
- **Testing Risk**: Low — existing test assertions updated
- **Rollback Risk**: None — instant git revert available

## Phase 0 Completion Checklist

- [x] All NEEDS CLARIFICATION items from Technical Context resolved
- [x] Technology choices documented with rationale
- [x] Alternatives evaluated for key decisions
- [x] Implementation approach clear and justified
- [x] Risks identified and assessed
- [x] No hidden dependencies discovered

**Status**: ✅ **PHASE 0 COMPLETE** — Ready for Phase 1 design artifacts
