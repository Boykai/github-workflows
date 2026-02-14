# Research: Spec Kit Custom Agent Assignment by Status

**Feature**: 002-speckit-agent-assignment  
**Date**: 2026-02-13  
**Purpose**: Resolve all Technical Context unknowns and document design decisions

## Research Tasks

### R1: How to extend `assign_copilot_to_issue()` for per-status agents

**Decision**: Reuse the existing `assign_copilot_to_issue()` method as-is — it already accepts `custom_agent` and `custom_instructions` parameters. No changes needed to the assignment API call itself. The change is in **who calls it and with what agent name**, not in how the call works.

**Rationale**: The REST API (`POST /repos/{owner}/{repo}/issues/{issue_number}/assignees`) and GraphQL fallback (`addAssigneesToAssignable` with `agentAssignment`) both accept a `customAgent` string field. Passing `"speckit.specify"`, `"speckit.plan"`, `"speckit.tasks"`, or `"speckit.implement"` is functionally identical to the current `custom_agent` usage — only the value changes per status.

**Alternatives considered**:
- Creating a new assignment method per agent type — rejected because the underlying API is the same; only the `custom_agent` value differs.
- Batch-assigning multiple agents at once — rejected because GitHub Copilot supports only one active agent per issue at a time.

---

### R2: How to detect comment-based agent completion

**Decision**: Add a `check_agent_completion_comment()` method to `GitHubProjectsService` that uses the existing `get_issue_with_comments()` GraphQL query (which returns up to 100 comments) and scans for a comment body matching the pattern `<agent-name>: All done!>`. The scan checks comments in reverse chronological order for the most recent completion marker.

**Rationale**: The `get_issue_with_comments()` method already fetches issue comments via GraphQL (`GET_ISSUE_WITH_COMMENTS_QUERY`). Adding comment pattern matching requires no new API calls — it's a filter on data we already retrieve. This is simpler than using the REST timeline API or webhooks.

**Alternatives considered**:
- Webhook-based detection (GitHub `issue_comment` event) — rejected because the system already uses polling and adding webhook handling for comments would introduce a second detection path, complicating the architecture.
- REST API `GET /repos/{owner}/{repo}/issues/{issue_number}/comments` — rejected because GraphQL query already fetches comments and is used elsewhere; would be a redundant API path.
- Regex pattern matching on comment body — considered but the completion marker is a simple string match, not a regex pattern. Exact match (or `startswith`) on `"<agent-name>: All done!>"` is sufficient.

---

### R3: How to restructure `execute_full_workflow()` for the new pipeline

**Decision**: Modify `execute_full_workflow()` to stop after placing the issue in Backlog with `speckit.specify` assigned, instead of running all the way through to In Progress. The polling service will handle all subsequent transitions (Backlog→Ready, Ready→In Progress). This decouples the synchronous issue creation from the asynchronous agent pipeline.

**Rationale**: Currently `execute_full_workflow()` chains: create issue → add to project (Backlog) → transition to Ready → `handle_ready_status()` (assign Copilot + move to In Progress). With the new pipeline, the issue must wait in Backlog for `speckit.specify` to complete before moving to Ready. This wait is inherently asynchronous (could take minutes to hours), so the polling service is the right place to detect completion and trigger transitions.

**Alternatives considered**:
- Keep `execute_full_workflow()` synchronous and add `await` loops for agent completion — rejected because blocking a FastAPI request for minutes/hours is not viable.
- Use background tasks (`asyncio.create_task`) spawned from `execute_full_workflow()` — rejected because this creates orphan tasks that are hard to track and duplicate the polling service's responsibility.

**Changes to `execute_full_workflow()`**:
1. Create issue from recommendation (unchanged)
2. Add to project with Backlog status (unchanged)
3. Assign `speckit.specify` agent to the issue (NEW — replaces transition to Ready)
4. Return context with `state = BACKLOG` (changed from continuing to Ready)
5. Remove direct calls to `transition_to_ready()` and `handle_ready_status()`

---

### R4: How to extend the polling service for multi-status monitoring

