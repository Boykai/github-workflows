# Data Model: Chores Page Audit — Modern Best Practices, Modular Design, and Zero Bugs

**Feature Branch**: `043-chores-page-audit`
**Date**: 2026-03-16

## Overview

This document describes the key entities rendered on the Chores page and their relationships. Since this is an audit-and-polish feature (no new entities), the data model captures the **existing** entities that components interact with, their validation rules, and state transitions. This serves as a reference for auditing component correctness.

## Entity Diagram

```text
┌─────────────────────┐
│   Project           │
│   (project_id, name,│
│    owner, repo)     │
└────────┬────────────┘
         │ 1
         │
         │ has many
         ▼
┌─────────────────────┐       ┌─────────────────────┐
│   Chore             │       │   ChoreTemplate     │
│   (id, name, status,│       │   (name, about,     │
│    schedule_type,   │       │    path, content)    │
│    schedule_value,  │       └─────────────────────┘
│    execution_count, │              ▲
│    template_path,   │              │ created from
│    ai_enhance,      │──────────────┘
│    pipeline_id)     │
└────────┬────────────┘
         │
    ┌────┴──────┬──────────────────┐
    ▼           ▼                  ▼
┌────────┐ ┌──────────┐   ┌──────────────┐
│Schedule│ │EditState │   │TriggerResult │
└────────┘ └──────────┘   └──────────────┘
```

## Entities

### Chore

The primary entity representing a recurring repository maintenance task.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✅ | Unique chore identifier |
| `project_id` | string | ✅ | Associated project ID |
| `name` | string | ✅ | Chore display name (max 200 characters) |
| `template_path` | string | ✅ | Path to the issue template in `.github/ISSUE_TEMPLATE/` |
| `template_content` | string | ✅ | Current content of the chore template |
| `schedule_type` | `'time' \| 'count'` | ✅ | Trigger type: time-based (days) or count-based (issues) |
| `schedule_value` | number | ✅ | Trigger threshold: days between runs or issue count |
| `status` | `'active' \| 'paused'` | ✅ | Whether the chore is actively monitored for triggers |
| `execution_count` | number | ✅ | Total number of times this chore has been triggered |
| `last_triggered_at` | string (ISO 8601) \| null | ❌ | Timestamp of last trigger (null if never triggered) |
| `next_checkpoint` | string (ISO 8601) \| null | ❌ | Computed next trigger check time |
| `ai_enhance_enabled` | boolean | ✅ | Whether AI refinement is applied when triggering |
| `agent_pipeline_id` | string \| null | ❌ | Pipeline to use for execution (null = Auto) |
| `pr_number` | number \| null | ❌ | Associated PR number for template changes |
| `pr_url` | string \| null | ❌ | URL of the associated PR |
| `file_sha` | string \| null | ❌ | Git SHA of the template file (for conflict detection) |
| `created_at` | string (ISO 8601) | ✅ | Creation timestamp |
| `updated_at` | string (ISO 8601) | ✅ | Last update timestamp |

**Validation Rules**:

- `name` must be 1–200 characters, non-empty
- `schedule_value` must be a positive integer
- `schedule_type` must be one of `'time'` or `'count'`
- `status` must be one of `'active'` or `'paused'`
- `template_path` must reference a valid `.github/ISSUE_TEMPLATE/` path

**UI Rendering Notes**:

- Rendered as `ChoreCard` in the catalog grid
- Status shown as toggle switch (active = green, paused = muted)
- `last_triggered_at` shown as relative time ("2 hours ago") when recent, absolute when older
- `next_checkpoint` shown as relative time until next trigger check
- `execution_count` displayed as stat in ChoreCardStats
- Long `name` truncated with `text-ellipsis` and full text in Tooltip
- Long `template_path` truncated with `text-ellipsis` and full text in Tooltip

---

### ChoreTemplate

A repository-defined issue template available for creating chores.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Template display name |
| `about` | string | ❌ | Template description |
| `path` | string | ✅ | File path in `.github/ISSUE_TEMPLATE/` |
| `content` | string | ✅ | Full template content |

**Validation Rules**:

- `name` must be a non-empty string
- `path` must be a valid file path
- `content` can be empty (blank template)

**UI Rendering Notes**:

- Displayed in AddChoreModal template selector
- `about` shown as description under template name
- `path` shown as secondary text, truncated with tooltip for long paths

---

### ChoreSchedule (embedded in Chore)

