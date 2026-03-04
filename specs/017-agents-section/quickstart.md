# Quickstart: Agents Section on Project Board

**Feature**: `017-agents-section` | **Date**: 2026-03-03

## Overview

The Agents section adds a new panel below the existing Chores section on the project board page. It lets users view, create, delete, and (P3) edit Custom GitHub Agent configurations directly from the UI.

## Prerequisites

- Running instance of the app (frontend + backend via `docker compose up`)
- Authenticated user with a valid session
- A GitHub project selected on the project board page
- Repository must have write access for the authenticated user

## Quick Walkthrough

### Viewing Agents

1. Navigate to the project board page
2. Select a project from the dropdown
3. The **Agents** section appears below **Chores** in the right-side panel
4. Each agent card shows:
   - Name and description
   - Status badge: **Active** (green) or **Pending PR** (yellow)
   - Delete button

### Creating an Agent

**Direct (detailed input):**

1. Click **+ Add Agent** in the Agents section header
2. Enter the agent name (e.g., "Security Reviewer")
3. Enter the description (one-line summary)
4. Enter the system prompt (detailed instructions for the agent)
5. Optionally configure tools and pipeline column
6. Click **Create**
7. System creates a branch, commits `.agent.md` + `.prompt.md` files, and opens a PR
8. Success confirmation shows a link to the PR

**AI-assisted (sparse input):**

1. Click **+ Add Agent**
2. Enter just a brief description (e.g., "reviews code for security issues")
3. System detects sparse input and opens a chat refinement flow
4. Answer the AI's clarifying questions
5. Review the generated agent preview
6. Confirm to create the agent

### Deleting an Agent

1. Click the delete button on an agent card
2. Confirm the deletion in the dialog
3. System opens a PR to remove the agent files from the repository
4. The agent is removed from the local list immediately

### Pipeline Integration

- Agents are immediately available for pipeline assignment upon creation
- Open the Settings page → Agent Pipeline section
- Newly created agents appear in the agent dropdown even before their PR is merged

## API Endpoints

All endpoints are under `/api/v1/agents/`:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/{project_id}` | List all agents (merged from SQLite + repo) |
| POST | `/{project_id}` | Create a new agent |
| PATCH | `/{project_id}/{agent_id}` | Update an agent (P3) |
| DELETE | `/{project_id}/{agent_id}` | Delete an agent (opens removal PR) |
| POST | `/{project_id}/chat` | AI chat refinement for sparse input |

## Key Files

### Backend
- `backend/src/api/agents.py` — REST router
- `backend/src/services/agents/service.py` — Business logic
- `backend/src/models/agents.py` — Pydantic models
- `backend/src/services/agent_creator.py` — Shared file generation functions

### Frontend
- `frontend/src/components/agents/AgentsPanel.tsx` — Container panel
- `frontend/src/components/agents/AgentCard.tsx` — Individual agent card
- `frontend/src/components/agents/AddAgentModal.tsx` — Creation form
- `frontend/src/hooks/useAgents.ts` — TanStack Query hooks
- `frontend/src/services/api.ts` — API client (`agentsApi` object)

### Documentation
- `docs/custom-agents-best-practices.md` — Best practices guide

## Agent File Format

Created agents produce two files:

**`.github/agents/<slug>.agent.md`:**
```yaml
---
description: One-line description of the agent
tools: ["read", "edit", "search"]
---

Full system prompt content goes here...
```

**`.github/prompts/<slug>.prompt.md`:**
````
```prompt
---
agent: <slug>
---
```
````
