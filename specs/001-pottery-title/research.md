# Research: Update Project Title to 'pottery'

**Branch**: `copilot/update-project-title-to-pottery-again` | **Date**: 2026-02-16 | **Spec**: [spec.md](./spec.md)

## Overview

This document captures all research findings and technology decisions for updating the project title from "Welcome to Tech Connect 2026!" to "pottery". The feature involves straightforward text replacements across HTML, documentation, and configuration files.

## Research Tasks Completed

### 1. Locate All Title References

**Question**: Where does "Welcome to Tech Connect 2026!" appear in the codebase?

**Findings**:
- `frontend/index.html` line 7: `<title>Welcome to Tech Connect 2026!</title>`
- `frontend/e2e/ui.spec.ts` line 15: Test assertion checking for the title
- `frontend/src/App.tsx`: Does NOT contain the old title (verified)

**Decision**: Update HTML title tag and E2E test assertion.

**Rationale**: Search reveals only 2 locations that need updates in production code and tests.

**Alternatives Considered**: None - this is a direct text search requirement.

---

### 2. README Project Name Strategy

**Question**: How should the project be referenced in README.md?

**Findings**:
- Current README title: "# GitHub Projects Chat Interface"
- README contains descriptive text about the project but doesn't use "Welcome to Tech Connect 2026!"
- The README focuses on describing functionality rather than a brand name

**Decision**: Update README title to "# pottery" and replace "GitHub Projects Chat Interface" references with "pottery" where appropriate.

**Rationale**: The feature spec requires documentation consistency (FR-002) and the README title is the most prominent documentation element. The word "pottery" should replace the project name while preserving technical details about being a chat interface.

**Alternatives Considered**: 
- Keep "GitHub Projects Chat Interface" as subtitle → Rejected: Spec requires "pottery" as the project name
- Add "pottery" as subtitle → Rejected: Spec specifies "pottery" should be the primary title

---

### 3. Package Configuration Approach

**Question**: Which fields in package.json and pyproject.toml should be updated?

**Findings**:
- `frontend/package.json`:
  - Line 2: `"name": "github-projects-chat-frontend"` (package identifier)
  - No description field currently
- `backend/pyproject.toml`:
  - Line 2: `name = "github-projects-chat-backend"` (package identifier)
  - Line 4: `description = "FastAPI backend for GitHub Projects Chat Interface"`

**Decision**: 
- **DO NOT** change package `name` fields (preserve for backward compatibility per FR-005)
- **ADD** description to frontend/package.json: `"description": "pottery - A conversational DevOps interface"`
- **UPDATE** backend/pyproject.toml description to: `"pottery - FastAPI backend for conversational DevOps"`

**Rationale**: FR-005 explicitly requires preserving package identifiers. FR-004 requires updating human-readable descriptions. Adding/updating description fields achieves brand consistency while maintaining technical compatibility.

**Alternatives Considered**:
- Change package names → Rejected: Violates FR-005 backward compatibility requirement
- Leave descriptions unchanged → Rejected: Violates FR-004 metadata update requirement

---

### 4. Visual Identity Consistency

**Question**: Are there other title references in comments, documentation strings, or UI text?

**Findings**:
- Searched for "Tech Connect" and "Welcome to Tech Connect" in source code
- Found references only in test files and the spec files (which are documentation of old state)
- No hardcoded UI text elements display the old title beyond the HTML `<title>` tag

**Decision**: Limit changes to HTML title, test assertions, README, and package descriptions only.

**Rationale**: The spec assumptions state "No visual design changes (logos, styling, colors) are required - only text references". Search confirms no other user-facing text needs updating.

**Alternatives Considered**:
- Add "pottery" branding to UI header/footer → Rejected: Out of scope per spec assumptions
- Update code comments mentioning old title → Rejected: Comments are not user-facing (FR-003 specifies "visible references")

---

### 5. SEO and Meta Tags

**Question**: Should HTML meta tags be updated for "pottery"?

**Findings**:
- Current `frontend/index.html` has no meta description or og:title tags
- Only the `<title>` tag exists

**Decision**: Update only the `<title>` tag. Do not add new meta tags.

**Rationale**: FR-001 specifies updating the browser page title (the `<title>` element). Adding new meta tags would exceed the "smallest possible changes" principle and the spec's bounded scope of cosmetic text changes.

**Alternatives Considered**:
- Add comprehensive meta tags for SEO → Rejected: Out of scope, would violate minimal changes principle
- Add og:title for social sharing → Rejected: Not requested in spec, would add complexity

---

### 6. Backward Compatibility Verification

**Question**: Will changing the title break any existing functionality?

