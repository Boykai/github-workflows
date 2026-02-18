# Data Model: Custom Agent Workflow Configuration UI

**Feature**: 004-agent-workflow-config-ui | **Date**: 2026-02-17

---

## Entity Relationship Overview

```
BoardProject 1──* BoardColumn (via status_field.options)
WorkflowConfiguration 1──* AgentAssignment (via agent_mappings dict)
AgentAssignment *──1 AvailableAgent (via slug reference)
```

---

## New Entities

### AgentAssignment (Backend: Pydantic model, Frontend: TypeScript interface)

Represents a single agent assignment within a status column. Supports duplicates via UUID instance identity.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | UUID | No | `uuid4()` | Unique instance identity (server-generated) |
| `slug` | string | Yes | — | Agent identifier (e.g., `"speckit.specify"`, `"copilot"`) |
| `display_name` | string \| null | No | `null` | Human-readable name (populated from discovery) |
| `config` | dict \| null | No | `null` | Reserved for future per-assignment configuration |

**Backend (Pydantic v2):**
```python
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class AgentAssignment(BaseModel):
    """A single agent assignment within a workflow status column."""
    id: UUID = Field(default_factory=uuid4, description="Unique instance ID")
    slug: str = Field(..., description="Agent identifier slug")
    display_name: str | None = Field(default=None, description="Human-readable display name")
    config: dict | None = Field(default=None, description="Reserved for future per-assignment config")
```

**Frontend (TypeScript):**
```typescript
export interface AgentAssignment {
  id: string;           // UUID string
  slug: string;         // Agent identifier
  display_name?: string | null;
  config?: Record<string, unknown> | null;
}
```

**Validation Rules:**
- `slug` must be non-empty, alphanumeric + dots + hyphens + underscores
- `id` is auto-generated server-side; clients may omit on PUT (server assigns)
- `config` is opaque — validated only as valid JSON dict when present

**State Transitions:** None (stateless data object)

---

### AvailableAgent (Backend: Pydantic model, Frontend: TypeScript interface)

Represents an agent that can be assigned, returned from the discovery endpoint.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `slug` | string | Yes | — | Unique agent identifier |
| `display_name` | string | Yes | — | Human-readable name |
| `description` | string \| null | No | `null` | Agent description/purpose |
| `avatar_url` | string \| null | No | `null` | Avatar image URL |
| `source` | `"builtin" \| "repository"` | Yes | — | Where the agent comes from |

**Backend (Pydantic v2):**
```python
from enum import StrEnum

class AgentSource(StrEnum):
    BUILTIN = "builtin"
    REPOSITORY = "repository"

class AvailableAgent(BaseModel):
    """An agent available for assignment, from discovery."""
    slug: str = Field(..., description="Unique agent identifier")
    display_name: str = Field(..., description="Human-readable name")
    description: str | None = Field(default=None, description="Agent description")
    avatar_url: str | None = Field(default=None, description="Avatar URL")
    source: AgentSource = Field(..., description="Discovery source")
```

**Frontend (TypeScript):**
```typescript
export type AgentSource = 'builtin' | 'repository';

export interface AvailableAgent {
  slug: string;
  display_name: string;
  description?: string | null;
  avatar_url?: string | null;
  source: AgentSource;
}
```

---

### AgentPreset (Frontend-only constant)

Represents a preset agent configuration.

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Preset identifier (`"custom"`, `"copilot"`, `"speckit"`) |
| `label` | string | Display label |
| `description` | string | Short description |
| `mappings` | `Record<string, AgentAssignment[]>` | Agent assignments per status |

**Frontend (TypeScript):**
```typescript
export interface AgentPreset {
  id: string;
  label: string;
  description: string;
  mappings: Record<string, AgentAssignment[]>;
}
```

---

## Modified Entities

### WorkflowConfiguration (existing — modified)

**Change:** `agent_mappings` field type migrated from `dict[str, list[str]]` to `dict[str, list[AgentAssignment]]`.

| Field | Old Type | New Type | Migration |
|-------|----------|----------|-----------|
| `agent_mappings` | `dict[str, list[str]]` | `dict[str, list[AgentAssignmentInput]]` | `BeforeValidator` auto-promotes bare strings |

**Backend migration pattern (Pydantic v2):**
```python
from typing import Annotated
from pydantic import BeforeValidator

def _coerce_agent(v: str | dict | AgentAssignment) -> AgentAssignment | dict:
    """Accept a bare slug string and promote to AgentAssignment."""
    if isinstance(v, str):
        return AgentAssignment(slug=v)  # UUID auto-generated
    return v

AgentAssignmentInput = Annotated[AgentAssignment, BeforeValidator(_coerce_agent)]

class WorkflowConfiguration(BaseModel):
    # ... existing fields unchanged ...
    agent_mappings: dict[str, list[AgentAssignmentInput]] = Field(
        default_factory=lambda: {
            k: [AgentAssignment(slug=s) for s in v]
            for k, v in DEFAULT_AGENT_MAPPINGS.items()
        },
        description="Status name → ordered list of agent assignments",
    )
```

**Frontend type update:**
```typescript
export interface WorkflowConfiguration {
  // ... existing fields unchanged ...
  agent_mappings: Record<string, AgentAssignment[]>;  // was Record<string, string[]>
}
```

**Backward Compatibility:**
- PUT accepts both `["speckit.specify"]` (old) and `[{slug: "speckit.specify"}]` (new)
- GET always returns `AgentAssignment[]` with UUIDs
- `DEFAULT_AGENT_MAPPINGS` in constants.py remains `dict[str, list[str]]` — promoted at runtime

---

## Utility Functions

### Backend Helper

```python
def get_agent_slugs(config: WorkflowConfiguration, status: str) -> list[str]:
    """Extract ordered slug strings for a given status. Minimizes migration diff."""
    return [a.slug for a in config.agent_mappings.get(status, [])]
```

Used by: `workflow_orchestrator.py`, `agent_tracking.py`, `api/workflow.py`, `api/chat.py`

---

## Existing Entities (unchanged, for reference)

| Entity | Location | Relevance |
|--------|----------|-----------|
| `BoardColumn` | `frontend/src/types/index.ts` | Provides status list for agent row alignment |
| `BoardStatusOption` | `frontend/src/types/index.ts` | Status name + color used in column headers |
| `PipelineState` | `backend/src/services/workflow_orchestrator.py` | `agents: list[str]` — stays as slugs, extracted from `AgentAssignment.slug` |
| `DEFAULT_AGENT_MAPPINGS` | `backend/src/constants.py` | Unchanged; auto-promoted by `BeforeValidator` |
