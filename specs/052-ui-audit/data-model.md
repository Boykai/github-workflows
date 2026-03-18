# Data Model: UI Audit

**Feature**: `052-ui-audit`
**Date**: 2026-03-18

---

## Entities

### Audit Checklist

A structured evaluation framework defining all items that must be assessed for each page. This is a documentation-only entity used during the audit process — not a runtime data structure.

**File**: `specs/052-ui-audit/checklists/[page-name].md` (one per audited page)

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `page_name` | string | Name of the page being audited (e.g., "AppsPage") | Must match a file in `src/pages/` |
| `page_path` | string | File path relative to frontend root | Must exist in repository |
| `audit_date` | string | ISO 8601 date of audit completion | Valid ISO 8601 |
| `auditor` | string | Agent or person performing the audit | Non-empty |
| `categories` | AuditCategory[] | Array of 10 quality dimension evaluations | Exactly 10 categories |

**Validation Rules**:
- Every audit must evaluate all 10 categories — no categories may be skipped
- Each category contains multiple checklist items, each scored Pass/Fail/N/A

**State Transitions**: Draft → In Progress → Complete

---

### Audit Category

A single quality dimension evaluation within a page audit. One of the 10 standard categories defined in the spec.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `name` | string | Category name (e.g., "Component Architecture & Modularity") | Must be one of 10 defined categories |
| `items` | AuditItem[] | Individual checklist items within this category | At least 1 item per category |
| `pass_count` | number | Number of items scored Pass | ≥0 |
| `fail_count` | number | Number of items scored Fail | ≥0 |
| `na_count` | number | Number of items scored N/A | ≥0 |

**Validation Rules**:
- `pass_count + fail_count + na_count` must equal `items.length`
- No items may be left unscored (FR-002)

---

### Audit Item

A single evaluable checklist item within a category.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | string | Unique item identifier (e.g., "arch-001") | Unique within category |
| `description` | string | What is being evaluated | Non-empty |
| `status` | enum | Evaluation result | "Pass" \| "Fail" \| "N/A" |
| `finding` | AuditFinding \| null | Detailed finding if status is "Fail" | Required when status is "Fail", null otherwise |

**Validation Rules**:
- If `status` is "Fail", `finding` must be non-null (FR-003)
- If `status` is "Pass" or "N/A", `finding` may be null

---

### Audit Finding

A documented issue discovered during the audit evaluation. Each finding includes the problem, its location, and a recommended fix.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `issue_description` | string | Clear description of the problem | Non-empty |
| `affected_file` | string | File path where the issue exists | Must exist in repository |
| `affected_location` | string | Specific location within the file (line range, function name, component) | Non-empty |
| `severity` | enum | Impact assessment | "Critical" \| "Major" \| "Minor" |
| `recommended_fix` | string | Specific remediation action | Non-empty |
| `related_requirement` | string | Functional requirement ID from spec (e.g., "FR-004") | Must match a valid FR-### |

**Validation Rules**:
- All fields are required when a finding is created
- `severity` levels defined as:
  - **Critical**: Broken functionality, accessibility barrier, or security issue
  - **Major**: Missing state handling, type safety violation, or UX inconsistency
  - **Minor**: Code style, performance optimization, or documentation gap

---

### Page Audit Summary

Aggregated results across all categories for a single page. Used for tracking overall audit progress.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `page_name` | string | Name of the audited page | Must match a page in `src/pages/` |
| `total_items` | number | Total checklist items evaluated | >0 |
| `total_pass` | number | Items scored Pass | ≥0 |
| `total_fail` | number | Items scored Fail | ≥0 |
| `total_na` | number | Items scored N/A | ≥0 |
| `overall_status` | enum | Aggregate result | "Audit Passed" \| "Needs Remediation" |
| `critical_findings` | number | Count of Critical severity findings | ≥0 |
| `major_findings` | number | Count of Major severity findings | ≥0 |
| `minor_findings` | number | Count of Minor severity findings | ≥0 |

**Validation Rules**:
- `total_pass + total_fail + total_na` must equal `total_items`
- `overall_status` is "Audit Passed" when `total_fail` is 0
- `overall_status` is "Needs Remediation" when `total_fail` > 0
- `critical_findings + major_findings + minor_findings` must equal `total_fail`

**State Transitions**: N/A (derived from Audit Checklist data)

---

## Relationships

```text
Page Audit Summary (1) ──── contains ──── (10) Audit Category
Audit Category (1)     ──── contains ──── (N)  Audit Item
Audit Item (0..1)      ──── has ──────── (1)   Audit Finding
```

- Each page produces exactly one Audit Checklist with exactly 10 Audit Categories
- Each Audit Category contains a variable number of Audit Items (defined by the audit checklist standard)
- Each Audit Item with status "Fail" has exactly one Audit Finding
- Findings reference functional requirements from the spec via `related_requirement`

---

## Enumerated Values

### Audit Categories (10 standard dimensions)

| # | Category Name | Checklist Items |
|---|--------------|-----------------|
| 1 | Component Architecture & Modularity | 7 items |
| 2 | Data Fetching & State Management | 6 items |
| 3 | Loading, Error & Empty States | 5 items |
| 4 | Type Safety | 5 items |
| 5 | Accessibility (a11y) | 7 items |
| 6 | Text, Copy & UX Polish | 8 items |
| 7 | Styling & Layout | 6 items |
| 8 | Performance | 5 items |
| 9 | Test Coverage | 5 items |
| 10 | Code Hygiene | 6 items |

**Total**: 65 checklist items per page × 11 pages = 715 total evaluations

### Pages to Audit (11 pages)

| Page | File | Line Count | Extraction Needed |
|------|------|-----------|-------------------|
| AgentsPage | `src/pages/AgentsPage.tsx` | 230 | No |
| AgentsPipelinePage | `src/pages/AgentsPipelinePage.tsx` | 417 | Yes |
| AppPage | `src/pages/AppPage.tsx` | 141 | No |
| AppsPage | `src/pages/AppsPage.tsx` | 709 | Yes |
| ChoresPage | `src/pages/ChoresPage.tsx` | 166 | No |
| HelpPage | `src/pages/HelpPage.tsx` | 195 | No |
| LoginPage | `src/pages/LoginPage.tsx` | 119 | No |
| NotFoundPage | `src/pages/NotFoundPage.tsx` | 29 | No |
| ProjectsPage | `src/pages/ProjectsPage.tsx` | 631 | Yes |
| SettingsPage | `src/pages/SettingsPage.tsx` | 107 | No |
| ToolsPage | `src/pages/ToolsPage.tsx` | 87 | No |
