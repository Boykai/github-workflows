# Data Model: Fix — Use Exact User Input + Chat Agent Metadata When AI Enhance Is Disabled

## Overview

This feature is a bug fix — no new entities are introduced. The existing data models already support the required behavior. This document captures the relevant entities and the behavioral changes in how they are used.

## Backend Entities (Pydantic Models)

### ChatMessageRequest (No Changes)

**Location**: `backend/src/models/chat.py` lines 94–104

```python
class ChatMessageRequest(BaseModel):
    """Request to send a chat message."""

    content: str = Field(..., max_length=100000, description="Message content")
    ai_enhance: bool = Field(
        default=True,
        description="When True, AI rewrites description. When False, use raw input as description.",
    )
    file_urls: list[str] = Field(
        default_factory=list, description="URLs of uploaded files to attach to issue"
    )
```

**Behavioral Change**: The `ai_enhance` field is already defined and transmitted from the frontend. The change is in how the backend *reads* this field — specifically, the `send_message()` function must check `ai_enhance` before entering the task generation fallback path.

### AITaskProposal (No Changes)

**Location**: `backend/src/models/recommendation.py`

```python
class AITaskProposal(BaseModel):
    proposal_id: UUID
    session_id: UUID
    original_input: str
    proposed_title: str
    proposed_description: str
    edited_title: str | None = None
    edited_description: str | None = None
    status: ProposalStatus = ProposalStatus.PENDING
```

**Behavioral Change**: When AI Enhance is disabled, `proposed_description` will be the user's exact raw input (verbatim), and `proposed_title` will be a Chat Agent–generated title. When AI Enhance is enabled, both fields remain AI-generated as before.

### IssueRecommendation (No Changes)

**Location**: `backend/src/models/recommendation.py`

```python
class IssueRecommendation(BaseModel):
    recommendation_id: UUID
    session_id: UUID
    original_input: str
    title: str
    user_story: str
    ui_ux_description: str
    functional_requirements: list[str]
    technical_notes: str
    metadata: IssueMetadata
```

**Behavioral Change**: For the feature request path (priority 1), the `ai_enhance` flag is already forwarded in `action_data`. The recommendation generation itself does not change — only how the description body is composed when the recommendation is confirmed.

### GeneratedTask (No Changes)

**Location**: `backend/src/services/ai_agent.py` line 43

```python
@dataclass
class GeneratedTask:
    """AI-generated task with title and description."""
    title: str
    description: str
```

**Behavioral Change**: This dataclass continues to be used only in the `ai_enhance = true` fallback path via `generate_task_from_description()`, where both `title` and `description` are AI-generated. When AI Enhance is disabled, the fallback path bypasses `GeneratedTask` entirely and creates an `AITaskProposal` directly, using the raw user input as `proposed_description` and an AI-generated title.

## Frontend Types (TypeScript)

### ChatToolbarProps (No Changes)

**Location**: `frontend/src/components/chat/ChatToolbar.tsx`

```typescript
interface ChatToolbarProps {
  aiEnhance: boolean;
  onAiEnhanceChange: (enabled: boolean) => void;
  onFileSelect: (files: FileList) => void;
  isRecording: boolean;
  isVoiceSupported: boolean;
  onVoiceToggle: () => void;
  voiceError: string | null;
  fileCount: number;
}
```

**Behavioral Change**: None. The toggle UI remains unchanged.

### SendMessage Options (No Changes)

**Location**: `frontend/src/components/chat/ChatInterface.tsx`

```typescript
await sendMutation.mutateAsync({
  content,
  ai_enhance: options?.aiEnhance ?? true,
  file_urls: options?.fileUrls ?? [],
});
```

**Behavioral Change**: None. The `ai_enhance` value is already correctly transmitted to the backend.

## State Transitions

### Chat Request Pipeline (Modified)

```
User submits chat message
    │
    ├── ai_enhance = true (existing behavior, unchanged)
    │   ├── Priority 0: Agent command check
    │   ├── Priority 1: Feature request → generate_issue_recommendation()
    │   ├── Priority 2: Status change → parse_status_change_request()
    │   └── Priority 3: Fallback → generate_task_from_description() ← AI-enhanced
    │
    └── ai_enhance = false (NEW behavior)
        ├── Priority 0: Agent command check (unchanged)
        ├── Priority 1: Feature request → generate_issue_recommendation() (unchanged, ai_enhance in action_data)
        ├── Priority 2: Status change → parse_status_change_request() (unchanged)
        └── Priority 3: Fallback → generate title only, use raw input as description ← NEW BRANCH
```

### AITaskProposal Status (Unchanged)

```
PENDING → CONFIRMED (user clicks confirm)
PENDING → CANCELLED (proposal expires or user cancels)
PENDING → EDITED → CONFIRMED (user edits then confirms)
```

## Validation Rules

No new validation rules. Existing rules apply:

- **Content non-empty**: Enforced by `ChatMessageRequest.sanitize_content` field validator
- **Content max length**: 100,000 characters (Pydantic field constraint)
- **Issue body max length**: `GITHUB_ISSUE_BODY_MAX_LENGTH` — checked in `confirm_proposal()` before issue creation
- **ai_enhance default**: `True` — backward compatible with clients that don't send the field
