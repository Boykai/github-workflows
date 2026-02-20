# Data Model: Update App Title to "Happy Place"

**Feature**: 005-update-app-title | **Date**: 2026-02-20  
**Purpose**: Define entities and their relationships for feature implementation

## Model Overview

This feature involves no data model in the traditional sense (no database entities, API models, or state management). The "data" being changed consists of static string literals across presentation, configuration, and documentation files. This document exists to satisfy Phase 1 requirements and provides a complete inventory of all change locations.

## Entities

### Entity: ApplicationTitle

**Type**: Static String Literal (View Layer + Configuration)  
**Purpose**: User-facing text identifying the application name  
**Lifecycle**: Compile-time constant embedded in HTML/JSX/Python/Config files

**Attributes — Frontend (User-Facing)**:

| Attribute | File | Line | Current Value | New Value |
|-----------|------|------|---------------|-----------|
| `htmlTitle` | `frontend/index.html` | 7 | `Agent Projects` | `Happy Place` |
| `loginHeader` | `frontend/src/App.tsx` | 72 | `Agent Projects` | `Happy Place` |
| `authHeader` | `frontend/src/App.tsx` | 89 | `Agent Projects` | `Happy Place` |

**Attributes — E2E Test Assertions**:

| Attribute | File | Line | Current Value | New Value |
|-----------|------|------|---------------|-----------|
| `authTest1` | `frontend/e2e/auth.spec.ts` | 12 | `'Agent Projects'` | `'Happy Place'` |
| `authTest2` | `frontend/e2e/auth.spec.ts` | 24 | `'Agent Projects'` | `'Happy Place'` |
| `authTest3` | `frontend/e2e/auth.spec.ts` | 38 | `'Agent Projects'` | `'Happy Place'` |
| `authTitleTest` | `frontend/e2e/auth.spec.ts` | 62 | `/Agent Projects/i` | `/Happy Place/i` |
| `authTest4` | `frontend/e2e/auth.spec.ts` | 99 | `'Agent Projects'` | `'Happy Place'` |
| `uiTest1` | `frontend/e2e/ui.spec.ts` | 43 | `'Agent Projects'` | `'Happy Place'` |
| `uiTest2` | `frontend/e2e/ui.spec.ts` | 67 | `'Agent Projects'` | `'Happy Place'` |
| `integTest1` | `frontend/e2e/integration.spec.ts` | 69 | `'Agent Projects'` | `'Happy Place'` |

**Attributes — Backend Metadata**:

| Attribute | File | Line | Current Value | New Value |
|-----------|------|------|---------------|-----------|
| `apiStartLog` | `backend/src/main.py` | 75 | `Starting Agent Projects API` | `Starting Happy Place API` |
| `apiStopLog` | `backend/src/main.py` | 77 | `Shutting down Agent Projects API` | `Shutting down Happy Place API` |
| `apiTitle` | `backend/src/main.py` | 85 | `Agent Projects API` | `Happy Place API` |
| `apiDesc` | `backend/src/main.py` | 86 | `REST API for Agent Projects` | `REST API for Happy Place` |

**Attributes — Configuration & Documentation**:

| Attribute | File | Line | Current Value | New Value |
|-----------|------|------|---------------|-----------|
| `containerName` | `.devcontainer/devcontainer.json` | 2 | `Agent Projects` | `Happy Place` |
| `setupEcho` | `.devcontainer/post-create.sh` | 7 | `Setting up Agent Projects development environment` | `Setting up Happy Place development environment` |
| `envComment` | `.env.example` | 2 | `Agent Projects - Environment Configuration` | `Happy Place - Environment Configuration` |
| `readmeTitle` | `README.md` | 1 | `# Agent Projects` | `# Happy Place` |
| `backendTitle` | `backend/README.md` | 1 | `# Agent Projects — Backend` | `# Happy Place — Backend` |
| `backendDesc` | `backend/README.md` | 3 | `...powers Agent Projects and the...` | `...powers Happy Place and the...` |
| `pyprojectDesc` | `backend/pyproject.toml` | 4 | `FastAPI backend for Agent Projects` | `FastAPI backend for Happy Place` |

**Attributes — Code Comments**:

| Attribute | File | Line | Current Value | New Value |
|-----------|------|------|---------------|-----------|
| `apiComment` | `frontend/src/services/api.ts` | 2 | `API client service for Agent Projects` | `API client service for Happy Place` |
| `typesComment` | `frontend/src/types/index.ts` | 2 | `TypeScript types for Agent Projects API` | `TypeScript types for Happy Place API` |
| `testComment` | `backend/tests/test_api_e2e.py` | 2 | `...tests for the Agent Projects Backend` | `...tests for the Happy Place Backend` |

**Validation Rules**:
1. **Non-empty**: Title must not be empty string
2. **Exact casing**: Must be exactly "Happy Place" (title case, capital H and P) per FR-008
3. **Consistency**: All instances should use the same casing and spelling
4. **Character constraints**: ASCII-only, no encoding concerns

**State Transitions**: None — static values with no runtime changes

**Relationships**: None — no dependencies on other entities

---

## Entity Relationships

**Diagram**: N/A — single entity with no relationships

This feature modifies isolated string literals with no connections to:
- User data or session state
- Database records
- API request/response models
- Component props or state
- Configuration objects beyond cosmetic naming

---

## Data Validation

### Compile-Time Validation

- **TypeScript**: JSX string literals are type-checked as `string` (satisfied)
- **HTML**: `<title>` tag requires text content (satisfied)
- **Python**: String literals in FastAPI config are type-checked (satisfied)
- **Linter**: ESLint/Prettier/Ruff format strings but don't enforce content rules

### Runtime Validation

None required. Titles are static strings with no user input or dynamic generation.

### Human Validation (Acceptance Criteria)

From spec.md acceptance scenarios:
1. Browser tab displays "Happy Place" (visual inspection)
2. Login page header displays "Happy Place" (visual inspection)
3. Authenticated header displays "Happy Place" (visual inspection)
4. No old title "Agent Projects" references remain (codebase search)
5. E2E tests pass with updated assertions

---

## Data Flow

```
Developer edits source files (replace "Agent Projects" → "Happy Place")
       ↓
Git commit with new title strings
       ↓
Frontend: Vite build → Static HTML + React bundle
Backend: FastAPI reads config at startup
       ↓
Web server serves to browser / API serves OpenAPI docs
       ↓
Browser displays title in tab + headers
API docs display "Happy Place API"
```

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
- [x] Complete inventory of all change locations (21+ occurrences across 14 files)
- [x] Current and new values documented for each location
- [x] Validation rules defined (exact casing, non-empty)
- [x] Relationships documented (none — isolated strings)
- [x] Data flow described (source → build → display)
- [x] Security considerations addressed (no risks)
- [x] File/line references provided for implementation

**Status**: ✅ **DATA MODEL COMPLETE** - Ready for contracts and quickstart generation
