# Research: Use Selected Agent Pipeline Config from Project Page When Creating GitHub Issues via Chat

**Feature**: 030-chat-pipeline-config | **Date**: 2026-03-08

## R1: Pipeline Resolution Strategy — Backend vs Frontend

**Task**: Determine whether the chat should resolve the pipeline configuration on the frontend (sending a pipeline ID with the confirm request) or on the backend (resolving the assigned pipeline at issue-creation time).

**Decision**: Backend-side resolution. The `confirm_proposal` endpoint in `chat.py` will call a new `resolve_project_pipeline_mappings(project_id)` function in `config.py` that reads the project's `assigned_pipeline_id` from `project_settings`, fetches the full `PipelineConfig` from `pipeline_configs`, and converts its stages/agents into `agent_mappings` format. The frontend does not send a `pipeline_id` with the confirmation request.

**Rationale**: The backend has authoritative access to the database and can guarantee the pipeline still exists at the moment of issue creation. If the frontend sent a `pipeline_id`, there would be a time-of-check-to-time-of-use (TOCTOU) race condition: the pipeline could be deleted between when the user saw it in the chat UI and when they clicked "Confirm". Backend resolution eliminates this class of bug entirely. Additionally, the backend already has the pattern of resolving pipeline configuration at execution time (`load_user_agent_mappings()` in `config.py`), so this follows the established approach. The `confirm_proposal` endpoint already loads and manipulates `WorkflowConfiguration` — adding pipeline resolution fits naturally into that flow.

**Alternatives Considered**:

- **Frontend sends pipeline_id in ProposalConfirmRequest**: Rejected — introduces TOCTOU race condition. The backend would need to validate the ID anyway, making the frontend parameter redundant. Also increases API surface area unnecessarily.
- **Frontend sends full pipeline config (stages/agents) in request body**: Rejected — large payload, potential for tampering, and the config could be stale. The backend should be the source of truth.
- **WebSocket push from backend when pipeline changes**: Considered for real-time sync but rejected for the MVP scope — TanStack Query's refetch-on-focus and staleTime already provide near-real-time sync (< 2s). WebSocket could be a Phase 2 enhancement.

---

## R2: Pipeline-to-Agent-Mappings Conversion

**Task**: Determine how to convert a `PipelineConfig` (with abstract stages containing agents) into `WorkflowConfiguration.agent_mappings` (status name → ordered list of `AgentAssignment`).

**Decision**: Create a `load_pipeline_as_agent_mappings(project_id, pipeline_id)` function in `config.py` that: (1) fetches the `PipelineConfig` from the `pipeline_configs` table via `PipelineService.get_pipeline()`, (2) iterates over its `stages` in order, and (3) builds a dict mapping each stage's `name` to an ordered list of `AgentAssignment` objects derived from each stage's `agents` list. Each `PipelineAgentNode` has a `slug`, `display_name`, `model_id`, and `model_name` — these map directly to the `AgentAssignment` fields.

**Rationale**: The `PipelineConfig.stages` and `WorkflowConfiguration.agent_mappings` model the same concept (status → agents) using different data structures. The pipeline's stage `name` corresponds to the workflow's status name (e.g., "Backlog", "In Progress", "In Review"). The conversion is straightforward and deterministic. Placing this function in `config.py` alongside `load_user_agent_mappings()` keeps all mapping resolution logic co-located. The function returns `dict[str, list[AgentAssignment]] | None` to match the return type of `load_user_agent_mappings()`, allowing the caller to use either interchangeably.

**Alternatives Considered**:

- **Store pre-computed agent_mappings when pipeline is assigned**: Rejected — creates a synchronization problem. If the pipeline is edited after assignment, the pre-computed mappings would be stale. Computing on-the-fly ensures the latest pipeline definition is always used.
- **Add a method to PipelineService**: Considered, but the conversion produces `AgentAssignment` objects (a workflow_orchestrator model), not pipeline models. Putting it in `config.py` avoids a circular dependency between services.
- **Inline the conversion in chat.py**: Rejected — the same conversion is needed in `signal_chat.py` and `chores/service.py`. A shared utility function enables DRY reuse.

---

## R3: Resolution Priority and Fallback Chain

**Task**: Determine the priority order when multiple pipeline configuration sources exist (project-level assignment, user-specific mappings, default mappings).

**Decision**: Three-tier fallback chain:

1. **Project-level pipeline** (`assigned_pipeline_id` in `project_settings` for user `__workflow__`): Highest priority. If a pipeline is assigned to the project and the pipeline still exists, convert it to agent_mappings and use it.
2. **User-specific mappings** (`agent_pipeline_mappings` in `project_settings` for the current `github_user_id`): Second priority. If no project-level pipeline is assigned (or it was deleted), fall back to the user's manually configured mappings.
3. **Default agent mappings** (`DEFAULT_AGENT_MAPPINGS` in `models/workflow.py`): Lowest priority. If neither project pipeline nor user mappings exist, use the system default.

The resolution function `resolve_project_pipeline_mappings(project_id, github_user_id)` implements this chain and returns both the resolved mappings and metadata (source: "pipeline" | "user" | "default", pipeline_name: string | None) for the confirmation message.

