# Internal Event Contracts: Solune v0.1.0 Public Release

**Branch**: `050-solune-v010-release` | **Date**: 2026-03-17 | **Plan**: [plan.md](../plan.md)

## Overview

This document defines the internal event contracts for the Solune v0.1.0 release. Events are used for communication between services within the backend (FastAPI application), between the backend and GitHub (webhooks/labels), and between the backend and frontend (WebSocket messages). These are not REST API contracts — see [rest-api.md](./rest-api.md) for HTTP endpoints.

---

## Pipeline State Events

### Pipeline Run State Change

**Trigger**: Pipeline run transitions between states (pending → running → completed/failed/cancelled).

**Internal Event** (Python, emitted within service layer):

```python
@dataclass
class PipelineRunStateChanged:
    run_id: int
    pipeline_config_id: int
    project_id: str
    previous_status: str  # 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
    new_status: str
    timestamp: str  # ISO 8601
    error_message: str | None = None
```

**Consumers**:
- **Pipeline orchestrator**: Triggers next group execution or completes run
- **WebSocket notifier**: Pushes state update to connected frontends
- **Label manager**: Creates/updates GitHub labels for state tracking (FR-015)

---

### Pipeline Stage State Change

**Trigger**: Individual stage transitions between states.

**Internal Event**:

```python
@dataclass
class PipelineStageStateChanged:
    stage_state_id: int
    pipeline_run_id: int
    stage_id: str
    group_id: int | None
    previous_status: str  # 'pending' | 'running' | 'completed' | 'failed' | 'skipped'
    new_status: str
    agent_id: str | None
    timestamp: str  # ISO 8601
```

**Consumers**:
- **Group executor**: Determines if group is complete (all stages done) → triggers next group
- **Pipeline run manager**: Checks if all groups are complete → transitions run to 'completed'
- **WebSocket notifier**: Pushes stage update to connected frontends
- **Label manager**: Updates GitHub label for this stage

---

## GitHub Label Events (FR-015)

### Label Format

Labels follow a namespaced format to avoid collision with user labels:

```
solune:pipeline:{run_id}:stage:{stage_id}:{status}
```

**Examples**:
- `solune:pipeline:42:stage:build:running`
- `solune:pipeline:42:stage:build:completed`
- `solune:pipeline:42:stage:test:failed`

### Label Lifecycle

| Action | When | GitHub API Call |
|--------|------|-----------------|
| Create label | Stage transitions to 'running' (first time) | `POST /repos/{owner}/{repo}/labels` |
| Update label | Stage transitions to new state | Delete old + create new (GitHub labels are immutable names) |
| Query labels | Pipeline recovery on startup | `GET /repos/{owner}/{repo}/labels?per_page=100&q=solune:pipeline:` |

### Recovery Protocol (FR-002)

On application startup:
1. Query all `solune:pipeline:*` labels from GitHub
2. Parse run IDs and stage states from label names
3. Compare with persistent DB state
4. Reconcile any discrepancies (DB is source of truth, labels are supplementary)
5. Resume any runs in 'running' state

**Benefit**: Reduces API calls by ~60% for recovery — labels are queryable in a single API call vs. polling individual stage states.

---

## WebSocket Events

### Connection

**URL**: `ws://localhost:8000/api/v1/ws/pipeline/{project_id}`

**Authentication**: Session cookie (same as REST API)

### Server → Client Messages

#### Pipeline Run Update

```json
{
  "type": "pipeline.run.updated",
  "data": {
    "run_id": 1,
    "status": "running",
    "timestamp": "2026-03-17T15:00:00Z"
  }
}
```

#### Pipeline Stage Update

```json
{
  "type": "pipeline.stage.updated",
  "data": {
    "run_id": 1,
    "stage_id": "build",
    "status": "completed",
    "agent_id": "agent-build-01",
    "timestamp": "2026-03-17T15:05:00Z"
  }
}
```

#### Agent Activity Update

```json
{
  "type": "agent.activity",
  "data": {
    "agent_id": "agent-build-01",
    "pipeline_run_id": 1,
    "stage_id": "build",
    "activity": "Analyzing code structure...",
    "timestamp": "2026-03-17T15:02:30Z"
  }
}
```

