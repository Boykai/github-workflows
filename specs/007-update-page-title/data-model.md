# Data Model: Update Page Title to "Front"

**Feature**: 007-update-page-title | **Date**: 2026-02-19  
**Purpose**: Define entities and their relationships for feature implementation

## Model Overview

This feature involves no data model in the traditional sense (no database entities, API models, or state management). The "data" being changed consists of static string literals in presentation layer files. This document exists to satisfy Phase 1 requirements but is intentionally minimal due to the feature's lack of programmatic data structures.

## Entities

### Entity: ApplicationTitle

**Type**: Static String Literal (View Layer Only)  
**Purpose**: User-facing text identifying the application name  
**Lifecycle**: Compile-time constant embedded in HTML/JSX

**Attributes**:

| Attribute | Type | Constraints | Current Value | New Value |
|-----------|------|-------------|---------------|-----------|
| `htmlTitle` | `string` | Non-empty, < 100 chars | `"Agent Projects"` | `"Front"` |
| `loginTitle` | `string` | Non-empty, < 100 chars | `"Agent Projects"` | `"Front"` |
| `headerTitle` | `string` | Non-empty, < 100 chars | `"Agent Projects"` | `"Front"` |

**Locations**:
- `htmlTitle`: `frontend/index.html` line 7 (`<title>` element)
- `loginTitle`: `frontend/src/App.tsx` line 72 (`<h1>` in login view)
- `headerTitle`: `frontend/src/App.tsx` line 89 (`<h1>` in authenticated header)

**Validation Rules**:
1. **Non-empty**: Title must not be empty string
2. **Character constraints**: Valid Unicode text (no special validation for ASCII-only "Front")
3. **Length**: Reasonable length for browser tabs (< 100 chars; new value is 5 chars)
4. **Consistency**: All three instances should match for brand consistency (not programmatically enforced)

**State Transitions**: None — static values with no runtime changes

**Relationships**: None — no dependencies on other entities

---

## Entity Relationships

**Diagram**: N/A — single entity with no relationships

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
1. Browser tab displays "Front" (visual inspection)
2. Login page header displays "Front" (visual inspection)
3. Authenticated header displays "Front" (visual inspection)
4. No old title ("Agent Projects") references remain (codebase search)

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

## Security Considerations

**Threat Model**: None — static public strings with no user input or dynamic generation

- **No XSS risk**: Hardcoded strings, not user-generated content
- **No injection risk**: No dynamic SQL, shell commands, or template rendering
- **No authentication impact**: Title display is public information
- **No authorization impact**: No access control decisions based on title

---

## Phase 1 Data Model Completion Checklist

- [x] All entities identified (1 static entity: ApplicationTitle)
- [x] Entity attributes documented with current/new values
- [x] Validation rules defined (non-empty, length constraints)
- [x] Relationships documented (none — isolated strings)
- [x] Data flow described (source → build → display)
- [x] Security considerations addressed (no risks)
- [x] Alternative models evaluated (none needed — trivial change)

**Status**: ✅ **DATA MODEL COMPLETE** — Ready for contracts and quickstart generation
