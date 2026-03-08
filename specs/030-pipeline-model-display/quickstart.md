# Quickstart: Display Models Used in Agent Pipeline Section of Parent Issue Description

**Feature**: 030-pipeline-model-display | **Date**: 2026-03-08

## Prerequisites

- Python 3.12+
- The repository cloned and on the feature branch

```bash
git checkout 030-pipeline-model-display
```

## Setup

### Backend

```bash
cd backend
pip install -e ".[dev]"
```

## Files to Modify

| File | Changes |
|------|---------|
| `backend/src/services/agent_tracking.py` | Add `model` field to `AgentStep`, update `build_agent_pipeline_steps()`, `render_tracking_markdown()`, `parse_tracking_from_body()`, regex patterns |
| `backend/tests/unit/test_agent_tracking.py` | Update existing tests and add new tests for model column |

## Implementation Order

### Phase 1: Extend AgentStep Dataclass (FR-001, FR-006)

1. **agent_tracking.py** — Add `model` field to `AgentStep`
   - Add `model: str = ""` field to the `AgentStep` dataclass
   - Default `""` ensures backward compatibility with existing instantiations

**Verify**: All existing tests pass unchanged (the new field has a default value).

### Phase 2: Extract Model from AgentAssignment (FR-001, FR-002, FR-007)

2. **agent_tracking.py** — Update `build_agent_pipeline_steps()`
   - After extracting `agent_slug`, extract model name from `agent.config`
   - Logic: `model = agent.config.get("model_name", "") if isinstance(agent.config, dict) else ""`
   - Pass `model` to `AgentStep` constructor

**Verify**: Create `AgentStep` objects with model names using test helpers.

### Phase 3: Render Model Column (FR-001, FR-002, FR-003, FR-008)

3. **agent_tracking.py** — Update `render_tracking_markdown()`
   - Update table header to include "Model" column
   - Update table separator row
   - For each step, render `step.model or "TBD"` in the Model column
   - Escape `|` characters in model names: `model_display = (step.model or "TBD").replace("|", "\\|")`
   - Update module docstring to show new table format

**Verify**: Render a table with mixed model/TBD values → visually inspect Markdown output.

### Phase 4: Parse Model Column (FR-004, FR-006)

4. **agent_tracking.py** — Update `_ROW_RE` regex and `parse_tracking_from_body()`
   - Update `_ROW_RE` to match both 4-column and 5-column formats
   - Strategy: Use a regex that matches the new 5-column format, plus a separate fallback for old format
   - Populate `AgentStep.model` from parsed data (or `""` for old format)

**Verify**: Parse both old-format and new-format tracking sections.

### Phase 5: Update Tests

5. **test_agent_tracking.py** — Update all test cases
   - Update `SAMPLE_BODY` to use new 5-column format
   - Add old-format `SAMPLE_BODY_LEGACY` for backward compatibility tests
   - Update `TestBuildAgentPipelineSteps` to verify model extraction
   - Update `TestRenderTrackingMarkdown` to verify Model column
   - Update `TestParseTrackingFromBody` to verify model parsing
   - Add tests for edge cases: empty model → TBD, special characters in model name, backward compatibility

**Verify**: Run `python -m pytest tests/unit/test_agent_tracking.py -v --tb=short`

## Key Patterns to Follow

### Model Extraction Pattern

```python
def _extract_model_name(agent) -> str:
    """Extract model name from an AgentAssignment's config dict."""
    config = getattr(agent, "config", None)
    if isinstance(config, dict):
        model = config.get("model_name", "")
        return model if isinstance(model, str) else ""
    return ""
```

### Model Display Pattern

```python
def _format_model_for_table(model: str) -> str:
    """Format model name for Markdown table display."""
    if not model:
        return "TBD"
    return model.replace("|", "\\|")
```

### Backward-Compatible Parsing Pattern

```python
# New 5-column format
_ROW_RE = re.compile(
    r"\|\s*(\d+)\s*\|\s*([^|\n]+?)\s*\|\s*`([^`]+)`\s*\|\s*([^|\n]+?)\s*\|\s*([^|\n]+?)\s*\|"
)

# Old 4-column format (fallback)
_ROW_RE_OLD = re.compile(
    r"\|\s*(\d+)\s*\|\s*([^|\n]+?)\s*\|\s*`([^`]+)`\s*\|\s*([^|\n]+?)\s*\|"
)
```

## Verification

After implementation, verify:

1. **Model in table**: Create a pipeline with agents that have models assigned → the tracking table shows model names in the Model column.
2. **TBD placeholder**: Create a pipeline with agents that have no model → "TBD" appears in the Model column.
3. **Mixed models**: Pipeline with some agents having models and some without → correct mix of model names and "TBD".
4. **Backward parsing**: Parse an existing issue body with the old 4-column table → no errors, model defaults to "".
5. **Re-render migration**: Parse old table → modify state → re-render → new 5-column table with "TBD" for models.
6. **Special characters**: Model name containing `|` → escaped correctly, table renders properly.
7. **Idempotent**: Append tracking twice → same result (no double model column).
8. **Existing tests**: All existing tests in `test_agent_tracking.py` pass (updated for new column).
