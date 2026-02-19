# Research: Replace App Title with 'agentic'

**Feature**: 001-agentic-app-title | **Date**: 2026-02-19
**Purpose**: Resolve technical unknowns and document implementation approach

## Research Summary

This feature requires no significant research as it is a straightforward string replacement task. All technical context is already known from existing codebase exploration. This document exists to satisfy the Phase 0 requirement from the plan template, but contains minimal content due to the feature's simplicity.

## Decision Areas

### 1. Title Placement Strategy

**Decision**: Direct string replacement in source files (HTML, JSX, Python, JSON, shell scripts, markdown)

**Rationale**:
- Application uses hardcoded title strings "Agent Projects" across ~10 files
- No existing centralized configuration or constant for the app title
- Feature scope is limited to this single text replacement
- Adding configuration infrastructure would violate YAGNI principle

**Alternatives Considered**:
- **Centralized constant in config file**: Rejected — overkill for branding string. Would require import statements and additional files across frontend and backend. Adds complexity without benefit.
- **Environment variable**: Rejected — title is not environment-dependent. Would require .env changes, build-time substitution, and documentation updates.
- **i18n/localization system**: Rejected — "agentic" is a brand name, not translatable content. No i18n infrastructure exists in the project.

**Implementation**: Replace `"Agent Projects"` with `"agentic"` in all locations identified in the plan's Source Code section.

---

### 2. Casing and Formatting

**Decision**: Use exact string "agentic" (all lowercase) everywhere

**Rationale**:
- Spec explicitly states: "exact casing as specified, all lowercase"
- The brand name "agentic" is intentionally lowercase
- Backend pyproject.toml `name` field uses kebab-case by convention (`agent-projects-backend` → `agentic-backend`)
- FastAPI title follows the app name pattern (`"Agent Projects API"` → `"agentic API"`)

**Alternatives Considered**:
- **Title case "Agentic"**: Rejected — spec explicitly requires all lowercase
- **ALL CAPS "AGENTIC"**: Rejected — not requested
- **Mixed: "agentic" in UI, "Agentic" in docs**: Rejected — spec requires consistency

**Implementation**: Exact string "agentic" in all user-facing and developer-facing contexts

---

### 3. Scope of Changes

**Decision**: Update all locations where "Agent Projects" appears as an app title or app name reference

**Rationale**:
- Spec FR-001 through FR-007 cover browser tab, headers, E2E tests, devcontainer, backend metadata, and documentation
- The spec assumes "Agent Projects" appears in frontend HTML, frontend components, E2E test files, developer configuration, backend service metadata, and project documentation
- All these locations have been verified in the codebase

**Locations identified (13 instances across 10 files)**:

| File | Line | Current | New |
|------|------|---------|-----|
| `frontend/index.html` | 7 | `<title>Agent Projects</title>` | `<title>agentic</title>` |
| `frontend/src/App.tsx` | 72 | `<h1>Agent Projects</h1>` | `<h1>agentic</h1>` |
| `frontend/src/App.tsx` | 89 | `<h1>Agent Projects</h1>` | `<h1>agentic</h1>` |
| `frontend/e2e/auth.spec.ts` | 12,24,38,99 | `'Agent Projects'` | `'agentic'` |
| `frontend/e2e/auth.spec.ts` | 62 | `/Agent Projects/i` | `/agentic/i` |
| `frontend/e2e/ui.spec.ts` | 43,67 | `'Agent Projects'` | `'agentic'` |
| `frontend/e2e/integration.spec.ts` | 69 | `'Agent Projects'` | `'agentic'` |
| `backend/src/main.py` | 75 | `"Starting Agent Projects API"` | `"Starting agentic API"` |
| `backend/src/main.py` | 77 | `"Shutting down Agent Projects API"` | `"Shutting down agentic API"` |
| `backend/src/main.py` | 85 | `title="Agent Projects API"` | `title="agentic API"` |
| `backend/src/main.py` | 86 | `description="REST API for Agent Projects"` | `description="REST API for agentic"` |
| `.devcontainer/devcontainer.json` | 2 | `"name": "Agent Projects"` | `"name": "agentic"` |
| `.devcontainer/post-create.sh` | 7 | `"Setting up Agent Projects development environment..."` | `"Setting up agentic development environment..."` |
| `backend/pyproject.toml` | 2 | `name = "agent-projects-backend"` | `name = "agentic-backend"` |
| `backend/pyproject.toml` | 4 | `description = "FastAPI backend for Agent Projects"` | `description = "FastAPI backend for agentic"` |
| `README.md` | 1 | `# Agent Projects` | `# agentic` |
| `backend/README.md` | 1 | `# Agent Projects — Backend` | `# agentic — Backend` |

