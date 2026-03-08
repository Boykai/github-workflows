# Quickstart: Fix — Use Exact User Input + Chat Agent Metadata When AI Enhance Is Disabled

## Prerequisites

- Python 3.13+
- Node.js 22+ and npm
- Feature branch: `git checkout 029-fix-ai-enhance-disabled`

## Setup

### Backend

```bash
cd backend
pip install -e ".[dev]"
uvicorn src.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# App available at http://localhost:5173
```

## Files to Modify

| File | Change Type | Description |
|------|------------|-------------|
| `backend/src/api/chat.py` | **Modify** | Add `ai_enhance` check in the fallback task generation path |
| `backend/src/services/ai_agent.py` | **Modify** | Add `generate_title_from_description()` method for lightweight title-only generation |

## Files That May Need Test Updates

| File | Change Type | Description |
|------|------------|-------------|
| `backend/tests/unit/test_api_chat.py` | **Modify** | Add test case for `send_message` with `ai_enhance=False` in fallback path |
| `backend/tests/unit/test_ai_agent.py` | **Modify** | Add test case for `generate_title_from_description()` method |

## Implementation Order

### Step 1: Add Title Generation Method to AIAgentService

**File**: `backend/src/services/ai_agent.py`

Add a new method `generate_title_from_description()` that:
1. Takes `user_input`, `project_name`, and optional `github_token`
2. Calls the completion provider with a focused prompt asking only for a title
3. Returns a string title
4. Falls back to truncating the user input with an ellipsis when the AI call fails

**Verification**: Run `pytest backend/tests/unit/test_ai_agent.py -v` to ensure existing tests pass.

### Step 2: Add Pipeline Branching in send_message()

**File**: `backend/src/api/chat.py`

Before the existing `generate_task_from_description()` call at line 432, add:
```python
if not chat_request.ai_enhance:
    # Title-only fallback path: use raw input as description and generate the proposal title
    try:
        title = await ai_service.generate_title_from_description(
            user_input=chat_request.content,
            project_name=project_name,
            github_token=session.access_token,
        )

        proposal = AITaskProposal(
            session_id=session.session_id,
            original_input=chat_request.content,
            proposed_title=title,
            proposed_description=chat_request.content,  # Raw user input
        )
        _proposals[str(proposal.proposal_id)] = proposal

        assistant_message = ChatMessage(
            session_id=session.session_id,
            sender_type=SenderType.ASSISTANT,
            content=f"I've created a task proposal:\n\n**{title}**\n\n{chat_request.content[:200]}{'...' if len(chat_request.content) > 200 else ''}\n\nClick confirm to create this task.",
            action_type=ActionType.TASK_CREATE,
            action_data={
                "proposal_id": str(proposal.proposal_id),
                "proposed_title": title,
                "proposed_description": chat_request.content,
                "status": ProposalStatus.PENDING.value,
            },
        )
        add_message(session.session_id, assistant_message)
        _trigger_signal_delivery(session, assistant_message, project_name)
        return assistant_message

    except Exception as e:
        logger.error("Failed to generate metadata (ai_enhance=off): %s", e, exc_info=True)
        error_message = ChatMessage(
            session_id=session.session_id,
            sender_type=SenderType.ASSISTANT,
            content="I couldn't generate metadata for your request. Your input was preserved — please try again.",
        )
        add_message(session.session_id, error_message)
        return error_message
```

**Verification**:
1. Start backend: `uvicorn src.main:app --reload --port 8000`
2. Start frontend: `cd frontend && npm run dev`
3. Open the app, select a project
4. Toggle AI Enhance OFF (gray sparkles icon)
5. Type any message and submit
6. Verify: No error message appears; a task proposal is shown with the raw input as description
7. Click confirm and verify the GitHub issue is created with the raw input in the description body

### Step 3: Verify Agent Pipeline Config Is Appended

After confirming the proposal (step 2 verification), check the created GitHub issue:
1. The description body should contain the user's exact raw input
2. Below the raw input, there should be a `---` separator followed by `## 🤖 Agent Pipeline` section
3. The Agent Pipeline table should show the configured agent steps

No code changes needed for this — the existing `confirm_proposal()` flow handles it.

### Step 4: Run Full Test Suite

```bash
cd backend
pytest tests/ -v
```

Verify all existing tests pass and the new test cases for `ai_enhance=False` also pass.

## Verification Checklist

- [ ] AI Enhance ON: Existing behavior unchanged — AI-generated title and description
- [ ] AI Enhance OFF: User's raw input used as description, AI-generated title
- [ ] AI Enhance OFF: No "I couldn't generate a task" error message
- [ ] AI Enhance OFF: Task proposal shown with correct title and raw description
- [ ] AI Enhance OFF: Confirmed proposal creates GitHub issue with raw input as body
- [ ] AI Enhance OFF: Agent Pipeline config block appended to issue description
- [ ] AI Enhance OFF: Labels, estimates, priority, assignees populated (for feature requests)
- [ ] AI Enhance OFF: Metadata generation failure shows specific error, not generic
- [ ] Empty input: Validation error regardless of AI Enhance toggle state
