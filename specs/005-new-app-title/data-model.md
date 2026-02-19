# Data Model: Update App Title to "New App"

**Feature**: 005-new-app-title | **Date**: 2026-02-19  
**Purpose**: Define entities and their relationships for feature implementation

## Model Overview

This feature involves no data model in the traditional sense (no database entities, API models, or state management). The "data" being changed consists of static string literals in presentation layer files, backend metadata, configuration, and documentation. This document exists to satisfy Phase 1 requirements but is intentionally minimal due to feature's lack of programmatic data structures.

## Entities

### Entity: ApplicationTitle

**Type**: Static String Literal (View Layer + Configuration)  
**Purpose**: User-facing and developer-facing text identifying the application name  
**Lifecycle**: Compile-time/runtime constant embedded in HTML, JSX, Python, config files, and docs

**Attributes**:

| Attribute | Type | Constraints | Current Value | New Value |
|-----------|------|-------------|---------------|-----------|
| `htmlTitle` | `string` | Non-empty, < 100 chars | `"Agent Projects"` | `"New App"` |
| `loginHeaderTitle` | `string` | Non-empty, < 100 chars | `"Agent Projects"` | `"New App"` |
| `authenticatedHeaderTitle` | `string` | Non-empty, < 100 chars | `"Agent Projects"` | `"New App"` |
| `apiTitle` | `string` | Non-empty | `"Agent Projects API"` | `"New App API"` |
| `apiDescription` | `string` | Non-empty | `"REST API for Agent Projects"` | `"REST API for New App"` |
| `backendPackageName` | `string` | kebab-case | `"agent-projects-backend"` | `"new-app-backend"` |
| `backendPackageDesc` | `string` | Non-empty | `"FastAPI backend for Agent Projects"` | `"FastAPI backend for New App"` |
| `frontendPackageName` | `string` | kebab-case | `"agent-projects-frontend"` | `"new-app-frontend"` |
| `containerName` | `string` | Non-empty | `"Agent Projects"` | `"New App"` |
| `readmeHeading` | `string` | Non-empty | `"# Agent Projects"` | `"# New App"` |
| `backendReadmeHeading` | `string` | Non-empty | `"# Agent Projects — Backend"` | `"# New App — Backend"` |

**Locations**:
- `htmlTitle`: `frontend/index.html` line 7 (`<title>` element)
- `loginHeaderTitle`: `frontend/src/App.tsx` line 72 (`<h1>` in login view)
- `authenticatedHeaderTitle`: `frontend/src/App.tsx` line 89 (`<h1>` in authenticated view)
- `apiTitle`: `backend/src/main.py` line 85
- `apiDescription`: `backend/src/main.py` line 86
- `backendPackageName`: `backend/pyproject.toml` line 2
- `backendPackageDesc`: `backend/pyproject.toml` line 4
- `frontendPackageName`: `frontend/package.json`
- `containerName`: `.devcontainer/devcontainer.json` line 2
- `readmeHeading`: `README.md` line 1
- `backendReadmeHeading`: `backend/README.md` line 1

**Validation Rules**:
1. **Non-empty**: Title must not be empty string
2. **Character constraints**: Valid Unicode text (no special validation for ASCII-only "New App")
3. **Length**: Reasonable length for browser tabs (< 100 chars; new value is 7 chars)
4. **Consistency**: All user-facing instances should display "New App" for brand consistency

**State Transitions**: None - static values with no runtime changes

**Relationships**: None - no dependencies on other entities

---

## Entity Relationships

**Diagram**: N/A - single entity with no relationships

This feature modifies isolated string literals with no connections to:
- User data or session state
- Backend API models (beyond metadata)
- Database records
- Component props or state

---

## Data Validation

### Compile-Time Validation

- **TypeScript**: JSX string literals are type-checked as `string` (satisfied)
- **HTML**: `<title>` tag requires text content (satisfied)
- **Python**: FastAPI string parameters are validated at startup (satisfied)
- **TOML**: String values validated by parser (satisfied)

### Runtime Validation

None required. Titles are static strings with no user input or dynamic generation.

### Human Validation (Acceptance Criteria)

From spec.md acceptance scenarios:
1. Browser tab displays "New App" (visual inspection)
2. Authenticated header displays "New App" (visual inspection)
3. Login page header displays "New App" (visual inspection)
4. No old title ("Agent Projects") references remain (codebase search)
5. Configuration and manifest files updated (file inspection)

---

## Data Flow

```
Developer edits source files
       ↓
Git commit with new title strings
       ↓
Vite build process (frontend) + Python startup (backend)
       ↓
Static HTML + compiled React bundle + FastAPI metadata
       ↓
Web server serves to browser / API docs
       ↓
Browser displays title in tab/header; API docs show new title
```

**Flow Characteristics**:
- **Unidirectional**: Source → Build → Deploy → Display
- **No user input**: Users cannot change title (read-only display)
- **No persistence layer**: No database, localStorage, or cookies involved
- **No synchronization**: Title is not shared across users or sessions

---

## Security Considerations

**Threat Model**: None - static public strings with no user input or dynamic generation

**Security Properties**:
- **No XSS risk**: Hardcoded strings, not user-generated content
- **No injection risk**: No dynamic SQL, shell commands, or template rendering
- **No authentication impact**: Title display is public information
- **No authorization impact**: No access control decisions based on title

---

## Alternative Data Models Considered

### Alternative 1: Centralized Configuration

```typescript
// config/app.ts
export const APP_CONFIG = {
  title: "New App",
  version: "1.0.0"
};
```

**Rejected Rationale**: YAGNI violation. Adds unnecessary abstraction for single-use string. Future configurability is not a requirement.

### Alternative 2: Environment Variables

```bash
# .env
VITE_APP_TITLE="New App"
```

**Rejected Rationale**: Title is not environment-dependent (same in dev/staging/prod). Adds build-time complexity for no benefit.

---

## Phase 1 Data Model Completion Checklist

- [x] All entities identified (1 static entity: ApplicationTitle)
- [x] Entity attributes documented with current/new values
- [x] Validation rules defined (non-empty, length constraints)
- [x] Relationships documented (none - isolated strings)
- [x] Data flow described (source → build → display)
- [x] Storage mechanism identified (git source code)
- [x] Security considerations addressed (no risks)
- [x] Alternative models evaluated and rejected

**Status**: ✅ **DATA MODEL COMPLETE** - Ready for contracts and quickstart generation
