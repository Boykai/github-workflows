# Quickstart: Add 'Human' Agent Type to Agent Pipeline

**Feature**: 014-human-agent-pipeline | **Date**: 2026-02-28

## Prerequisites

- Existing development environment set up (Docker or local Python 3.11 + Node.js)
- Backend running (`cd backend && uvicorn src.main:app --reload`)
- Frontend running (`cd frontend && npm run dev`)
- GitHub OAuth configured for authentication

## Key Files to Modify

### Backend

| File | Action | Purpose |
|------|--------|---------|
| `backend/src/constants.py` | Modify | Add `"human"` to `AGENT_DISPLAY_NAMES`; add `"human"` to builtin agent list used by `list_available_agents()` |
| `backend/src/services/workflow_orchestrator/orchestrator.py` | Modify | Extend `create_all_sub_issues()` to assign Human sub-issues to the issue creator |
| `backend/src/services/copilot_polling/pipeline.py` | Modify | Skip Copilot assignment for Human steps; add sub-issue state check for completion |
| `backend/src/services/copilot_polling/helpers.py` | Modify | Extend `_check_agent_done_on_sub_or_parent()` to detect Human completion (sub-issue closed + 'Done!' from assigned user) |
| `backend/src/services/agent_tracking.py` | Modify | Add support for Human 'Done!' pattern (no agent prefix) |

### Frontend

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/components/board/AgentTile.tsx` | Modify | Add person icon and visual distinction for `"human"` slug |

## Implementation Order

1. **Backend constants** — Add `"human"` to `AGENT_DISPLAY_NAMES` and ensure it appears in the builtin agents list. This is the foundation: once the constant exists, the Human agent shows up in the API response.

2. **Sub-issue creation** — Modify `create_all_sub_issues()` in the orchestrator to detect the `"human"` slug and assign the sub-issue to the parent issue creator instead of Copilot. Handle the edge case where the creator cannot be resolved.

3. **Agent assignment skip** — Modify the pipeline's agent assignment logic to skip Copilot-specific workflows (PR creation, workspace assignment) for the Human agent. Instead, just mark the step as active (🔄).

4. **Completion detection (sub-issue closed)** — Add a check in the polling helpers to detect when the Human agent's sub-issue has been closed. This requires fetching the sub-issue state via the GitHub API.

5. **Completion detection ('Done!' comment)** — Extend the comment-checking logic to support the Human 'Done!' pattern: exact `Done!` match (no agent prefix), authorized only from the assigned user.

6. **Idempotency verification** — Ensure that if both completion signals arrive in the same polling cycle, the pipeline advances exactly once.

7. **Frontend visual distinction** — Add a person icon and "Human" label in `AgentTile.tsx` for agents with slug `"human"`.

8. **Integration testing** — Manually test the full flow: add Human step → trigger pipeline → verify sub-issue created and assigned → close sub-issue → verify pipeline advances.

9. **Edge case testing** — Test: creator unresolved fallback, non-assigned user 'Done!' comment (should be ignored), wrong casing 'done!' (should be ignored), both signals simultaneous.

## Testing Instructions

### Manual Testing — Backend

**1. Verify Human agent appears in agent list:**

```bash
curl -s http://localhost:8000/api/v1/workflow/agents \
  -H "Cookie: session=<your_session>" | python -m json.tool | grep -A4 '"human"'
```

Expected: `"human"` agent with `"source": "builtin"` and `"display_name": "Human"`.

**2. Verify Human agent can be added to pipeline config:**

```bash
curl -s -X POST http://localhost:8000/api/v1/workflow/config \
  -H "Cookie: session=<your_session>" \
  -H "Content-Type: application/json" \
  -d '{"agent_mappings": {"In Progress": [{"slug": "human", "display_name": "Human"}]}}'
```

Expected: 200 OK, configuration saved.

**3. Verify sub-issue creation with assignment:**

Trigger a pipeline with a Human step by creating a GitHub Issue in a configured project. Verify:
- Sub-issue created with title `[human] <parent title>`
- Sub-issue assigned to the parent issue creator
- Tracking table shows `human` as 🔄 Active

**4. Verify completion via sub-issue closure:**

Close the Human sub-issue. On the next polling cycle, verify:
- Human step marked as ✅ Done
- Pipeline advances to the next step

**5. Verify completion via 'Done!' comment:**

Instead of closing the sub-issue, comment exactly `Done!` on the parent issue (as the assigned user). Verify:
- Human step marked as ✅ Done
- Pipeline advances to the next step

### Manual Testing — Frontend

**1. Verify Human appears in Add Agent dropdown:**

Navigate to pipeline configuration. Click "+ Add Agent" on any column. Verify "Human" appears in the list with a person icon.

**2. Verify Human card rendering:**

Add a Human agent to a column. Verify:
- Card displays person icon (not a letter avatar)
- Card displays "Human" label
- Card is visually distinct from automated agent cards

### Automated Testing (Optional)

```bash
# Backend tests
cd backend && pytest tests/unit/ -k "human" -v

# Frontend tests
cd frontend && npm test -- --grep "human"
```

## Validation Test Cases

| # | Test Case | Expected Result |
|---|-----------|-----------------|
| 1 | Add Human to any column via dropdown | Human card appears with person icon |
| 2 | Trigger pipeline with Human step | Sub-issue created and assigned to issue creator |
| 3 | Close Human sub-issue | Pipeline advances to next step |
| 4 | Comment 'Done!' as assigned user | Pipeline advances to next step |
| 5 | Comment 'Done!' as non-assigned user | Pipeline does NOT advance |
| 6 | Comment 'done!' (lowercase) | Pipeline does NOT advance |
| 7 | Comment 'Done' (no exclamation) | Pipeline does NOT advance |
| 8 | Both signals simultaneously | Pipeline advances exactly once |
| 9 | Creator unresolved | Sub-issue created unassigned + warning |
| 10 | Human step as first step | Works correctly |
| 11 | Human step as middle step | Works correctly |
| 12 | Human step as last step | Works correctly |
| 13 | Existing pipeline sees Human option | Human available in dropdown without reconfiguration |
