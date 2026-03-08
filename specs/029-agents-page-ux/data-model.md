# Data Model: Agents Page — Sun/Moon Avatars, Featured Agents, Inline Editing with PR Flow, Bulk Model Update, Repo Name Display & Tools Editor

**Feature**: 029-agents-page-ux | **Date**: 2026-03-07

## Backend Entities (Pydantic Models)

### BulkModelUpdateRequest (New)

Request payload for the bulk model update endpoint.

```python
class BulkModelUpdateRequest(BaseModel):
    target_model_id: str              # ID of the model to apply to all agents
    target_model_name: str            # Display name of the target model
```

**Validation**:
- `target_model_id` must be a non-empty string (1–200 characters).
- `target_model_name` must be a non-empty string (1–200 characters).

### BulkModelUpdateResult (New)

Response from the bulk model update endpoint.

```python
class BulkModelUpdateResult(BaseModel):
    success: bool = True              # Overall success flag
    updated_count: int                # Number of agents successfully updated
    failed_count: int = 0             # Number of agents that failed to update
    updated_agents: list[str]         # Slugs of successfully updated agents
    failed_agents: list[str] = []     # Slugs of agents that failed
    target_model_id: str              # The model that was applied
    target_model_name: str            # Display name of the applied model
```

### Existing Models (Unchanged)

The following existing models are referenced but not structurally modified:

- **Agent** (`backend/src/models/agents.py`): `id`, `name`, `slug`, `description`, `system_prompt`, `default_model_id`, `default_model_name`, `status`, `tools`, `status_column`, `github_issue_number`, `github_pr_number`, `branch_name`, `source`, `created_at` — all fields unchanged.
- **AgentUpdate** (`backend/src/models/agents.py`): `name`, `description`, `system_prompt`, `tools`, `default_model_id`, `default_model_name` — all fields unchanged. Used by inline editing save flow.
- **AgentCreateResult** (`backend/src/models/agents.py`): `agent`, `pr_url`, `pr_number`, `issue_number`, `branch_name` — returned on save. Frontend uses `pr_url` to display the PR link.

---

## Frontend Types (TypeScript)

### AgentAvatar Types (New)

```typescript
/** Sun/Moon icon variant for agent avatars */
type CelestialIconVariant =
  | 'full-sun'
  | 'sunrise'
  | 'sun-face'
  | 'sun-cloud'
  | 'solar-eclipse'
  | 'sunburst'
  | 'full-moon'
  | 'crescent-moon'
  | 'half-moon'
  | 'waning-crescent'
  | 'moon-stars'
  | 'moonrise';

/** Props for the AgentAvatar component */
interface AgentAvatarProps {
  slug: string;               // Agent slug used for deterministic icon selection
  size?: 'sm' | 'md' | 'lg'; // Icon size: sm=24px, md=32px, lg=48px
  className?: string;         // Additional CSS classes
}
```

### BulkModelUpdate Types (New)

```typescript
/** Request payload for bulk model update */
interface BulkModelUpdateRequest {
  target_model_id: string;
  target_model_name: string;
}

/** Response from bulk model update */
interface BulkModelUpdateResult {
  success: boolean;
  updated_count: number;
  failed_count: number;
  updated_agents: string[];
  failed_agents: string[];
  target_model_id: string;
  target_model_name: string;
}
```

### Unsaved Changes Types (New)

```typescript
/** Tracks the dirty state of the agent editor form */
interface AgentEditorDirtyState {
  isDirty: boolean;              // Whether any field has been modified
  dirtyFields: Set<string>;      // Names of modified fields (e.g., 'name', 'tools')
}

/** Original agent values snapshot for comparison */
interface AgentEditorSnapshot {
  name: string;
  description: string;
  system_prompt: string;
  tools: string[];
  default_model_id: string;
  default_model_name: string;
}
```

### Existing Types (Unchanged)

```typescript
/** Existing AgentConfig — no structural changes */
export interface AgentConfig {
  id: string;
  name: string;
  slug: string;
  description: string;
  system_prompt: string;
  default_model_id: string;
  default_model_name: string;
  status: AgentStatus;
  tools: string[];
  status_column: string | null;
  github_issue_number: number | null;
  github_pr_number: number | null;
  branch_name: string | null;
  source: AgentSource;
  created_at: string | null;
}
```

---

## State Machines

### Inline Editor Lifecycle

```
                    ┌────────────┐
                    │   CLOSED    │  Agent card displayed (read-only)
                    └──────┬─────┘
                           │ User clicks "Edit" button on AgentCard
                           ▼
                    ┌────────────┐
                    │   OPEN      │  AddAgentModal opens in edit mode
                    │   (clean)   │  All fields pre-populated from agent data
                    └──────┬─────┘
                           │ User modifies any field
                           ▼
                    ┌────────────┐
                    │   OPEN      │  "Unsaved changes" banner visible
                    │   (dirty)   │  beforeunload listener active
                    └──────┬─────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        User clicks   User clicks   User clicks
         "Save"       "Close"/Esc    outside modal
              │            │            │
              ▼            ▼            ▼
       ┌────────────┐  ┌──────────────────┐
       │  SAVING     │  │  CONFIRM DIALOG   │
       │  (loading)  │  │  "Save / Discard  │
       └──────┬─────┘  │   / Cancel"       │
              │         └──────┬───────────┘
              │                │
         ┌────┴────┐     ┌────┼────────┐
         │         │     │    │        │
       Success   Error  Save Discard  Cancel
         │         │     │    │        │
         ▼         ▼     ▼    ▼        ▼
    ┌─────────┐ ┌──────┐  │  ┌──────┐ ┌──────┐
    │ SUCCESS  │ │ OPEN │  │  │CLOSED│ │ OPEN │
    │ (PR URL) │ │(dirty│  │  │      │ │(dirty│
    │ toast    │ │retry)│  │  └──────┘ │still)│
    └─────────┘ └──────┘  │           └──────┘
                          ▼
                    ┌────────────┐
                    │  SAVING     │ (same as above)
                    └────────────┘
```

