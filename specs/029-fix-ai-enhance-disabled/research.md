# Research: Fix — Use Exact User Input + Chat Agent Metadata When AI Enhance Is Disabled

## R1: Root Cause of the Generic Error When AI Enhance Is Disabled

**Task**: Determine exactly why the error "I couldn't generate a task from your description" is thrown when AI Enhance is disabled.

**Decision**: The error originates in `backend/src/api/chat.py` lines 465–476. The `send_message()` function has a three-priority pipeline: (0) agent commands, (1) feature request detection, (2) status change detection, and a fallback at (3) task generation via `generate_task_from_description()`. The `ai_enhance` flag is only passed through in priority 1 (feature requests) at line 329. In the fallback path (lines 430–476), the flag is never checked — the system unconditionally calls the AI enhancement step, which either fails or produces unwanted results, and the catch-all exception handler returns the generic error.

**Rationale**: The fix must add a conditional check for `chat_request.ai_enhance` at the start of the fallback task generation block (before line 432). When disabled, the system should bypass `generate_task_from_description()` and instead create a proposal using the raw user input as the description, with a Chat Agent–generated title.

**Alternatives Considered**:
- **Frontend-only fix (rejected)**: Could suppress the error on the frontend, but the issue wouldn't be created at all — the backend must handle the branching.
- **Always-skip task generation (rejected)**: Removing the fallback entirely would break the existing flow when AI Enhance is enabled.
- **Retry with different prompt (rejected)**: The problem isn't a transient failure — it's a logic gap in the pipeline.

## R2: Title Generation Strategy When AI Enhance Is Disabled

**Task**: Determine how to generate a useful fallback title when the user's input is used verbatim as the description.

**Decision**: Add a lightweight `generate_title_from_description()` helper in `AIAgentService` for the task fallback path while continuing to reuse `generate_issue_recommendation()` for the feature-request path. The fallback task proposal only needs a meaningful title plus the raw input body, so a focused title-generation helper keeps the branch simple and aligned with the existing proposal UX.

**Rationale**: The feature-request path and the generic task-proposal fallback path have different output contracts. `generate_issue_recommendation()` remains the right choice when the system is creating a full issue recommendation with structured metadata. The task fallback path only needs a concise proposal title, so a dedicated helper avoids over-generating unused fields and keeps the fallback branch explicit.

**Alternatives Considered**:
- **Reuse `generate_issue_recommendation()` everywhere (rejected)**: The fallback task proposal does not use labels, estimates, priority, or assignees, so generating the full recommendation payload would add complexity without improving the user-visible proposal flow.
- **Simple title extraction without AI (rejected)**: Using the first sentence or truncation would produce low-quality titles. The Chat Agent can generate a meaningful title from raw input.
- **Skip title generation entirely (rejected)**: The fallback proposal still needs a meaningful title to keep the confirmation UX usable.

## R3: Pipeline Branching Architecture

**Task**: Determine the best way to implement the two-track pipeline (full AI pipeline vs. title-only fallback).

**Decision**: Add a conditional check at the top of the fallback task generation block in `send_message()` (line 430). When `chat_request.ai_enhance` is `False`:
1. Call a lightweight method to generate a title from the raw input (using the existing AI service).
2. Create an `AITaskProposal` with `proposed_description` set to the user's exact `chat_request.content`.
3. Skip `generate_task_from_description()` entirely.
4. Return the proposal to the user for confirmation (same UX flow as the enhanced path).

When `chat_request.ai_enhance` is `True`: Keep the existing behavior unchanged.

**Rationale**: This is the minimal change that fixes the bug while preserving backward compatibility. The branching happens at a single point in the pipeline, and both paths converge at the same proposal confirmation flow. The Agent Pipeline configuration block is already appended during `confirm_proposal()` (via the workflow orchestrator), so no additional work is needed for that.

**Alternatives Considered**:
- **Middleware-level branching (rejected)**: Moving the branching to a middleware or decorator would over-engineer a single-endpoint fix and violate Constitution V (Simplicity).
- **Separate endpoint for non-enhanced flow (rejected)**: Would duplicate the proposal/confirmation UX and increase frontend complexity unnecessarily.
- **Feature flag at the service layer (rejected)**: The `ai_enhance` flag is already a per-request parameter — no need for an additional feature flag system.

## R4: Error Handling Refinement for Metadata Generation Failures

**Task**: Determine how to surface specific, actionable errors when the Chat Agent metadata generation itself fails (independent of AI Enhance).

**Decision**: In the fallback path for AI Enhance disabled, wrap the title generation call in a separate try/except block. If it fails, return a specific error message: "I couldn't generate metadata for your request. Your input was preserved — please try again." This replaces the generic catch-all error. The existing error handling for AI Enhance enabled remains unchanged.

**Rationale**: FR-007 requires specific, actionable errors when metadata generation fails independently. By separating the error handling for the two paths, we can provide targeted feedback without affecting the existing enhanced flow. The error message tells the user their input wasn't lost and gives clear guidance.

**Alternatives Considered**:
- **Unified error handler for both paths (rejected)**: Would require checking `ai_enhance` in the exception handler, adding complexity to an already-complex function.
- **Silent fallback with no title (rejected)**: Creating an issue with no title or a placeholder title would violate FR-008 (structural parity).
- **Frontend toast-based error reporting (rejected)**: The error must originate from the backend response to maintain API consistency.

## R5: Agent Pipeline Configuration Append Strategy

**Task**: Verify that the Agent Pipeline configuration block is appended correctly for issues created with AI Enhance disabled.

**Decision**: No additional work needed. The Agent Pipeline configuration block is appended during `confirm_proposal()` in `backend/src/api/chat.py` lines 603–696, via the `WorkflowOrchestrator.create_all_sub_issues()` and `assign_agent_for_status()` calls. This happens after the issue is created from the proposal, regardless of the `ai_enhance` flag. The tracking table is appended by `append_tracking_to_body()` in `agent_tracking.py` (line 136) which is called from the orchestrator.

**Rationale**: The Agent Pipeline configuration is already structurally independent of the AI Enhance setting. Both the enhanced and non-enhanced paths converge at `confirm_proposal()`, which handles the pipeline configuration uniformly. The tracking section uses a clearly delimited markdown format (horizontal rule + "## 🤖 Agent Pipeline" heading) that is visually distinct from the user's raw input.

**Alternatives Considered**:
- **Append tracking in send_message instead of confirm_proposal (rejected)**: Would require duplicating tracking logic and would add the tracking block before the user confirms the proposal.
- **Different tracking format for non-enhanced issues (rejected)**: Would violate FR-008 (structural parity) and create confusion in downstream automations.

## R6: Input Validation for Empty/Whitespace Messages

**Task**: Determine whether empty/whitespace input validation already exists or needs to be added.

**Decision**: Input validation already exists. The `ChatMessageRequest` model in `backend/src/models/chat.py` (line 106) has a `field_validator("content")` that sanitizes content. The `sanitize_content` validator at line 110 checks `if not v or not v.strip()` and presumably raises a validation error for empty/whitespace-only input. No additional work needed for FR-009.

**Rationale**: Pydantic field validators run before the request reaches the `send_message()` function, so empty input is already rejected at the API layer. The existing validation satisfies FR-009 without any code changes.

**Alternatives Considered**:
- **Additional check in send_message (rejected)**: Would be redundant with the Pydantic validator and violate DRY.
- **Frontend-only validation (rejected)**: Must be validated server-side as well for API safety.
