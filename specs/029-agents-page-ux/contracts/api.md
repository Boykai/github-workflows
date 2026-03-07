# API Contracts: Agents Page — Sun/Moon Avatars, Featured Agents, Inline Editing with PR Flow, Bulk Model Update, Repo Name Display & Tools Editor

**Feature**: 029-agents-page-ux | **Date**: 2026-03-07

## Base URL

All endpoints are prefixed with `/api/v1/agents` and require an authenticated session (same auth pattern as existing endpoints in `/api/v1/agents/*`).

---

## New Endpoints

### Bulk Update Agent Models

```
PATCH /api/v1/agents/{project_id}/bulk-model
```

**Description**: Update the default model for all active agents in a project. Applies the specified model as a runtime preference to all agents (both repo-sourced and locally-created). This does not create PRs — model preferences are stored locally in SQLite as runtime overrides, consistent with the existing per-agent model update behavior.

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | string | The project identifier |

**Request Body**:
```json
{
  "target_model_id": "gpt-4o",
  "target_model_name": "GPT-4o"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `target_model_id` | string | Yes | The model ID to apply to all agents (1–200 chars) |
| `target_model_name` | string | Yes | The display name of the target model (1–200 chars) |

**Response** (200 OK):
```json
{
  "success": true,
  "updated_count": 8,
  "failed_count": 0,
  "updated_agents": [
    "security-reviewer",
    "code-helper",
    "doc-writer",
    "test-runner",
    "debug-agent",
    "refactor-bot",
    "linter-agent",
    "deploy-agent"
  ],
  "failed_agents": [],
  "target_model_id": "gpt-4o",
  "target_model_name": "GPT-4o"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | `true` if all agents updated, `false` if any failed |
| `updated_count` | integer | Number of agents successfully updated |
| `failed_count` | integer | Number of agents that failed to update |
| `updated_agents` | string[] | Slugs of successfully updated agents |
| `failed_agents` | string[] | Slugs of agents that failed (with error details in logs) |
| `target_model_id` | string | The model ID that was applied |
| `target_model_name` | string | The display name of the model that was applied |

**Error Responses**:
- `400 Bad Request` — Missing or invalid `target_model_id` / `target_model_name`
  ```json
  {
    "detail": "target_model_id and target_model_name are required"
  }
  ```
- `401 Unauthorized` — Missing or invalid session
- `404 Not Found` — Project not found
  ```json
  {
    "detail": "Project not found"
  }
  ```

---

## Existing Endpoints (Unchanged but Referenced)

### Update Agent (Used by Inline Editor Save)

```
PATCH /api/v1/agents/{project_id}/{agent_id}
```

**Description**: Update an agent's configuration. When changes affect repo-committed fields (name, description, system_prompt, tools), a PR is created. When only the model is changed, it's stored as a runtime preference without a PR.

**Already implemented** — the inline editor save flow calls this endpoint. No changes to the endpoint contract. The frontend enhancement is to surface the `pr_url` from the `AgentCreateResult` response in a success toast/notification.

**Response** (200 OK): Returns `AgentCreateResult`:
```json
{
  "agent": { /* AgentConfig object */ },
  "pr_url": "https://github.com/owner/repo/pull/42",
  "pr_number": 42,
  "issue_number": 15,
  "branch_name": "agent/update-my-agent"
}
```

### List Agents (Used by Featured Agents, Bulk Update Dialog)

```
GET /api/v1/agents/{project_id}
```

**Already implemented** — returns all agents from the repo's default branch. The Featured Agents selection logic runs entirely on the frontend using this data. The bulk update confirmation dialog also uses this list to show which agents will be affected.

### Get Agent Tools (Used by Tools Editor)

```
GET /api/v1/agents/{project_id}/{agent_id}/tools
```

**Already implemented** — returns the tools assigned to an agent. Used by the tools editor to populate the current tool list.

### Update Agent Tools (Used by Tools Editor Save)

```
PUT /api/v1/agents/{project_id}/{agent_id}/tools
```

**Already implemented** — replaces all tools for an agent. The tools editor submits the reordered tool list via this endpoint (tool order is preserved in the array). Note: This is a separate endpoint from the agent update (`PATCH /{agent_id}`). When the inline editor saves, it calls both the agent update endpoint (for name, description, system_prompt) and the tools update endpoint (for tool list changes) if tools were modified.

---

## Frontend API Client Methods

Added to `frontend/src/services/api.ts` in the `agentsApi` namespace:

```typescript
// Bulk model update
agentsApi: {
  // Existing methods remain unchanged...

  bulkUpdateModels: async (
    projectId: string,
    targetModelId: string,
    targetModelName: string,
  ): Promise<BulkModelUpdateResult> => {
    const response = await fetch(
      `${API_BASE}/agents/${projectId}/bulk-model`,
      {
        method: 'PATCH',
        headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_model_id: targetModelId,
          target_model_name: targetModelName,
        }),
      },
    );
    if (!response.ok) {
      throw new Error(`Bulk model update failed: ${response.statusText}`);
    }
    return response.json();
  },
}
```

---

## Query Keys (TanStack Query)

| Operation | Type | Key | Notes |
|-----------|------|-----|-------|
| Bulk model update | Mutation | N/A | Invalidates `['agents', 'list', projectId]` on success |
| Update agent (inline editor save) | Mutation | N/A | Already exists; invalidates agents list + pending |
| List agents | Query | `['agents', 'list', projectId]` | Already exists; used by Featured Agents + Bulk dialog |
| Agent tools | Query | `['agent-tools', projectId, agentId]` | Already exists; used by tools editor |
| Update agent tools | Mutation | N/A | Already exists; invalidates agent-tools query |

---

## Repository Name Parsing

The repository name is derived from the project context, not from the agent model. The parsing logic:

```typescript
// Extract repo name from "owner/repo" format
function getRepoName(fullRepo: string): string {
  const parts = fullRepo.split('/');
  return parts[parts.length - 1] || fullRepo;
}
```

This is a pure frontend presentation concern — no API changes needed. The repo name is displayed on agent cards as a chip/bubble with CSS truncation.
