# Research: Update App Title to "New App"

**Feature**: 005-new-app-title | **Date**: 2026-02-19  
**Purpose**: Resolve technical unknowns and document implementation approach

## Research Summary

This feature requires no significant research as it is a straightforward string replacement task. All technical context is already known from existing codebase exploration. This document exists to satisfy the Phase 0 requirement from the plan template, but contains minimal content due to the feature's simplicity.

## Decision Areas

### 1. Title Placement Strategy

**Decision**: Direct string replacement in source files (HTML, JSX, Python, TOML, JSON, Markdown, Shell)

**Rationale**: 
- Application uses hardcoded title strings "Agent Projects" in ~10 locations
- No existing centralized configuration or constant for app title
- Feature scope is limited to this single update
- Adding configuration infrastructure would violate YAGNI principle

**Alternatives Considered**:
- **Centralized constant in config file**: Rejected - overkill for single-use string. Would require import statements and additional file. Adds complexity without benefit.
- **Environment variable**: Rejected - title is not environment-dependent. Would require .env changes, build-time substitution, and documentation updates.
- **i18n/localization system**: Rejected - spec explicitly states "No internationalization/localization is required" (Assumptions section)

**Implementation**: Replace all instances of "Agent Projects" with "New App" across:
1. `frontend/index.html` line 7 (`<title>` tag)
2. `frontend/src/App.tsx` lines 72, 89 (`<h1>` headers)
3. `backend/src/main.py` lines 85-86 (FastAPI title/description)
4. `backend/pyproject.toml` lines 2, 4 (package name/description)
5. `backend/README.md` line 1 (heading)
6. `README.md` line 1 (heading)
7. `.devcontainer/devcontainer.json` line 2 (container name)
8. `.devcontainer/post-create.sh` (echo message)
9. `.env.example` line 2 (header comment)
10. `frontend/e2e/auth.spec.ts` (title/heading assertions)
11. `frontend/e2e/ui.spec.ts` (heading assertions)
12. `frontend/e2e/integration.spec.ts` (heading assertions)

---

### 2. Scope of Title References

**Decision**: Update all occurrences including config, docs, backend metadata, and test assertions

**Rationale**:
- Spec FR-005 requires removing ALL references to previous title
- Spec FR-006 requires updating all configuration and manifest files
- Spec FR-007 requires updating all documentation files
- E2E tests currently assert "Agent Projects" in title/heading checks — these must be updated to avoid test failures

**Alternatives Considered**:
- **Frontend-only changes**: Rejected - spec requires comprehensive update across all areas (FR-005, FR-006, FR-007)
- **Skip test updates**: Rejected - existing E2E tests hardcode "Agent Projects" and will fail

**Implementation**: Full codebase scan and replace of "Agent Projects" references

---

### 3. Package Name Handling

**Decision**: Update `agent-projects-backend` and `agent-projects-frontend` package names to `new-app-backend` and `new-app-frontend`

**Rationale**:
- Package names in pyproject.toml and package.json reference the old title
- FR-006 requires updating configuration files
- Package names are internal identifiers with no external dependencies

**Alternatives Considered**:
- **Keep old package names**: Rejected - creates inconsistency and violates FR-006
- **Use different naming convention**: Rejected - maintaining kebab-case convention matches existing patterns

**Implementation**: 
- `backend/pyproject.toml`: `agent-projects-backend` → `new-app-backend`
- `frontend/package.json`: `agent-projects-frontend` → `new-app-frontend`

---

### 4. Browser Compatibility

**Decision**: No special handling required

**Rationale**:
- Standard HTML `<title>` tag and React JSX are universally supported
- Spec requires support for modern browsers: Chrome, Firefox, Safari, Edge
- "New App" contains only ASCII characters — no encoding concerns

**Alternatives Considered**:
- **Character encoding validation**: Rejected - ASCII text requires no special encoding
- **Browser-specific polyfills**: Rejected - no browser compatibility issues for plain text strings

**Implementation**: Direct string replacement with no encoding or compatibility adjustments

---

### 5. Testing Strategy

**Decision**: Update existing E2E test assertions; no new tests required

**Rationale**:
- Existing E2E tests (`auth.spec.ts`, `ui.spec.ts`, `integration.spec.ts`) assert "Agent Projects" in title and heading checks
- These assertions MUST be updated to match "New App" or tests will fail
- Constitution Principle IV (Test Optionality): No new tests needed, but existing tests must remain valid
- Feature is visual change with no new programmatic logic

**Alternatives Considered**:
- **New unit tests**: Rejected - no business logic to test
- **Skip E2E updates**: Rejected - existing tests will break on CI
- **Automated visual regression**: Rejected - overkill for text change

**Implementation**: 
1. Update all E2E test assertions from "Agent Projects" to "New App"
2. Run existing E2E tests to verify passing
3. Manual browser verification as secondary validation

---

### 6. Accessibility Impact

**Decision**: No accessibility changes required

**Rationale**:
- HTML `<title>` is already screen-reader accessible (WCAG 2.4.2)
- React headers are semantic `<h1>` elements (screen reader compatible)
- Text change maintains same semantic meaning (application identifier)
- No ARIA attributes, roles, or labels require updates

**Alternatives Considered**:
- **Add ARIA labels**: Rejected - existing semantic HTML is sufficient
- **Document title update pattern**: Rejected - single-page app doesn't change title dynamically per route

**Implementation**: Direct string replacement preserves existing accessibility properties

---

### 7. Rollback Strategy

**Decision**: Standard git revert

**Rationale**:
- Changes are simple string replacements
- No database migrations, API changes, or state management involved
- Git commit revert immediately restores previous title
- No deployment coordination required

**Alternatives Considered**:
- **Feature flag**: Rejected - massive overkill for static text change
- **Dual title support**: Rejected - unnecessary complexity for one-time update

**Implementation**: Single atomic commit with clear message enables instant rollback if needed

---

## Implementation Risks

**Risk Level**: MINIMAL

- **Technical Risk**: None - simple string replacements in well-understood files
- **User Impact**: Positive - updates branding as requested
- **Testing Risk**: Low - E2E test assertion updates straightforward
- **Rollback Risk**: None - instant git revert available

## Best Practices Applied

1. **YAGNI (You Aren't Gonna Need It)**: No configuration infrastructure for single string
2. **KISS (Keep It Simple)**: Direct replacement over abstraction
3. **DRY (Don't Repeat Yourself)**: Acceptable - multiple instances across different files is inherent to the problem domain
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
