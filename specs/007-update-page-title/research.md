# Research: Update Page Title to "Front"

**Feature**: 007-update-page-title | **Date**: 2026-02-19  
**Purpose**: Resolve technical unknowns and document implementation approach

## Research Summary

This feature requires no significant research as it is a straightforward string replacement task. All technical context is already known from existing codebase exploration. This document exists to satisfy the Phase 0 requirement from the plan template, but contains minimal content due to the feature's simplicity.

## Decision Areas

### 1. Title Placement Strategy

**Decision**: Direct string replacement in source files (HTML + JSX)

**Rationale**: 
- Application uses hardcoded title strings in 3 locations (2 source files)
- No existing centralized configuration or constant for the title
- Feature scope is limited to this single update
- Adding configuration infrastructure would violate YAGNI principle

**Alternatives Considered**:
- **Centralized constant in config file**: Rejected — overkill for single-use string. Would require import statements and additional file. Adds complexity without benefit.
- **Environment variable**: Rejected — title is not environment-dependent. Would require .env changes, build-time substitution, and documentation updates.
- **i18n/localization system**: Rejected — application has no i18n infrastructure and the spec does not require it.

**Implementation**: Replace `"Agent Projects"` with `"Front"` in:
1. `frontend/index.html` line 7 (`<title>` tag)
2. `frontend/src/App.tsx` line 72 (`<h1>` in login view)
3. `frontend/src/App.tsx` line 89 (`<h1>` in authenticated header)

---

### 2. E2E Test Assertion Updates

**Decision**: Update all existing E2E test assertions that reference "Agent Projects"

**Rationale**:
- 8 hardcoded title assertions exist across 3 E2E test files
- Tests will fail if source title changes but assertions remain
- This is maintenance of existing tests, not new test creation (Constitution Principle IV satisfied)
- Leaving broken test assertions would introduce regressions (violates spec FR-004)

**Alternatives Considered**:
- **Leave tests unchanged**: Rejected — tests would fail, blocking CI pipeline
- **Delete title assertions**: Rejected — removes valid test coverage for page structure
- **Use regex patterns instead of exact strings**: Rejected — less precise; existing tests use `toContainText` which is already flexible

**Implementation**: Replace `'Agent Projects'` with `'Front'` in:
1. `frontend/e2e/auth.spec.ts` — lines 12, 24, 38, 99 (toContainText assertions)
2. `frontend/e2e/auth.spec.ts` — line 62 (toHaveTitle regex assertion)
3. `frontend/e2e/ui.spec.ts` — lines 43, 67 (toContainText assertions)
4. `frontend/e2e/integration.spec.ts` — line 69 (toContainText assertion)

---

### 3. Scope Boundary: Backend and Non-User-Facing References

**Decision**: Do NOT update backend, documentation, devcontainer, or other non-user-facing references

**Rationale**:
- Spec Assumptions explicitly state: "The title change applies only to the page title (browser tab) and the main visible heading, not to backend service names, internal project identifiers, or documentation unless they are user-facing"
- Backend references (main.py FastAPI config, pyproject.toml, README.md) are internal/developer-facing
- `.devcontainer/devcontainer.json`, `.env.example`, `post-create.sh` are development environment files
- `frontend/src/services/api.ts` and `frontend/src/types/index.ts` contain JSDoc comments, not user-facing text

**Files explicitly out of scope**:
- `backend/src/main.py` — API title/description (developer-facing)
- `backend/pyproject.toml` — Package description (developer-facing)
- `backend/README.md` — Documentation (developer-facing)
- `README.md` — Documentation (developer-facing)
- `.devcontainer/devcontainer.json` — Dev environment (developer-facing)
- `.devcontainer/post-create.sh` — Dev setup script (developer-facing)
- `.env.example` — Config template (developer-facing)
- `frontend/src/services/api.ts` — JSDoc comment (not rendered)
- `frontend/src/types/index.ts` — JSDoc comment (not rendered)
- `backend/tests/test_api_e2e.py` — Test docstring (not rendered)

---

### 4. Testing Strategy

**Decision**: Manual verification + existing E2E test assertion updates

**Rationale**:
- Feature is visual change with no programmatic logic
- Constitution Principle IV (Test Optionality): New tests are optional by default
- Existing E2E tests already cover title assertions and must be updated
- Spec acceptance criteria are human-verifiable (open app, observe title)

**Alternatives Considered**:
- **New unit tests**: Rejected — no business logic to test. Would only verify string literals match constants.
- **Automated visual regression**: Rejected — overkill for single text change.

**Implementation**: 
1. Update existing E2E test assertions to use "Front"
2. Manual verification in browser (primary acceptance criteria)

---

### 5. Accessibility Impact

**Decision**: No accessibility changes required

**Rationale**:
- HTML `<title>` is already screen-reader accessible (WCAG 2.4.2)
- React headers are semantic `<h1>` elements (screen reader compatible)
- Text change from "Agent Projects" to "Front" maintains same semantic meaning (application identifier)
- No ARIA attributes, roles, or labels require updates

---

### 6. Performance Considerations

**Decision**: No performance impact

**Rationale**:
- Shorter title string ("Front" = 5 chars vs "Agent Projects" = 14 chars)
- No runtime performance change — titles are static strings loaded once
- React re-renders unaffected — title changes are in different render paths

---

## Implementation Risks

**Risk Level**: MINIMAL

- **Technical Risk**: None — simple string replacements in well-understood files
- **User Impact**: Positive — updates branding to intended label
- **Testing Risk**: Low — existing E2E assertions updated; manual verification sufficient
- **Rollback Risk**: None — instant git revert available

## Phase 0 Completion Checklist

- [x] All NEEDS CLARIFICATION items from Technical Context resolved
- [x] Technology choices documented with rationale
- [x] Alternatives evaluated for key decisions
- [x] Implementation approach clear and justified
- [x] Risks identified and assessed
- [x] No hidden dependencies discovered

**Status**: ✅ **PHASE 0 COMPLETE** — Ready for Phase 1 design artifacts
