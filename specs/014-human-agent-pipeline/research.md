# Research: Add 'Human' Agent Type to Agent Pipeline

**Feature**: 014-human-agent-pipeline | **Date**: 2026-02-28

## R1: Agent Registration Strategy — Builtin Constant vs. Database Entity

**Decision**: Register 'Human' as a builtin agent constant in `constants.py`, alongside existing agents like `speckit.specify` and `copilot-review`.

**Rationale**: The existing agent discovery system combines builtin agents (defined in `constants.py` via `AGENT_DISPLAY_NAMES` and `DEFAULT_AGENT_MAPPINGS`) with repository-discovered agents (from `.github/agents/*.agent.md` files). The `list_available_agents()` service already merges both sources into a unified `AvailableAgent` list. Adding 'Human' as a builtin constant ensures it appears in all pipelines by default (FR-002, FR-010) without database migration or manual configuration. The agent slug `human` follows the existing naming pattern (lowercase, no dots for non-speckit agents like `copilot-review`).

**Alternatives considered**:
- **Database-stored agent entity**: Rejected because it would require a new migration, new CRUD endpoints, and manual setup per pipeline — violating FR-002 (must apply to all existing pipelines without reconfiguration).
- **Repository agent file (`.github/agents/human.agent.md`)**: Rejected because repository agents are optional and per-repository. The Human agent must be universally available across all pipelines (FR-001) without requiring a file in each repository.

## R2: Sub-Issue Creation — Reuse vs. New Path

**Decision**: Reuse the existing `create_all_sub_issues()` method in `WorkflowOrchestrator` with a conditional branch for the Human agent slug that injects the parent issue creator as the assignee.

**Rationale**: The orchestrator already creates sub-issues for all agents in a pipeline via `create_all_sub_issues()` (orchestrator.py:267-376). Each sub-issue is created with `github_projects_service.create_sub_issue()` and optionally assigned via `assign_issue()`. The Human agent needs only two modifications: (1) resolve the parent issue creator username from the issue metadata, and (2) call `assign_issue()` with that username instead of the Copilot bot username. This reuses the same Sub Issue creation mechanism (FR-003) and adds assignee injection (FR-004).

**Alternatives considered**:
- **Separate Human sub-issue creation function**: Rejected because it would duplicate the sub-issue creation, project-adding, and tracking logic. DRY principle (Constitution V) favors a conditional branch within the existing function.
- **Pre-creation hook pattern**: Rejected as over-engineering. A simple `if agent_slug == "human"` conditional is sufficient and readable.

## R3: Completion Detection — Dual-Signal Architecture

**Decision**: Extend the existing completion detection to support two signals for Human steps: (1) Sub Issue closed event, and (2) exact 'Done!' comment from the assigned user on the parent issue.

**Rationale**: The existing pipeline uses `check_last_comment_for_done()` in `agent_tracking.py` to detect agent completion via a comment pattern `<agent>: Done!`. For automated agents, this is the only signal. For Human agents, the Sub Issue closure is the primary UX-friendly signal (humans close issues), while 'Done!' comment support maintains pattern consistency (FR-006). The polling pipeline in `copilot_polling/pipeline.py` already checks completion on each polling cycle, so adding a Sub Issue state check alongside the existing comment check requires minimal changes to the `_check_agent_done_on_sub_or_parent()` helper.

**Alternatives considered**:
- **Webhook-only approach**: Rejected because the existing system uses a polling model (`copilot_polling/`). Adding a webhook listener would introduce a parallel detection mechanism, increasing complexity and requiring new infrastructure (webhook endpoint, event routing, signature verification). The polling approach is simpler and already proven.
- **Comment-only completion (no Sub Issue close)**: Rejected because humans naturally close issues to signal completion. Requiring a specific comment format would be a poor UX for human tasks. Both signals must be supported (FR-005, FR-006).
- **Any comment triggers completion**: Rejected because it would be error-prone. Only the exact 'Done!' string from the assigned user ensures intentional completion signaling (FR-012, edge case in spec).

## R4: Idempotent Pipeline Advancement

**Decision**: Use the existing `pipeline.current_agent_index` as the single source of truth for pipeline position. The `_advance_pipeline()` function already increments this index atomically. If both completion signals arrive in the same or consecutive polling cycles, the second call finds the agent already advanced and becomes a no-op.

