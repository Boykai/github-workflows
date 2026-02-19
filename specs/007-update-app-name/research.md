# Research: Update App Name to "Robot"

**Feature**: 007-update-app-name | **Date**: 2026-02-19  
**Purpose**: Resolve technical unknowns and document implementation approach

## Research Summary

This feature requires no significant research as it is a straightforward string replacement task. All technical context is already known from codebase exploration. The current app name "Agent Projects" appears in ~12 files across frontend, backend, configuration, documentation, and tests. This document exists to satisfy the Phase 0 requirement from the plan template, but contains minimal content due to the feature's simplicity.

## Decision Areas

### 1. Replacement Strategy

**Decision**: Direct string replacement in source files (HTML, TSX, Python, JSON, TOML, Markdown, Shell)

**Rationale**: 
- Application uses hardcoded "Agent Projects" strings in ~12 locations across the stack
- No existing centralized configuration or constant for the app name
- Feature scope is limited to this single display-name update
- Adding centralized configuration infrastructure would violate YAGNI principle

**Alternatives Considered**:
- **Centralized constant in config file**: Rejected — overkill for display-name string. Would require import changes across both frontend and backend stacks. Adds complexity without benefit for a one-time rename.
- **Environment variable**: Rejected — app name is not environment-dependent. Would require .env changes, build-time substitution for frontend, and runtime reading for backend.
- **i18n/localization system**: Rejected — spec explicitly states "Localization/i18n is not currently in use; all name references are hardcoded English strings" (Assumptions section)

**Implementation**: Replace all instances of `"Agent Projects"` with `"Robot"` in the files identified during codebase exploration.

---

### 2. Scope of Replacement

**Decision**: Replace "Agent Projects" in all user-facing content, configuration files, and documentation. Internal package names (e.g., `agent-projects-backend` in pyproject.toml `[project].name`) and directory structures are NOT renamed unless they surface to end users.

**Rationale**:
- Spec assumption: "The rename applies only to the display name; internal package names, directory structures, and repository names are not changed unless they surface to end users."
- The pyproject.toml `name` field is an internal Python package identifier, not user-facing → update only the `description` field.
- The pyproject.toml `description` field says "FastAPI backend for Agent Projects" — this surfaces in `pip show` output and should be updated.
- The `.env.example` header comment references the app name → update for developer clarity.
- The `.devcontainer/devcontainer.json` `name` field is shown in VS Code/Codespaces UI → update as user-facing.

**Alternatives Considered**:
- **Rename Python package name**: Rejected — would require import path changes, directory renames, and is explicitly out of scope.
- **Rename repository**: Rejected — explicitly out of scope per assumptions.

---

### 3. Backend Log and API Metadata

**Decision**: Update FastAPI `title` and `description` fields and startup log messages.

**Rationale**:
- FR-003 requires backend startup logs to use "Robot"
- FR-004 requires auto-generated API documentation to display "Robot"
- FastAPI `title` and `description` are shown on `/api/docs` (Swagger) and `/api/redoc` pages
- Startup log messages in the `lifespan` context manager reference "Agent Projects API"

**Implementation**:
- `backend/src/main.py` line 75: `"Starting Agent Projects API"` → `"Starting Robot API"`
- `backend/src/main.py` line 77: `"Shutting down Agent Projects API"` → `"Shutting down Robot API"`
- `backend/src/main.py` line 85: `title="Agent Projects API"` → `title="Robot API"`
- `backend/src/main.py` line 86: `description="REST API for Agent Projects"` → `description="REST API for Robot"`

---

### 4. E2E Test Assertions

**Decision**: Update all Playwright E2E test assertions that check for "Agent Projects" to expect "Robot"

**Rationale**:
- FR-008 requires all existing automated tests to be updated to expect "Robot"
- 8 assertions across 3 test files currently check for "Agent Projects" in `<h1>` elements
- 1 assertion checks the page title matches `/Agent Projects/i`
- Leaving these unchanged would cause test failures

**Files requiring updates**:
- `frontend/e2e/auth.spec.ts` — 5 assertions
- `frontend/e2e/ui.spec.ts` — 2 assertions
- `frontend/e2e/integration.spec.ts` — 1 assertion

---

### 5. Documentation Updates

**Decision**: Update README.md and backend/README.md to reference "Robot"

**Rationale**:
- FR-007 requires all README and documentation files to reference "Robot"
- `README.md` line 1: heading says "# Agent Projects"
- `backend/README.md` line 1: heading says "# Agent Projects — Backend"
- `backend/README.md` line 3: text references "Agent Projects"

**Alternatives Considered**:
- **Skip documentation updates**: Rejected — FR-007 explicitly requires it.

---

### 6. Testing Strategy

**Decision**: Update existing E2E test assertions; no new tests needed

**Rationale**:
- Constitution Principle IV (Test Optionality): Tests are optional by default
- FR-008 explicitly mandates updating existing test assertions
- Feature is a visual/textual change with no programmatic logic requiring new tests
- Manual verification by searching codebase for "Agent Projects" post-implementation confirms completeness

---

## Implementation Risks

**Risk Level**: MINIMAL

- **Technical Risk**: None — simple string replacements in well-understood files
- **User Impact**: Positive — establishes "Robot" branding
- **Testing Risk**: Low — update existing assertions, no new test infrastructure
- **Rollback Risk**: None — instant git revert available

## Phase 0 Completion Checklist

- [x] All NEEDS CLARIFICATION items from Technical Context resolved (none existed)
- [x] Technology choices documented with rationale
- [x] Alternatives evaluated for key decisions
- [x] Implementation approach clear and justified
- [x] Risks identified and assessed
- [x] No hidden dependencies discovered

**Status**: ✅ **PHASE 0 COMPLETE** — Ready for Phase 1 design artifacts
