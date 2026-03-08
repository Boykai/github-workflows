# Data Model: Display Models Used in Agent Pipeline Section of Parent Issue Description

**Feature**: 030-pipeline-model-display | **Date**: 2026-03-08

## Backend Entities

### AgentStep (Modified)

The `AgentStep` dataclass in `backend/src/services/agent_tracking.py` represents one row in the pipeline tracking table. A new `model` field is added.

| Field | Type | Description | Default | Change |
|-------|------|-------------|---------|--------|
| `index` | `int` | Row sequence number (1-based) | Required | Unchanged |
| `status` | `str` | Pipeline status column name (e.g., "Backlog", "Ready") | Required | Unchanged |
| `agent_name` | `str` | Agent slug identifier (e.g., "speckit.specify") | Required | Unchanged |
| `model` | `str` | Model name assigned to this agent (e.g., "gpt-4o") | `""` | **NEW** |
| `state` | `str` | Execution state emoji + text (⏳ Pending, 🔄 Active, ✅ Done) | Required | Unchanged |

**Source**: `backend/src/services/agent_tracking.py` lines 62–69

**Validation**:

- `model` is a free-form string. Empty string `""` indicates no model assigned.
- When rendered, empty `model` displays as "TBD" in the Markdown table.
- Pipe characters (`|`) in model names are escaped to `\|` to prevent Markdown table breakage.

### AgentAssignment (Unchanged)

The `AgentAssignment` Pydantic model provides the model data via its `config` dictionary.

| Field | Type | Description | Relevant |
|-------|------|-------------|----------|
| `id` | `UUID` | Unique instance ID | No |
| `slug` | `str` | Agent identifier slug | Yes — maps to `AgentStep.agent_name` |
| `display_name` | `str \| None` | Human-readable display name | No |
| `config` | `dict \| None` | Per-assignment configuration | **Yes — contains `model_name`** |

**Source**: `backend/src/models/agent.py` lines 17–23

**Config dict structure** (when model is assigned):

```python
{
    "model_id": "gpt-4o",        # Model identifier
    "model_name": "GPT-4o",      # Display name (used in pipeline table)
}
```

**Config dict** (when no model assigned): `None` or `{}`

---

## Markdown Table Format

### Current Format (Before Change)

```markdown
| # | Status | Agent | State |
|---|--------|-------|-------|
| 1 | Backlog | `speckit.specify` | ✅ Done |
| 2 | Ready | `speckit.plan` | 🔄 Active |
| 3 | In Progress | `speckit.implement` | ⏳ Pending |
```

### New Format (After Change)

```markdown
| # | Status | Agent | Model | State |
|---|--------|-------|-------|-------|
| 1 | Backlog | `speckit.specify` | gpt-4o | ✅ Done |
| 2 | Ready | `speckit.plan` | claude-3-5-sonnet | 🔄 Active |
| 3 | In Progress | `speckit.implement` | TBD | ⏳ Pending |
```

### Column Definitions

| Column | Width | Content | Notes |
|--------|-------|---------|-------|
| # | Fixed | Sequential 1-based integer | Unchanged |
| Status | Variable | Pipeline status name | Unchanged |
| Agent | Variable | Agent slug in backticks | Unchanged |
| Model | Variable | Model display name or "TBD" | **NEW** |
| State | Fixed | Emoji + state text | Unchanged |

---

## Function Signatures (Changes)

### `build_agent_pipeline_steps()` — Updated

```python
def build_agent_pipeline_steps(
    agent_mappings: dict[str, list[AgentAssignment]],
    status_order: list[str],
) -> list[AgentStep]:
```

**Change**: Now extracts `model_name` from each `AgentAssignment.config` dict and passes it to `AgentStep.model`. Signature unchanged — backward compatible.

### `render_tracking_markdown()` — Updated

```python
def render_tracking_markdown(steps: list[AgentStep]) -> str:
```

**Change**: Renders new 5-column table header and includes `step.model` (or "TBD" if empty) in each row. Escapes pipe characters in model names. Signature unchanged.

### `parse_tracking_from_body()` — Updated

```python
def parse_tracking_from_body(body: str) -> list[AgentStep] | None:
```

**Change**: Updated regex matches both 4-column (legacy) and 5-column (new) table rows. Populates `AgentStep.model` from parsed data. Signature unchanged — backward compatible.

### `update_agent_state()` — Unchanged Behavior

```python
def update_agent_state(body: str, agent_name: str, new_state: str) -> str:
```

**Change**: No code change needed. This function parses the existing table (which now returns `AgentStep` with `model` populated), updates the state, and re-renders. The model field is preserved through the parse → modify → render cycle.

---

## State Transitions

### Model Display Lifecycle

```text
Agent assigned to pipeline (no model)
    │
    │  AgentAssignment.config = None
    │  AgentStep.model = ""
    │  Table shows: "TBD"
    │
    ▼
User assigns model via pipeline UI
    │
    │  AgentAssignment.config = {"model_id": "gpt-4o", "model_name": "GPT-4o"}
    │  AgentStep.model = "GPT-4o"
    │  Table shows: "GPT-4o"
    │
    ▼
User changes model
    │
    │  AgentAssignment.config = {"model_id": "claude-3-5-sonnet", "model_name": "Claude 3.5 Sonnet"}
    │  AgentStep.model = "Claude 3.5 Sonnet"
    │  Table shows: "Claude 3.5 Sonnet"
    │
    ▼
User removes model assignment
    │
    │  AgentAssignment.config = None or {}
    │  AgentStep.model = ""
    │  Table shows: "TBD"
```

### Backward Compatibility Flow

```text
Existing issue with old 4-column table
    │
    │  parse_tracking_from_body() → AgentStep(model="")
    │  (regex matches old format, model defaults to "")
    │
    ▼
Pipeline state update (mark_agent_active / mark_agent_done)
    │
    │  parse → modify state → render_tracking_markdown()
    │  Re-renders with new 5-column format
    │  model = "" → displays as "TBD"
    │
    ▼
Issue now has new 5-column table (naturally migrated)
```

---

## Database Changes

### No Schema Changes Required

The model data is already stored in the `agent_pipeline_mappings` JSON column of the `project_settings` table. The `AgentAssignment.config` dict contains `model_name` when set via the pipeline UI. No new columns, tables, or migrations are needed.

---

## localStorage / Frontend State

### No Frontend Changes

This feature is entirely backend. The frontend `AgentAssignment` type already includes `config?: Record<string, unknown> | null` which can carry `model_name`. The pipeline tracking table is rendered server-side into the GitHub issue body as Markdown text.
