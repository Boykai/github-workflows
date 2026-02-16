# Research & Technical Decisions: Add Dollar Sign to Application Title

**Feature**: 003-dollar-app-title  
**Branch**: `copilot/add-dollar-sign-to-header`  
**Date**: 2026-02-16  
**Phase**: 0 (Outline & Research)

## Overview

This document captures all research findings and technical decisions for adding a dollar sign ($) prefix to the application title. The research phase resolves unknowns from the Technical Context and establishes best practices for implementation.

## Research Tasks

### 1. Dollar Sign Placement Decision

**Question**: Should the dollar sign be placed before or after the app title?

**Research Findings**:
- Financial app conventions (Mint, Personal Capital, YNAB) consistently place currency symbols as prefixes
- Spec assumption states: "Based on common financial app conventions, the dollar sign will be placed at the beginning of the title (prefix position)"
- Prefix placement ($App Name) is more readable and immediately communicates financial context
- Screen readers naturally announce symbols in prefix position

**Decision**: Place dollar sign as prefix before the title text

**Rationale**: Follows industry conventions for financial applications and improves immediate brand recognition. Prefix position ensures the financial context is communicated first.

**Alternatives Considered**:
- Suffix position (App Name$) - Rejected: Less conventional, financial context not immediately apparent
- Parenthetical (App Name ($)) - Rejected: Too verbose, reduces visual impact

---

### 2. Dollar Sign Styling Approach

**Question**: How should the dollar sign be styled to match existing title styling?

**Research Findings**:
- Current title in App.tsx uses standard `<h1>` tag with no inline styles
- Styling is inherited from CSS (App.css, index.css)
- No special treatment needed for the $ character - it will inherit font-family, size, color, and weight automatically
- Typography: Dollar sign is a standard character in all web fonts, no compatibility concerns

**Decision**: No special styling required - use plain text dollar sign within existing `<h1>` tags

**Rationale**: Simplest approach that maintains consistency. The $ character will automatically inherit all h1 styling properties.

**Alternatives Considered**:
- Wrap $ in `<span>` with specific styling - Rejected: Unnecessary complexity, no benefit
- Use dollar sign emoji or icon - Rejected: Spec requires text-based dollar sign for accessibility

---

### 3. Accessibility Implementation

**Question**: How to ensure screen readers properly announce the dollar sign?

**Research Findings**:
- Screen readers (NVDA, JAWS, VoiceOver) announce "$" as "dollar sign" or "dollar" by default
- No aria-label needed - plain text in `<h1>` is naturally accessible
- HTML `<title>` element is automatically read by screen readers when page loads
- FR-005 requirement: "System MUST ensure the dollar sign is properly announced by screen readers as part of the title text"

**Decision**: Use plain text dollar sign with no special ARIA attributes

**Rationale**: Screen readers handle currency symbols natively. Adding ARIA labels could cause duplicate announcements or confusion.

**Alternatives Considered**:
- Add aria-label="Dollar Welcome to Tech Connect 2026" - Rejected: Overrides native behavior, unnecessary
- Use aria-hidden="true" on $ with descriptive text - Rejected: Violates accessibility by hiding content

---

### 4. Responsive Design Considerations

**Question**: Will the dollar sign display properly across mobile and desktop layouts?

**Research Findings**:
- Current title spans from 320px mobile to 4K desktop without issues
- Dollar sign adds only 1 character - minimal impact on title width
- CSS uses fluid layouts and responsive font sizing (if applicable)
- No media queries or breakpoint changes needed

**Decision**: No responsive design changes required

**Rationale**: Adding one character has negligible impact on layout. Existing responsive design handles title text width.

**Alternatives Considered**:
- Add mobile-specific styling for $ - Rejected: Unnecessary, no layout issues predicted
- Reduce font-size on mobile to accommodate $ - Rejected: Character addition doesn't warrant size reduction

---

### 5. Browser Compatibility

**Question**: Does the dollar sign character render consistently across browsers?

**Research Findings**:
- Dollar sign ($, U+0024) is part of ASCII and universally supported
- All target browsers (Chrome, Firefox, Safari, Edge) render $ identically
- UTF-8 encoding in HTML and TypeScript source files ensures proper character handling
- No polyfills or fallbacks needed

**Decision**: Use standard dollar sign character ($) with UTF-8 encoding

**Rationale**: Dollar sign is a universal character with 100% browser support. No compatibility concerns.

**Alternatives Considered**:
- HTML entity `&#36;` - Rejected: Unnecessary encoding, plain $ is more readable in source
- Unicode escape in JSX - Rejected: Over-engineering for a standard character

---

### 6. Testing Strategy

