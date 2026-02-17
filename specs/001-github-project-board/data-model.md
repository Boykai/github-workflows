# Data Model: Real-Time GitHub Project Board

**Date**: 2026-02-16  
**Feature**: 001-github-project-board

## Entities

### BoardProject

A GitHub Project V2 with metadata for board display.

| Field | Type | Description |
|-------|------|-------------|
| project_id | string | GitHub GraphQL node ID (e.g., `PVT_xxx`) |
| name | string | Project title |
| description | string? | Short description |
| url | string | GitHub project URL |
| owner_login | string | Owner username or org name |
| status_field | StatusField | The Status field configuration |

### StatusField

Configuration for the project's Status single-select field.

| Field | Type | Description |
|-------|------|-------------|
| field_id | string | GraphQL node ID for the field |
| options | StatusOption[] | Available status values |

### StatusOption

A single status option (maps to a board column).

| Field | Type | Description |
|-------|------|-------------|
| option_id | string | Unique option ID |
| name | string | Display name (e.g., "In Progress") |
| color | StatusColor | Color enum value |
| description | string? | Optional description text |

### StatusColor (enum)

GitHub's predefined status colors.

| Value | Hex (approx) |
|-------|--------------|
| GRAY | #6e7781 |
| BLUE | #0969da |
| GREEN | #1a7f37 |
| YELLOW | #bf8700 |
| ORANGE | #bc4c00 |
| RED | #cf222e |
| PINK | #bf3989 |
| PURPLE | #8250df |

### BoardItem

An item (issue/draft/PR) on the board with all display metadata.

| Field | Type | Description |
|-------|------|-------------|
| item_id | string | Project item GraphQL ID |
| content_id | string? | Underlying issue/PR GraphQL ID |
| content_type | ContentType | "issue" \| "draft_issue" \| "pull_request" |
| title | string | Issue/PR title |
| number | int? | Issue/PR number (null for drafts) |
| repository | Repository? | Repository info (null for drafts) |
| url | string? | GitHub URL (null for drafts) |
| body | string? | Description/body text |
| status | string | Current status option name |
| status_option_id | string | Status option ID |
| assignees | Assignee[] | Assigned users |
| priority | PriorityValue? | Priority custom field |
| size | SizeValue? | Size custom field |
| estimate | float? | Estimate custom field (numeric) |
| linked_prs | LinkedPR[] | Pull requests linked to this issue |

### ContentType (enum)

| Value | Description |
|-------|-------------|
| issue | GitHub Issue |
| draft_issue | Project draft issue |
| pull_request | GitHub Pull Request |

### Repository

Repository reference for an issue/PR.

| Field | Type | Description |
|-------|------|-------------|
| owner | string | Repository owner login |
| name | string | Repository name |

### Assignee

User assigned to an issue.

| Field | Type | Description |
|-------|------|-------------|
| login | string | GitHub username |
| avatar_url | string | Avatar image URL |

### PriorityValue

Priority custom field value.

| Field | Type | Description |
|-------|------|-------------|
| name | string | Priority name (e.g., "P1", "High") |
| color | StatusColor? | Option color if configured |

### SizeValue

Size custom field value.

| Field | Type | Description |
|-------|------|-------------|
| name | string | Size name (e.g., "S", "XS", "Medium") |
| color | StatusColor? | Option color if configured |

### LinkedPR

A pull request linked to an issue.

| Field | Type | Description |
|-------|------|-------------|
| pr_id | string | PR GraphQL ID |
| number | int | PR number |
| title | string | PR title |
| state | PRState | open \| closed \| merged |
| url | string | PR URL on GitHub |

### PRState (enum)

| Value | Description |
|-------|-------------|
| open | PR is open |
| closed | PR closed without merge |
| merged | PR was merged |

---

## Relationships

```
BoardProject
    └── StatusField
            └── StatusOption[] (1:N - columns)

BoardItem
    ├── StatusOption (N:1 - current column)
    ├── Repository? (N:1 - source repo)
    ├── Assignee[] (N:M)
    ├── PriorityValue? (1:1)
    ├── SizeValue? (1:1)
    └── LinkedPR[] (1:N)
```

---

## Validation Rules

1. **BoardItem.status_option_id** must match one of `StatusField.options[].option_id`
2. **BoardItem.number** is required when `content_type` is "issue" or "pull_request"
3. **BoardItem.repository** is required when `content_type` is not "draft_issue"
4. **BoardItem.estimate** must be non-negative if present
5. **Assignee.avatar_url** must be a valid HTTPS URL

---

## State Transitions

Board items can transition between any status (no restrictions enforced by this feature):

```
[Any Status] ──────► [Any Other Status]
     │
     └── Status is updated in GitHub; board reflects via polling
```

The board is read-only; state changes happen in GitHub directly.
