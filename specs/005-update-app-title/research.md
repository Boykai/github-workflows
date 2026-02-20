# Research: Update App Title to "Happy Place"

**Feature**: 005-update-app-title | **Date**: 2026-02-20  
**Purpose**: Resolve technical unknowns and document implementation approach

## Research Summary

This feature requires no significant research as it is a straightforward string replacement task. All technical context is already known from codebase exploration. The current title "Agent Projects" appears in 21+ locations across 14 files spanning frontend, backend, configuration, tests, and documentation. This document exists to satisfy the Phase 0 requirement and records decisions for implementation.

## Decision Areas

### 1. Title Replacement Strategy

**Decision**: Direct string replacement in all source files containing "Agent Projects"

**Rationale**: 
- Application uses hardcoded title strings across ~14 files
- No existing centralized configuration or constant for the app title
- Feature scope is a one-time branding update
- Adding configuration infrastructure would violate YAGNI principle (Constitution V)

**Alternatives Considered**:
- **Centralized constant in config file**: Rejected — overkill for branding string. Would require import statements in every file and adds complexity without benefit for a one-time change.
- **Environment variable (VITE_APP_TITLE)**: Rejected — title is not environment-dependent (same in dev/staging/prod). Would require build-time substitution and documentation updates.
- **i18n/localization system**: Rejected — spec does not require internationalization. "Happy Place" is a fixed product name.

**Implementation**: Replace `"Agent Projects"` with `"Happy Place"` in all identified locations (see data-model.md for complete inventory).

---

### 2. Scope of Changes

**Decision**: Update all user-facing code, E2E tests, backend metadata, configuration files, and documentation

**Rationale**:
- FR-007 requires no residual "Agent Projects" references in user-facing files
- E2E tests (FR-006) assert the old title and will fail without updates
- Backend API metadata (FastAPI title/description) is user-facing via OpenAPI docs
- Configuration and documentation updates ensure full consistency

**Alternatives Considered**:
- **Frontend-only changes**: Rejected — leaves inconsistency in backend API docs, tests, and configuration
- **User-facing only (skip comments)**: Considered — code comments in api.ts, index.ts, and test_api_e2e.py reference "Agent Projects" but are not user-facing. However, updating them maintains codebase consistency per FR-007.

**Implementation**: 
- **P1 (User-facing)**: frontend/index.html, frontend/src/App.tsx
- **P1 (Tests)**: frontend/e2e/auth.spec.ts, ui.spec.ts, integration.spec.ts
- **P2 (Backend metadata)**: backend/src/main.py (FastAPI config + logger)
- **P2 (Config/Docs)**: README.md, backend/README.md, .devcontainer/*, .env.example, backend/pyproject.toml
- **P2 (Code comments)**: frontend/src/services/api.ts, frontend/src/types/index.ts, backend/tests/test_api_e2e.py

---

### 3. Casing Consistency

**Decision**: Use exact title case "Happy Place" (capital H, capital P) everywhere

**Rationale**:
- FR-008 mandates consistent "Happy Place" casing
- No variations (e.g., "happy place", "HAPPY PLACE", "happy-place") should be used
- The title is a proper name/brand and follows standard title case conventions

**Alternatives Considered**:
- **Lowercase in URLs/slugs**: Not applicable — no URL routing changes required
- **UPPER_CASE in env vars**: Not applicable — no environment variables use the title

**Implementation**: All replacements use exactly `"Happy Place"` for the display name. Backend API title becomes `"Happy Place API"` and description becomes `"REST API for Happy Place"` to maintain the existing pattern.

---

### 4. Testing Strategy

**Decision**: Update existing E2E test assertions; no new tests required

**Rationale**:
- Constitution Principle IV (Test Optionality): New tests are optional by default
- Existing E2E tests explicitly assert `"Agent Projects"` in 8 locations across 3 test files
- These tests will fail without updates, blocking CI
- Manual verification sufficient for visual confirmation

**Alternatives Considered**:
- **New unit tests for title**: Rejected — no business logic to test; React Testing Library tests would only verify string literals
- **Automated visual regression**: Rejected — overkill for text change
- **Skip E2E test updates**: Rejected — tests will fail and block CI pipeline

**Implementation**:
1. Update all E2E assertions from `"Agent Projects"` to `"Happy Place"` 
2. Update `toHaveTitle(/Agent Projects/i)` to `toHaveTitle(/Happy Place/i)`
3. Run existing E2E tests to confirm all pass

---

### 5. Backend API Title

**Decision**: Update FastAPI metadata to reflect "Happy Place"

**Rationale**:
- FastAPI `title` and `description` appear in auto-generated OpenAPI/Swagger docs
- These are user-facing when developers access `/docs` endpoint
- Logger messages reference "Agent Projects API" and should be updated for operational clarity

**Alternatives Considered**:
- **Leave backend unchanged**: Rejected — creates inconsistency between frontend branding and API documentation
- **Remove API title entirely**: Rejected — OpenAPI docs need a title for identification

**Implementation**:
- `title="Happy Place API"` (line 85 of main.py)
- `description="REST API for Happy Place"` (line 86 of main.py)
- Logger messages: `"Starting Happy Place API"` and `"Shutting down Happy Place API"`

---

### 6. Documentation Updates

**Decision**: Update README.md files and configuration comments

**Rationale**:
- Spec Assumptions state: "Documentation files may reference the app name but are considered secondary; they should be updated for consistency but are not blockers"
- README.md is the first thing contributors see — should reflect current name
- Configuration file comments (.env.example, devcontainer.json, post-create.sh) should match

**Alternatives Considered**:
- **Skip documentation**: Possible per spec but leaves confusing inconsistency
- **Separate PR for docs**: Rejected — simple string replacements are easier to batch

**Implementation**: Update headings and references in README.md, backend/README.md, .devcontainer/devcontainer.json, .devcontainer/post-create.sh, .env.example, backend/pyproject.toml

---

### 7. Rollback Strategy

**Decision**: Standard git revert

**Rationale**:
- Changes are simple string replacements across multiple files
- No database migrations, API contract changes, or state management involved
- Git commit revert immediately restores previous title
- No deployment coordination required

**Alternatives Considered**:
- **Feature flag**: Rejected — massive overkill for static text change
- **Dual title support**: Rejected — unnecessary complexity

**Implementation**: Single atomic commit (or small series of commits) with clear messages enables instant rollback

---

## Implementation Risks

**Risk Level**: MINIMAL

- **Technical Risk**: None — simple string replacements in well-understood files
- **User Impact**: Positive — establishes new brand identity
- **Testing Risk**: Low — existing E2E tests updated to match new title
- **Rollback Risk**: None — instant git revert available
- **Merge Conflict Risk**: Low — title strings are isolated and unlikely to conflict

## Phase 0 Completion Checklist

- [x] All NEEDS CLARIFICATION items from Technical Context resolved (none existed)
- [x] Technology choices documented with rationale
- [x] Alternatives evaluated for key decisions
- [x] Implementation approach clear and justified
- [x] Risks identified and assessed
- [x] No hidden dependencies discovered
- [x] Complete inventory of files requiring changes documented

**Status**: ✅ **PHASE 0 COMPLETE** - Ready for Phase 1 design artifacts
