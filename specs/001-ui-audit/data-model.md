# Data Model: UI Audit

**Feature**: `001-ui-audit` | **Date**: 2026-03-27 | **Plan**: [plan.md](plan.md)

## Overview

The UI Audit feature is a frontend-only quality assessment. It does not introduce new persistent entities or API endpoints. The data model describes the conceptual entities used to track and execute the audit process, and the existing frontend entities that are the targets of the audit.

---

## Audit Entities

### AuditPage

Represents a single page file that is the subject of an audit pass.

| Field | Type | Description |
|-------|------|-------------|
| pageName | `string` | Human-readable page name (e.g., "ProjectsPage") |
| filePath | `string` | Absolute path to the page file (e.g., `src/pages/ProjectsPage.tsx`) |
| lineCount | `number` | Current line count of the page file |
| featureDir | `string` | Associated feature component directory (e.g., `src/components/board/`) |
| relatedHooks | `string[]` | List of custom hooks used by the page |
| relatedTypes | `string[]` | List of type files referenced by the page |
| auditStatus | `AuditStatus` | Current audit progress |

```typescript
type AuditStatus = 'not-started' | 'in-progress' | 'passed' | 'has-findings';
```

### AuditFinding

Represents a specific issue identified during the audit of a page.

| Field | Type | Description |
|-------|------|-------------|
| pageRef | `string` | Reference to the AuditPage (pageName) |
| category | `AuditCategory` | Checklist category this finding belongs to |
| severity | `FindingSeverity` | How critical the finding is |
| description | `string` | Human-readable description of the issue |
| location | `string` | File path and line number(s) where the issue was found |
| remediationStatus | `RemediationStatus` | Current fix status |
| frReference | `string` | Functional requirement ID (e.g., "FR-001") |

```typescript
type AuditCategory =
  | 'architecture'
  | 'data-fetching'
  | 'states'
  | 'type-safety'
  | 'accessibility'
  | 'ux-polish'
  | 'styling'
  | 'performance'
  | 'testing'
  | 'hygiene';

type FindingSeverity = 'must-fix' | 'should-fix' | 'not-applicable';

type RemediationStatus = 'open' | 'fixed' | 'waived';
```

### AuditChecklist

The set of quality criteria applied to each page, derived from the 45 functional requirements in the spec.

| Field | Type | Description |
|-------|------|-------------|
| category | `AuditCategory` | Checklist category |
| checklistItem | `string` | Description of the criterion |
| frReference | `string` | Functional requirement ID |
| pageResults | `Record<string, CheckResult>` | Per-page pass/fail/NA results |
| notes | `string` | Additional context or justification |

```typescript
type CheckResult = 'pass' | 'fail' | 'not-applicable';
```

---

## Existing Frontend Entities (Audit Targets)

These are the existing TypeScript types used across the pages being audited. They are not modified by this feature — listed here for reference during implementation.

### Core Types (from `src/types/index.ts`)

| Entity | Key Fields | Used By |
|--------|-----------|---------|
| `Project` | id, name, owner, repo, description | ProjectsPage, AgentsPage |
| `BoardItem` | id, title, status, assignees, labels | ProjectsPage (board) |
| `BoardDataResponse` | columns, items, metadata | ProjectsPage |
| `Pipeline` | id, name, stages, project_id | AgentsPipelinePage |
| `AgentAssignment` | agent_id, pipeline_id, config | AgentsPage |
| `Chore` | id, name, schedule, status | ChoresPage |
| `ActivityEvent` | id, type, timestamp, details | ActivityPage |
| `Tool` | id, name, description, schema | ToolsPage |
| `UserSettings` | theme, notifications, preferences | SettingsPage |

### App Types (from `src/types/apps.ts`)

| Entity | Key Fields | Used By |
|--------|-----------|---------|
| `App` | id, name, description, status, config | AppsPage, AppPage |
| `AppCreateInput` | name, description, template | AppsPage (create dialog) |
| `AppUpdateInput` | name, description, config | AppPage (edit) |

---

## Page-to-Entity Mapping

| Page | Primary Entities | Data Sources | Has Collections |
|------|-----------------|--------------|-----------------|
| ProjectsPage | Project, BoardItem, BoardDataResponse | useProjects, useProjectBoard | Yes (projects list, board items) |
| AgentsPipelinePage | Pipeline, AgentAssignment | usePipelineConfig, useAgentConfig | Yes (pipelines, stages) |
| AppsPage | App, AppCreateInput | useApps, useAppsPaginated, useCreateApp | Yes (apps grid) |
| ActivityPage | ActivityEvent | useActivityFeed | Yes (activity timeline) |
| AgentsPage | AgentAssignment, Project | useAgentConfig, useProjects | Yes (agents catalog) |
| ChoresPage | Chore | useChores | Yes (chores list) |
| ToolsPage | Tool | useTools | Yes (tools catalog) |
| SettingsPage | UserSettings | useSettings | No (single form) |
| AppPage | App | useApp | No (single detail) |
| HelpPage | — | — (static content) | No |
| LoginPage | — | — (auth flow) | No |
| NotFoundPage | — | — (static) | No |

---

## Validation Rules

### From Functional Requirements

| Rule | Entity/Field | FR Reference |
|------|-------------|--------------|
| Page file ≤ 250 lines | AuditPage.lineCount | FR-001 |
| No prop drilling > 2 levels | AuditPage (structural) | FR-004 |
| State blocks > 15 lines must be extracted | AuditPage (hooks) | FR-005 |
| No `any` type annotations | All page types | FR-016 |
| All collections must have empty states | Pages with collections | FR-013 |
| All data-fetching pages must show loading indicators | Pages with data sources | FR-010 |
| Destructive actions require confirmation | Pages with delete/remove/stop | FR-028 |
| All interactive elements keyboard-accessible | All pages | FR-018 |
| All form fields must have labels | Pages with forms | FR-021 |

### State Transitions

```
AuditPage.auditStatus:
  not-started → in-progress   (audit begins)
  in-progress → passed        (all checks pass or N/A)
  in-progress → has-findings  (one or more must-fix findings)
  has-findings → in-progress  (remediation applied, re-audit)
  has-findings → passed       (all findings fixed or waived)

AuditFinding.remediationStatus:
  open → fixed                (code change applied)
  open → waived               (justified exception documented)
```

---

## Relationships

```
AuditPage 1──* AuditFinding     (one page has many findings)
AuditChecklist 1──* AuditPage   (one checklist item applies to all pages)
AuditFinding *──1 AuditChecklist (each finding references a checklist item)
```

No new database tables, API endpoints, or persistent storage is introduced by this feature. The audit entities are conceptual — they are tracked in the spec artifacts (plan.md, tasks.md) and validated through code inspection, linting, type checking, and test execution.
