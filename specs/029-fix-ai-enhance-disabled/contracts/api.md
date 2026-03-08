# API Contracts: Fix — Use Exact User Input + Chat Agent Metadata When AI Enhance Is Disabled

## Base URL

All endpoints prefixed with `/api/v1/chat` and require authenticated session.

## Modified Endpoints

### Send Chat Message

`POST /api/v1/chat/messages`

**Request Body** (no changes to schema):

```json
{
  "content": "Fix the login page timeout issue",
  "ai_enhance": false,
  "file_urls": []
}
```

**Behavior when `ai_enhance = true`** (unchanged):

1. Priority 0: Check for `/agent` command → handle agent creation
2. Priority 1: Detect feature request → call `generate_issue_recommendation()` → return `IssueRecommendation` with `action_type: ISSUE_CREATE`
3. Priority 2: Detect status change → return status change proposal
4. Priority 3 (fallback): Call `generate_task_from_description()` → return `AITaskProposal` with `action_type: TASK_CREATE`

**Behavior when `ai_enhance = false`** (MODIFIED — fallback path only):

1. Priority 0: Check for `/agent` command → handle agent creation (unchanged)
2. Priority 1: Detect feature request → call `generate_issue_recommendation()` → return `IssueRecommendation` with `action_type: ISSUE_CREATE` and `ai_enhance: false` in `action_data` (unchanged — already implemented)
3. Priority 2: Detect status change → return status change proposal (unchanged)
4. **Priority 3 (fallback): NEW BEHAVIOR**
   - Skip `generate_task_from_description()`
   - Generate title only using a lightweight Chat Agent call
   - Create `AITaskProposal` with:
     - `proposed_title`: Chat Agent–generated title from raw input
     - `proposed_description`: User's exact, unmodified `content` text
   - Return proposal with `action_type: TASK_CREATE`

**Response (ai_enhance = false, fallback path)** — 200 OK:

```json
{
  "session_id": "uuid",
  "sender_type": "assistant",
  "content": "I've created a task proposal:\n\n**Fix Login Page Timeout Issue**\n\nFix the login page timeout issue...\n\nClick confirm to create this task.",
  "action_type": "task_create",
  "action_data": {
    "proposal_id": "uuid",
    "proposed_title": "Fix Login Page Timeout Issue",
    "proposed_description": "Fix the login page timeout issue",
    "status": "pending"
  }
}
```

**Error Responses** (MODIFIED):

| Condition | ai_enhance = true | ai_enhance = false |
|-----------|-------------------|---------------------|
| AI task generation fails | "I couldn't generate a task from your description. Please try again with more detail." (unchanged) | "I couldn't generate metadata for your request. Your input was preserved — please try again." (NEW — specific error) |
| Empty content | 422 Validation Error (unchanged) | 422 Validation Error (unchanged) |
| No project selected | 422 "Please select a project first" (unchanged) | 422 "Please select a project first" (unchanged) |
| AI not configured | AI not configured message (unchanged) | AI not configured message (unchanged) |

### Confirm Proposal

`POST /api/v1/chat/proposals/{proposal_id}/confirm`

**Behavior** (unchanged):

1. Create GitHub Issue with `proposal.final_title` and `proposal.final_description` (which is the raw user input when ai_enhance was false)
2. Add issue to project
3. Set up workflow config and assign agent
4. Append Agent Pipeline tracking table to issue body (via orchestrator)
5. Create sub-issues and start pipeline

No changes needed — the confirm flow is already agnostic to the `ai_enhance` flag.

## No New Endpoints

This is a bug fix — no new API endpoints are required. The existing `send_message` and `confirm_proposal` endpoints handle both the enhanced and non-enhanced flows.

## Backend Service Method Changes

### AIAgentService

**New method**: `generate_title_from_description(user_input, project_name, github_token)` → `str`

- Lightweight Chat Agent call to generate a meaningful title from raw user input
- Reuses the existing completion provider (`_call_completion`)
- Uses a focused prompt asking only for a title (not full task generation)
- Returns a string title
- Falls back to a truncated version of the user input if the AI call fails

**Existing method** (no changes): `generate_task_from_description()` — still used when `ai_enhance = true`

**Existing method** (no changes): `generate_issue_recommendation()` — still used for feature requests regardless of `ai_enhance`
