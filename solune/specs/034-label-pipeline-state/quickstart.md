# Quickstart: GitHub Label-Based Agent Pipeline State Tracking

**Branch**: `034-label-pipeline-state` | **Date**: 2026-03-11

## Developer Guide — Pipeline Label Integration

### Section 1: Label Constants & Utilities

#### Before: Ad-hoc label construction

```python
# In orchestrator.py — labels built inline
labels = ["ai-generated", "feature", "backend"]
if is_blocking:
    labels.append("blocking")
```

#### After: Pipeline labels via constants and builders

```python
from src.constants import (
    build_pipeline_label,
    build_agent_label,
    find_pipeline_label,
    find_agent_label,
    has_stalled_label,
    ACTIVE_LABEL,
    STALLED_LABEL,
)

# Build labels for issue creation
pipeline_label = build_pipeline_label("speckit-full")  # → "pipeline:speckit-full"
agent_label = build_agent_label("speckit.plan")         # → "agent:speckit.plan"

# Parse labels from a task
config_name = find_pipeline_label(task.labels or [])   # → "speckit-full" or None
agent_slug = find_agent_label(task.labels or [])        # → "speckit.plan" or None
is_stalled = has_stalled_label(task.labels or [])       # → True/False
```

---

### Section 2: Label Write Path at Pipeline Transitions

#### Before: Issue creation without pipeline labels

```python
# In orchestrator.py — create_issue_from_recommendation()
issue = await self.github.create_issue(
    access_token=ctx.access_token,
    owner=ctx.repository_owner,
    repo=ctx.repository_name,
    title=recommendation.title,
    body=body,
    labels=self._build_labels(recommendation),
)
```

#### After: Issue creation with pipeline:<config> label

```python
# In orchestrator.py — create_issue_from_recommendation()
issue = await self.github.create_issue(
    access_token=ctx.access_token,
    owner=ctx.repository_owner,
    repo=ctx.repository_name,
    title=recommendation.title,
    body=body,
    labels=self._build_labels(recommendation, pipeline_config_name=config.name),
)
```

#### Before: Agent assignment without label swap

```python
# In orchestrator.py — assign_agent_for_status()
# Only updates tracking table in issue body
await self.github.update_issue_body(...)
```

#### After: Agent assignment with label swap + active label move

```python
# In orchestrator.py — assign_agent_for_status(self, ctx, status, agent_index=0) -> bool
# ctx.issue_number provides the parent issue number; agent_index selects which agent to assign.
# 1. Update tracking table (existing)
await self.github.update_issue_body(...)

# 2. Swap agent label on parent issue (derive slugs from pipeline state)
old_agent_label = build_agent_label(old_agent_slug) if old_agent_slug else None
new_agent_label = build_agent_label(new_agent_slug)
await self.github.update_issue_state(
    access_token=ctx.access_token,
    owner=ctx.repository_owner,
    repo=ctx.repository_name,
    issue_number=ctx.issue_number,
    labels_add=[new_agent_label],
    labels_remove=[lbl for lbl in [old_agent_label, STALLED_LABEL] if lbl],
)

# 3. Move active label between sub-issues
if old_sub_issue_number:
    await self.github.update_issue_state(
        ..., issue_number=old_sub_issue_number,
        labels_remove=[ACTIVE_LABEL],
    )
await self.github.update_issue_state(
    ..., issue_number=new_sub_issue_number,
    labels_add=[ACTIVE_LABEL],
)
```

---

### Section 3: Fast-Path Pipeline Reconstruction

#### Before: Always fetch issue body + parse tracking table

```python
# In pipeline.py — _get_or_reconstruct_pipeline()
cached = _cp.get_pipeline_state(issue_number)
if cached:
    return cached

# Expensive: fetch issue body from GitHub API
issue_data = await get_issue_with_comments(access_token, owner, repo, issue_number)
body = issue_data.get("body", "")
steps = _cp.parse_tracking_from_body(body)
# ... reconstruct from tracking table or sub-issues ...
```

#### After: Label fast-path before any API calls

