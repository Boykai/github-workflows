# Data Model: Frontend Polish & Performance

**Feature**: 001-frontend-polish-performance
**Date**: 2026-03-22
**Input**: [spec.md](./spec.md), [research.md](./research.md)

## Entities

### ErrorHint

Represents a structured error recovery hint returned by the `getErrorHint()` utility. Used by error boundaries, error banners, and error-variant empty states to display actionable recovery suggestions.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | `string` | Yes | Short classification label for the error (e.g., "Authentication Error", "Rate Limit Exceeded") |
| `hint` | `string` | Yes | Actionable, human-readable recovery suggestion (e.g., "Your session may have expired — try logging out and back in") |
| `action` | `ErrorHintAction \| undefined` | No | Optional navigation action for direct recovery (e.g., link to /login or /settings) |

#### ErrorHintAction (sub-type)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `label` | `string` | Yes | Button or link text (e.g., "Go to Login", "Open Settings") |
| `href` | `string` | Yes | Navigation URL (e.g., "/login", "/settings") |

#### Validation Rules

- `title` must be non-empty, max 50 characters
- `hint` must be non-empty, max 200 characters
- `action.href` must be a valid relative URL path (starts with `/`)

#### Error Classification Mapping

| Condition | Title | Hint | Action |
|-----------|-------|------|--------|
| Status 401 | "Authentication Error" | "Your session may have expired — try logging out and back in." | `{ label: "Go to Login", href: "/login" }` |
| Status 403 | "Permission Denied" | "You don't have permission to access this resource. Check your GitHub permissions." | — |
| Status 404 | "Not Found" | "This resource may have been moved or deleted." | — |
| Status 422 | "Validation Error" | "Please review the submitted data for correctness." | — |
| Status 429 | "Rate Limit Exceeded" | "Too many requests. {Reset time info}. Consider reducing polling frequency." | `{ label: "Open Settings", href: "/settings" }` |
| Status 500+ | "Server Error" | "Something went wrong on our end. Please wait a moment and try again." | — |
| Network/CORS | "Connection Error" | "Unable to reach the server. Check your network connection and try again." | — |
| Unknown | "Unexpected Error" | "An unexpected error occurred — please try again or contact support." | — |

---

### ChoreName

Represents a lightweight chore identifier returned by the `GET /{project_id}/chore-names` endpoint. Used exclusively for set-membership checks against template names.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| (value) | `string` | Yes | The chore name string. Returned as a plain `string[]` array, not wrapped in objects. |

#### Endpoint Response Shape

```json
["Daily Standup Prep", "PR Review Reminder", "Sprint Metrics Report"]
```

#### Validation Rules

- Response is always a `string[]` (never null, empty array for projects with no chores)
- Individual names are non-empty strings matching existing chore names in the database
- No pagination, no filtering, no sorting — returns the complete set

---

## Relationships

```text
┌──────────────────┐
│   ErrorBoundary   │──uses──▶ getErrorHint() ──returns──▶ ErrorHint
└──────────────────┘

┌──────────────────────────┐
│ ProjectBoardErrorBanners │──uses──▶ getErrorHint() ──returns──▶ ErrorHint
└──────────────────────────┘

┌──────────────┐
│  EmptyState   │◀──hint prop──── ErrorHint.hint
└──────────────┘

┌──────────────┐        ┌─────────────────┐
│ ChoresPanel  │──uses──▶ useAllChoreNames │──fetches──▶ /chore-names endpoint
└──────────────┘        └─────────────────┘
                                │
                            returns
                                │
                                ▼
                          ChoreName[] (string[])
```

## State Transitions

### Error Classification Flow

```text
Error occurs → getErrorHint(error) called at render time
  │
  ├─ Has HTTP status? ──▶ Classify by status code ──▶ Return mapped ErrorHint
  │
  ├─ Is TypeError / fetch failure? ──▶ Return "Connection Error" hint
  │
  └─ Unknown error type ──▶ Return generic fallback hint
```

### Chore Names Data Flow

```text
ChoresPanel mounts
  │
  ├─ useAllChoreNames(projectId) fires query
  │   └─ GET /api/v1/chores/{project_id}/chore-names
  │       └─ Returns string[] of ALL chore names (unpaginated)
  │
  ├─ Build Set<string> from response
  │
  └─ uncreatedTemplates = templates.filter(t => !namesSet.has(t.name))
      └─ Accurate regardless of pagination/filter state
```
