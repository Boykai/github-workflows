# Data Model: Update Project Title to 'pottery'

**Branch**: `copilot/update-project-title-to-pottery-again` | **Date**: 2026-02-16 | **Spec**: [spec.md](./spec.md)

## Overview

This document defines the data entities for the pottery title update feature. Since this is a text replacement feature with no database or runtime data structures, the "data model" describes the file change entities and their relationships.

## Entity: File Change

A file change represents a modification to a single file in the repository.

### Properties

| Property | Type | Description | Validation Rules |
|----------|------|-------------|------------------|
| `file_path` | string | Absolute path from repository root | Must exist in repository |
| `change_type` | enum | Type of change: REPLACE, ADD_FIELD, UPDATE_FIELD | One of the defined types |
| `target_line` | number | Line number to modify (if applicable) | Positive integer |
| `old_value` | string | Original text to replace | Must match file content exactly |
| `new_value` | string | New text to insert | Must be lowercase "pottery" or contain "pottery" |
| `preserve_formatting` | boolean | Whether to maintain existing formatting | Always true per FR-006 |

### File Change Types

1. **REPLACE**: Direct text replacement (HTML title, test assertions)
2. **ADD_FIELD**: Add new JSON field (package.json description)
3. **UPDATE_FIELD**: Modify existing TOML field (pyproject.toml description)

## Entity: Package Identifier

Package identifiers that MUST remain unchanged per FR-005.

### Properties

| Property | Type | Description | Validation Rules |
|----------|------|-------------|------------------|
| `package_name` | string | Package identifier | Cannot be modified |
| `file_path` | string | Location of package definition | Must exist |
| `field_name` | string | Field name in config file | "name" in package.json or pyproject.toml |

### Preserved Identifiers

| Package | Identifier | File | Line |
|---------|-----------|------|------|
| Frontend | `github-projects-chat-frontend` | frontend/package.json | 2 |
| Backend | `github-projects-chat-backend` | backend/pyproject.toml | 2 |

## Entity: Documentation Section

Sections of documentation that reference the project title.

### Properties

| Property | Type | Description | Validation Rules |
|----------|------|-------------|------------------|
| `file_path` | string | Path to documentation file | Must be .md file |
| `section_type` | enum | TITLE, HEADING, BODY_TEXT | One of the defined types |
| `line_number` | number | Line containing the reference | Positive integer |
| `old_text` | string | Original project name | "GitHub Projects Chat Interface" |
| `new_text` | string | Updated project name | "pottery" |

## Relationships

```
FileChange (1) ─── affects ──▶ (1) File
     │
     └── validates against ──▶ (1) FunctionalRequirement

PackageIdentifier (1) ─── constrains ──▶ (1) FileChange
     │
     └── enforces ──▶ (1) BackwardCompatibility

DocumentationSection (1) ─── contains ──▶ (1..n) FileChange
     │
     └── requires ──▶ (1) ConsistencyCheck
```

## File Change Inventory

### 1. frontend/index.html

**Entity**: File Change  
**Type**: REPLACE  
**Priority**: P1 (User Story 1)

```yaml
file_path: frontend/index.html
change_type: REPLACE
target_line: 7
old_value: "Welcome to Tech Connect 2026!"
new_value: "pottery"
preserve_formatting: true
validation: Must maintain HTML structure, only change text content
```

**State Transitions**:
- Initial: `<title>Welcome to Tech Connect 2026!</title>`
- Final: `<title>pottery</title>`

---

### 2. README.md

**Entity**: Documentation Section  
**Type**: REPLACE (Title)  
**Priority**: P2 (User Story 2)

```yaml
file_path: README.md
change_type: REPLACE
target_line: 1
old_value: "# GitHub Projects Chat Interface"
new_value: "# pottery"
preserve_formatting: true
validation: Must maintain markdown heading syntax
```

**State Transitions**:
- Initial: `# GitHub Projects Chat Interface`
- Final: `# pottery`

**Additional References**:
The README contains one additional reference on line 3:
```yaml
target_line: 3
old_value: "> **A new way of working with DevOps**"
new_value: "> **pottery: A new way of working with DevOps**"
preserve_formatting: true
```

---

### 3. frontend/package.json

**Entity**: File Change + Package Identifier  
**Type**: ADD_FIELD  
**Priority**: P3 (User Story 3)

```yaml
file_path: frontend/package.json
change_type: ADD_FIELD
target_line: 3 (after "version" field)
field_name: "description"
new_value: "pottery - A conversational DevOps interface for GitHub Projects"
preserve_formatting: true
validation: Must be valid JSON, maintain existing fields

preserved_identifier:
  field_name: "name"
  field_value: "github-projects-chat-frontend"
  must_not_change: true
```

**State Transitions**:
- Initial: No description field exists
- Final: `"description": "pottery - A conversational DevOps interface for GitHub Projects",`

---

### 4. backend/pyproject.toml

**Entity**: File Change + Package Identifier  
**Type**: UPDATE_FIELD  
**Priority**: P3 (User Story 3)

```yaml
file_path: backend/pyproject.toml
change_type: UPDATE_FIELD
target_line: 4
field_name: "description"
old_value: "FastAPI backend for GitHub Projects Chat Interface"
new_value: "pottery - FastAPI backend for conversational DevOps"
preserve_formatting: true
validation: Must be valid TOML, maintain existing fields

preserved_identifier:
  field_name: "name"
  field_value: "github-projects-chat-backend"
  must_not_change: true
```

