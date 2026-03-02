# API Reference

All endpoints are prefixed with `/api/v1`. Interactive docs available at `/api/docs` when `DEBUG=true`.

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

## Webhooks

| Method | Path | Description |
|--------|------|-------------|
| POST | `/webhooks/github` | Handle GitHub webhook events (PR `ready_for_review`) |
