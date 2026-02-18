# Research: Custom Agent Workflow Configuration UI

**Feature**: 004-agent-workflow-config-ui | **Date**: 2026-02-17

---

## R1: GitHub Agent Discovery API

### Decision
Use the **GitHub Contents API** to read `.github/agents/*.agent.md` files, combined with a hardcoded list of built-in agents.

### Rationale
- **No dedicated listing API exists** — GitHub treats custom agents as file-based configuration, not as a first-class API resource. No REST endpoint like `GET /repos/{owner}/{repo}/copilot/agents` exists. GraphQL has no `customAgents` field.
- The existing codebase already uses the GitHub REST API with OAuth tokens that have repo contents access (see `github_projects.py`'s `_client.get` helper).
- File format is `.agent.md` (markdown with YAML frontmatter), **not** `.yml` — correcting the original spec assumption.

### Alternatives Considered
| Alternative | Why Rejected |
|---|---|
| GraphQL query for agents | No such field exists in GitHub's GraphQL schema |
| GitHub MCP Server tools | No agent-listing tool available |
| `suggestedActors` GraphQL query | Only returns assignable actors (users/bots), not custom agent profiles |
| Hardcode agent list | Would break when users add/remove custom agents from repos |
| GitHub CLI (`gh copilot`) | Not a server-side API |

### Key API Details

**List agent files:**
```
GET /repos/{owner}/{repo}/contents/.github/agents
Accept: application/vnd.github+json
```
- 200: Array of content objects (filter for `*.agent.md`)
- 404: Directory doesn't exist → no custom agents, return built-in only

**Read agent file:**
```
GET /repos/{owner}/{repo}/contents/.github/agents/{filename}
Accept: application/vnd.github.raw+json
```
Returns raw markdown. Parse YAML frontmatter for `name`, `description`, `tools`.

**Agent file format (`.agent.md`):**
```markdown
---
name: readme-creator
description: Agent specializing in creating and improving README files
tools: ["read", "edit", "search"]
model: claude-opus-4.6
target: github-copilot
---

Prompt instructions in markdown body...
```

Frontmatter fields: `name` (optional, defaults to filename), `description` (required), `tools` (optional), `model` (optional, IDE-only), `target` (optional: `vscode` | `github-copilot`).

**Built-in agents (always available):**
- GitHub Copilot (`copilot`) — default coding agent
- GitHub Copilot Review (`copilot-review`) — code review agent

---

## R2: @dnd-kit Library Patterns

### Decision
Use `@dnd-kit/core` + `@dnd-kit/sortable` with **one `DndContext` per column** (N independent contexts), `verticalListSortingStrategy`, and `restrictToVerticalAxis` modifier.

### Rationale
- Separate `DndContext` per column provides **isolation by design** — no cross-column dragging risk, no collision filtering needed.
- `sortableKeyboardCoordinates` provides accessible keyboard sorting (Space/Enter to pick up, arrow keys to move, Escape to cancel).
- `arrayMove` from `@dnd-kit/sortable` handles reorder logic purely.
- Built-in CSS transitions via `useSortable({ transition: { duration: 150 } })`.

### Core Pattern
```tsx
// Per-column: DndContext → SortableContext → useSortable items
<DndContext sensors={sensors} modifiers={[restrictToVerticalAxis]} onDragEnd={handleDragEnd}>
  <SortableContext items={agentIds} strategy={verticalListSortingStrategy}>
    {agents.map(agent => <SortableAgentTile key={agent.id} agent={agent} />)}
  </SortableContext>
</DndContext>
```

### Package Versions
| Package | Version |
|---|---|
| `@dnd-kit/core` | 6.3.1 |
| `@dnd-kit/sortable` | 10.0.0 |
| `@dnd-kit/modifiers` | 9.0.0 |
| `@dnd-kit/utilities` | 3.2.2 |

### Alternatives Considered
| Alternative | Why Rejected |
|---|---|
| `react-beautiful-dnd` | Unmaintained (archived by Atlassian), no TS types |
| `react-dnd` | Lower-level, more boilerplate, no built-in sortable presets |
| Single shared `DndContext` | Only needed for cross-column dragging, adds complexity |

---

## R3: Data Model Migration (`agent_mappings`)

### Decision
Migrate from `dict[str, list[str]]` to `dict[str, list[AgentAssignment]]` with **backward-compatible input** using Pydantic v2 `BeforeValidator`.

### Sub-Decisions

#### Backward Compatibility
- **PUT endpoint accepts both formats**: bare strings auto-promote to `AgentAssignment` via `BeforeValidator`
- **GET response always returns new format**: `list[AgentAssignment]` with UUIDs
- Keep backward compat for one release cycle only

#### Pydantic v2 Pattern
Use `Annotated[AgentAssignment, BeforeValidator(_coerce_agent)]`:
```python
def _coerce_agent(v: str | dict | AgentAssignment) -> AgentAssignment | dict:
    if isinstance(v, str):
        return AgentAssignment(slug=v)
    return v
```

**Why not discriminated union?** Requires a shared `type` literal field — bare strings don't have fields.
**Why not `model_validator` on parent?** Couples coercion to parent model. `BeforeValidator` on items is composable and testable.

#### UUID Generation
- **Server-side** via `default_factory=uuid4`. Client never sends IDs for new assignments.
- Frontend uses temporary `tempId` for optimistic UI, replaces with server-returned `id` after PUT succeeds.
- No database, so collision risk is zero.

#### Default Mappings
- Keep `DEFAULT_AGENT_MAPPINGS` as `dict[str, list[str]]` in constants.py (unchanged)
- Auto-promote at runtime in `WorkflowConfiguration.agent_mappings` field default factory
- Single source of truth for promotion logic

### Downstream Adaptation
Add a `get_agent_slugs(config, status) -> list[str]` helper to minimize diff noise in downstream consumers (orchestrator, tracking, WebSocket code) — they continue working with `list[str]` via slug extraction.

### Affected Files
| File | Change |
|---|---|
| `models/chat.py` | Add `AgentAssignment` model, update `WorkflowConfiguration` |
| `constants.py` | No change (strings auto-promoted) |
| `workflow_orchestrator.py` | Use `get_agent_slugs()` or `.slug` access |
| `agent_tracking.py` | Use `.slug` access |
| `api/workflow.py` | Use `.slug` for WebSocket messages |
| `api/chat.py` | Use `.slug` access |
| `frontend/types/index.ts` | Add `AgentAssignment` interface |

---

## R4: Preset Configurations

### Decision
Define three built-in presets as constants (backend and frontend):

| Preset | Description | Mappings |
|---|---|---|
| **Custom** | Empty config — user starts from scratch | All statuses → `[]` |
| **GitHub Copilot** | Copilot for implementation + review | `In Progress→copilot`, `In Review→copilot-review`, others → `[]` |
| **Spec Kit** | Default SpecKit pipeline | `Backlog→speckit.specify`, `Ready→speckit.plan+speckit.tasks`, `In Progress→speckit.implement`, `In Review→copilot-review` |

### Rationale
- Presets are static definitions, not dynamic — no API needed
- "Replace with confirmation" behavior (per spec FR-022): clicking a preset shows a confirmation dialog, then replaces entire config
- Spec Kit preset matches existing `DEFAULT_AGENT_MAPPINGS` from constants.py

---

## R5: Agent Row UI Architecture

### Decision
The agent configuration row is a **single React component** (`AgentConfigRow`) rendered between the board header and board columns, spanning the full width. It contains one `AgentColumnCell` per status column, aligned with the board columns below.

### Key Patterns
- **State management**: `useAgentConfig` custom hook owns local agent state, dirty tracking, diff computation
- **Data flow**: `ProjectBoardPage` → passes `boardData.columns` (status list) + `workflowConfig` → `AgentConfigRow`
- **Save**: `useAgentConfig.save()` calls `PUT /api/v1/workflow/config` via existing `useWorkflow.updateConfig()`
- **Dirty detection**: Deep compare local state vs. server state; visual indicators (dot/highlight) on changed columns
- **Collapse**: `useState<boolean>` in `AgentConfigRow`, default expanded, toggle button in row header
