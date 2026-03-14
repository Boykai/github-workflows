# Data Model: GitHub Label-Based Agent Pipeline State Tracking

**Branch**: `034-label-pipeline-state` | **Date**: 2026-03-11

## New Constants

### Pipeline Label Constants

**Location**: `backend/src/constants.py` (extend existing file)

```python
# ---------------------------------------------------------------------------
# Pipeline label constants
# ---------------------------------------------------------------------------
PIPELINE_LABEL_PREFIX = "pipeline:"
AGENT_LABEL_PREFIX = "agent:"
ACTIVE_LABEL = "active"
STALLED_LABEL = "stalled"

# Label colors (hex without '#')
PIPELINE_LABEL_COLOR = "0052cc"   # Blue
AGENT_LABEL_COLOR = "7057ff"      # Purple
ACTIVE_LABEL_COLOR = "0e8a16"     # Green
STALLED_LABEL_COLOR = "d73a4a"    # Red

# Label descriptions for pre-creation
PIPELINE_LABEL_DESCRIPTIONS = {
    ACTIVE_LABEL: "Active agent sub-issue in pipeline",
    STALLED_LABEL: "Pipeline agent is stalled and needs recovery",
}
```

**Used by**: `constants.py` (utilities), `orchestrator.py` (write path), `pipeline.py` (fast-path), `recovery.py` (stalled detection), `state_validation.py` (cross-check)

---

## New Pure Functions

### Label Parsing Utilities

**Location**: `backend/src/constants.py` (extend existing file)

```python
def extract_pipeline_config(label_name: str) -> str | None:
    """Extract pipeline config name from a 'pipeline:<config>' label.

    Returns the config name (e.g., 'speckit-full') or None if the label
    does not match the pipeline prefix.
    """
    if label_name.startswith(PIPELINE_LABEL_PREFIX):
        return label_name[len(PIPELINE_LABEL_PREFIX):]
    return None


def extract_agent_slug(label_name: str) -> str | None:
    """Extract agent slug from an 'agent:<slug>' label.

    Returns the agent slug (e.g., 'speckit.plan') or None if the label
    does not match the agent prefix.
    """
    if label_name.startswith(AGENT_LABEL_PREFIX):
        return label_name[len(AGENT_LABEL_PREFIX):]
    return None


def build_pipeline_label(config_name: str) -> str:
    """Build a 'pipeline:<config>' label from a config name.

    >>> build_pipeline_label("speckit-full")
    'pipeline:speckit-full'
    """
    return f"{PIPELINE_LABEL_PREFIX}{config_name}"


def build_agent_label(agent_slug: str) -> str:
    """Build an 'agent:<slug>' label from an agent slug.

    >>> build_agent_label("speckit.plan")
    'agent:speckit.plan'
    """
    return f"{AGENT_LABEL_PREFIX}{agent_slug}"


def find_pipeline_label(labels: list[dict[str, str]] | list) -> str | None:
    """Find the pipeline config name from a list of label dicts.

    Scans labels for the first 'pipeline:<config>' match.
    Returns the config name or None.
    """
    for lbl in labels:
        name = lbl.get("name", "") if isinstance(lbl, dict) else getattr(lbl, "name", "")
        config = extract_pipeline_config(name)
        if config is not None:
            return config
    return None


def find_agent_label(labels: list[dict[str, str]] | list) -> str | None:
    """Find the current agent slug from a list of label dicts.

    Scans labels for the first 'agent:<slug>' match.
    Returns the agent slug or None.
    """
    for lbl in labels:
        name = lbl.get("name", "") if isinstance(lbl, dict) else getattr(lbl, "name", "")
        slug = extract_agent_slug(name)
        if slug is not None:
            return slug
    return None


def has_stalled_label(labels: list[dict[str, str]] | list) -> bool:
    """Check if the stalled label is present in a list of label dicts."""
    for lbl in labels:
        name = lbl.get("name", "") if isinstance(lbl, dict) else getattr(lbl, "name", "")
        if name == STALLED_LABEL:
            return True
    return False
```

**Used by**: `pipeline.py` (fast-path), `recovery.py` (stalled check), `polling_loop.py` (parent filter), `state_validation.py` (cross-check), `orchestrator.py` (label swap)

---

## Modified Models

### Task Model Extension

**Location**: `backend/src/models/task.py` (extend existing model)

```python
class Task(BaseModel):
    # ... existing fields unchanged ...
    task_id: UUID = Field(default_factory=uuid4)
    project_id: str
    github_item_id: str
    github_content_id: str | None = None
    github_issue_id: str | None = None
    issue_number: int | None = None
    repository_owner: str | None = None
    repository_name: str | None = None
    title: str = Field(..., max_length=256)
    description: str | None = Field(default=None, max_length=65535)
    status: str
    status_option_id: str
    assignees: list[str] | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # NEW: Label data from GraphQL board query
    labels: list[dict[str, str]] | None = None
```

