# Data Model: Add Dollar Sign to Application Title

**Feature**: 003-dollar-app-title  
**Branch**: `copilot/add-dollar-sign-to-header`  
**Date**: 2026-02-16  
**Phase**: 1 (Design & Contracts)

## Overview

This document defines the data entities and their relationships for adding a dollar sign to the application title. Since this is a simple text modification feature, the "data model" captures the static string literals that will be updated and their validation rules.

## Entities

### Entity: ApplicationTitle

**Type**: Static String Literal (View Layer Only)  
**Purpose**: User-facing text identifying the application name in header and browser tab  
**Lifecycle**: Compile-time constant embedded in HTML/JSX

**Attributes**:

| Attribute | Type | Constraints | Current Value | New Value |
|-----------|------|-------------|---------------|-----------|
| `htmlTitle` | `string` | Non-empty, < 100 chars | `"Welcome to Tech Connect 2026!"` | `"$Welcome to Tech Connect 2026!"` |
| `loginHeaderTitle` | `string` | Non-empty, < 100 chars | `"Welcome to Tech Connect 2026!"` | `"$Welcome to Tech Connect 2026!"` |
| `authHeaderTitle` | `string` | Non-empty, < 100 chars | `"Welcome to Tech Connect 2026!"` | `"$Welcome to Tech Connect 2026!"` |

**Locations**:
- `htmlTitle`: `frontend/index.html` line 7 (`<title>` element inside `<head>`)
- `loginHeaderTitle`: `frontend/src/App.tsx` line 69 (`<h1>` in unauthenticated/login view)
- `authHeaderTitle`: `frontend/src/App.tsx` line 85 (`<h1>` in authenticated app header)

**Validation Rules**:
1. **Non-empty**: Title must not be empty string
2. **Character constraints**: Valid Unicode text (dollar sign $ is U+0024, standard ASCII)
3. **Length**: Reasonable length for browser tabs (< 100 chars; new value is 33 chars)
4. **Consistency**: All three instances should match for brand consistency (not programmatically enforced)
5. **Prefix format**: Dollar sign must be first character followed immediately by rest of title

**State Transitions**: None - static values with no runtime changes

**Relationships**: None - no dependencies on other entities

---

## Entity Relationships

**Diagram**: N/A - single entity with no relationships

This feature modifies isolated string literals with no connections to:
- User data or session state
- Backend API models or database records
- Configuration objects or environment variables
- Component props or state (titles are hardcoded)
- Theme or styling variables (CSS inheritance handles styling)

---

## Data Validation

### Compile-Time Validation

- **TypeScript**: JSX string literals are type-checked as `string` (satisfied)
- **HTML**: `<title>` tag requires text content (satisfied)
- **Linter**: ESLint/Prettier format strings but don't enforce content rules
- **Build**: Vite build process verifies HTML and JSX syntax

### Runtime Validation

None required. Titles are static strings with no user input, API calls, or dynamic generation.

### Human Validation (Acceptance Criteria)

From spec.md acceptance scenarios:
1. **SC-001**: Browser tab displays "$Welcome to Tech Connect 2026!" on first page load across all browsers
2. **SC-002**: Title displays correctly on screens from 320px mobile to 4K desktop
3. **SC-003**: Screen readers announce dollar sign as part of title
4. **SC-004**: Visual inspection confirms dollar sign styling matches title styling

---

## Data Flow

### Static Title Rendering Flow

```text
Build Time:
  index.html (line 7) → Browser <title> tag
  App.tsx (line 69) → React render → DOM <h1> (login view)
  App.tsx (line 85) → React render → DOM <h1> (authenticated view)

Runtime:
  User loads page → Browser reads <title> from HTML
  User sees login page → React renders App.tsx:69 <h1>
  User authenticates → React renders App.tsx:85 <h1>
  
  No state changes, no API calls, no data persistence
```

### CSS Styling Inheritance

```text
index.css (global styles)
  ↓
App.css (component styles)
  ↓
<h1> elements inherit: font-family, font-size, color, font-weight
  ↓
$ character inherits same styling automatically
```

---

## Data Constraints

### Technical Constraints

