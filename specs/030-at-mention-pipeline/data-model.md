# Data Model: @ Mention in Chat to Select Agent Pipeline Configuration

**Feature**: 030-at-mention-pipeline | **Date**: 2026-03-08

## New Frontend Types (TypeScript)

### MentionToken

Represents a single @mention reference within the chat input.

```typescript
interface MentionToken {
  pipelineId: string;          // UUID of the referenced pipeline (FR-005)
  pipelineName: string;        // Display name at time of insertion
  isValid: boolean;            // Whether the pipeline still exists
  position: number;            // Character offset in the input content
}
```

**Relationships**: References a `PipelineConfigSummary` by `pipelineId`. Embedded within the chat input DOM as a `<span>` element with `data-pipeline-id` and `data-pipeline-name` attributes.

### MentionInputState

Internal state managed by the `useMentionAutocomplete` hook.

```typescript
interface MentionInputState {
  isAutocompleteOpen: boolean;         // Whether the dropdown is visible
  filterQuery: string;                 // Text typed after "@" for filtering
  highlightedIndex: number;            // Currently highlighted dropdown item (-1 = none)
  mentionTriggerOffset: number | null; // Cursor offset where "@" was typed (null = not active)
  activePipelineId: string | null;     // Last valid mention's pipeline ID (for submission)
  activePipelineName: string | null;   // Last valid mention's display name (for indicator)
  tokens: MentionToken[];              // All mention tokens currently in the input
  hasInvalidTokens: boolean;           // Whether any token references a deleted/unknown pipeline
}
```

### MentionFilterResult

A pipeline matching the current filter query, ready for display in the autocomplete dropdown.

```typescript
interface MentionFilterResult {
  pipeline: PipelineConfigSummary;     // Full summary from pipelinesApi.list()
  matchIndices: [number, number][];    // Character ranges in name that match the query (for highlighting)
}
```

---

## Modified Backend Model (Pydantic)

### ChatMessageRequest (Modified — Backend)

```python
class ChatMessageRequest(BaseModel):
    content: str = Field(..., max_length=100000, description="Message content")
    ai_enhance: bool = Field(
        default=True,
        description="When True, AI rewrites description. When False, use raw input as description.",
    )
    file_urls: list[str] = Field(
        default_factory=list, description="URLs of uploaded files to attach to issue"
    )
    # NEW FIELD
    pipeline_id: str | None = Field(
        default=None,
        description="Optional pipeline configuration ID from @mention selection. "
        "When provided, overrides the project's default pipeline assignment for this submission.",
    )
```

**Validation Rules**:

- `pipeline_id` is optional (default `None`) — backward-compatible with existing clients (FR-013).
- When provided, must be a valid UUID string referencing an existing `pipeline_configs` record.
- The backend validates the pipeline exists at processing time; returns 400 if the referenced pipeline is not found (FR-008).

---

## Modified Frontend Type

### ChatMessageRequest (Modified — Frontend)

```typescript
export interface ChatMessageRequest {
  content: string;
  ai_enhance?: boolean;
  file_urls?: string[];
  pipeline_id?: string;         // NEW: Optional pipeline ID from @mention
}
```

---

## Existing Entities (Unchanged)

The following existing entities are used but not modified:

- **PipelineConfigSummary** (`frontend/src/types/index.ts`): `id`, `name`, `description`, `stage_count`, `agent_count`, `total_tool_count`, `is_preset`, `preset_id`, `stages`, `updated_at` — used as the data source for autocomplete dropdown items. Already returned by `pipelinesApi.list()`.

- **PipelineConfig** (`frontend/src/types/index.ts`): Full pipeline configuration — referenced by `pipeline_id` at submission time; not directly used by the mention UI.

- **CommandAutocomplete** (`frontend/src/components/chat/CommandAutocomplete.tsx`): Existing slash-command autocomplete component — pattern reference for keyboard navigation, ARIA roles, and positioning. Not modified; `MentionAutocomplete` is a sibling component with the same structural approach.

- **ChatInterface** (`frontend/src/components/chat/ChatInterface.tsx`): Main chat component — modified to wire `MentionInput` and `MentionAutocomplete` in place of the current `<textarea>`. The `onSendMessage` callback signature changes to accept an optional `pipeline_id` parameter.

---

## State Machines

### Autocomplete Lifecycle

```text
                    ┌──────────────┐
                    │    IDLE      │  (No "@" detected)
                    │ dropdown=off │
                    └──────┬───────┘
                           │ User types "@" (preceded by space/newline/start)
                           ▼
                    ┌──────────────┐
                    │  FILTERING   │  (Dropdown visible, filtering active)
                    │ dropdown=on  │
                    │ query=""     │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────────┐
              │            │                │
        User types     User selects     User presses
        more chars     item (Enter/     Escape or
              │        click)           clicks outside
              ▼            │                │
        ┌──────────┐       │                │
        │ FILTERING│       │                │
        │ query=   │       │                │
        │ "abc"    │       │                │
        └──────────┘       │                │
                           ▼                ▼
                    ┌──────────────┐  ┌──────────────┐
                    │  TOKEN       │  │    IDLE      │
                    │  INSERTED    │  │ "@" stays as │
                    │ dropdown=off │  │ plain text   │
                    └──────┬───────┘  └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │    IDLE      │
                    └──────────────┘
```

### Mention Validation on Submit

```text
User clicks Submit
    │
    ▼
Extract all [data-pipeline-id] spans from input DOM
    │
    ▼
Any tokens found?
    │
    ├─ No  → Submit with pipeline_id = null (default behavior, FR-013)
    │
    └─ Yes → Validate each token against cached pipeline list
                │
                ├─ All invalid → Block submission, show error (FR-008)
                │
                ├─ Mixed valid/invalid → Use last valid, show warning on invalid tokens
                │
                └─ All valid → Multiple?
                                │
                                ├─ Yes → Use last valid, show "using [name]" notification (FR-007)
                                │
                                └─ No  → Use the single valid token's pipeline_id
                                          │
                                          ▼
                                    Submit with pipeline_id set
```

### Pipeline Indicator States

| Input State | Indicator Display | Style |
|------------|-------------------|-------|
| No @mention tokens | Hidden | — |
| One valid @mention | "Using pipeline: [name]" | Blue/neutral badge |
| Multiple valid @mentions | "Using pipeline: [last name]" + "Multiple pipelines — using last" tooltip | Blue badge with info icon |
| One or more invalid @mentions (no valid) | "Pipeline not found" | Red/amber warning badge |
| Mix of valid and invalid | "Using pipeline: [last valid name]" + warning on invalid tokens | Blue badge + amber inline warnings |

---

## DOM Structure for MentionInput

The `MentionInput` component renders a `contentEditable` div that contains a mix of text nodes and mention token spans:

```html
<div
  contenteditable="true"
  role="textbox"
  aria-multiline="true"
  aria-label="Chat input"
  class="mention-input ..."
>
  I want to create issues using
  <span
    contenteditable="false"
    data-pipeline-id="uuid-1234"
    data-pipeline-name="Code Review Pipeline"
    class="mention-token mention-token--valid ..."
  >@Code Review Pipeline</span>
  for the frontend module
</div>
```

**Key attributes**:

- `contentEditable="false"` on token spans makes them atomic (single-unit deletion, no cursor inside).
- `data-pipeline-id` carries the UUID for extraction on submit (FR-005).
- `data-pipeline-name` carries the display name for validation and indicator display.
- `mention-token--valid` / `mention-token--invalid` CSS classes control visual state (FR-004, FR-010).