**State Transitions**:
- Initial: `description = "FastAPI backend for GitHub Projects Chat Interface"`
- Final: `description = "pottery - FastAPI backend for conversational DevOps"`

---

### 5. frontend/e2e/ui.spec.ts (Test Update)

**Entity**: File Change  
**Type**: REPLACE  
**Priority**: Test alignment with P1

```yaml
file_path: frontend/e2e/ui.spec.ts
change_type: REPLACE
target_line: 15
old_value: "Welcome to Tech Connect 2026!"
new_value: "pottery"
preserve_formatting: true
validation: Must maintain test structure, update assertion value only
```

**State Transitions**:
- Initial: `await expect(page).toHaveTitle('Welcome to Tech Connect 2026!');`
- Final: `await expect(page).toHaveTitle('pottery');`

---

## Validation Rules

### Global Constraints

1. **Case Sensitivity** (FR-001, Spec Assumptions)
   - All instances of "pottery" MUST be lowercase
   - No Title Case or UPPERCASE variants allowed

2. **Backward Compatibility** (FR-005)
   - Package `name` fields MUST NOT change
   - Package identifiers: `github-projects-chat-frontend`, `github-projects-chat-backend`

3. **Formatting Preservation** (FR-006)
   - Markdown syntax unchanged
   - HTML structure unchanged
   - JSON/TOML validity maintained
   - Indentation and whitespace preserved

4. **Link Integrity** (FR-007)
   - No broken links after changes (verified: no title-dependent links exist)
   - All external URLs remain valid

### Per-File Validation

| File | Validation Command | Expected Result |
|------|-------------------|-----------------|
| frontend/index.html | `grep -n "pottery" frontend/index.html` | Line 7 matches |
| README.md | `head -1 README.md` | Returns "# pottery" |
| frontend/package.json | `jq .name frontend/package.json` | Returns "github-projects-chat-frontend" (unchanged) |
| frontend/package.json | `jq .description frontend/package.json` | Returns string containing "pottery" |
| backend/pyproject.toml | `grep "name = " backend/pyproject.toml` | Returns "github-projects-chat-backend" (unchanged) |
| backend/pyproject.toml | `grep "description = " backend/pyproject.toml` | Returns string containing "pottery" |
| frontend/e2e/ui.spec.ts | `grep "toHaveTitle" frontend/e2e/ui.spec.ts` | Contains "pottery" |

## Success Verification

### SC-001: Browser Tab Title (100ms load)
**Verification**: Launch frontend dev server, open browser, verify tab shows "pottery"
**Data Source**: frontend/index.html `<title>` element
**Pass Criteria**: Browser tab displays "pottery" exactly

### SC-002: 100% Documentation Replacement
**Verification**: Search all .md files for old title
**Command**: `grep -r "GitHub Projects Chat Interface" *.md`
**Pass Criteria**: No matches in README.md title

### SC-003: Package Metadata Consistency
**Verification**: Check package configs have descriptions with "pottery"
**Commands**:
- `jq .description frontend/package.json`
- `grep description backend/pyproject.toml`
**Pass Criteria**: Both return strings containing "pottery"

### SC-004: Zero Broken Links
**Verification**: Run link checker on README
**Pass Criteria**: All links return 200 status or valid file paths

### SC-005: 5-Second Verification
**Verification**: Visual inspection + grep search
**Commands**:
- Open browser to verify title
- `grep -n "pottery" frontend/index.html README.md`
**Pass Criteria**: Can confirm changes in under 5 seconds

## Edge Cases

### Edge Case 1: Hardcoded References in Code

**Status**: ✅ Verified not present  
**Analysis**: Searched JavaScript/TypeScript and Python code for title references  
**Finding**: No hardcoded references to "Welcome to Tech Connect 2026!" in source code

### Edge Case 2: Comments and Documentation Strings

**Status**: ✅ Out of scope  
**Analysis**: FR-003 specifies "visible references" only  
**Decision**: Code comments are not user-facing, excluded from scope

### Edge Case 3: Test Fixtures and Mock Data

**Status**: ✅ Addressed  
**Analysis**: Only one test validates page title (frontend/e2e/ui.spec.ts)  
**Action**: Update test assertion (included in file change inventory)

## Dependencies

**None** - This feature has no external dependencies. All changes are text edits to existing files using standard tooling.

## Change Impact Summary

| Impact Area | Assessment | Notes |
|-------------|-----------|-------|
| Breaking Changes | None | Package identifiers preserved |
| API Changes | None | No API modifications |
| Database Schema | None | No database in use |
| Configuration | Minimal | Only description fields |
| Testing | Minimal | One test assertion update |
| Documentation | Moderate | README title and references |
| User-Facing | High | Browser tab title (most visible) |

## Implementation Order

Based on user story priorities:

1. **Phase 1 (P1)**: frontend/index.html - Browser tab title
2. **Phase 1 (P1)**: frontend/e2e/ui.spec.ts - Test alignment
3. **Phase 2 (P2)**: README.md - Documentation consistency
4. **Phase 3 (P3)**: frontend/package.json - Package metadata
5. **Phase 3 (P3)**: backend/pyproject.toml - Package metadata

## Rollback Strategy

All changes are reversible by restoring original values:
- No database migrations to reverse
- No API changes to deprecate
- Simple text reversion if needed

**Rollback File**: Original values documented in this data model's "old_value" fields
