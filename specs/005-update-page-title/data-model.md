# Data Model: Update Page Title to "Objects"

**Feature**: 005-update-page-title | **Date**: 2026-02-19  
**Purpose**: Define entities and their relationships for feature implementation

## Model Overview

This feature involves no data model in the traditional sense (no database entities, API models, or state management). The "data" being changed consists of static string literals across presentation layer files, backend configuration, tests, and documentation. This document exists to satisfy Phase 1 requirements but is intentionally minimal due to the feature's lack of programmatic data structures.

## Entities

### Entity: ApplicationTitle

**Type**: Static String Literal (Cross-Stack)  
**Purpose**: User-facing and developer-facing text identifying the application name  
**Lifecycle**: Compile-time constant embedded in HTML/JSX/Python source

**Attributes**:

| Attribute | Type | Constraints | Current Value | New Value |
|-----------|------|-------------|---------------|-----------|
| `htmlTitle` | `string` | Non-empty, < 100 chars | `"Agent Projects"` | `"Objects"` |
| `loginHeaderTitle` | `string` | Non-empty, < 100 chars | `"Agent Projects"` | `"Objects"` |
| `appHeaderTitle` | `string` | Non-empty, < 100 chars | `"Agent Projects"` | `"Objects"` |
| `apiTitle` | `string` | Non-empty | `"Agent Projects API"` | `"Objects API"` |
| `apiDescription` | `string` | Non-empty | `"REST API for Agent Projects"` | `"REST API for Objects"` |
| `logStartup` | `string` | Non-empty | `"Starting Agent Projects API"` | `"Starting Objects API"` |
| `logShutdown` | `string` | Non-empty | `"Shutting down Agent Projects API"` | `"Shutting down Objects API"` |

**Locations**:
- `htmlTitle`: `frontend/index.html` line 7 (`<title>` element)
- `loginHeaderTitle`: `frontend/src/App.tsx` line 72 (`<h1>` in login view)
- `appHeaderTitle`: `frontend/src/App.tsx` line 89 (`<h1>` in authenticated view)
- `apiTitle`: `backend/src/main.py` line 85 (FastAPI title parameter)
- `apiDescription`: `backend/src/main.py` line 86 (FastAPI description parameter)
- `logStartup`: `backend/src/main.py` line 75 (logger.info call)
- `logShutdown`: `backend/src/main.py` line 77 (logger.info call)

**Validation Rules**:
1. **Non-empty**: Title must not be empty string
2. **Character constraints**: Valid Unicode text (no special validation for ASCII-only "Objects")
3. **Length**: Reasonable length for browser tabs (< 100 chars; new value is 7 chars)
4. **Consistency**: All user-facing instances should display "Objects" for brand consistency

**State Transitions**: None — static values with no runtime changes

**Relationships**: None — no dependencies on other entities

---

## Entity Relationships

**Diagram**: N/A — single entity with no relationships

This feature modifies isolated string literals with no connections to:
- User data or session state
- Database records
- Component props or state
- Dynamic configuration objects

---

## Data Validation

### Compile-Time Validation

- **TypeScript**: JSX string literals are type-checked as `string` (satisfied)
- **HTML**: `<title>` tag requires text content (satisfied)
- **Python**: String literals in FastAPI configuration are type-safe (satisfied)
- **Linter**: ESLint/Prettier format strings but don't enforce content rules

### Runtime Validation

None required. Titles are static strings with no user input or dynamic generation.

### Human Validation (Acceptance Criteria)

From spec.md acceptance scenarios:
1. Browser tab displays "Objects" (visual inspection)
2. Login page header displays "Objects" (visual inspection)
3. Authenticated header displays "Objects" (visual inspection)
4. No old title references remain (codebase search)
5. All navigation elements display "Objects" (visual inspection)

---

## Data Storage

**Storage Mechanism**: Git repository source code  
**Format**: Plain text (HTML, TypeScript/TSX, Python, TOML, JSON, Markdown, Shell)  
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
Vite build process (frontend) + uvicorn startup (backend)
       ↓
Static HTML + compiled React bundle + running API
       ↓
Browser displays title in tab/header; API returns title in OpenAPI docs
```

**Flow Characteristics**:
- **Unidirectional**: Source → Build → Deploy → Display
- **No user input**: Users cannot change title (read-only display)
- **No persistence layer**: No database, localStorage, or cookies involved
- **No synchronization**: Title is not shared across users or sessions

---

## Phase 1 Data Model Completion Checklist

- [x] All entities identified (1 static entity: ApplicationTitle)
- [x] Entity attributes documented with current/new values
- [x] Validation rules defined (non-empty, length constraints)
- [x] Relationships documented (none — isolated strings)
- [x] Data flow described (source → build → display)
- [x] Storage mechanism identified (git source code)
- [x] Security considerations addressed (no risks — static public strings)
- [x] Performance impact assessed (negligible — shorter string)
- [x] Migration approach defined (string replacement)

**Status**: ✅ **DATA MODEL COMPLETE** - Ready for contracts and quickstart generation
