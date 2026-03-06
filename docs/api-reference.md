# API Reference

This document lists every HTTP, WebSocket, and SSE endpoint exposed by the backend. Use it to understand which paths exist, what authentication they require, and what they do.

All endpoints are prefixed with `/api/v1`. Interactive docs available at `/api/docs` when `DEBUG=true`.

Unless noted, all endpoints require an active session cookie set by the OAuth flow. The `/health`, `/auth/github`, and `/auth/github/callback` endpoints are unauthenticated.

## Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |

## Authentication

| Method | Path | Description |
|--------|------|-------------|
| GET | `/auth/github` | Initiate GitHub OAuth flow |
| GET | `/auth/github/callback` | OAuth callback handler |
| POST | `/auth/session` | Set session cookie from token |
| GET | `/auth/me` | Get current authenticated user |
| POST | `/auth/logout` | Logout and clear session |
| POST | `/auth/dev-login` | Dev-only PAT login (`DEBUG=true` only) |

## Projects

| Method | Path | Description |
|--------|------|-------------|
| GET | `/projects` | List user's GitHub Projects |
| GET | `/projects/{id}` | Get project details |
| GET | `/projects/{id}/tasks` | Get project tasks |
| POST | `/projects/{id}/select` | Select active project (starts polling) |
| WS | `/projects/{id}/subscribe` | WebSocket for real-time updates |
| GET | `/projects/{id}/events` | SSE fallback for real-time updates |

## Board

| Method | Path | Description |
|--------|------|-------------|
| GET | `/board/projects` | List projects with status field configuration |
| GET | `/board/projects/{project_id}` | Get board data (columns + items) |

## Chat

| Method | Path | Description |
|--------|------|-------------|
| GET | `/chat/messages` | Get chat messages for session |
| POST | `/chat/messages` | Send message, get AI response (supports `#agent` command) |
| DELETE | `/chat/messages` | Clear chat history |
| POST | `/chat/proposals/{id}/confirm` | Confirm task proposal |
| DELETE | `/chat/proposals/{id}` | Cancel task proposal |

### `#agent` Command

Send `#agent <description> #<status-name>` via chat or Signal to create a custom GitHub agent:
- Fuzzy status column matching (`#in-review`, `#InReview`, `#IN_REVIEW`)
- AI-generated preview with natural language edit loop
- 8-step pipeline: save config → create column → create issue → create branch → commit files → open PR → move to In Review → update pipeline mappings

## Tasks

| Method | Path | Description |
|--------|------|-------------|
| POST | `/tasks` | Create a task (GitHub Issue + project attachment) |
| PATCH | `/tasks/{id}/status` | Update task status |

## Chores

| Method | Path | Description |
|--------|------|-------------|
| GET | `/chores/{project_id}` | List all chores for a project |
| POST | `/chores/{project_id}` | Create a new chore (generates template, commits via PR, creates tracking issue) |
| PATCH | `/chores/{project_id}/{chore_id}` | Update a chore (schedule, status) |
| DELETE | `/chores/{project_id}/{chore_id}` | Remove a chore, closing any open associated issue |
| POST | `/chores/{project_id}/{chore_id}/trigger` | Manually trigger a chore — creates a GitHub issue and runs agent pipeline |
| POST | `/chores/{project_id}/chat` | Interactive chat for sparse-input template refinement |
| POST | `/chores/evaluate-triggers` | Evaluate all active chores for trigger conditions |

## Cleanup

| Method | Path | Description |
|--------|------|-------------|
| POST | `/cleanup/preflight` | Preflight check: compute branch/PR deletion lists without mutations |
| POST | `/cleanup/execute` | Execute cleanup: delete branches and close PRs (main branch protected) |
| GET | `/cleanup/history` | Retrieve audit trail of past cleanup operations |

## Settings

| Method | Path | Description |
|--------|------|-------------|
| GET | `/settings/user` | Get effective user settings |
| PUT | `/settings/user` | Update user preferences |
| GET | `/settings/global` | Get global settings |
| PUT | `/settings/global` | Update global settings |
| GET | `/settings/project/{project_id}` | Get effective project settings |
| PUT | `/settings/project/{project_id}` | Update project-specific settings |

## Workflow & Pipeline

| Method | Path | Description |
|--------|------|-------------|
| POST | `/workflow/recommendations/{id}/confirm` | Confirm issue recommendation → full workflow |
| POST | `/workflow/recommendations/{id}/reject` | Reject recommendation |
| POST | `/workflow/pipeline/{issue_number}/retry` | Retry a failed/stalled agent |
| GET | `/workflow/config` | Get workflow configuration |
| PUT | `/workflow/config` | Update workflow configuration |
| GET | `/workflow/agents` | List available agents (repo + built-in) |
| GET | `/workflow/transitions` | Get transition audit log |
| GET | `/workflow/pipeline-states` | Get all active pipeline states |
| GET | `/workflow/pipeline-states/{issue_number}` | Get pipeline state for specific issue |
| POST | `/workflow/notify/in-review` | Send In Review notification |
| GET | `/workflow/polling/status` | Get polling service status |
| POST | `/workflow/polling/start` | Start background polling |
| POST | `/workflow/polling/stop` | Stop background polling |
| POST | `/workflow/polling/check-issue/{issue_number}` | Manually check a specific issue |
| POST | `/workflow/polling/check-all` | Check all In Progress issues |

## Signal

| Method | Path | Description |
|--------|------|-------------|
| GET | `/signal/connection` | Get Signal connection status |
| POST | `/signal/connection/link` | Generate QR code for linking |
| GET | `/signal/connection/link/status` | Poll link completion status |
| DELETE | `/signal/connection` | Disconnect Signal account |
| GET | `/signal/preferences` | Get notification preferences |
| PUT | `/signal/preferences` | Update notification preferences |
| GET | `/signal/banners` | Get active conflict banners |
| POST | `/signal/banners/{id}/dismiss` | Dismiss a conflict banner |

## Agents

Manage custom GitHub Agent configurations stored per-project.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/agents/{project_id}` | List all agents for a project (merged from SQLite + GitHub repo) |
| POST | `/agents/{project_id}` | Create a new agent configuration |
| PATCH | `/agents/{project_id}/{agent_id}` | Update an existing agent configuration |
| DELETE | `/agents/{project_id}/{agent_id}` | Delete an agent configuration |
| POST | `/agents/{project_id}/chat` | Conversational refinement of an agent definition |

## MCP

Manage Model Context Protocol server configurations (stored per-user, under the `/settings` prefix).

| Method | Path | Description |
|--------|------|-------------|
| GET | `/settings/mcps` | List all MCP configurations for the authenticated user |
| POST | `/settings/mcps` | Add a new MCP configuration |
| DELETE | `/settings/mcps/{mcp_id}` | Remove an MCP configuration (owner only) |

## Metadata

Read and refresh cached GitHub repository metadata (labels, branches, milestones, collaborators).

| Method | Path | Description |
|--------|------|-------------|
| GET | `/metadata/{owner}/{repo}` | Get cached repository metadata context |
| POST | `/metadata/{owner}/{repo}/refresh` | Force-refresh metadata cache for a repository |

## Webhooks

| Method | Path | Description |
|--------|------|-------------|
| POST | `/webhooks/github` | Handle GitHub webhook events (PR `ready_for_review`) |