**Alternatives Considered**:
- **Frontend-only changes**: Rejected — spec FR-005, FR-006, FR-007 explicitly require devcontainer, backend, and documentation updates
- **Partial updates**: Rejected — spec requires 100% consistency (SC-001, SC-003, SC-004)

---

### 4. Testing Strategy

**Decision**: Update existing E2E test assertions; no new tests required

**Rationale**:
- Constitution Principle IV (Test Optionality): Tests are optional by default
- Existing E2E tests assert the current title "Agent Projects" — these must be updated to "agentic" to avoid false failures
- No new business logic is introduced; manual verification is sufficient for acceptance criteria
- FR-004 explicitly requires updating E2E test assertions

**Alternatives Considered**:
- **New unit tests**: Rejected — no business logic to test. Would only verify string literals match constants.
- **Automated visual regression**: Rejected — overkill for text-only change
- **Skip test updates**: Rejected — existing tests would fail with wrong title assertion

**Implementation**:
1. Update all E2E test assertions from "Agent Projects" to "agentic"
2. Run existing test suites to verify no regressions

---

### 5. Backend pyproject.toml Name Convention

**Decision**: Change `name = "agent-projects-backend"` to `name = "agentic-backend"`

**Rationale**:
- Python package names use kebab-case by PEP 625 convention
- The current pattern is `{app-name}-backend`
- Maintaining the pattern: `agentic-backend`

**Alternatives Considered**:
- **Keep as "agent-projects-backend"**: Rejected — inconsistent with new branding
- **Use "agentic" without suffix**: Rejected — the `-backend` suffix distinguishes it from potential frontend package

---

### 6. Documentation References

**Decision**: Update README headers and first-line descriptions; preserve all other README content

**Rationale**:
- Spec FR-007 requires updating project documentation references
- README files use the app name in headers (`# Agent Projects`) and inline references
- Body content that references "Agent Projects" as a product name should also be updated for consistency

**Alternatives Considered**:
- **Full README rewrite**: Rejected — out of scope. Only title/name references change.
- **No README changes**: Rejected — spec explicitly requires documentation updates (FR-007, SC-004)

---

### 7. Rollback Strategy

**Decision**: Standard git revert

**Rationale**:
- Changes are simple string replacements
- No database migrations, API contract changes, or state management involved
- Git commit revert immediately restores previous title
- No deployment coordination required

**Alternatives Considered**:
- **Feature flag**: Rejected — massive overkill for static text change
- **Dual title support**: Rejected — unnecessary complexity for one-time branding update

---

## Implementation Risks

**Risk Level**: MINIMAL

- **Technical Risk**: None — simple string replacements in well-understood files
- **User Impact**: Positive — improves branding clarity
- **Testing Risk**: Low — existing E2E assertions updated, manual verification sufficient
- **Rollback Risk**: None — instant git revert available

## Best Practices Applied

1. **YAGNI (You Aren't Gonna Need It)**: No configuration infrastructure for single string
2. **KISS (Keep It Simple)**: Direct replacement over abstraction
3. **DRY (Don't Repeat Yourself)**: Acceptable — multiple instances across separate files is inherent to the architecture, not harmful duplication
4. **Atomic Changes**: Single feature branch for all related changes

## Phase 0 Completion Checklist

- [x] All NEEDS CLARIFICATION items from Technical Context resolved
- [x] Technology choices documented with rationale
- [x] Alternatives evaluated for key decisions
- [x] Implementation approach clear and justified
- [x] Risks identified and assessed
- [x] No hidden dependencies discovered

**Status**: ✅ **PHASE 0 COMPLETE** — Ready for Phase 1 design artifacts
