# Data Model: App Title Update to 'GitHub Workflows'

**Feature**: 001-app-title-update | **Date**: 2026-02-14  
**Purpose**: Define entities and their relationships for feature implementation

## Model Overview

This feature involves no data model in the traditional sense (no database entities, API models, or state management). The "data" being changed consists of static string literals in presentation layer files. This document exists to satisfy Phase 1 requirements but is intentionally minimal due to feature's lack of programmatic data structures.

## Entities

### Entity: ApplicationTitle

**Type**: Static String Literal (View Layer Only)  
**Purpose**: User-facing text identifying the application name  
**Lifecycle**: Compile-time constant embedded in HTML/JSX

**Attributes**:

| Attribute | Type | Constraints | Current Value | New Value |
|-----------|------|-------------|---------------|-----------|
| `htmlTitle` | `string` | Non-empty, < 100 chars | `"Welcome to Tech Connect 2026!"` | `"GitHub Workflows"` |
| `headerTitle` | `string` | Non-empty, < 100 chars | `"Welcome to Tech Connect 2026!"` | `"GitHub Workflows"` |
| `loginTitle` | `string` | Non-empty, < 100 chars | `"Welcome to Tech Connect 2026!"` | `"GitHub Workflows"` |

**Locations**:
- `htmlTitle`: `frontend/index.html` line 7 (`<title>` element)
- `headerTitle`: `frontend/src/App.tsx` line 85 (`<h1>` in authenticated view)
- `loginTitle`: `frontend/src/App.tsx` line 69 (`<h1>` in login view)

**Validation Rules**:
1. **Non-empty**: Title must not be empty string
2. **Character constraints**: Valid Unicode text (no special validation for ASCII-only "GitHub Workflows")
3. **Length**: Reasonable length for browser tabs (< 100 chars; new value is 17 chars)
4. **Consistency**: All three instances should match for brand consistency (not programmatically enforced)

**State Transitions**: None - static values with no runtime changes

**Relationships**: None - no dependencies on other entities

---

## Entity Relationships

**Diagram**: N/A - single entity with no relationships

This feature modifies isolated string literals with no connections to:
- User data or session state
- Backend API models
- Database records
- Configuration objects
- Component props or state

---

## Data Validation

### Compile-Time Validation

- **TypeScript**: JSX string literals are type-checked as `string` (satisfied)
- **HTML**: `<title>` tag requires text content (satisfied)
- **Linter**: ESLint/Prettier format strings but don't enforce content rules

### Runtime Validation

None required. Titles are static strings with no user input or dynamic generation.

### Human Validation (Acceptance Criteria)

From spec.md acceptance scenarios:
1. Browser tab displays "GitHub Workflows" (visual inspection)
2. Authenticated header displays "GitHub Workflows" (visual inspection)
3. Login page header displays "GitHub Workflows" (visual inspection)
4. No old title references remain (codebase search)

---

## Data Storage

**Storage Mechanism**: Git repository source code  
**Format**: Plain text (HTML, TypeScript/TSX)  
**Persistence**: Version controlled via git  
**Backup**: GitHub remote repository  
**Encryption**: Not applicable (public source code)

---

## Data Flow

```
Developer edits source files
       ↓
Git commit with new title strings
       ↓
Vite build process (frontend)
       ↓
Static HTML + compiled React bundle
       ↓
Web server serves to browser
       ↓
Browser displays title in tab/header
```

**Flow Characteristics**:
- **Unidirectional**: Source → Build → Deploy → Display
- **No user input**: Users cannot change title (read-only display)
- **No persistence layer**: No database, localStorage, or cookies involved
- **No synchronization**: Title is not shared across users or sessions

---

## Data Constraints

### Technical Constraints

- **Browser title length**: Browsers truncate long titles with ellipsis (~50-100 chars depending on browser/OS)
- **Character encoding**: UTF-8 in HTML/JSX source files (standard)
- **HTML validation**: `<title>` must be within `<head>` element (already satisfied)

### Business Constraints

From spec.md requirements:
- **FR-001**: MUST display "GitHub Workflows" as browser page title
- **FR-002**: MUST display "GitHub Workflows" in main application header
- **FR-004**: MUST maintain title consistently across all pages
- **FR-005**: MUST remove/replace all previous title references

### Accessibility Constraints

- **WCAG 2.4.2**: Page title must describe topic/purpose (satisfied - "GitHub Workflows" describes app)
- **Screen readers**: Title must be announcements (HTML `<title>` is automatically announced)

---

## Data Migration

**Migration Type**: In-place string replacement  
**Rollback**: Git revert to previous commit  
**Data Loss Risk**: None - no user data involved  
**Backward Compatibility**: N/A - no API contracts or data formats

**Migration Steps**:
1. Replace string in `frontend/index.html`
2. Replace 2 strings in `frontend/src/App.tsx`
3. Commit changes
4. Deploy updated frontend

**No database migrations required** - this is a frontend-only change

---

## Security Considerations

**Threat Model**: None - static public strings with no user input or dynamic generation

**Security Properties**:
- **No XSS risk**: Hardcoded strings, not user-generated content
- **No injection risk**: No dynamic SQL, shell commands, or template rendering
- **No authentication impact**: Title display is public information
- **No authorization impact**: No access control decisions based on title

---

## Performance Characteristics

**Size Impact**:
- Old title: 29 chars (`"Welcome to Tech Connect 2026!"`)
- New title: 17 chars (`"GitHub Workflows"`)
- **Savings**: 12 bytes × 3 instances = 36 bytes total (negligible)

**Runtime Impact**:
- Title rendering: O(1) - single DOM text node update
- No performance degradation expected

**Memory Impact**: Negligible - string literal storage in compiled JavaScript

---

## Alternative Data Models Considered

### Alternative 1: Centralized Configuration

```typescript
// config/app.ts
export const APP_CONFIG = {
  title: "GitHub Workflows",
  version: "1.0.0"
};
```

**Rejected Rationale**: YAGNI violation. Adds unnecessary abstraction for single-use string. Future configurability is not a requirement.

### Alternative 2: Environment Variables

```bash
# .env
VITE_APP_TITLE="GitHub Workflows"
```

**Rejected Rationale**: Title is not environment-dependent (same in dev/staging/prod). Adds build-time complexity for no benefit.

### Alternative 3: i18n/Localization

```typescript
// locales/en.json
{
  "app.title": "GitHub Workflows"
}
```

**Rejected Rationale**: Spec explicitly states "No internationalization/localization is required" (Assumptions section).

---

## Phase 1 Data Model Completion Checklist

- [x] All entities identified (1 static entity: ApplicationTitle)
- [x] Entity attributes documented with current/new values
- [x] Validation rules defined (non-empty, length constraints)
- [x] Relationships documented (none - isolated strings)
- [x] Data flow described (source → build → display)
- [x] Storage mechanism identified (git source code)
- [x] Security considerations addressed (no risks)
- [x] Performance impact assessed (negligible)
- [x] Migration approach defined (string replacement)
- [x] Alternative models evaluated and rejected

**Status**: ✅ **DATA MODEL COMPLETE** - Ready for contracts and quickstart generation
