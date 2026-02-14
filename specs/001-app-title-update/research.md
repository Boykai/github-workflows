# Research: Update App Title to "GitHub Workflows"

**Feature**: 001-app-title-update  
**Phase**: 0 - Research & Technology Decisions  
**Date**: 2026-02-14

## Overview

This document captures technical decisions for updating the application title from "Welcome to Tech Connect 2026!" to "GitHub Workflows" in both browser tabs and UI headers.

## Technology Stack Analysis

### Current Implementation

**Frontend Framework**: React 18.3.1 with TypeScript  
**Build Tool**: Vite 5.4.0  
**State Management**: TanStack React Query v5  
**Testing**: Vitest + Playwright for E2E

**Current Title Locations**:
1. `frontend/index.html` (line 7): `<title>Welcome to Tech Connect 2026!</title>`
2. `frontend/src/App.tsx` (line 69): Login screen header
3. `frontend/src/App.tsx` (line 85): Main application header

## Research Decisions

### Decision 1: Document Title Management Approach

**Decision**: Use React's `useEffect` hook with direct `document.title` assignment

**Rationale**: 
- No additional dependencies needed (keeping the application simple)
- React 18 supports direct DOM manipulation in effects safely
- Standard pattern recommended by React documentation
- Maintains consistency with existing codebase patterns

**Alternatives Considered**:
- `react-helmet` or `react-helmet-async`: Rejected - adds unnecessary dependency for a simple title update
- Custom hook abstraction: Rejected - YAGNI principle, single location makes abstraction premature
- Static HTML only: Rejected - doesn't support dynamic title updates and SPA navigation

**Implementation Pattern**:
```typescript
useEffect(() => {
  document.title = "GitHub Workflows";
}, []);
```

### Decision 2: Component Location for Browser Title

**Decision**: Place `document.title` update in `App.tsx` component's main render path

**Rationale**:
- App.tsx is the root component, guarantees execution on all routes
- Single source of truth for application-wide title
- Executes once during initial render
- Consistent with React component lifecycle best practices

**Alternatives Considered**:
- `index.html` static title only: Rejected - doesn't guarantee consistency with dynamic UI
- Multiple locations per route: Rejected - violates DRY and FR-003 (consistency requirement)
- Separate TitleManager component: Rejected - over-engineering for single title

### Decision 3: Header Text Update Strategy

**Decision**: Replace hard-coded strings with "GitHub Workflows" constant

**Rationale**:
- Maintains existing component structure (no refactoring needed)
- Simple find-and-replace operation
- Preserves all existing functionality and styling
- Zero risk of breaking changes

**Alternatives Considered**:
- Extract to configuration file: Rejected - YAGNI, no requirement for configurability
- Create AppTitle component: Rejected - premature abstraction, no reuse benefits
- Use environment variables: Rejected - adds build complexity for static value

### Decision 4: Title Constant Definition

**Decision**: Define title as inline string literal in both locations

**Rationale**:
- Two locations only (not enough to justify extraction)
- No requirement for runtime configurability
- Keeps code simple and readable
- Easy to search and update if needed in future

**Alternatives Considered**:
- Shared constant file: Rejected - adds indirection for 2 uses
- Package.json name field: Rejected - couples UI to package metadata
- Environment variable: Rejected - unnecessary configuration complexity

### Decision 5: Testing Strategy

**Decision**: Manual browser verification only (no automated tests)

**Rationale**:
- Constitution Principle IV: Tests are optional by default
- Simple text change with visual verification
- No complex logic requiring unit tests
- Existing E2E tests can verify indirectly if needed

**Alternatives Considered**:
- Unit test for document.title: Rejected - brittle, mocks DOM unnecessarily
- E2E test with Playwright: Rejected - overkill for simple text verification
- Visual regression test: Rejected - no visual layout changes

### Decision 6: Browser Compatibility Verification

**Decision**: Use standard `document.title` property (universally supported)

**Rationale**:
- Supported in all browsers since IE4 (1997)
- No polyfills or fallbacks needed
- FR-004 requirement satisfied by default
- Zero compatibility risk

**Alternatives Considered**:
- Browser-specific title handling: Rejected - unnecessary complexity
- Fallback mechanisms: Rejected - no unsupported browsers exist

### Decision 7: Deployment Impact

**Decision**: No build configuration changes required

**Rationale**:
- Change is code-only (HTML + TypeScript)
- Vite build process handles automatically
- No new dependencies or build steps
- FR-005 requirement satisfied (no functionality impact)

**Alternatives Considered**:
- Update build scripts: Rejected - no changes needed
- Environment-specific titles: Rejected - out of scope

### Decision 8: Scope Adherence

**Decision**: Limit changes to index.html and App.tsx only

**Rationale**:
- Spec boundaries are clear (in-scope vs out-of-scope)
- No README, package.json, or metadata updates needed
- Minimal surface area reduces risk
- Aligns with "smallest possible changes" principle

**Alternatives Considered**:
- Update all documentation: Rejected - explicitly out of scope
- Change package name: Rejected - explicitly out of scope
- Update favicon/logo: Rejected - explicitly out of scope

## Implementation Summary

**Files to Modify**:
1. `frontend/index.html` - Update `<title>` tag (1 line)
2. `frontend/src/App.tsx` - Update 2 `<h1>` elements (2 lines)
3. `frontend/src/App.tsx` - Add `useEffect` for document.title (3 lines)

**Total Lines Changed**: ~6 lines

**Dependencies Added**: 0

**Risk Level**: Minimal (text-only changes)

**Testing Strategy**: Manual verification in browser

## Constitution Compliance

✅ **Specification-First**: All decisions traceable to spec requirements  
✅ **Template-Driven**: Following plan template structure  
✅ **Agent-Orchestrated**: Single-purpose research phase  
✅ **Test Optionality**: No tests needed for simple text change  
✅ **Simplicity/DRY**: Minimal changes, no premature abstraction
