# File Change Contracts: Update Project Title to 'pottery'

**Branch**: `copilot/update-project-title-to-pottery-again` | **Date**: 2026-02-16 | **Spec**: [spec.md](../spec.md)

## Overview

This document specifies the exact changes to be made to each file, serving as a contract between the planning phase and implementation phase. Each change includes before/after states, validation rules, and acceptance criteria.

## Contract 1: HTML Page Title Update

**File**: `frontend/index.html`  
**User Story**: P1 - Browser Tab Title Update  
**Functional Requirement**: FR-001

### Change Specification

**Location**: Line 7  
**Change Type**: REPLACE text content within `<title>` element

**Before**:
```html
    <title>Welcome to Tech Connect 2026!</title>
```

**After**:
```html
    <title>pottery</title>
```

### Validation Rules

1. ✅ Must be lowercase "pottery" (no Title Case)
2. ✅ HTML structure unchanged (opening/closing tags remain)
3. ✅ No whitespace changes to surrounding lines
4. ✅ Character encoding remains UTF-8
5. ✅ File remains valid HTML5

### Acceptance Criteria

- [ ] Line 7 contains exactly `<title>pottery</title>` with proper indentation (4 spaces)
- [ ] Browser tab displays "pottery" when page loads
- [ ] HTML validation passes (`<!DOCTYPE html>` declaration present)
- [ ] No other lines in file are modified

### Test Verification

**Command**: `grep -n "<title>" frontend/index.html`  
**Expected Output**: `7:    <title>pottery</title>`

**E2E Test**: `frontend/e2e/ui.spec.ts` will validate browser displays "pottery"

---

## Contract 2: E2E Test Update

**File**: `frontend/e2e/ui.spec.ts`  
**User Story**: Test alignment with P1  
**Functional Requirement**: Test validation of FR-001

### Change Specification

**Location**: Line 15  
**Change Type**: REPLACE string argument in test assertion

**Before**:
```typescript
  await expect(page).toHaveTitle('Welcome to Tech Connect 2026!');
```

**After**:
```typescript
  await expect(page).toHaveTitle('pottery');
```

### Validation Rules

1. ✅ Test method signature unchanged (`toHaveTitle`)
2. ✅ String argument is lowercase "pottery"
3. ✅ Semicolon and code formatting preserved
4. ✅ No changes to test structure or logic

### Acceptance Criteria

- [ ] Line 15 contains exactly the updated assertion
- [ ] Test passes when run against updated frontend
- [ ] TypeScript compilation succeeds
- [ ] No other test assertions are modified

### Test Verification

**Command**: `npm run test:e2e` (from frontend directory)  
**Expected Outcome**: Test passes, validates browser title is "pottery"

---

## Contract 3: README Title Update

**File**: `README.md`  
**User Story**: P2 - Documentation Consistency  
**Functional Requirement**: FR-002

### Change Specification

**Location**: Line 1  
**Change Type**: REPLACE markdown heading text

**Before**:
```markdown
# GitHub Projects Chat Interface
```

**After**:
```markdown
# pottery
```

### Secondary Change

**Location**: Line 3  
**Change Type**: UPDATE subtitle to include brand name

**Before**:
```markdown
> **A new way of working with DevOps** — leveraging AI in a conversational web app to create, manage, and execute GitHub Issues on a GitHub Project Board.
```

**After**:
```markdown
> **pottery: A new way of working with DevOps** — leveraging AI in a conversational web app to create, manage, and execute GitHub Issues on a GitHub Project Board.
```

### Validation Rules

1. ✅ Markdown heading syntax preserved (`#` with space)
2. ✅ Line breaks and formatting unchanged
3. ✅ All markdown syntax valid (can be parsed without errors)
4. ✅ All links remain functional (no broken references)
5. ✅ Brand name is lowercase "pottery"

### Acceptance Criteria

- [ ] Line 1 is exactly `# pottery` (no trailing whitespace)
- [ ] Line 3 includes "pottery:" prefix
- [ ] Markdown renders correctly in GitHub preview
- [ ] Table of contents (if auto-generated) updates to reference "pottery"
- [ ] All links in README remain valid (SC-004)

### Test Verification

**Command**: `head -5 README.md`  
**Expected Output**: Shows "# pottery" on line 1 and "pottery:" on line 3

**Link Validation**: `markdown-link-check README.md` (if available)

---

## Contract 4: Frontend Package Description

**File**: `frontend/package.json`  
**User Story**: P3 - Package and Module Names  
**Functional Requirement**: FR-004, FR-005

### Change Specification

**Location**: After line 3 (after `"version"` field)  
**Change Type**: ADD_FIELD

**Before**:
```json
{
  "name": "github-projects-chat-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
```

**After**:
```json
{
  "name": "github-projects-chat-frontend",
  "private": true,
  "version": "0.1.0",
  "description": "pottery - A conversational DevOps interface for GitHub Projects",
  "type": "module",
```

### Validation Rules

1. ✅ JSON syntax valid (no trailing commas, proper quotes)
2. ✅ `"name"` field MUST remain `"github-projects-chat-frontend"` (FR-005)
3. ✅ New field includes "pottery" (lowercase)
4. ✅ Indentation matches existing fields (2 spaces)
5. ✅ Comma added after description field

