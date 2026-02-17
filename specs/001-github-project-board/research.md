# Research: Real-Time GitHub Project Board

**Date**: 2026-02-16  
**Feature**: 001-github-project-board

## Research Tasks

### 1. GitHub Projects V2 GraphQL API - Custom Fields

**Decision**: Use `fieldValues(first: 20)` with inline fragments for each field type

**Rationale**: GitHub's GraphQL API returns custom field values as a polymorphic union type. Each field type (SingleSelect, Number, Text, Date) requires its own inline fragment to access the value. This approach handles Priority (SingleSelect), Size (SingleSelect), and Estimate (Number) fields gracefully.

**Alternatives Considered**:
- Using `fieldValueByName()` for each field individually → Rejected: Requires multiple queries/fragments per field
- REST API for custom fields → Rejected: Not available; Projects V2 is GraphQL-only

**Query Pattern**:
```graphql
fieldValues(first: 20) {
  nodes {
    ... on ProjectV2ItemFieldSingleSelectValue {
      name
      optionId
      field { ... on ProjectV2FieldCommon { name } }
    }
    ... on ProjectV2ItemFieldNumberValue {
      number
      field { ... on ProjectV2FieldCommon { name } }
    }
  }
}
```

---

### 2. GitHub Projects V2 GraphQL API - Linked Pull Requests

**Decision**: Use timeline events on issues to discover linked PRs

**Rationale**: GitHub links PRs to issues via `CONNECTED_EVENT` and `CROSS_REFERENCED_EVENT` timeline items. The existing codebase already has this query pattern in `github_projects.py`.

**Alternatives Considered**:
- Using REST API `GET /repos/{owner}/{repo}/issues/{issue_number}/timeline` → Rejected: Would require additional API call per issue
- Only showing manually linked PRs → Rejected: Would miss cross-referenced PRs from commit messages

**Query Pattern**:
```graphql
timelineItems(itemTypes: [CONNECTED_EVENT, CROSS_REFERENCED_EVENT], first: 50) {
  nodes {
    ... on ConnectedEvent {
      subject {
        ... on PullRequest { id number title state url }
      }
    }
    ... on CrossReferencedEvent {
      source {
        ... on PullRequest { id number title state url }
      }
    }
  }
}
```

---

### 3. Status Field Colors and Descriptions

**Decision**: Query status field options when fetching project metadata

**Rationale**: GitHub provides `color` (enum: GRAY, BLUE, GREEN, YELLOW, ORANGE, RED, PINK, PURPLE) and `description` fields on single-select options. These map to column headers.

**Alternatives Considered**:
- Hardcoding color mappings → Rejected: Projects have customizable status colors
- Ignoring colors entirely → Rejected: FR-008 requires colored status dots

**Response Structure**:
```json
{
  "options": [
    { "id": "f75ad846", "name": "Backlog", "color": "GRAY", "description": "Items not started" },
    { "id": "47fc9ee4", "name": "In Progress", "color": "YELLOW", "description": "Work in progress" },
    { "id": "98236657", "name": "Done", "color": "GREEN", "description": "Completed" }
  ]
}
```

---

### 4. Rate Limiting for 15-Second Polling

**Decision**: Implement 15-second polling with monitoring; rate limits are acceptable

**Rationale**: 
- 15-second polling = 240 requests/hour per user
- GitHub allows 5,000 points/hour for authenticated users
- Query cost is typically 1 point per simple query
- Existing codebase has exponential backoff for rate limit handling

**Alternatives Considered**:
- WebSocket/real-time subscription → Rejected: GitHub doesn't offer GraphQL subscriptions for Projects V2
- GitHub Webhooks → Rejected: Would require webhook endpoint; polling is simpler for read-only board
- Longer polling interval (60s) → Rejected: User expects near-real-time updates

**Best Practices Implemented**:
1. Include `rateLimit { remaining resetAt cost }` in queries for monitoring
2. Use existing `MAX_RETRIES = 3` and exponential backoff
3. Batch project items and field values in single query
4. Limit pagination to reasonable defaults (`first: 100`)

---

### 5. Existing Code Patterns

**Decision**: Follow established patterns from `github_projects.py` and frontend hooks

**Rationale**: The codebase has mature patterns for GitHub API interaction, error handling, and state management.

**Key Patterns to Reuse**:

| Pattern | Location | Usage |
|---------|----------|-------|
| GraphQL query with fragments | `github_projects.py` L22-45 | Use fragment pattern for reusable field selections |
| Rate limit handling | `github_projects.py` L549-600 | Exponential backoff with retry |
| React Query polling | `useProjects.ts` | Use `refetchInterval` for 15s polling |
| Real-time sync hook | `useRealTimeSync.ts` | Pattern for sync status indicator |
| Type definitions | `frontend/src/types/index.ts` | Extend existing types with board-specific fields |

---

## Summary

All unknowns resolved. The GitHub Projects V2 GraphQL API provides all required data:
- Custom fields via `fieldValues` polymorphic query
- Linked PRs via issue timeline events
- Status colors via field options
- Rate limits are acceptable for 15-second polling (240 req/hr << 5000 limit)

Implementation can proceed using existing codebase patterns.
