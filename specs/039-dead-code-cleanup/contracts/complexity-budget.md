# Complexity Budget Contract

**Feature**: 039-dead-code-cleanup
**Date**: 2026-03-13
**Version**: 1.0

## Purpose

Defines the cyclomatic complexity targets for function decomposition and the rules governing how high-complexity functions are broken into smaller units. All complexity reduction work in Phase 4 MUST follow this contract.

## Complexity Thresholds

### Project-Wide Targets

| Threshold | CC Range | Action Required |
|-----------|----------|----------------|
| Green | CC ≤ 15 | No action needed |
| Yellow | 16 ≤ CC ≤ 30 | Acceptable; decompose if opportunity arises |
| Orange | 31 ≤ CC ≤ 40 | Should decompose in next cleanup cycle |
| Red | CC > 40 | MUST decompose — blocks further feature work on the function |

### Feature-Specific Targets

| Function | Current CC | Target CC | Threshold |
|----------|-----------|-----------|-----------|
| `post_agent_outputs_from_pr` | 123 | < 30 | Yellow max |
| `assign_agent_for_status` | 91 | < 25 | Yellow mid |
| `recover_stalled_issues` | 72 | < 20 | Yellow low |
| `GlobalSettings` | 96 | < 30 | Yellow max |
| `LoginPage` | 90 | < 30 | Yellow max |

## Decomposition Rules

### Rule 1: Preserve Public API

**MUST**: The original function signature and return type remain unchanged.
**MUST**: All extracted sub-functions are private (Python: `_` prefix; TypeScript: unexported or `_` prefix).
**MUST NOT**: Change the function's observable behavior (same inputs → same outputs/side effects).

### Rule 2: Co-locate Extracted Functions

**MUST**: Extracted sub-functions are defined in the same module/file as the original.
**MUST NOT**: Create new files solely for extracted functions.
**EXCEPTION**: If a module exceeds 500 lines after extraction, sub-functions MAY be moved to a `_helpers.py` or `_utils.ts` file in the same directory.

### Rule 3: Name for Intent

**MUST**: Extracted function names describe their purpose, not their extraction origin.

```python
# Good:
async def _detect_agent_pr(owner, repo, branch) -> Optional[PR]:
async def _extract_markdown_files(pr) -> list[FileContent]:
async def _post_done_marker(issue_number, agent_name) -> None:

# Bad:
async def _post_agent_outputs_step1(...)
async def _handle_inner_loop(...)
```

### Rule 4: Minimize Parameter Passing

**SHOULD**: Pass only the data each sub-function needs, not the entire parent context.
**SHOULD**: Use named parameters for clarity when a function takes more than 3 arguments.
**MAY**: Use a dataclass/TypedDict to group related parameters if 5+ are needed.

### Rule 5: Test Coverage Preservation

**MUST**: All existing tests pass after decomposition without modification.
**SHOULD**: Extracted functions are testable individually (but new tests are not required by this feature).
**MUST NOT**: Change error types, log messages, or return value shapes.

## Decomposition Plans

### `post_agent_outputs_from_pr` (CC=123 → 4–5 functions, each CC < 30)

| Sub-function | Responsibility | Estimated CC |
|-------------|---------------|-------------|
| `_get_active_pipeline_tasks` | Filter tasks with active pipelines and pending agent outputs | 8–12 |
| `_detect_agent_pr_completion` | Check if agent's PR work is complete (merged/ready) | 10–15 |
| `_extract_pr_markdown_files` | Fetch .md files from PR for comment posting | 5–8 |
| `_post_agent_comments` | Post markdown comments to sub-issue, Done marker to parent | 10–15 |
| `_update_tracking_after_output` | Update agent tracking table with output status | 5–8 |

### `assign_agent_for_status` (CC=91 → 4 functions, each CC < 25)

| Sub-function | Responsibility | Estimated CC |
|-------------|---------------|-------------|
| `_resolve_agent_for_status` | Look up agent from config with tracking table overrides | 10–15 |
| `_validate_assignment_context` | Validate issue context, check agent-index bounds | 8–12 |
| `_create_or_update_pipeline_state` | Create/update PipelineState for tracking | 8–10 |
| `_execute_agent_assignment` | Branch creation, Copilot assignment, tracking update | 12–18 |

### `recover_stalled_issues` (CC=72 → 4 functions, each CC < 20)

| Sub-function | Responsibility | Estimated CC |
|-------------|---------------|-------------|
| `_bootstrap_recovery_config` | Load config, resolve task list if not provided | 5–8 |
| `_detect_stalled_issue` | Check if issue meets stall criteria (no PR, no assignment) | 10–15 |
| `_check_recovery_cooldown` | Verify issue is past cooldown period | 3–5 |
| `_execute_recovery_reassignment` | Reassign agent with state reconciliation | 10–15 |

### `GlobalSettings` (CC=96 → verify/extract)

Already delegates to subcomponents (`AISettingsSection`, `DisplaySettings`, `WorkflowSettings`, `NotificationSettings`). If CC measurement includes subcomponent code:
- Verify CC of the `GlobalSettings` function itself (not file-level)
- If form orchestration exceeds CC=30, extract `useGlobalSettingsForm` custom hook

### `LoginPage` (CC=90 → 3 sub-components, each CC < 30)

| Sub-component | Responsibility | Estimated CC |
|-------------|---------------|-------------|
| `HeroSection` | Branding, tagline, feature highlights JSX | 10–15 |
| `ThemeToggle` | Dark/light mode switch button | 3–5 |
| `AuthPanel` | Login button, OAuth callback display | 10–15 |

## Verification

### During Decomposition
- Run `calculate_cyclomatic_complexity` on each extracted function
- Verify CC < target for every sub-function
- Run existing test suite — zero failures

### After Phase 4 Complete
- Run `find_most_complex_functions` with limit=10
- All results should be CC < 40
- Run `find_dead_code` — all extracted functions must have callers
- Run full test suite (backend + frontend) — zero regressions
