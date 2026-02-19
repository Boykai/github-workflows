# Research: Update App Title to "Hello World"

**Feature**: 005-hello-world-title  
**Date**: 2026-02-19  
**Status**: Complete

## Research Tasks

### RT-001: Current Title Location Inventory

**Task**: Identify all locations where the current title "Agent Projects" is defined or referenced.

**Decision**: The title "Agent Projects" appears in 24 locations across the codebase, categorized into three tiers:

| Tier | Category | Files | Count |
|------|----------|-------|-------|
| 1 | User-facing display | `frontend/index.html`, `frontend/src/App.tsx` | 3 |
| 2 | API/Backend metadata | `backend/src/main.py`, `backend/pyproject.toml`, `backend/README.md` | 6 |
| 3 | Tests & config | `frontend/e2e/*.spec.ts`, `.devcontainer/devcontainer.json`, `.env.example`, JSDoc comments | 15 |

**Rationale**: A tiered approach ensures P1 user-facing changes are addressed first, followed by metadata and test consistency. All tiers must be updated to satisfy FR-005 (no old title references remain).

**Alternatives considered**:
- Partial update (display only): Rejected — violates FR-005 and SC-003
- Centralized title constant: Rejected — over-engineering for a simple rename; violates Constitution Principle V (Simplicity/YAGNI)

### RT-002: Frontend Technology Stack

**Task**: Confirm frontend framework and build tooling for implementation approach.

**Decision**: The frontend uses React 18.3.1 with TypeScript, built with Vite 5.4.0. The title is set in two ways:
1. Static HTML `<title>` tag in `frontend/index.html` (browser tab)
2. React `<h1>` elements in `frontend/src/App.tsx` (login page and app header)

**Rationale**: Direct string replacement in these files is the simplest and most maintainable approach. No dynamic title management library is needed.

**Alternatives considered**:
- react-helmet or similar title management library: Rejected — unnecessary dependency for a static title
- Environment variable for title: Rejected — YAGNI; title is not environment-specific per spec assumptions

### RT-003: E2E Test Update Strategy

**Task**: Determine how to update existing E2E tests that assert the current title.

**Decision**: Update all Playwright E2E test assertions from "Agent Projects" to "Hello World" via direct string replacement. Tests are located in:
- `frontend/e2e/auth.spec.ts` (5 assertions)
- `frontend/e2e/ui.spec.ts` (2 assertions)
- `frontend/e2e/integration.spec.ts` (1 assertion)

**Rationale**: Tests should reflect the new expected behavior. These are not new tests but existing assertions that need updating to match the new title.

**Alternatives considered**:
- Parameterized test fixtures with title config: Rejected — adds complexity for a one-time change

### RT-004: Backend API Metadata

**Task**: Determine whether backend API title should also change.

**Decision**: Yes, update the FastAPI OpenAPI metadata (`title` and `description` in `backend/src/main.py`) and package description in `backend/pyproject.toml` to reference "Hello World" instead of "Agent Projects".

**Rationale**: Maintains consistency across the full stack. The OpenAPI docs (Swagger UI) display this title, making it user-visible. FR-005 requires removing all references to the previous title.

**Alternatives considered**:
- Keep backend title as "Agent Projects API": Rejected — violates FR-005

### RT-005: Non-functional References

**Task**: Determine handling of comments, README, and config file references.

**Decision**: Update all references including:
- JSDoc comments in `frontend/src/types/index.ts` and `frontend/src/services/api.ts`
- `.devcontainer/devcontainer.json` name field
- `.env.example` header comment
- `backend/README.md` headings and descriptions

**Rationale**: Complete consistency per FR-005. Comments and config that reference the old name would create confusion for developers.

**Alternatives considered**:
- Skip comment/config updates: Rejected — leaves stale references that violate SC-003
