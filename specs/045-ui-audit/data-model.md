# Data Model: UI Audit Issue Template

**Feature**: `045-ui-audit` | **Date**: 2026-03-16 | **Plan**: [plan.md](plan.md)

## Overview

This feature delivers a GitHub issue template — a static Markdown file with YAML front matter. There are no runtime entities, databases, or API endpoints. The data model documents the structural entities that compose the template and the relationships between them, serving as a reference for the task generation phase.

## Entities

### IssueTemplate

The top-level artefact: a Markdown file in `.github/ISSUE_TEMPLATE/` that GitHub renders as an issue creation form.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `name` | String | YAML front matter, required | Template display name in the "New Issue" picker (e.g., "UI Aduit") |
| `about` | String | YAML front matter, required | Short description shown in the template picker |
| `title` | String | YAML front matter, required | Default issue title (e.g., "[CHORE] UI Aduit") |
| `labels` | String | YAML front matter, required | Comma-separated labels auto-applied on issue creation (e.g., "chore") |
| `assignees` | String | YAML front matter, optional | Default assignees (empty for this template) |
| `body` | Markdown | Everything after YAML front matter | The issue body containing checklist, guide, files, and verification sections |

**Validation Rules**:

- `name` must be non-empty and unique among templates in `.github/ISSUE_TEMPLATE/`.
- `title` must follow the format `[CHORE] <template name>` per FR-010.
- `labels` must include `chore` per FR-009.
- `body` must contain all sections defined below.

---

### AuditCategory

One of the ten thematic sections grouping related checklist items.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `number` | Integer | 1–10, sequential | Section number within the checklist |
| `name` | String | Non-empty, unique within template | Category heading (e.g., "Component Architecture & Modularity") |
| `items` | List[ChecklistItem] | Minimum 4 per SC-003 | Ordered list of audit items within this category |

**Validation Rules**:

- Exactly 10 categories must exist per FR-002.
- Each category must contain at least 4 items per SC-003.
- Total items across all categories must be ≥59 per FR-012.

**Categories (fixed set)**:

1. Component Architecture & Modularity (7 items)
2. Data Fetching & State Management (6 items)
3. Loading, Error & Empty States (5 items)
4. Type Safety (5 items)
5. Accessibility (a11y) (7 items)
6. Text, Copy & UX Polish (8 items)
7. Styling & Layout (6 items)
8. Performance (5 items)
9. Test Coverage (5 items)
10. Code Hygiene (6 items)

---

### ChecklistItem

A single, actionable audit criterion formatted as a GitHub checkbox.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `label` | String | Bold, short identifier | The item's heading (e.g., "Single Responsibility") |
| `description` | String | Non-empty, single pass/fail condition | Observable condition to evaluate (e.g., "Page file is ≤250 lines") |
| `checked` | Boolean | Default: `false` | Whether the item has been completed (rendered as `- [ ]` or `- [x]`) |

**Validation Rules**:

- Each item must describe exactly one pass/fail condition per FR-004.
- Language must be clear and unambiguous per FR-011.
- No item should require external documentation to understand per SC-004.

---

### ImplementationPhase

One of six sequential phases in the implementation guide section.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `number` | Integer | 1–6, sequential | Phase number |
| `name` | String | Non-empty | Phase heading (e.g., "Discovery & Assessment") |
| `steps` | List[String] | Ordered, numbered | Specific actions to perform in this phase |

**Validation Rules**:

- Exactly 6 phases must exist per FR-006.
- Each phase depends only on preceding phases (no circular dependencies) per US3-AC4.
- Steps within a phase are numbered sequentially.

**Phases (fixed set)**:

1. Discovery & Assessment (9 steps)
2. Structural Fixes (4 steps)
3. States & Error Handling (4 steps)
4. Accessibility & UX Polish (5 steps)
5. Testing (3 steps)
6. Validation (4 steps)

---

### RelevantFilesSection

A reference section with placeholder paths mapping to the repository's frontend directory structure.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `category` | String | One of: Page & Components, Hooks & API, Types, Shared, Tests | File grouping |
| `paths` | List[String] | Uses `[PageName]` and `[feature]` placeholders | File or directory paths |

**Validation Rules**:

- Paths must be valid when placeholders are replaced with actual page/feature names per FR-007.
- Shared component paths must reference actual shared UI primitives (Button, Card, Input, Tooltip, ConfirmationDialog) and common components (CelestialLoader, ErrorBoundary) per US4-AC2.

---

### VerificationSection

Commands and manual checks listed at the end of the template for post-remediation validation.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `number` | Integer | Sequential | Verification step number |
| `command_or_check` | String | Non-empty | CLI command or manual check description |
| `expected_result` | String | Implicit in description | What constitutes a pass (e.g., "0 warnings", "all tests pass") |

**Validation Rules**:

- Must include lint, type-check, test, and manual browser checks per FR-008.
- Each command must produce a clear pass/fail result per SC-006.

## Relationships

```text
IssueTemplate 1──* AuditCategory          (exactly 10)
AuditCategory 1──* ChecklistItem           (≥4 per category, ≥59 total)
IssueTemplate 1──* ImplementationPhase     (exactly 6, ordered)
IssueTemplate 1──1 RelevantFilesSection    (one section with multiple categories)
IssueTemplate 1──1 VerificationSection     (one section with multiple steps)
```

## State Transitions

### ChecklistItem Lifecycle

```text
[Unchecked] ──(developer evaluates and marks)──→ [Checked]
[Unchecked] ──(not applicable, developer adds note)──→ [Checked + N/A note]
```

Items are binary (checked or unchecked). There is no intermediate state. GitHub's issue UI automatically tracks progress counters (e.g., "7/7").

### Audit Issue Lifecycle

```text
[Created from template] → [In Progress (items being checked)] → [All items checked] → [Closed]
```

An audit issue is considered complete when all applicable checklist items across all 10 categories are checked (US2-AC5).
