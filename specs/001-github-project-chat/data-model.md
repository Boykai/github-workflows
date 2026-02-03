# Data Model: GitHub Projects Chat Interface

**Date**: 2026-01-30
**Feature**: 001-github-project-chat

## Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐
│   UserSession   │       │  GitHubProject  │
├─────────────────┤       ├─────────────────┤
│ session_id (PK) │       │ project_id (PK) │
│ github_user_id  │──────<│ owner_id        │
│ access_token    │       │ name            │
│ refresh_token   │       │ type            │
│ token_expires   │       │ url             │
│ selected_proj   │───────│ status_columns  │
│ created_at      │       └─────────────────┘
│ updated_at      │               │
└─────────────────┘               │ 1:N
                                  │
                          ┌───────┴───────┐
                          │     Task      │
                          ├───────────────┤
                          │ task_id (PK)  │
                          │ project_id(FK)│
                          │ title         │
                          │ description   │
                          │ status        │
                          │ github_item_id│
                          │ created_at    │
                          │ updated_at    │
                          └───────────────┘

┌─────────────────┐       ┌─────────────────┐
│   ChatMessage   │       │ AITaskProposal  │
├─────────────────┤       ├─────────────────┤
│ message_id (PK) │       │ proposal_id(PK) │
│ session_id (FK) │       │ session_id (FK) │
│ sender_type     │       │ original_input  │
│ content         │       │ proposed_title  │
│ action_type     │       │ proposed_desc   │
│ action_data     │       │ status          │
│ timestamp       │       │ created_at      │
└─────────────────┘       │ expires_at      │
                          └─────────────────┘
```

## Entities

### UserSession

Represents an authenticated user's session with GitHub OAuth tokens and preferences.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| session_id | UUID | Yes | Unique session identifier |
| github_user_id | string | Yes | GitHub user ID from OAuth |
| github_username | string | Yes | GitHub username for display |
| github_avatar_url | string | No | User's avatar URL |
| access_token | string | Yes | Encrypted GitHub OAuth access token |
| refresh_token | string | No | Encrypted OAuth refresh token |
| token_expires_at | datetime | No | Token expiration timestamp |
| selected_project_id | string | No | Currently selected GitHub Project ID |
| created_at | datetime | Yes | Session creation time |
| updated_at | datetime | Yes | Last activity time |

**Validation Rules**:
- `access_token` must be encrypted at rest
- `session_id` is generated server-side (UUID v4)
- `updated_at` refreshed on every authenticated request
- Session expires after 8 hours of inactivity

**State Transitions**:
```
Created → Active → Expired
           │
           └──→ Revoked (on logout or token revocation)
```

### GitHubProject

Represents a GitHub Project V2 board accessible to the user.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| project_id | string | Yes | GitHub Project V2 node ID (PVT_xxx) |
| owner_id | string | Yes | Owner (user/org) node ID |
| owner_login | string | Yes | Owner username/org name |
| name | string | Yes | Project display name |
| type | enum | Yes | PROJECT_TYPE: 'organization', 'user', 'repository' |
| url | string | Yes | GitHub web URL for the project |
| description | string | No | Project description |
| status_columns | array | Yes | List of StatusColumn objects |
| item_count | integer | No | Total items in project |
| cached_at | datetime | Yes | When this data was fetched |

**StatusColumn** (embedded):
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| field_id | string | Yes | Status field node ID |
| name | string | Yes | Column display name (e.g., "Todo") |
| option_id | string | Yes | Option ID for this status value |
| color | string | No | Display color |

**Validation Rules**:
- `project_id` must match GitHub's Project V2 ID format
- `type` must be one of the defined enum values
- `status_columns` must have at least one entry

### Task

Represents a work item in a GitHub Project (draft item or linked issue).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| task_id | UUID | Yes | Internal task identifier |
| project_id | string | Yes | Parent project ID (FK) |
| github_item_id | string | Yes | GitHub Project item node ID |
| github_content_id | string | No | Linked issue/PR node ID (if not draft) |
| title | string | Yes | Task title (max 256 chars) |
| description | string | No | Task body/description (max 65535 chars) |
| status | string | Yes | Current status column name |
| status_option_id | string | Yes | Status field option ID |
| assignees | array | No | List of assigned user logins |
| created_at | datetime | Yes | Task creation time |
| updated_at | datetime | Yes | Last modification time |

**Validation Rules**:
- `title` max length: 256 characters
- `description` max length: 65,535 characters
- `status` must match a valid `status_columns` entry in parent project

**State Transitions** (status-based):
```
Todo → In Progress → Done
  │         │          │
  └─────────┴──────────┴──→ (any other custom status)
