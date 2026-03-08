# Component Contracts: Fix — Use Exact User Input + Chat Agent Metadata When AI Enhance Is Disabled

## Overview

This is a backend-focused bug fix. Frontend component changes are minimal — the existing toggle, chat interface, and proposal confirmation flow remain structurally unchanged. The fix is in how the backend processes the `ai_enhance` flag in the task generation fallback path.

## Existing Components (No Changes)

### ChatToolbar

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

**Behavior**: No changes. The AI Enhance toggle pill renders ON/OFF state. Toggle state is persisted in `localStorage` with key `chat-ai-enhance`. Default is `true`.

### ChatInterface

**Location**: `frontend/src/components/chat/ChatInterface.tsx`

**Behavior**: No changes. The `sendMessage` mutation already passes `ai_enhance` from the component state to the API request. The proposal confirmation flow (`confirm_proposal`) is agnostic to the AI Enhance setting.

**Key code** (unchanged):
```typescript
await sendMutation.mutateAsync({
  content,
  ai_enhance: options?.aiEnhance ?? true,
  file_urls: options?.fileUrls ?? [],
});
```

## Behavioral Changes (Backend Only)

### send_message() Pipeline — Fallback Path

**Location**: `backend/src/api/chat.py` — `send_message()` function, lines 430–476

**Current Behavior**:
```
if not feature_request and not status_change:
    → generate_task_from_description(user_input)  # Always calls AI enhancement
    → Create AITaskProposal
    → Return proposal
    on error → "I couldn't generate a task from your description..."
```

**New Behavior**:
```
if not feature_request and not status_change:
    if ai_enhance is False:
        → Generate title only (lightweight Chat Agent call)
        → Create AITaskProposal with raw user input as description
        → Return proposal
        on error → "I couldn't generate metadata for your request..."
    else:
        → generate_task_from_description(user_input)  # Existing behavior
        → Create AITaskProposal
        → Return proposal
        on error → "I couldn't generate a task from your description..."
```

### User-Visible Differences

| Aspect | AI Enhance ON | AI Enhance OFF |
|--------|--------------|----------------|
| Issue description | AI-rewritten content | User's exact raw input |
| Issue title | AI-generated | AI-generated (lightweight call) |
| Labels/metadata | AI-generated (when feature request) | AI-generated (when feature request) |
| Agent Pipeline config | Appended on confirm | Appended on confirm |
| Proposal preview | Shows AI-enhanced description | Shows raw user input |
| Error on failure | "I couldn't generate a task..." | "I couldn't generate metadata..." |
| Toggle UI | Sparkles icon colored | Sparkles icon gray |

## Error Message Component

No new error components needed. The backend returns the error as a `ChatMessage` with `sender_type: ASSISTANT`, which is rendered in the existing chat message list. The only change is the error message text for the AI Enhance disabled + metadata generation failure case.