**Rationale**: The project-level pipeline is the authoritative configuration set by the project owner/admin on the Projects page. It should take precedence over individual user overrides to ensure consistency across all team members. User-specific mappings are preserved as a fallback for backward compatibility (users who configured mappings before the pipeline feature existed). The default mappings ensure the system always has a valid configuration, even for new projects with no pipeline. This chain matches the spec's requirement (FR-003): "System MUST NOT default to a hardcoded or previously used Agent Pipeline when a valid Project-page selection exists."

**Alternatives Considered**:

- **User mappings override project pipeline**: Rejected — contradicts FR-003 and FR-001. The spec explicitly requires that the project-page selection takes precedence. User overrides would create inconsistency ("I selected Pipeline Alpha on the Project page, but my issue used something else").
- **No fallback, require explicit pipeline**: Rejected — would break backward compatibility for existing users who have no pipeline assigned. The default mappings ensure the system always works.
- **Merge project pipeline with user overrides**: Rejected — complex merging logic with unclear semantics. Which takes precedence for a given status? Too much implicit behavior. Clean tier-based fallback is simpler and more predictable.

---

## R4: Chat UI Pipeline Indicator — Warning and Confirmation

**Task**: Determine how to surface pipeline state in the chat UI (warning when none selected, confirmation after creation).

**Decision**: Two UI elements:

1. **PipelineWarningBanner** (new component): Shown above the chat input area when no pipeline is assigned to the current project. Uses the existing `GET /pipelines/{projectId}/assignment` endpoint via a `useSelectedPipeline(projectId)` hook. Displays an amber/yellow inline warning: "⚠ No Agent Pipeline selected — issues will use the default pipeline. Select one on the Project page." The banner disappears when a pipeline is assigned (React Query refetch on window focus or mutation invalidation).

2. **Pipeline name in TaskPreview confirmation**: After issue creation succeeds, the `TaskPreview` component (which shows the created issue) displays a small badge or text line: "Agent Pipeline: {pipeline_name}" (or "Agent Pipeline: Default" if fallback was used). This requires the `confirm_proposal` backend response to include the resolved pipeline name — add a `pipeline_name: str | None` field to the `AITaskProposal` response model.

**Rationale**: The warning banner addresses FR-005 (warn when no pipeline selected) and the confirmation text addresses FR-007 (surface applied pipeline name). Both are lightweight additions to existing UI components. The hook-based approach (`useSelectedPipeline`) ensures the banner state is always in sync with the Project page (FR-004) via React Query's cache and refetch mechanics. No modal or blocking dialog is needed — an inline banner is less intrusive and matches the chat's conversational UI pattern.

**Alternatives Considered**:

- **Blocking modal when no pipeline**: Rejected — too intrusive for the chat context. A modal would interrupt the conversation flow. The spec says "SHOULD display a warning," not "MUST block."
- **Pipeline selector in chat**: Rejected — duplicates the Project page's selector. The spec wants the chat to "silently inherit" the Project page selection, not provide its own selection UI. Adding a selector in chat would create a confusing dual-source-of-truth.
- **Toast notification for pipeline name**: Considered but deferred — a toast is transient and could be missed. An inline text in the confirmation is persistent and always visible in the chat history.

---

## R5: Handling Deleted or Unavailable Pipelines

**Task**: Determine how to handle the case where a selected pipeline is deleted mid-session.

**Decision**: Backend-side graceful degradation with frontend notification.

**Backend**: When `resolve_project_pipeline_mappings()` finds an `assigned_pipeline_id` but the pipeline no longer exists in `pipeline_configs`, it: (1) logs a warning, (2) clears the stale `assigned_pipeline_id` in `project_settings` (auto-cleanup), and (3) falls through to the next tier in the fallback chain (user mappings or defaults). The `pipeline_name` in the response will indicate the fallback source.

**Frontend**: The `useSelectedPipeline` hook's query will return an empty `pipeline_id` after the backend clears the stale assignment. React Query's refetch-on-focus will pick this up, causing the `PipelineWarningBanner` to appear in the chat. Additionally, the `PipelineSelector` on the Projects page already handles this case (line 63-67 in `PipelineSelector.tsx`): "⚠ Selected pipeline no longer available."

**Rationale**: Auto-cleanup prevents persistent stale references. The backend is the right place to detect and clean up deleted pipelines because it has access to the database and can do it atomically. The frontend notification happens naturally through React Query cache invalidation — no special WebSocket or polling needed. This approach handles FR-008 (detect deleted pipelines, notify user, prompt re-selection) with minimal new code.

**Alternatives Considered**:

- **Proactive deletion notification via WebSocket**: Rejected for MVP — adds significant complexity. The backend doesn't currently broadcast pipeline deletions. The lazy detection approach (check at issue-creation time) is simpler and covers the critical path.
- **Frontend periodic polling for pipeline validity**: Rejected — unnecessary network overhead. The refetch-on-focus pattern is sufficient for detecting stale pipelines within a reasonable timeframe.
- **Soft-delete pipelines instead of hard-delete**: Rejected — would require schema changes and doesn't solve the core problem (the user still needs to re-select). The auto-cleanup approach is simpler.