```python
# In pipeline.py — _get_or_reconstruct_pipeline()
cached = _cp.get_pipeline_state(issue_number)
if cached:
    return cached

# NEW: Fast-path from labels (zero API calls)
if labels:
    config_name = find_pipeline_label(labels)
    agent_slug = find_agent_label(labels)
    if config_name and agent_slug:
        workflow_config = await _cp.get_workflow_config(project_id)
        pipeline_config = next(
            (pc for pc in (workflow_config.pipeline_configs or [])
             if pc.name == config_name), None
        ) if workflow_config else None
        if pipeline_config:
            state = _build_pipeline_from_labels(
                issue_number, project_id, status,
                config_name, agent_slug, pipeline_config,
            )
            if state:
                _cp.set_pipeline_state(issue_number, state)
                return state

# Fallthrough: fetch issue body (existing behavior unchanged)
issue_data = await get_issue_with_comments(access_token, owner, repo, issue_number)
# ...
```

---

### Section 4: Task Model with Labels

#### Before: Task without labels

```python
# In projects.py — get_project_items()
all_tasks.append(
    Task(
        project_id=project_id,
        github_item_id=item["id"],
        title=content.get("title", "Untitled"),
        status=status_value.get("name", "Todo"),
        # ... other fields ...
    )
)
```

#### After: Task with labels propagated from GraphQL

```python
# In projects.py — get_project_items()
# NOTE: Requires GET_PROJECT_ITEMS_QUERY to include labels(first: 20) { nodes { id name color } }
# in the Issue content type (same selection as BOARD_GET_PROJECT_ITEMS_QUERY already has).
content_labels = [
    {"name": ln.get("name", ""), "color": ln.get("color", "")}
    for ln in content.get("labels", {}).get("nodes", [])
    if ln
]

all_tasks.append(
    Task(
        project_id=project_id,
        github_item_id=item["id"],
        title=content.get("title", "Untitled"),
        status=status_value.get("name", "Todo"),
        labels=content_labels or None,
        # ... other fields ...
    )
)
```

---

### Section 5: Stalled Detection via Labels

#### Before: Expensive reconciliation for every active issue

```python
# In recovery.py — recover_stalled_issues()
for task in active_tasks:
    # Always fetch issue body + parse tracking + check sub-issues
    issue_data = await get_issue_with_comments(...)
    steps = _cp.parse_tracking_from_body(issue_data["body"])
    # ... validate every step against GitHub ground truth ...
```

#### After: Skip reconciliation when labels confirm active state

```python
# In recovery.py — recover_stalled_issues()
for task in active_tasks:
    # NEW: Quick check — if agent: label present and within grace period, skip
    if task.labels and find_agent_label(task.labels):
        if not has_stalled_label(task.labels):
            # Agent is assigned and not marked stalled — skip expensive checks
            continue

    # Fallthrough: existing reconciliation for issues without labels
    issue_data = await get_issue_with_comments(...)
    # ...
```

---

### Section 6: Frontend Label Display

#### Before: Board cards without pipeline indicators

```tsx
// In IssueCard.tsx — no pipeline-specific rendering
<Card>
  <CardTitle>{task.title}</CardTitle>
  <CardStatus>{task.status}</CardStatus>
</Card>
```

#### After: Board cards with agent badge, pipeline tag, stalled indicator

```tsx
// In IssueCard.tsx — parse pipeline labels from task.labels
const agentSlug = task.labels?.find(l => l.name.startsWith("agent:"))?.name.slice(6);
const pipelineConfig = task.labels?.find(l => l.name.startsWith("pipeline:"))?.name.slice(9);
const isStalled = task.labels?.some(l => l.name === "stalled");

<Card>
  <CardTitle>{task.title}</CardTitle>
  {agentSlug && <Badge variant="purple">{agentSlug}</Badge>}
  {pipelineConfig && <Tag variant="blue">{pipelineConfig}</Tag>}
  {isStalled && <WarningIcon className="text-red-500" />}
  <CardStatus>{task.status}</CardStatus>
</Card>
```