**Decision**: Extend `poll_for_copilot_completion()` to add two new check functions alongside `check_in_progress_issues()`:
1. `check_backlog_issues()` — polls Backlog issues for `speckit.specify: All done!>` comment
2. `check_ready_issues()` — polls Ready issues for `speckit.plan: All done!>` and `speckit.tasks: All done!>` comments

Each function follows the same pattern as `check_in_progress_issues()`: fetch project items, filter by status, check each matching issue.

**Rationale**: The polling loop already iterates on a configurable interval and has error handling, deduplication, and state tracking. Adding new status checks is a natural extension. The functions share the same `get_project_items()` call (called once per poll cycle, results filtered by status).

**Alternatives considered**:
- Separate polling loops per status — rejected because they'd make redundant `get_project_items()` API calls and complicate lifecycle management.  
- Event-driven architecture (webhooks for all transitions) — rejected per clarification Q4; extending polling is simpler and consistent with the existing approach.

**Polling flow after changes**:
```
poll_for_copilot_completion():
  items = get_project_items()
  
  1. check_backlog_issues(items)
     → For each Backlog issue: check for "speckit.specify: All done!>"
     → If found: transition to Ready, assign speckit.plan
  
  2. check_ready_issues(items)
     → For each Ready issue: check pipeline state
     → If awaiting plan: check for "speckit.plan: All done!>"
       → If found: assign speckit.tasks, update pipeline state
     → If awaiting tasks: check for "speckit.tasks: All done!>"
       → If found: transition to In Progress, assign speckit.implement
  
  3. check_in_progress_issues(items)  # existing, unchanged
     → Check for Copilot PR completion
     → Transition to In Review
  
  4. check_in_review_issues(items)    # existing, unchanged
     → Ensure Copilot review requested
```

---

### R5: Pipeline state management for sequential agents

**Decision**: Introduce a `PipelineState` dataclass to track per-issue pipeline progress. Store instances in a module-level dict (`_pipeline_states: dict[int, PipelineState]`) keyed by issue number. On system restart, reconstruct state by scanning issue comments for completion markers.

**Rationale**: The Ready status has a two-agent pipeline (plan→tasks). The system needs to know whether to check for plan completion or tasks completion. A simple dataclass with `current_agent` and `completed_agents` fields provides this tracking without a database.

**Data structure**:
```python
@dataclass
class PipelineState:
    issue_number: int
    status: str                     # "Backlog", "Ready", "In Progress"
    agents: list[str]               # Ordered agents for this status
    current_agent_index: int        # Index of currently active agent
    completed_agents: list[str]     # Agents that have completed
    started_at: datetime | None     # When current agent was assigned
    
    @property
    def current_agent(self) -> str | None:
        if self.current_agent_index < len(self.agents):
            return self.agents[self.current_agent_index]
        return None
    
    @property
    def is_complete(self) -> bool:
        return self.current_agent_index >= len(self.agents)
```

**Reconstruction on restart**:
```python
async def reconstruct_pipeline_state(issue_number, status, agent_mappings, issue_comments):
    agents = agent_mappings.get(status, [])
    completed = []
    for agent in agents:
        marker = f"{agent}: All done!>"
        if any(marker in comment.body for comment in issue_comments):
            completed.append(agent)
        else:
            break  # Sequential pipeline — stop at first incomplete agent
    
    return PipelineState(
        issue_number=issue_number,
        status=status,
        agents=agents,
        current_agent_index=len(completed),
        completed_agents=completed,
    )
```

**Alternatives considered**:
- Store pipeline state in GitHub Issue labels — rejected because labels are not ordered and would require complex label management.
- Store pipeline state in a database — rejected per spec constraint (in-memory only; comments are durable store).
- Use GitHub Issue custom fields — rejected because Projects V2 custom fields are project-level, not issue-level metadata.

---

### R6: Agent mapping configuration model

**Decision**: Replace the single `custom_agent: str` field on `WorkflowConfiguration` with `agent_mappings: dict[str, list[str]]` that maps status names to ordered lists of agent names. Provide defaults matching the spec: `{"Backlog": ["speckit.specify"], "Ready": ["speckit.plan", "speckit.tasks"], "In Progress": ["speckit.implement"]}`.

