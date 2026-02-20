# File Change Contracts: Update App Title to "Happy Place"

**Feature**: 005-update-app-title | **Date**: 2026-02-20  
**Purpose**: Define the contract for all file changes required by this feature

## Overview

This feature requires no API contract changes (no new endpoints, no schema changes, no request/response modifications). All changes are string replacements within existing files. This document serves as the change manifest — the contract between the plan and implementation phases.

## Change Contract

### Contract 1: Frontend User-Facing Title (P1)

**Files**: `frontend/index.html`, `frontend/src/App.tsx`  
**Change Type**: String replacement  
**Old Value**: `Agent Projects`  
**New Value**: `Happy Place`  
**Occurrences**: 3 (1 in index.html, 2 in App.tsx)

**Verification**: 
- Open app in browser → tab shows "Happy Place"
- Login page header shows "Happy Place"
- Authenticated page header shows "Happy Place"

---

### Contract 2: E2E Test Assertions (P1)

**Files**: `frontend/e2e/auth.spec.ts`, `frontend/e2e/ui.spec.ts`, `frontend/e2e/integration.spec.ts`  
**Change Type**: Test assertion string replacement  
**Old Value**: `Agent Projects` (and `/Agent Projects/i` regex)  
**New Value**: `Happy Place` (and `/Happy Place/i` regex)  
**Occurrences**: 8 (5 in auth.spec.ts, 2 in ui.spec.ts, 1 in integration.spec.ts)

**Verification**: All E2E tests pass with updated assertions

---

### Contract 3: Backend API Metadata (P2)

**File**: `backend/src/main.py`  
**Change Type**: FastAPI config and logger string replacement  
**Changes**:
- `title="Agent Projects API"` → `title="Happy Place API"`
- `description="REST API for Agent Projects"` → `description="REST API for Happy Place"`
- `"Starting Agent Projects API"` → `"Starting Happy Place API"`
- `"Shutting down Agent Projects API"` → `"Shutting down Happy Place API"`  
**Occurrences**: 4

**Verification**: FastAPI OpenAPI docs at `/docs` show "Happy Place API"

---

### Contract 4: Configuration Files (P2)

**Files**: `.devcontainer/devcontainer.json`, `.devcontainer/post-create.sh`, `.env.example`, `backend/pyproject.toml`  
**Change Type**: String replacement in config/metadata  
**Old Value**: `Agent Projects`  
**New Value**: `Happy Place`  
**Occurrences**: 4

**Verification**: `grep -r "Agent Projects" .devcontainer/ .env.example backend/pyproject.toml` returns no results

---

### Contract 5: Documentation (P2)

**Files**: `README.md`, `backend/README.md`  
**Change Type**: Markdown heading and body text replacement  
**Old Value**: `Agent Projects`  
**New Value**: `Happy Place`  
**Occurrences**: 3 (1 in README.md, 2 in backend/README.md)

**Verification**: Visual inspection of README files

---

### Contract 6: Code Comments (P2)

**Files**: `frontend/src/services/api.ts`, `frontend/src/types/index.ts`, `backend/tests/test_api_e2e.py`  
**Change Type**: Comment string replacement  
**Old Value**: `Agent Projects`  
**New Value**: `Happy Place`  
**Occurrences**: 3

**Verification**: `grep -r "Agent Projects" frontend/src/ backend/tests/` returns no results

---

## Summary

| Contract | Priority | Files | Occurrences |
|----------|----------|-------|-------------|
| Frontend Title | P1 | 2 | 3 |
| E2E Tests | P1 | 3 | 8 |
| Backend API | P2 | 1 | 4 |
| Configuration | P2 | 4 | 4 |
| Documentation | P2 | 2 | 3 |
| Code Comments | P2 | 3 | 3 |
| **Total** | — | **15** | **25** |

## API Contract Impact

**No API contracts are affected by this change.** Specifically:
- No REST endpoints added, removed, or modified
- No request/response schemas changed
- No authentication/authorization flows affected
- No WebSocket message formats changed
- The only API-related change is the cosmetic title/description in OpenAPI metadata
