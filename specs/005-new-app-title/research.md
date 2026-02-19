# Research: Update App Title to "New App"

**Feature**: 005-new-app-title | **Date**: 2026-02-19  
**Purpose**: Resolve technical unknowns and document implementation approach

## Research Summary

This feature requires no significant research as it is a straightforward string replacement task. All technical context is already known from existing codebase exploration. The current application title "Agent Projects" appears in ~20 locations across frontend, backend, configuration, tests, and documentation. This document exists to satisfy the Phase 0 requirement from the plan template.

## Decision Areas

### 1. Title Replacement Scope

**Decision**: Full replacement of "Agent Projects" with "New App" across all user-facing text, configuration, tests, and documentation

**Rationale**: 
- Spec FR-005 requires removing/replacing ALL references to previous title
- Spec FR-006 requires updating all configuration and manifest files
- Spec FR-007 requires updating all documentation files
- The broader scope (vs. frontend-only) ensures complete branding consistency per P3 user story

**Alternatives Considered**:
- **Frontend-only changes**: Rejected - would leave inconsistent branding in backend metadata, config files, tests, and docs. Violates FR-005, FR-006, FR-007.
- **Selective replacement (user-facing only)**: Rejected - would leave stale references in E2E tests (causing failures), backend API docs, and developer-facing files

**Implementation**: Replace "Agent Projects" → "New App" and "Agent Projects API" → "New App API" across all identified locations:
1. `frontend/index.html` line 7 (`<title>` tag)
2. `frontend/src/App.tsx` lines 72, 89 (`<h1>` headers)
3. `backend/src/main.py` lines 75, 77, 85, 86 (FastAPI title, description, log messages)
4. `backend/pyproject.toml` line 4 (package description)
5. `backend/README.md` line 1 (documentation header)
6. `backend/tests/test_api_e2e.py` line 2 (test file comment)
7. `.devcontainer/devcontainer.json` line 2 (container name)
8. `.devcontainer/post-create.sh` line 7 (setup message)
9. `frontend/e2e/auth.spec.ts` lines 12, 24, 38, 62, 99 (test assertions)
10. `frontend/e2e/ui.spec.ts` lines 43, 67 (test assertions)
11. `frontend/e2e/integration.spec.ts` line 69 (test assertion)
12. `frontend/src/types/index.ts` line 2 (file header comment)
13. `frontend/src/services/api.ts` line 2 (file header comment)
14. `README.md` line 1 (root documentation header)

---

### 2. Title Variant Strategy

**Decision**: Use "New App" for the base title and "New App API" for backend API-specific references (matching existing pattern)

**Rationale**:
- Current codebase uses "Agent Projects" as the base and "Agent Projects API" for backend FastAPI title/description
- Maintaining this naming convention ensures consistency
- Backend API docs (Swagger/ReDoc) will display "New App API" which clearly identifies the API component

**Alternatives Considered**:
- **Use "New App" everywhere (no API suffix)**: Rejected - loses clarity about which component the API docs describe
- **Use "New App Backend"**: Rejected - doesn't match existing naming convention of "{AppName} API"

**Implementation**: Two replacement patterns:
- "Agent Projects API" → "New App API" (backend API-specific: FastAPI title, description, log messages)
- "Agent Projects" → "New App" (all other locations)

---

### 3. Testing Strategy

**Decision**: Update existing E2E test assertions to match new title; no new tests needed

**Rationale**:
- 8 existing E2E test assertions reference "Agent Projects" in heading/title checks
- These will fail if not updated, breaking CI pipeline
- Constitution Principle IV (Test Optionality): No new tests needed for string replacements
- Manual verification sufficient for visual confirmation

**Alternatives Considered**:
- **Skip test updates**: Rejected - would break CI with 8 failing assertions
- **Add new unit tests for title**: Rejected - overkill for static strings; violates YAGNI principle

**Implementation**: Update assertions in:
- `frontend/e2e/auth.spec.ts`: 5 assertions → replace `'Agent Projects'` with `'New App'`
- `frontend/e2e/ui.spec.ts`: 2 assertions → replace `'Agent Projects'` with `'New App'`
- `frontend/e2e/integration.spec.ts`: 1 assertion → replace `'Agent Projects'` with `'New App'`

---

### 4. Documentation and Comment Updates

**Decision**: Update all documentation headers and file comments referencing "Agent Projects"

**Rationale**:
- FR-007 explicitly requires documentation updates
- File header comments (types/index.ts, services/api.ts, test_api_e2e.py) reference "Agent Projects"
- README files serve as primary documentation and must reflect new branding
- Developer-facing consistency is important for P3 user story

**Alternatives Considered**:
- **Skip comment updates**: Rejected - leaves stale references, violates FR-005 (no remnants of old title)
- **Only update READMEs**: Rejected - incomplete; file comments would still reference old title

**Implementation**: Update header comments and documentation in all identified files

---

### 5. Configuration File Strategy

**Decision**: Update devcontainer name and post-create script message; preserve internal package names

**Rationale**:
- `devcontainer.json` "name" field is user-visible in VS Code and should reflect current branding
- `post-create.sh` echo message is visible during container setup
- `frontend/package.json` "name" field (`agent-projects-frontend`) is an internal npm identifier, not user-facing
- `backend/pyproject.toml` "name" field (`agent-projects-backend`) is an internal Python package identifier, not user-facing
- Only the pyproject.toml "description" field is user-facing and needs update

**Alternatives Considered**:
- **Rename npm/Python packages**: Rejected - internal identifiers with no user-facing impact; would require dependency updates and potential CI changes
- **Skip all config files**: Rejected - violates FR-006 (update configuration files)

**Implementation**: Update user-facing config values while preserving internal package identifiers

---

### 6. Rollback Strategy

**Decision**: Standard git revert

**Rationale**:
- All changes are string replacements with no data migrations or API contract changes
- Single atomic commit enables instant rollback
- No deployment coordination required

**Alternatives Considered**:
- **Feature flag**: Rejected - massive overkill for static text change
- **Dual title support**: Rejected - unnecessary complexity

**Implementation**: Single atomic commit with clear message enables instant rollback if needed

---

## Implementation Risks

**Risk Level**: MINIMAL

- **Technical Risk**: None - simple string replacements in well-understood files
- **User Impact**: Positive - updates branding as requested
- **Testing Risk**: Low - existing E2E assertions updated to match; CI should pass
- **Rollback Risk**: None - instant git revert available

## Best Practices Applied

1. **YAGNI (You Aren't Gonna Need It)**: No configuration infrastructure for single string
2. **KISS (Keep It Simple)**: Direct replacement over abstraction
3. **DRY (Don't Repeat Yourself)**: Acceptable - title appears in multiple files due to different tech stacks (HTML, React, Python, config)
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