**Question**: What testing approach is needed to verify the dollar sign changes?

**Research Findings**:
- Existing E2E tests (frontend/e2e/ui.spec.ts) verify page title and header content
- Tests use text matchers that will catch the title change
- Spec acceptance criteria (SC-001 through SC-004) focus on visual verification
- No new test infrastructure needed - existing Playwright tests will validate changes

**Decision**: Rely on existing E2E tests; no new test files required

**Rationale**: Tests not explicitly required by spec (per constitution IV. Test Optionality). Existing tests will naturally verify the updated titles.

**Alternatives Considered**:
- Add unit tests for title text - Rejected: Static strings don't warrant unit tests
- Add accessibility-specific tests - Rejected: Out of scope, would require new testing tools (axe-core)

---

### 7. Cross-Browser Font Rendering

**Question**: Do different system fonts affect dollar sign appearance?

**Research Findings**:
- Default browser fonts (system-ui, sans-serif) all include well-formed dollar signs
- CSS font-family inheritance ensures consistency with existing title styling
- No custom web fonts appear to be loaded for titles (based on index.css patterns)
- Edge case consideration from spec: "How does the dollar sign display with different system fonts?"

**Decision**: Accept default system font rendering; no font-specific adjustments

**Rationale**: System fonts are designed for consistency. Dollar sign is a common glyph with good rendering across fonts.

**Alternatives Considered**:
- Force specific font for dollar sign - Rejected: Would create inconsistency with rest of title
- Add font-variant-numeric CSS - Rejected: Applies to numbers, not currency symbols

---

### 8. HTML Character Encoding

**Question**: How should the dollar sign be encoded in HTML and JSX?

**Research Findings**:
- HTML file (index.html) uses `<meta charset="UTF-8" />` declaration
- TypeScript/JSX files are UTF-8 by default in modern tooling (Vite)
- Dollar sign can be written directly as `$` in both HTML and JSX
- No escaping needed - $ is not a special character in HTML or JSX syntax

**Decision**: Use literal `$` character in all source files

**Rationale**: Most readable and maintainable approach. UTF-8 encoding handles the character natively.

**Alternatives Considered**:
- HTML entity `&dollar;` - Rejected: Not a standard entity, won't work
- Hex escape `\x24` - Rejected: Reduces code readability for no benefit

---

### 9. SEO and Metadata Impact

**Question**: Does adding a dollar sign to the page title affect SEO?

**Research Findings**:
- Search engines (Google, Bing) index special characters in `<title>` tags
- Currency symbols in titles are common and don't negatively impact SEO
- Title length remains well under 60-character recommendation (< 30 chars after change)
- No Open Graph or Twitter Card meta tags to update (if they exist, would need updating)

**Decision**: No SEO-specific changes required beyond the title update

**Rationale**: Dollar sign in title is SEO-neutral. Character count remains optimal.

**Alternatives Considered**:
- Add dollar sign to meta description - Rejected: Out of scope, no meta description tag present
- Create separate SEO title without $ - Rejected: Inconsistent branding, unnecessary complexity

---

### 10. Change Scope Boundaries

**Question**: Where should the dollar sign be added, and what's explicitly out of scope?

**Research Findings**:
- Spec identifies 3 locations: HTML `<title>` (index.html:7), login header (App.tsx:69), authenticated header (App.tsx:85)
- Current title: "Welcome to Tech Connect 2026!"
- New title: "$Welcome to Tech Connect 2026!" (prefix position)
- Backend API, README, package.json, or documentation not mentioned in spec

**Decision**: Update only the 3 frontend user-facing title instances

**Rationale**: Spec functional requirements (FR-001 through FR-006) explicitly scope to header and browser title. Other files out of scope.

**Alternatives Considered**:
- Update README.md title - Rejected: Out of scope per spec boundaries
- Update package.json "name" field - Rejected: Technical artifact, not user-facing
- Add $ to backend API responses - Rejected: No backend title exposure in spec

---

## Research Summary

All research tasks completed successfully. No blocking issues identified. Key findings:

1. **Simple implementation**: Plain text dollar sign prefix with no special styling or encoding
2. **Zero breaking changes**: Existing responsive design, accessibility, and browser compatibility maintained
3. **No new dependencies**: All changes use existing HTML/React/CSS capabilities
4. **Testing coverage**: Existing E2E tests will validate changes naturally

## Next Steps

Proceed to Phase 1:
- Generate data-model.md (title entity and attributes)
- Generate contracts/ (3 file modification contracts)
- Generate quickstart.md (step-by-step implementation guide)
- Run update-agent-context.sh copilot
- Re-evaluate Constitution Check post-design
