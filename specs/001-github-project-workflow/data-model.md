# Data Model: AI-Assisted GitHub Issue Creation and Workflow Management

**Date**: February 2, 2026  
**Spec**: [spec.md](./spec.md)

## Entity Definitions

### 1. IssueRecommendation

Represents an AI-generated structured recommendation for a GitHub Issue before user confirmation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| recommendation_id | UUID | Yes | Unique identifier for the recommendation |
| session_id | UUID | Yes | Chat session that created this recommendation |
| original_input | string | Yes | User's original feature request text |
| title | string | Yes | AI-generated issue title (max 256 chars) |
| user_story | string | Yes | User story in "As a... I want... So that..." format |
| ui_ux_description | string | Yes | UI/UX guidance for implementation |
| functional_requirements | string[] | Yes | List of specific, testable requirements |
| status | enum | Yes | PENDING, CONFIRMED, REJECTED |
| created_at | datetime | Yes | When recommendation was generated |
| confirmed_at | datetime | No | When user confirmed (if applicable) |

**Relationships**:
- Belongs to one `UserSession`
- Creates one `GitHubIssue` when confirmed

**Validation Rules**:
- `title` must be non-empty, max 256 characters
- `user_story` must follow standard format or be clearly descriptive
- `functional_requirements` must have at least 1 item
- `status` transitions: PENDING → CONFIRMED | REJECTED (one-way)

---

### 2. GitHubIssue (Extension)

Extends existing system knowledge of GitHub issues created via the workflow.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| issue_id | string | Yes | GitHub Issue node ID |
| issue_number | int | Yes | Human-readable issue number |
| repository_owner | string | Yes | Repository owner login |
| repository_name | string | Yes | Repository name |
| title | string | Yes | Issue title |
| body | string | Yes | Issue body (markdown) |
| html_url | string | Yes | URL to issue on GitHub |
| recommendation_id | UUID | No | Linked recommendation (if created via workflow) |
| project_item_id | string | No | GitHub Project item ID after attachment |
| created_at | datetime | Yes | When issue was created |
| workflow_status | enum | Yes | Current workflow state |

**Workflow Status Values**:
- `CREATED` - Issue created but not yet added to project
- `BACKLOG` - Added to project with Backlog status
- `READY` - Status updated to Ready
- `IN_PROGRESS` - Status In Progress, Copilot assigned
- `IN_REVIEW` - Status In Review, owner assigned
- `ERROR` - Workflow failed at some step

---

### 3. WorkflowTransition

Audit log for all status transitions and assignments in the workflow.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| transition_id | UUID | Yes | Unique identifier |
| issue_id | string | Yes | GitHub Issue node ID |
| project_id | string | Yes | GitHub Project node ID |
| from_status | string | No | Previous status (null for initial) |
| to_status | string | Yes | New status |
| assigned_user | string | No | User assigned (if applicable) |
| triggered_by | enum | Yes | AUTOMATIC, MANUAL, DETECTION |
| success | bool | Yes | Whether transition succeeded |
| error_message | string | No | Error details if failed |
| timestamp | datetime | Yes | When transition occurred |

**Purpose**: Enables FR-021 (log all status transitions and assignments for audit purposes).

---

### 4. WorkflowConfiguration

Configuration for the workflow orchestrator (per project).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| project_id | string | Yes | GitHub Project node ID |
| repository_owner | string | Yes | Target repository owner |
| repository_name | string | Yes | Target repository name |
| copilot_assignee | string | Yes | Username to assign for implementation (default: "github-copilot") |
| review_assignee | string | No | Username for review (default: repository owner) |
| status_backlog | string | Yes | Name of Backlog status column |
| status_ready | string | Yes | Name of Ready status column |
| status_in_progress | string | Yes | Name of In Progress status column |
| status_in_review | string | Yes | Name of In Review status column |
| enabled | bool | Yes | Whether workflow automation is active |

**Default Values**:
- `copilot_assignee`: "github-copilot" (requires valid account)
- `status_backlog`: "Backlog"
- `status_ready`: "Ready"
- `status_in_progress`: "In Progress"
- `status_in_review`: "In Review"

---

## State Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        WORKFLOW STATES                               │
└─────────────────────────────────────────────────────────────────────┘

[User Message]
      │
      ▼
┌──────────────┐   AI generates    ┌────────────────────┐
│  ANALYZING   │ ─────────────────►│  RECOMMENDATION    │
│              │   recommendation   │     PENDING        │
└──────────────┘                   └────────────────────┘
                                          │
                    ┌─────────────────────┴─────────────────────┐
                    │                                           │
              User confirms                               User rejects
                    │                                           │
                    ▼                                           ▼
           ┌──────────────┐                            ┌──────────────┐
           │   CREATING   │                            │   REJECTED   │
           │    ISSUE     │                            │    (End)     │
           └──────────────┘                            └──────────────┘
                    │
                    ▼
           ┌──────────────┐   Add to project   ┌──────────────┐
           │ ISSUE_CREATED│ ──────────────────►│   BACKLOG    │
           └──────────────┘                    └──────────────┘
                                                      │
                                               Auto-transition
                                                      │
                                                      ▼
                                               ┌──────────────┐
                                               │    READY     │
                                               └──────────────┘
                                                      │
                                            Status detection →
                                            Assign Copilot
                                                      │
                                                      ▼
                                               ┌──────────────┐
                                               │ IN_PROGRESS  │
                                               └──────────────┘
                                                      │
                                            Completion detected →
                                            Assign Owner
                                                      │
                                                      ▼
                                               ┌──────────────┐
                                               │  IN_REVIEW   │
                                               │    (End)     │
                                               └──────────────┘
```

## Existing Entities (Unchanged)

The following entities from the existing codebase remain unchanged:

- **Task** (`backend/src/models/task.py`) - GitHub Project items
- **GitHubProject** (`backend/src/models/project.py`) - Project board metadata
- **UserSession** (`backend/src/models/user.py`) - Authenticated user session
- **ChatMessage** (`backend/src/models/chat.py`) - Chat conversation messages
- **AITaskProposal** (`backend/src/models/chat.py`) - Existing task proposals (will coexist with IssueRecommendation)

## Data Flow

```
1. Feature Request Input
   User → ChatMessage → AI Agent → IssueRecommendation

2. Issue Creation
   IssueRecommendation (confirmed) → GitHub REST API → GitHubIssue

3. Project Attachment
   GitHubIssue → GitHub GraphQL API → Project Item → Task (existing model)

4. Workflow Transitions
   Status Detection → WorkflowTransition (audit) → GitHub GraphQL API
```