**Rationale**: A dict of status→agent-list naturally represents both single-agent statuses (Backlog, In Progress) and multi-agent pipelines (Ready). Using a list even for single agents keeps the data model uniform and avoids special-casing.

**Default mapping**:
```python
DEFAULT_AGENT_MAPPINGS = {
    "Backlog": ["speckit.specify"],
    "Ready": ["speckit.plan", "speckit.tasks"],
    "In Progress": ["speckit.implement"],
}
```

**Alternatives considered**:
- Keep `custom_agent` as a string and add a separate `agent_pipeline` field — rejected because it splits related configuration across two fields.
- Use a list of `AgentMappingEntry` objects with `status` and `agents` fields — rejected because it's more verbose than a dict and harder to look up by status.
- Nested Pydantic model `AgentMapping` with individual status fields — rejected because it would not support dynamic status names, which the spec requires for configurability (FR-013).

---

### R7: Frontend type synchronization

**Decision**: Update the `WorkflowConfiguration` TypeScript interface in `frontend/src/types/index.ts` to replace the missing `custom_agent` field with `agent_mappings: Record<string, string[]>`. This is a minor type change — the frontend displays configuration but doesn't drive agent assignment.

**Rationale**: The frontend `WorkflowConfiguration` type is already missing the `custom_agent` field present in the backend model. Adding `agent_mappings` brings the type in sync. The change is additive and doesn't break existing UI components since `custom_agent` wasn't referenced in the frontend.

**Alternatives considered**:
- Leave the frontend type unchanged — rejected because type inconsistency would cause confusion and potential runtime errors when displaying config.
- Create a separate `AgentMappingConfig` type — rejected because the mapping is a property of `WorkflowConfiguration`, not a standalone entity.

---

### R8: WebSocket notification integration

**Decision**: Use the existing `connection_manager.broadcast_to_project()` pattern to send real-time notifications for agent assignment and completion events. Add new notification types: `"agent_assigned"` and `"agent_completed"` with payload including `issue_number`, `agent_name`, `status`, and `timestamp`.

**Rationale**: The workflow orchestrator already sends WebSocket notifications for status transitions. Adding agent-specific notifications follows the established pattern. The `broadcast_to_project()` method handles serialization and delivery to all connected clients for a given project.

**Notification payloads**:
```python
# Agent assigned
{
    "type": "agent_assigned",
    "issue_number": 42,
    "agent_name": "speckit.plan",
    "status": "Ready",
    "timestamp": "2026-02-13T10:30:00Z"
}

# Agent completed
{
    "type": "agent_completed", 
    "issue_number": 42,
    "agent_name": "speckit.plan",
    "status": "Ready",
    "next_agent": "speckit.tasks",  # or null if pipeline complete
    "timestamp": "2026-02-13T10:35:00Z"
}
```

**Alternatives considered**:
- SSE (Server-Sent Events) for notifications — rejected because the system already uses WebSocket and adding SSE would be a parallel notification channel.
- Polling-based notifications (client polls an endpoint) — rejected because it adds latency and increases API load.

---

### R9: Error handling and fallback strategy

**Decision**: On agent assignment failure, the system (1) logs the error with full context, (2) sends a WebSocket notification with the error details, (3) leaves the issue in its current status for manual intervention, and (4) does not retry automatically. The pipeline state records the failure for visibility.

**Rationale**: Agent failures could be transient (API rate limit) or permanent (invalid agent name). Automatic retry could cause repeated failures and noise. Leaving the issue in place preserves the workflow state and allows the user to investigate and manually re-trigger.

**Alternatives considered**:
- Automatic retry with exponential backoff — rejected for simplicity; the polling service will naturally re-attempt on the next cycle if the issue is still in the same status and no completion marker exists.
- Move issue to an "Error" status — rejected because there's no such status in the project board, and adding one would change the project configuration.
- Fall back to generic Copilot (no custom agent) — considered but rejected as default behavior because it would bypass the Spec Kit pipeline; instead, fall back to `copilot_assignee` (configured human assignee) if set.