The trigger configuration for a chore.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schedule_type` | `'time' \| 'count'` | ✅ | Type of trigger: time-based or count-based |
| `schedule_value` | number | ✅ | Threshold value: days for time-based, issue count for count-based |

**UI Rendering Notes**:

- Edited via `ChoreScheduleConfig` component
- Time-based displays as "Every X days"
- Count-based displays as "Every X issues"
- Both displayed with appropriate icons

---

### ChoreEditState

The in-progress inline editing state for a chore's template content.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `original` | string | ✅ | Original template content before editing |
| `current` | string | ✅ | Current content being edited |
| `isDirty` | boolean | ✅ | Whether the content has been modified |
| `fileSha` | string \| null | ❌ | Git file SHA for conflict detection during PR creation |

**Validation Rules**:

- `isDirty` is computed: `original !== current`
- `fileSha` required for inline update (PR creation) — absence triggers fresh fetch

**UI Rendering Notes**:

- Managed by `ChoreInlineEditor`
- Dirty indicator shown when `isDirty` is true
- Save triggers `useInlineUpdateChore` mutation with `fileSha` for conflict detection
- File SHA mismatch returns error requiring user to refresh

---

### ChoreTriggerResult

Result of manually or automatically triggering a chore.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `triggered` | boolean | ✅ | Whether the trigger executed |
| `issue_number` | number \| null | ❌ | Created issue number (if triggered) |
| `issue_url` | string \| null | ❌ | URL of created issue |
| `message` | string | ❌ | Human-readable result message |

**UI Rendering Notes**:

- Success: Toast notification with issue link
- Failure: Error toast with user-friendly message
- Trigger button disabled during mutation

---

### EvaluateChoreTriggersResponse

Result of the periodic trigger evaluation polling.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `evaluated` | number | ✅ | Number of chores evaluated |
| `triggered` | number | ✅ | Number of chores that fired |
| `skipped` | number | ✅ | Number of chores skipped (paused or not due) |
| `results` | ChoreTriggerResult[] | ✅ | Per-chore trigger results |

**UI Rendering Notes**:

- Polling occurs every 60 seconds via `useEvaluateChoresTriggers`
- Results silently update chore list via query invalidation
- No direct UI rendering — triggers refresh the chore list data

---

### FeaturedRitualCard (computed)

A computed spotlight card derived from chore data for the FeaturedRitualsPanel.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | `'next_run' \| 'most_recent' \| 'most_run'` | ✅ | Spotlight category |
| `chore` | Chore \| null | ❌ | The chore featured (null if no qualifying chore) |
| `label` | string | ✅ | Display label ("Next Run", "Most Recently Run", "Most Run") |
| `value` | string | ✅ | Computed display value (time until, time since, count) |

**UI Rendering Notes**:

- Three cards displayed in `FeaturedRitualsPanel`
- Null chore results in a "—" placeholder
- Values use relative time formatting

---

### ChoreInlineUpdateResponse

Response from updating a chore's template content via inline editor.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pr_number` | number | ✅ | PR number created or updated |
| `pr_url` | string | ✅ | URL of the PR |
| `merged` | boolean | ✅ | Whether the PR was auto-merged |

**UI Rendering Notes**:

- Success: Toast or inline message with PR link
- Merged: Additional confirmation that changes are live
- Not merged: Indication that PR is pending review

---

### ChoreCreateResponse

Response from creating a new chore (with optional auto-merge).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `chore` | Chore | ✅ | The created chore entity |
| `pr_number` | number \| null | ❌ | PR number if auto-merge was requested |
| `pr_url` | string \| null | ❌ | PR URL if auto-merge was requested |
| `merged` | boolean | ❌ | Whether the PR was auto-merged |

**UI Rendering Notes**:

- Success: Modal closes, chore list refreshed, success toast
- Auto-merge: Additional info about PR status

---

## State Transitions

### Page-Level States

```text
┌──────────────┐    project selected    ┌──────────────┐
│  No Project  │ ─────────────────────► │   Loading    │
│  Selected    │                        │   Chores     │
└──────────────┘                        └──────┬───────┘
                                               │
                                    ┌──────────┼──────────┐
                                    ▼          ▼          ▼
                              ┌──────────┐ ┌────────┐ ┌───────┐
                              │Populated │ │ Empty  │ │ Error │
                              │ Catalog  │ │ Chores │ │       │
                              └──────────┘ └────────┘ └───────┘
                                    │                     │
                                    │    rate limit       │
                                    ▼                     │
                              ┌──────────┐                │
                              │Rate Limit│ ◄──────────────┘
                              │ Banner   │
                              └──────────┘
```

### Chore Status States

```text
active ◄──► paused
  │              │
  │  (toggle)    │  (toggle)
  └──────────────┘
```

### Chore CRUD Flow

```text
                    ┌────────────────┐
                    │  AddChoreModal │
                    │  (template     │
                    │   selection)   │
                    └───────┬────────┘
                            │ create
                            ▼
┌──────────┐         ┌────────────┐         ┌──────────┐
│  Edit    │ ◄─────► │   Active   │ ──────► │ Deleted  │
│  Inline  │  save   │   Chore    │ confirm │ (removed)│
└──────────┘         └─────┬──────┘         └──────────┘
                           │
                      trigger │
                           ▼
                    ┌────────────┐
                    │  Triggered │
                    │  (issue    │
                    │  created)  │
                    └────────────┘
```

### AddChoreModal Flow

```text
┌───────────┐   select    ┌───────────┐   chat    ┌───────────┐   confirm   ┌───────────┐
│ Template  │ ──────────► │   Name +  │ ────────► │   Chat    │ ──────────► │  Auto-    │
│ Selection │             │  Content  │           │   Refine  │             │  Merge?   │
└───────────┘             └───────────┘           └───────────┘             └─────┬─────┘
                                                                                  │
                                                                    create        │
                                                                                  ▼
                                                                          ┌───────────┐
                                                                          │  Created  │
                                                                          │  (close)  │
                                                                          └───────────┘
```

### Inline Editor Flow

```text
closed ──► editing (click edit) ──► dirty (content changed) ──► saving (save clicked)
  ▲              │                        │                          │
  │              │ cancel                 │ discard (confirm)        │ success
  │              ▼                        ▼                          ▼
  └──────── closed                   closed                     closed (PR created)
                                                                     │ conflict
                                                                     ▼
                                                              error (SHA mismatch)
```
