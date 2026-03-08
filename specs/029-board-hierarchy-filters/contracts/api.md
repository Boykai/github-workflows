# API Contracts: Project Board — Parent Issue Hierarchy, Sub-Issue Display, Agent Pipeline Fixes & Functional Filters

**Feature**: 029-board-hierarchy-filters  
**Date**: 2026-03-07

## A1: Board Data Response — Extended Fields

**Endpoint**: `GET /board/projects/{project_id}`  
**Change**: Response shape extended with labels, timestamps, and milestone on each `BoardItem`

### Response Shape Changes

```json
{
  "project": { /* unchanged */ },
  "columns": [
    {
      "status": { "option_id": "abc123", "name": "In Progress", "color": "YELLOW" },
      "items": [
        {
          "item_id": "PVI_abc",
          "content_id": "I_123",
          "content_type": "issue",
          "title": "Implement login flow",
          "number": 42,
          "repository": { "owner": "Boykai", "name": "github-workflows" },
          "url": "https://github.com/Boykai/github-workflows/issues/42",
          "body": "Description snippet...",
          "status": "In Progress",
          "status_option_id": "abc123",
          "assignees": [{ "login": "Boykai", "avatar_url": "https://avatars.githubusercontent.com/u/123" }],
          "priority": { "name": "P1", "color": "RED" },
          "size": { "name": "L", "color": "ORANGE" },
          "estimate": 8.0,
          "linked_prs": [],
          "sub_issues": [
            {
              "id": "I_456",
              "number": 43,
              "title": "[speckit.implement] Login form component",
              "url": "https://github.com/Boykai/github-workflows/issues/43",
              "state": "open",
              "assigned_agent": "speckit.implement",
              "assignees": [],
              "linked_prs": []
            }
          ],
          "labels": [
            { "id": "LA_abc", "name": "enhancement", "color": "0075ca" },
            { "id": "LA_def", "name": "p1", "color": "d73a4a" }
          ],
          "created_at": "2026-03-01T10:00:00Z",
          "updated_at": "2026-03-07T15:30:00Z",
          "milestone": "Sprint 5"
        }
      ],
      "item_count": 1,
      "estimate_total": 8.0
    }
  ],
  "rate_limit": { /* unchanged */ }
}
```

### New Fields on BoardItem

| Field | Type | Source | Nullable | Purpose |
|-------|------|--------|----------|---------|
| `labels` | `Label[]` | GraphQL `issue.labels.nodes` | No (empty array if no labels) | FR-004: Label chips on cards; FR-009: Filter by label |
| `created_at` | `string \| null` | GraphQL `issue.createdAt` | Yes (null for draft issues) | FR-010: Sort by created date |
| `updated_at` | `string \| null` | GraphQL `issue.updatedAt` | Yes (null for draft issues) | FR-010: Sort by updated date |
| `milestone` | `string \| null` | GraphQL `issue.milestone.title` | Yes (null if no milestone) | FR-009: Filter by milestone; FR-011: Group by milestone |

### Label Object Shape

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| `id` | `string` | `"LA_kwDOABCDEf"` | GraphQL node ID |
| `name` | `string` | `"enhancement"` | Display text |
| `color` | `string` | `"0075ca"` | Hex without `#` prefix (GitHub convention) |

## A2: Parent-Only Board Filtering — Backend Logic

**Endpoint**: `GET /board/projects/{project_id}`  
**Change**: Sub-issues are now excluded from ALL columns, not just Done/Closed/Completed

### Current Behavior (Before)

```python
# service.py lines 970-990
_DONE_STATUS_NAMES = frozenset({"done", "closed", "completed"})

all_sub_issue_ids: set[str] = set()
for board_item in all_items:
    for si in board_item.sub_issues:
        if si.id:
            all_sub_issue_ids.add(si.id)

if all_sub_issue_ids:
    for col in columns:
        if col.status.name.lower() in _DONE_STATUS_NAMES:  # Only Done columns
            col.items = [it for it in col.items if it.content_id not in all_sub_issue_ids]
```

### New Behavior (After)

```python
all_sub_issue_ids: set[str] = set()
for board_item in all_items:
    for si in board_item.sub_issues:
        if si.id:
            all_sub_issue_ids.add(si.id)

if all_sub_issue_ids:
    for col in columns:
        # Filter sub-issues from ALL columns — parent-only board view (FR-001)
        col.items = [it for it in col.items if it.content_id not in all_sub_issue_ids]
```

### Impact

- Sub-issues that were previously visible as standalone cards in non-Done columns will no longer appear
- `item_count` and `estimate_total` per column should be recalculated after filtering
- The `sub_issues` array on each parent `BoardItem` remains unchanged (sub-issue data is still available for the collapsible panel)

## A3: GraphQL Query Extension

**File**: `backend/src/services/github_projects/graphql.py`  
**Query**: `BOARD_GET_PROJECT_ITEMS_QUERY`

### Added Fields in `... on Issue` Fragment

```graphql
... on Issue {
  id
  number
  title
  body
  url
  createdAt          # NEW
  updatedAt          # NEW
  milestone {        # NEW
    title
  }
  labels(first: 20) { # NEW
    nodes {
      id
      name
      color
    }
  }
  # ... existing fields unchanged
}
```

### Service Layer Parsing (Pseudocode)

```python
# In the item processing loop (service.py ~lines 709-824):
if content_type == "Issue":
    issue_content = content_node
    
    # NEW: Parse labels
    labels_data = issue_content.get("labels", {}).get("nodes", [])
    labels = [
        Label(id=l["id"], name=l["name"], color=l["color"])
        for l in labels_data
    ]
    
    # NEW: Parse timestamps
    created_at = issue_content.get("createdAt")
    updated_at = issue_content.get("updatedAt")
    
    # NEW: Parse milestone
    milestone_node = issue_content.get("milestone")
    milestone = milestone_node["title"] if milestone_node else None
    
    board_item = BoardItem(
        # ... existing fields ...
        labels=labels,
        created_at=created_at,
        updated_at=updated_at,
        milestone=milestone,
    )
```

## A4: Agent List Endpoint — No Changes Required

**Endpoint**: `GET /workflow/agents`  
**Status**: No changes needed

The `AvailableAgent` response already includes `default_model_name` and `tools_count` fields. The Agent Pipeline model/tool count bug is a frontend data-binding issue (slug mismatch in `AgentTile.tsx` lookup), not a backend data gap. See component contracts (C3) for the fix.