**Findings**:
- Title is purely presentational (browser tab display)
- No JavaScript code references `document.title`
- Package names remain unchanged
- No APIs or internal services reference the project title

**Decision**: Changes are safe and backward compatible.

**Rationale**: The browser title is not used programmatically. Package identifiers remain unchanged. No breaking changes possible.

**Alternatives Considered**: None - this is a verification task.

---

### 7. Test Update Strategy

**Question**: Which tests need updates and what should they verify?

**Findings**:
- `frontend/e2e/ui.spec.ts` line 15: `await expect(page).toHaveTitle('Welcome to Tech Connect 2026!');`
- This is the only test that validates the page title
- Test is straightforward - just updates expected string

**Decision**: Update E2E test to expect "pottery" instead of "Welcome to Tech Connect 2026!".

**Rationale**: SC-001 requires verifying the browser tab displays "pottery". The existing E2E test validates this requirement and just needs the expected value updated.

**Alternatives Considered**:
- Remove the test → Rejected: Would reduce test coverage
- Add new tests → Rejected: Existing test already covers the requirement

---

### 8. Documentation Impact Analysis

**Question**: What documentation files require updates beyond README?

**Findings**:
- Checked `.env.example`, `docker-compose.yml`, and other configuration files
- No references to "Welcome to Tech Connect 2026!" or project title in these files
- Documentation is centralized in README.md

**Decision**: Update only README.md for documentation changes.

**Rationale**: Comprehensive search shows README is the only documentation file referencing the project title.

**Alternatives Considered**: None - this is a search verification task.

---

### 9. Case Sensitivity Decision

**Question**: Should "pottery" be lowercase, Title Case, or UPPERCASE?

**Findings**:
- Spec assumptions explicitly state: "The primary user-facing brand name should be simply 'pottery' (lowercase, single word)"
- Spec FR-001 states: "System MUST display 'pottery' as the browser page title"

**Decision**: Use lowercase "pottery" in all locations (HTML title, README, package descriptions).

**Rationale**: Spec explicitly defines lowercase as the required format.

**Alternatives Considered**:
- "Pottery" (Title Case) → Rejected: Contradicts spec assumptions
- "POTTERY" (uppercase) → Rejected: Contradicts spec assumptions

---

### 10. Link and Reference Validation

**Question**: Are there internal links or references that will break after title changes?

**Findings**:
- README contains links to external documentation (GitHub docs, GitHub settings, etc.)
- No internal links reference the project title
- No anchor links depend on title text

**Decision**: No link updates required beyond text changes.

**Rationale**: FR-007 requires "no broken links or references result from title changes". Analysis confirms links are independent of title text.

**Alternatives Considered**: None - this is a validation task confirming no additional work needed.

---

## Summary of Decisions

| Decision | Value | Requirement Addressed |
|----------|-------|----------------------|
| HTML Title | "pottery" | FR-001, SC-001 |
| README Title | "# pottery" | FR-002, SC-002 |
| Frontend package.json | Add description field with "pottery" | FR-004, SC-003 |
| Backend pyproject.toml | Update description to include "pottery" | FR-004, SC-003 |
| Package identifiers | Keep unchanged | FR-005 |
| E2E Test | Update expected title to "pottery" | Test alignment with FR-001 |
| Case format | Lowercase "pottery" | Spec assumptions |
| Scope | 4 files total | SC-004, SC-005 |

## Technology Stack

**No new technologies or dependencies required.**

This feature uses only existing tools:
- Text editing (HTML, Markdown, JSON, TOML)
- Existing test frameworks (Playwright E2E tests)
- Standard repository structure (no changes)

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Breaking package references | Low | High | Preserve all package identifiers (name fields) unchanged |
| Test failures | Low | Low | Update test assertions to match new title |
| Inconsistent branding | Low | Medium | Use lowercase "pottery" consistently per spec |
| Broken links | Very Low | Medium | FR-007 verification confirms no link dependencies |

## Verification Checklist

- ✅ Located all references to old title in codebase
- ✅ Identified which package fields to preserve vs. update
- ✅ Confirmed backward compatibility approach
- ✅ Verified no broken links will result
- ✅ Determined case format (lowercase) from spec
- ✅ Identified test updates required
- ✅ Confirmed scope limited to 4 files
- ✅ Validated no new dependencies needed

## Next Steps (Phase 1)

1. Create data-model.md documenting the file change entities
2. Create contracts/ directory with detailed change specifications
3. Create quickstart.md with step-by-step implementation guide
4. Run update-agent-context.sh to update Copilot context
5. Re-evaluate Constitution Check post-design
