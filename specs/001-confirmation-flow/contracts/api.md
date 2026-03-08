# API Contracts: Confirmation Flow for Critical Actions

**Feature**: 001-confirmation-flow | **Date**: 2026-03-08

## No New Backend Endpoints

This feature is entirely a frontend UI concern. No new backend API endpoints are required. The confirmation dialog is a client-side component that intercepts user actions before they are dispatched to the existing backend API.

---

## Existing Endpoints Referenced (Unchanged)

The following existing endpoints are called after the user confirms an action. Their contracts are unchanged — only the frontend trigger mechanism changes (from `window.confirm()` to the `useConfirmation` hook).

### Delete Agent

```text
DELETE /api/v1/agents/{project_id}/{agent_id}
```

**Description**: Deletes an agent configuration. For repo-sourced agents, this opens a PR to delete the `.agent.md` file. For locally-created agents, this removes the SQLite record directly.

**Called by**: `AgentCard.tsx` → `handleDelete` (after user confirms via `useConfirmation`)

**Request**: No body required.

**Response** (200 OK):

```json
{
  "agent": { /* deleted AgentConfig object */ },
  "pr_url": "https://github.com/owner/repo/pull/42",
  "pr_number": 42
}
```

---

### Clear Pending Agents

```text
DELETE /api/v1/agents/{project_id}/pending
```

**Description**: Removes all pending/stale agent records from the local SQLite database for a project. Does not affect the repository or any active agent configurations.

**Called by**: `AgentsPanel.tsx` → `handleClearPending` (after user confirms via `useConfirmation`)

**Request**: No body required.

**Response** (200 OK):

```json
{
  "deleted_count": 3
}
```

---

### Delete Chore

```text
DELETE /api/v1/chores/{project_id}/{chore_id}
```

**Description**: Permanently deletes a chore definition and its associated trigger history.

**Called by**: `ChoreCard.tsx` → `handleDelete` (after user confirms via `useConfirmation`)

**Request**: No body required.

**Response** (200 OK):

```json
{
  "success": true
}
```

---

### Delete Pipeline

```text
DELETE /api/v1/pipelines/{project_id}
```

**Description**: Deletes the agent pipeline configuration for a project.

**Called by**: `AgentsPipelinePage.tsx` → `handleDelete` (after user confirms via `useConfirmation`)

**Request**: No body required.

**Response** (200 OK):

```json
{
  "success": true
}
```

---

## Frontend API Client

No new API client methods are needed. The existing mutation hooks (`useDeleteAgent`, `useClearPendingAgents`, `useDeleteChore`, pipeline delete mutation) remain unchanged. Only the call sites that invoke these mutations are modified to use the new confirmation flow.

## Query Keys (TanStack Query)

No new query keys are introduced. Existing mutation invalidation patterns remain unchanged:

| Operation | Mutation Hook | Invalidates |
|-----------|--------------|-------------|
| Delete Agent | `useDeleteAgent` | `['agents', 'list', projectId]` |
| Clear Pending | `useClearPendingAgents` | `['agents', 'pending', projectId]` |
| Delete Chore | `useDeleteChore` | `['chores', projectId]` |
| Delete Pipeline | Pipeline delete mutation | `['pipeline', projectId]` |
