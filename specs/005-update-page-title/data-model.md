# Data Model: Update Page Title to "Objects"

**Feature**: 005-update-page-title | **Date**: 2026-02-19  
**Purpose**: Define entities and their relationships for feature implementation

## Model Overview

This feature involves no data model in the traditional sense (no database entities, API models, or state management). The "data" being changed consists of static string literals in presentation layer files, backend configuration, and documentation. This document exists to satisfy Phase 1 requirements but is intentionally minimal due to the feature's lack of programmatic data structures.

## Entities

### Entity: ApplicationTitle

**Type**: Static String Literal (View + Config Layer)  
**Purpose**: User-facing and developer-facing text identifying the application name  
**Lifecycle**: Compile-time constant embedded in HTML/JSX/Python/Config

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
- `apiTitle`: `backend/src/main.py` line 85 (FastAPI title)
- `apiDescription`: `backend/src/main.py` line 86 (FastAPI description)
- `logStartup`: `backend/src/main.py` line 75 (startup log)
- `logShutdown`: `backend/src/main.py` line 77 (shutdown log)

**Validation Rules**:
1. **Non-empty**: Title must not be empty string
2. **Character constraints**: Valid Unicode text (no special validation for ASCII-only "Objects")
3. **Length**: Reasonable length for browser tabs (< 100 chars; new value is 7 chars)
4. **Consistency**: All user-facing instances should match for brand consistency (not programmatically enforced)

**State Transitions**: None — static values with no runtime changes

**Relationships**: None — no dependencies on other entities

---

## Entity Relationships

**Diagram**: N/A — single entity with no relationships

This feature modifies isolated string literals with no connections to:
- User data or session state
- Database records
- Configuration objects (beyond FastAPI metadata)
- Component props or state

---

## Data Flow

```
Developer edits source files
       ↓
Git commit with new title strings
       ↓
Vite build (frontend) + Python startup (backend)
       ↓
Static HTML + compiled React bundle + FastAPI app
       ↓
Web server serves to browser / API docs
       ↓
Browser displays title in tab/header; API docs display new title
```

**Flow Characteristics**:
- **Unidirectional**: Source → Build → Deploy → Display
- **No user input**: Users cannot change title (read-only display)
- **No persistence layer**: No database, localStorage, or cookies involved
- **No synchronization**: Title is not shared across users or sessions

---

## Data Constraints

### Technical Constraints

- **Browser title length**: Browsers truncate long titles with ellipsis (~50–100 chars); new value is 7 chars — well within limits
- **Character encoding**: UTF-8 in HTML/JSX/Python source files (standard)
- **HTML validation**: `<title>` must be within `<head>` element (already satisfied)

### Business Constraints

From spec.md requirements:
- **FR-001**: MUST display "Objects" as browser page title
- **FR-002**: MUST display "Objects" in main page heading/header
- **FR-003**: All navigation elements referencing the title MUST display "Objects"
- **FR-004**: Title change MUST NOT affect other labels/headings
- **FR-006**: All automated tests MUST be updated to expect "Objects"
- **FR-007**: Backend API metadata MUST also reflect "Objects"

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
- [x] Storage mechanism identified (git source code)
- [x] Security considerations addressed (no risks)
- [x] Performance impact assessed (negligible)
- [x] Migration approach defined (string replacement)

**Status**: ✅ **DATA MODEL COMPLETE** — Ready for contracts and quickstart generation