### Client → Server Messages

#### Subscribe to Pipeline

```json
{
  "type": "subscribe",
  "data": {
    "pipeline_config_id": 42
  }
}
```

#### Unsubscribe

```json
{
  "type": "unsubscribe",
  "data": {
    "pipeline_config_id": 42
  }
}
```

---

## MCP Propagation Events (FR-019)

### MCP Config Updated

**Trigger**: User updates project MCP tool configuration via settings.

**Internal Event**:

```python
@dataclass
class MCPConfigUpdated:
    project_id: str
    tools: list[str]  # ["*"] or explicit tool list
    updated_by: str  # GitHub user ID
    timestamp: str  # ISO 8601
```

**Consumers**:
- **Agent file writer**: Updates all agent configuration files for the project
- **Agent service**: Refreshes in-memory agent tool configuration

### Agent File Update

**Trigger**: MCP config propagation writes updated configuration to agent files.

**File Format** (YAML, written to agent config directory):

```yaml
# Auto-generated by Solune MCP sync
# Last updated: 2026-03-17T15:00:00Z
name: agent-build-01
tools:
  - "*"
mcp_config:
  version: "1.0"
  tools:
    - name: "code-search"
      enabled: true
    - name: "file-edit"
      enabled: true
```

---

## Startup Validation Events (FR-005, FR-048)

### Startup Check Results

**Trigger**: Application startup, before accepting any requests.

**Internal Event**:

```python
@dataclass
class StartupValidationResult:
    check_name: str  # 'encryption_key' | 'session_secret' | 'database' | 'github_oauth'
    status: str  # 'configured' | 'missing' | 'using_default' | 'connected' | 'error'
    message: str | None = None
    blocking: bool = True  # If True, startup is aborted on failure
```

**Behavior**:
- All blocking checks MUST pass before the application accepts requests
- Failed blocking checks cause the application to exit with a clear error message listing ALL failures (not one at a time — spec edge case #3)
- Non-blocking checks log warnings but allow startup

### Required Startup Checks

| Check | Blocking | Condition for Pass |
|-------|----------|-------------------|
| `encryption_key` | Yes | `ENCRYPTION_KEY` is set, not empty, valid Fernet key |
| `session_secret` | Yes (production) | `SESSION_SECRET_KEY` is set, not default, ≥64 chars |
| `github_oauth` | Yes | `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` are set |
| `database` | Yes | SQLite database is accessible, migrations are current |
| `debug_mode` | Yes (production) | `DEBUG` is not `true` when `ENCRYPTION_KEY` is production-grade |
| `webhook_secret` | No | `GITHUB_WEBHOOK_SECRET` is set (warn if missing) |

**Production Detection**: The system considers itself in production mode when `ENCRYPTION_KEY` is set to a non-default value AND `FRONTEND_URL` does not contain `localhost`.

---

## Onboarding Tour Events (FR-038)

### Tour State Change

**Internal Event**:

```python
@dataclass
class OnboardingTourStateChanged:
    user_id: str
    action: str  # 'started' | 'advanced' | 'dismissed' | 'completed' | 'restarted'
    step: int  # Current step after action
    timestamp: str  # ISO 8601
```

**Consumers**:
- **Analytics** (future): Track onboarding completion rates
- **Help page**: Display tour restart option when `action` was 'dismissed' or 'completed'

### Tour Steps (9 steps, celestial-themed per spec assumption #8)

| Step | Target Element | Content |
|------|---------------|---------|
| 1 | Welcome overlay | "Welcome to Solune — your AI-powered development companion" |
| 2 | Projects sidebar | "Projects are your workspaces. Each represents a GitHub repository." |
| 3 | Create Project button | "Start by creating your first project." |
| 4 | Pipeline config section | "Configure how your AI agents work together." |
| 5 | Pipeline builder | "Design your pipeline visually with drag and drop." |
| 6 | Agents panel | "Meet your AI agents. They work in parallel to accelerate your workflow." |
| 7 | Chat input | "Chat with your agents directly. Attach files, use voice input." |
| 8 | Settings gear | "Customize Solune to fit your workflow." |
| 9 | Help icon | "Need help? Find FAQs and restart this tour anytime." |