**Rationale**: The existing `_advance_pipeline()` function (pipeline.py:664-941) checks `pipeline.current_agent` before advancing. If the current agent has already been marked complete and the index incremented, any subsequent call for the same agent will find a mismatch and skip. This inherent idempotency satisfies FR-008 without additional locking or deduplication logic.

**Alternatives considered**:
- **Explicit completion flag/set**: Rejected as unnecessary. The `current_agent_index` already serves as a monotonically increasing cursor that prevents double-advancement.
- **Database-level locking**: Rejected because the pipeline state is in-memory per polling cycle, not persisted to a database. The single-threaded polling loop already provides sequential processing guarantees.

## R5: Pipeline Blocking Behavior — Human as Async Step

**Decision**: Treat the Human step identically to automated agent steps in the pipeline state machine. The pipeline already blocks on each agent until completion is detected. No special "async" or "blocking" flag is needed for Human agents.

**Rationale**: The `PipelineState` model already supports blocking semantics — `current_agent_index` only advances when completion is detected, and `pipeline.is_complete` returns `False` until all agents finish. The polling loop in `pipeline.py` checks each agent's completion status on every cycle. The Human agent simply won't receive a 'Done!' signal until the human acts, which naturally blocks the pipeline. This satisfies FR-007 and FR-009 without any state machine changes.

**Alternatives considered**:
- **Special "human_pending" state**: Rejected as unnecessary complexity. The existing "active" (🔄) state already represents "waiting for completion."
- **Timeout mechanism for Human steps**: Rejected as out of scope. The spec does not mention timeouts, and humans may take days to complete tasks. The pipeline should wait indefinitely.

## R6: Agent Assignment Skipping — Human Steps Must Not Be Assigned to Copilot

**Decision**: Add a conditional check in the pipeline's agent assignment logic to skip the Copilot-specific assignment flow (PR creation, workspace assignment) for the Human agent. Instead, the Human agent's sub-issue is already assigned to the issue creator during sub-issue creation (R2).

**Rationale**: The existing `assign_agent_for_status()` method in the orchestrator assigns agents to GitHub Copilot by triggering workspace creation and PR assignment. For Human agents, this must be skipped — the Human step has no code to produce, no PR to create. The assignment was already handled during sub-issue creation. The pipeline should simply mark the Human step as "active" (🔄) in the tracking table and wait for completion signals.

**Alternatives considered**:
- **Assign to Copilot and immediately complete**: Rejected because it misunderstands the Human agent's purpose. The Human agent must wait for human action.
- **Create a separate assignment path**: Rejected in favor of a simple `if agent == "human": skip` conditional in the existing assignment flow.

## R7: Frontend Visual Distinction

**Decision**: Add a conditional rendering path in `AgentTile.tsx` that displays a person icon (👤 or SVG) and "Human" label for agents with the `human` slug. The existing `AddAgentPopover.tsx` requires no changes since it already renders any agent from the available agents list.

**Rationale**: The `AgentTile` component already renders an avatar (first letter or `avatar_url`), display name, and source badge. For the Human agent, the avatar should be a person icon instead of a letter, and the source badge could show "builtin" (matching other builtin agents). The `AddAgentPopover` already filters and displays all agents returned by `workflowApi.listAgents()`, so adding 'Human' to the builtin constants automatically makes it appear in the dropdown (FR-001, FR-010).

**Alternatives considered**:
- **New HumanAgentTile component**: Rejected because the visual differences are minimal (icon + label). A conditional branch within `AgentTile` is simpler and avoids component proliferation (Constitution V).
- **Custom CSS class approach**: Rejected in favor of inline conditional logic, consistent with how the component already handles avatar URLs and source badges.

## R8: Issue Creator Resolution and Error Handling

**Decision**: Resolve the issue creator's GitHub username from the parent issue metadata (available via GitHub API's `issue.user.login`). If the creator cannot be resolved, create the sub-issue without an assignee and add a warning comment to the parent issue.

**Rationale**: The GitHub API always includes `user.login` in issue payloads, so resolution failure is extremely rare (possible only if the user account is deleted between issue creation and pipeline trigger). The fallback of creating an unassigned sub-issue with a visible warning satisfies FR-011's requirement for clear error handling without blocking the pipeline entirely.

**Alternatives considered**:
- **Fail the pipeline on creator resolution failure**: Rejected because a missing assignee should not block the entire pipeline. The human task is still trackable via the sub-issue.
- **Assign to a default/fallback user**: Rejected because there is no universally appropriate fallback user. An unassigned sub-issue is more honest and visible.