- **Browser title length**: Browsers truncate long titles with ellipsis (~50-100 chars depending on browser/OS)
  - Current: 31 chars → New: 32 chars (well under limit)
- **Character encoding**: UTF-8 in HTML/JSX source files (standard)
- **HTML validation**: `<title>` must be within `<head>` element (already satisfied)
- **JSX syntax**: `<h1>` must have text content (satisfied)

### Business Constraints

From spec.md requirements:
- **FR-001**: MUST display dollar sign ($) as part of the application title in header
- **FR-002**: MUST maintain consistent visual styling between $ and rest of title
- **FR-003**: MUST display correctly in desktop header layouts
- **FR-004**: MUST display correctly in mobile header layouts
- **FR-005**: MUST ensure $ is properly announced by screen readers
- **FR-006**: MUST preserve existing header functionality and layout

### Accessibility Constraints

- **WCAG 2.4.2**: Page title must describe topic/purpose (satisfied - financial app context added)
- **Screen readers**: Dollar sign must be announced (native support, no special ARIA needed)
- **Keyboard navigation**: No impact (titles are non-interactive text)

---

## Data Migration

**Migration Required**: No

This is a frontend static text change with no data persistence:
- No database schema changes
- No API contract changes
- No localStorage or sessionStorage changes
- No configuration file migrations

**Rollback**: Simple - revert the 3 string changes in index.html and App.tsx

---

## Data Security & Privacy

**Security Impact**: None

- No user input or data collection
- No API endpoints affected
- No authentication/authorization changes
- Dollar sign ($) is not a special character in HTML/JS (no XSS concerns)
- No sensitive information in title text

**Privacy Impact**: None

- No PII in titles
- No tracking or analytics changes required
- Browser tab title is already public/visible

---

## Data Testing Strategy

### Manual Verification

1. **Visual inspection**: Open app in browser, verify $ appears in all 3 locations
2. **Responsive testing**: Resize browser window, verify $ remains visible and styled
3. **Cross-browser**: Test in Chrome, Firefox, Safari, Edge
4. **Screen reader**: Test with screen reader (optional), verify $ is announced

### Automated Testing

- **E2E tests**: Existing Playwright tests in `frontend/e2e/ui.spec.ts` will need updates to expect new title text
- **Unit tests**: Not applicable for static strings
- **Integration tests**: Not applicable (no API/service integration)

### Test Data

No test data required. Title strings are hardcoded constants.

---

## Performance Considerations

**Performance Impact**: Negligible

- Adding 1 character to 3 strings has no measurable performance impact
- No additional network requests
- No computational overhead
- No bundle size increase (1 byte × 3 = 3 bytes)

**Rendering Performance**:
- Browser title: Instant (static HTML)
- React headers: Part of existing render cycle (no additional renders)

---

## Edge Cases & Error Handling

### Edge Cases from Spec

1. **Custom browser zoom** (50%-200%): Dollar sign will scale with rest of title text (CSS inheritance)
2. **Different system fonts**: $ glyph is present in all standard fonts (ASCII character)
3. **Browser extensions modifying styles**: Out of control/scope; same behavior as rest of title
4. **Custom CSS user styles**: Out of control/scope; same behavior as rest of title

### Error Scenarios

None applicable. Static text cannot fail at runtime.

### Fallback Behavior

No fallback needed. If $ character somehow failed to render (impossible in modern browsers), rest of title would still display.

---

## Future Considerations

### Potential Extensions (Out of Current Scope)

1. **Dynamic title**: Make title configurable via environment variable
2. **Localization**: Support different currency symbols for international users (€, £, ¥)
3. **Theme-specific icons**: Add currency icon that changes with theme
4. **Animation**: Add subtle animation to $ on page load

These are explicitly NOT part of this feature per spec boundaries.

---

## References

- **Feature Spec**: `specs/003-dollar-app-title/spec.md`
- **Research**: `specs/003-dollar-app-title/research.md`
- **Current Implementation**:
  - `frontend/index.html` line 7
  - `frontend/src/App.tsx` lines 69, 85
- **Related Past Feature**: `specs/001-app-title-update/` (changed title to "Welcome to Tech Connect 2026!")
