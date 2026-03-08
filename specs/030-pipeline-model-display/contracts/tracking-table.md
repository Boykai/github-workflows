# Tracking Table Contract: Agent Pipeline Markdown Table

**Feature**: 030-pipeline-model-display | **Date**: 2026-03-08

## Table Structure

### Header

```markdown
## 🤖 Agents Pipelines
```

The tracking section is preceded by a `---` horizontal rule separator.

### Table Schema

```markdown
| # | Status | Agent | Model | State |
|---|--------|-------|-------|-------|
```

### Row Format

```markdown
| {index} | {status} | `{agent_name}` | {model_display} | {state} |
```

| Field | Type | Format | Example |
|-------|------|--------|---------|
| `index` | Integer | 1-based sequential | `1`, `2`, `3` |
| `status` | String | Pipeline status name | `Backlog`, `Ready`, `In Progress` |
| `agent_name` | String | Backtick-wrapped slug | `` `speckit.specify` `` |
| `model_display` | String | Model name or "TBD" | `gpt-4o`, `claude-3-5-sonnet`, `TBD` |
| `state` | String | Emoji + state text | `⏳ Pending`, `🔄 Active`, `✅ Done` |

### Model Display Rules

| Condition | Display Value |
|-----------|--------------|
| `AgentAssignment.config` is `None` | `TBD` |
| `AgentAssignment.config` is `{}` (empty dict) | `TBD` |
| `AgentAssignment.config.model_name` is `""` (empty string) | `TBD` |
| `AgentAssignment.config.model_name` is `"gpt-4o"` | `gpt-4o` |
| `AgentAssignment.config.model_name` contains pipe char | Escaped with backslash for Markdown table safety |

### Complete Example

```markdown
---

## 🤖 Agents Pipelines

| # | Status | Agent | Model | State |
|---|--------|-------|-------|-------|
| 1 | Backlog | `speckit.specify` | gpt-4o | ⏳ Pending |
| 2 | Ready | `speckit.plan` | claude-3-5-sonnet | ⏳ Pending |
| 3 | Ready | `speckit.tasks` | TBD | ⏳ Pending |
| 4 | In Progress | `speckit.implement` | gpt-4o | ⏳ Pending |
```

### Edge Cases

#### Empty Pipeline (No Agents)

```markdown
---

## 🤖 Agents Pipelines

| # | Status | Agent | Model | State |
|---|--------|-------|-------|-------|
```

#### Single Agent

```markdown
---

## 🤖 Agents Pipelines

| # | Status | Agent | Model | State |
|---|--------|-------|-------|-------|
| 1 | Ready | `my-agent` | gpt-4o | ⏳ Pending |
```

#### All Agents Without Models

```markdown
---

## 🤖 Agents Pipelines

| # | Status | Agent | Model | State |
|---|--------|-------|-------|-------|
| 1 | Backlog | `speckit.specify` | TBD | ✅ Done |
| 2 | Ready | `speckit.plan` | TBD | 🔄 Active |
| 3 | In Progress | `speckit.implement` | TBD | ⏳ Pending |
```

## Parsing Contract

### Regex Pattern (New Format — 5 Columns)

```python
# Matches: | 1 | Backlog | `speckit.specify` | gpt-4o | ⏳ Pending |
_ROW_RE = re.compile(
    r"\|\s*(\d+)\s*\|\s*([^|\n]+?)\s*\|\s*`([^`]+)`\s*\|\s*([^|\n]+?)\s*\|\s*([^|\n]+?)\s*\|"
)
```

**Groups**:

1. Index (integer)
2. Status (string)
3. Agent name (string, without backticks)
4. Model name (string)
5. State (string with emoji)

### Backward Compatibility (Old Format — 4 Columns)

Old tables without the Model column are still parseable. The parser uses a fallback regex (`_ROW_RE_OLD`) for the old 4-column format when the primary 5-column regex (`_ROW_RE`) finds no matches:

```python
# Old format: | 1 | Backlog | `speckit.specify` | ⏳ Pending |
# New format: | 1 | Backlog | `speckit.specify` | gpt-4o | ⏳ Pending |
```

When parsing old format, `model` defaults to `""` (renders as "TBD" on next re-render).

## Rendering Contract

### Function: `render_tracking_markdown(steps: list[AgentStep]) -> str`

**Input**: List of `AgentStep` objects (each with `index`, `status`, `agent_name`, `model`, `state`)

**Output**: Markdown string containing:

1. Empty line
2. `---` separator
3. Empty line
4. `## 🤖 Agents Pipelines` header
5. Empty line
6. Table header row: `| # | Status | Agent | Model | State |`
7. Table separator row: `|---|--------|-------|-------|-------|`
8. One data row per step
9. Trailing empty line

**Model rendering rule**: If `step.model` is empty (`""`), render `TBD`. Otherwise render the model name with pipe characters escaped.