### Bulk Model Update Flow

```
User clicks "Update All Models" button
    │
    ▼
┌────────────────────────────────┐
│  BULK MODEL DIALOG (Step 1)    │
│  Select target model           │
│  [ModelSelector component]     │
└──────────────┬─────────────────┘
               │ User selects model
               ▼
┌────────────────────────────────┐
│  BULK MODEL DIALOG (Step 2)    │
│  Confirmation:                 │
│  "Update all X agents to       │
│   [Model Name]?"              │
│  Agent list:                   │
│  • agent-1 (current: GPT-4o)  │
│  • agent-2 (current: Claude)  │
│  • ...                         │
│  [Cancel] [Confirm]           │
└──────────────┬─────────────────┘
               │
         ┌─────┴──────┐
         │            │
       Cancel      Confirm
         │            │
         ▼            ▼
    ┌────────┐  ┌────────────┐
    │ CLOSED  │  │  UPDATING   │
    └────────┘  │  (loading)  │
                └──────┬─────┘
                       │
                 ┌─────┴──────┐
                 │            │
               Success     Failure
                 │            │
                 ▼            ▼
          ┌──────────┐  ┌──────────┐
          │  SUCCESS  │  │  ERROR   │
          │  toast:   │  │  toast:  │
          │  "Updated │  │  "N of M │
          │   X agents│  │   failed"│
          └──────────┘  └──────────┘
```

### Featured Agents Selection Algorithm

```
Input: agents[] (full list), agentUsageCounts{} (slug → count)

Step 1: Select by usage
    usageAgents = agents
      .filter(a => agentUsageCounts[a.slug] > 0)
      .sort((a, b) => agentUsageCounts[b.slug] - agentUsageCounts[a.slug])
      .slice(0, 3)

Step 2: If usageAgents.length < 3, supplement with recent
    threeDaysAgo = Date.now() - (3 * 24 * 60 * 60 * 1000)
    recentAgents = agents
      .filter(a => a.created_at && new Date(a.created_at) > threeDaysAgo)
      .filter(a => !usageAgents.includes(a))
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))

    spotlightAgents = [...usageAgents, ...recentAgents].slice(0, 3)

Step 3: If spotlightAgents.length === 0
    Hide Featured Agents section (or show empty state)

Output: spotlightAgents (0–3 agents)
```

### Tools Editor State

```
┌─────────────────────────────────────┐
│  Tools Editor (within modal)        │
│                                     │
│  Ordered list:                      │
│  ┌─────────────────────────────┐    │
│  │ 1. read          [↑] [↓] [×]│    │
│  │ 2. edit          [↑] [↓] [×]│    │
│  │ 3. search        [↑] [↓] [×]│    │
│  │ 4. github/*      [↑] [↓] [×]│    │
│  └─────────────────────────────┘    │
│                                     │
│  [+ Add Tools]   ← opens ToolSelectorModal
│                                     │
│  Validation: ≥1 tool required       │
│  Error: "At least one tool must     │
│          be assigned" (inline)      │
└─────────────────────────────────────┘

State changes tracked in tools: string[]
- Add: append to end of array
- Remove: filter out by tool ID
- Move up: swap [i] with [i-1]
- Move down: swap [i] with [i+1]
All changes → isDirty = true
```

---

## Database Changes

### No Schema Changes Required

The existing `agent_configs` table already has all required columns:
- `default_model_id` / `default_model_name` — used by bulk model update
- `created_at` — used by Featured Agents recency filter
- `tools` (JSON) — used by tools editor

The bulk model update endpoint uses the existing `agent_model_preferences` storage in the agents service (`get_model_preferences()` / `update_agent()`) which writes to the `agent_configs` table.

---

## Agent Config File Format (Unchanged)

The `.github/agents/*.agent.md` file format is unchanged:

```yaml
---
description: Agent description here
tools: ["read", "edit", "search", "github/*"]
---

System prompt content goes here...
```

The inline editor reads and writes this format via the existing `_generate_agent_config()` method in `agent_creator.py`. Model preferences (`default_model_id`, `default_model_name`) are stored only in SQLite as runtime overrides, not in the `.agent.md` file.

---

## localStorage Keys

No new localStorage keys are introduced by this feature. The agent editor form state is managed in React component state within the modal lifecycle.

---

## Avatar Hash Function

```typescript
function getAvatarIndex(slug: string): number {
  let hash = 0;
  for (let i = 0; i < slug.length; i++) {
    hash = ((hash << 5) - hash + slug.charCodeAt(i)) | 0;
  }
  return Math.abs(hash) % AVATAR_COUNT; // AVATAR_COUNT = 12
}
```

This is a standard djb2-style hash function. It produces consistent results for the same input string, distributes values well across the modulus range, and is fast enough for synchronous rendering.