```

### ChatMessage

Represents a single message in the chat conversation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| message_id | UUID | Yes | Unique message identifier |
| session_id | UUID | Yes | Parent session ID (FK) |
| sender_type | enum | Yes | SENDER_TYPE: 'user', 'assistant', 'system' |
| content | string | Yes | Message text content |
| action_type | enum | No | ACTION_TYPE: 'task_create', 'status_update', 'project_select', null |
| action_data | object | No | Action-specific payload (JSON) |
| timestamp | datetime | Yes | Message timestamp |

**ActionData Schemas** (by action_type):

`task_create`:
```json
{
  "proposal_id": "uuid",
  "task_id": "uuid",
  "status": "pending|confirmed|cancelled"
}
```

`status_update`:
```json
{
  "task_id": "uuid",
  "old_status": "string",
  "new_status": "string",
  "confirmed": boolean
}
```

`project_select`:
```json
{
  "project_id": "string",
  "project_name": "string"
}
```

**Validation Rules**:
- `content` max length: 10,000 characters
- `action_data` must validate against schema for `action_type`
- Messages are session-scoped (not persisted across sessions in MVP)

### AITaskProposal

Temporary entity for AI-generated tasks awaiting user confirmation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| proposal_id | UUID | Yes | Unique proposal identifier |
| session_id | UUID | Yes | Parent session ID (FK) |
| original_input | string | Yes | User's original natural language input |
| proposed_title | string | Yes | AI-generated task title |
| proposed_description | string | Yes | AI-generated task description |
| status | enum | Yes | PROPOSAL_STATUS: 'pending', 'confirmed', 'edited', 'cancelled' |
| edited_title | string | No | User-modified title (if edited) |
| edited_description | string | No | User-modified description (if edited) |
| created_at | datetime | Yes | Proposal creation time |
| expires_at | datetime | Yes | Auto-expiration time (created_at + 10 min) |

**Validation Rules**:
- `proposed_title` max length: 256 characters
- `proposed_description` max length: 65,535 characters
- Auto-expire and set `status` to 'cancelled' after `expires_at`

**State Transitions**:
```
                    ┌──→ confirmed ──→ (Task created)
                    │
pending ──→ edited ─┼──→ confirmed ──→ (Task created)
   │                │
   │                └──→ cancelled
   │
   └──────────────────→ cancelled (timeout or user cancel)
```

## Enumerations

### PROJECT_TYPE
```python
class ProjectType(str, Enum):
    ORGANIZATION = "organization"
    USER = "user"
    REPOSITORY = "repository"
```

### SENDER_TYPE
```python
class SenderType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
```

### ACTION_TYPE
```python
class ActionType(str, Enum):
    TASK_CREATE = "task_create"
    STATUS_UPDATE = "status_update"
    PROJECT_SELECT = "project_select"
```

### PROPOSAL_STATUS
```python
class ProposalStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    EDITED = "edited"
    CANCELLED = "cancelled"
```

## Indexes and Performance

### Recommended Indexes (for future database storage)

| Entity | Index | Type | Rationale |
|--------|-------|------|-----------|
| UserSession | session_id | Primary | Fast session lookup |
| UserSession | github_user_id | Unique | User lookup |
| UserSession | updated_at | B-tree | Session cleanup |
| GitHubProject | project_id | Primary | Project lookup |
| GitHubProject | owner_id | B-tree | User's projects query |
| Task | task_id | Primary | Task lookup |
| Task | project_id, status | Composite | Board view queries |
| ChatMessage | session_id, timestamp | Composite | Message history |
| AITaskProposal | session_id, status | Composite | Active proposals |

## API Response Shapes

### Project List Response
```json
{
  "projects": [
    {
      "project_id": "PVT_xxx",
      "name": "Sprint 42",
      "type": "organization",
      "owner_login": "acme-corp",
      "item_count": 24,
      "status_columns": [
        {"name": "Todo", "field_id": "PVTSSF_xxx", "option_id": "xxx"},
        {"name": "In Progress", "field_id": "PVTSSF_xxx", "option_id": "yyy"},
        {"name": "Done", "field_id": "PVTSSF_xxx", "option_id": "zzz"}
      ]
    }
  ]
}
```

### Task Preview Response (AI-generated)
```json
{
  "proposal_id": "550e8400-e29b-41d4-a716-446655440000",
  "proposed_title": "Add OAuth2 authentication flow",
  "proposed_description": "## Overview\nImplement GitHub OAuth2 authentication...\n\n## Technical Details\n- Use authorization code flow with PKCE\n- Store tokens securely in session\n\n## Acceptance Criteria\n- [ ] User can log in with GitHub\n- [ ] Token refresh works automatically",
  "original_input": "Add authentication so users can log in with their GitHub accounts",
  "status": "pending",
  "expires_at": "2026-01-30T12:10:00Z"
}
```