### Acceptance Criteria

- [ ] `name` field unchanged (verified with `jq .name frontend/package.json`)
- [ ] `description` field present with "pottery" in value
- [ ] JSON is valid (verified with `jq . frontend/package.json`)
- [ ] File can be parsed by npm (`npm install --dry-run` succeeds)

### Test Verification

**Command**: `jq '.name, .description' frontend/package.json`  
**Expected Output**:
```
"github-projects-chat-frontend"
"pottery - A conversational DevOps interface for GitHub Projects"
```

---

## Contract 5: Backend Package Description

**File**: `backend/pyproject.toml`  
**User Story**: P3 - Package and Module Names  
**Functional Requirement**: FR-004, FR-005

### Change Specification

**Location**: Line 4  
**Change Type**: UPDATE_FIELD value

**Before**:
```toml
[project]
name = "github-projects-chat-backend"
version = "0.1.0"
description = "FastAPI backend for GitHub Projects Chat Interface"
requires-python = ">=3.11"
```

**After**:
```toml
[project]
name = "github-projects-chat-backend"
version = "0.1.0"
description = "pottery - FastAPI backend for conversational DevOps"
requires-python = ">=3.11"
```

### Validation Rules

1. ✅ TOML syntax valid
2. ✅ `name` field MUST remain `"github-projects-chat-backend"` (FR-005)
3. ✅ Description includes "pottery" (lowercase)
4. ✅ Quotes and equal sign formatting preserved
5. ✅ No changes to other fields

### Acceptance Criteria

- [ ] `name` field unchanged (verified with `grep "^name = " backend/pyproject.toml`)
- [ ] `description` field contains "pottery"
- [ ] TOML is valid (can be parsed without errors)
- [ ] Python tooling can read file (`pip install -e backend --dry-run` succeeds)

### Test Verification

**Command**: `grep -E "^(name|description) = " backend/pyproject.toml`  
**Expected Output**:
```
name = "github-projects-chat-backend"
description = "pottery - FastAPI backend for conversational DevOps"
```

---

## Cross-Cutting Contracts

### Contract CC-1: Backward Compatibility

**Requirement**: FR-005

**Package Identifiers That MUST NOT Change**:

| File | Field | Value | Validation Command |
|------|-------|-------|-------------------|
| frontend/package.json | name | `github-projects-chat-frontend` | `jq .name frontend/package.json` |
| backend/pyproject.toml | name | `github-projects-chat-backend` | `grep "^name = " backend/pyproject.toml` |

**Acceptance Criteria**:
- [ ] Both package identifiers remain exactly as before
- [ ] No import statements need updating
- [ ] No CI/CD pipeline changes required

### Contract CC-2: Link Integrity

**Requirement**: FR-007

**Verification**:
- All HTTP/HTTPS URLs in README must return 2xx status codes (or be known external docs)
- All relative file paths must reference existing files
- No anchor links depend on title text (verified: none exist)

**Acceptance Criteria**:
- [ ] README link check passes
- [ ] No 404 errors when clicking links
- [ ] All referenced files exist

### Contract CC-3: Formatting Preservation

**Requirement**: FR-006

**Verification**:
- HTML: Valid HTML5 (check with validator)
- Markdown: Valid markdown syntax
- JSON: Valid JSON (check with `jq`)
- TOML: Valid TOML (check with Python toml parser)

**Acceptance Criteria**:
- [ ] All files pass syntax validation
- [ ] Indentation preserved (use `git diff` to verify only content changed)
- [ ] Line endings unchanged (LF on Unix, CRLF on Windows if applicable)

---

## Implementation Checklist

Use this checklist during implementation to verify all contracts are fulfilled:

### Phase 1: P1 Changes (Browser Title)
- [ ] Contract 1: Update frontend/index.html line 7
- [ ] Contract 2: Update frontend/e2e/ui.spec.ts line 15
- [ ] Verify E2E test passes
- [ ] Verify browser displays "pottery" in tab

### Phase 2: P2 Changes (Documentation)
- [ ] Contract 3: Update README.md line 1
- [ ] Contract 3: Update README.md line 3
- [ ] Verify markdown renders correctly
- [ ] Verify all links work (Contract CC-2)

### Phase 3: P3 Changes (Package Metadata)
- [ ] Contract 4: Add description to frontend/package.json
- [ ] Contract 5: Update description in backend/pyproject.toml
- [ ] Verify JSON/TOML syntax valid
- [ ] Verify package names unchanged (Contract CC-1)

### Final Verification
- [ ] All 5 contracts completed
- [ ] All cross-cutting contracts (CC-1, CC-2, CC-3) verified
- [ ] Run full test suite (`npm test` and `pytest`)
- [ ] Visual confirmation: Open app in browser, check title
- [ ] Git diff review: Only expected lines changed

---

## Contract Acceptance

Each contract is considered fulfilled when:
1. All validation rules pass
2. All acceptance criteria are checked
3. Test verification commands return expected results
4. Cross-cutting contracts are satisfied

**Final Sign-Off**: Implementation complete when all contracts accepted and checklist items checked.