**Note**: Labels are `list[dict[str, str]]` where each dict has `{"name": "...", "color": "..."}`. This avoids importing the `Label` Pydantic model from `board.py` and maintains Task model independence. The `is_sub_issue()` helper in `helpers.py` already handles this dict format.

---

## New Module

### State Validation Service

**Location**: `backend/src/services/copilot_polling/state_validation.py` (new file)

```python
"""Consolidated label vs tracking table validation.

Cross-checks pipeline labels against the Markdown tracking table and
corrects whichever source is stale by consulting GitHub ground truth.
"""

async def validate_pipeline_labels(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    labels: list[dict[str, str]],
    tracking_steps: list,  # list[AgentStep]
    pipeline_config_name: str | None = None,
) -> tuple[bool, list[str]]:
    """Cross-check labels vs tracking table, fix stale source.

    Args:
        access_token: GitHub access token.
        owner: Repository owner.
        repo: Repository name.
        issue_number: Parent issue number.
        labels: Current labels on the issue.
        tracking_steps: Parsed tracking table steps.
        pipeline_config_name: Pipeline config name from label (if known).

    Returns:
        Tuple of (corrections_made: bool, correction_descriptions: list[str]).
    """
    ...
```

**Dependencies**: `constants.py` (label utilities), `issues.py` (`update_issue_state()`), `agent_tracking.py` (tracking table parsing)

---

## Modified Functions (Signature Changes)

### orchestrator.py — _build_labels()

**Location**: `backend/src/services/workflow_orchestrator/orchestrator.py`

```python
@staticmethod
def _build_labels(
    recommendation: IssueRecommendation,
    pipeline_config_name: str | None = None,  # NEW parameter
) -> list[str]:
    """Build final labels from recommendation metadata.

    When pipeline_config_name is provided, adds a 'pipeline:<config>'
    label for pipeline state tracking.
    """
    labels = list(recommendation.metadata.labels) if recommendation.metadata.labels else []

    if "ai-generated" not in labels:
        labels.insert(0, "ai-generated")

    # ... existing priority/size/blocking logic ...

    # NEW: Add pipeline label if config name provided
    if pipeline_config_name:
        labels.append(build_pipeline_label(pipeline_config_name))

    return with_blocking_label(labels, recommendation.is_blocking)
```

### orchestrator.py — assign_agent_for_status()

**Current signature** (unchanged, behavior extended):

```python
async def assign_agent_for_status(
    self,
    ctx: WorkflowContext,
    status: str,
    agent_index: int = 0,
) -> bool:
```

**New behavior**: After assigning the new agent:
1. Swap `agent:<old_slug>` → `agent:<new_slug>` via `update_issue_state(labels_add=[new], labels_remove=[old])`.
2. Move `active` label: remove from previous sub-issue, add to new sub-issue.
3. Remove `stalled` label if present.

---

## Entity Relationship Summary

```text
┌─────────────────────────────────────────────────────────────────┐
│                        Parent Issue                             │
│                                                                 │
│  Labels: [pipeline:speckit-full] [agent:speckit.plan] [stalled] │
│  Body: ## 🤖 Agents Pipelines (tracking table)                 │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Sub-Issue 1  │  │  Sub-Issue 2  │  │  Sub-Issue 3  │        │
│  │ [speckit.     │  │ [speckit.     │  │ [speckit.     │        │
│  │  specify]     │  │  plan]        │  │  tasks]       │        │
│  │ Labels: []    │  │ Labels:       │  │ Labels: []    │        │
│  │ State: Done   │  │ [active]      │  │ State: Pending│        │
│  └──────────────┘  │ State: Active │  └──────────────┘         │
│                     └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘

Label Lifecycle:
  Issue Created  → [pipeline:<config>] applied (set-once)
  Agent Assigned → [agent:<slug>] swapped, [active] moved to sub-issue
  Agent Done     → [agent:<slug>] swapped to next, [active] moved
  Pipeline Done  → [agent:*] removed
  Stalled        → [stalled] applied
  Recovered      → [stalled] removed

Data Flow:
  GraphQL Board Query → labels(first:20) → BoardItem.labels → Task.labels
                                                                    ↓
  Polling Loop → is_sub_issue(task) ← uses task.labels
                                                                    ↓
  Fast-Path → find_pipeline_label() + find_agent_label()
                    ↓                          ↓
              PipelineConfig lookup    current_agent_index
                    ↓                          ↓
              ──────── PipelineState built ────────
```
