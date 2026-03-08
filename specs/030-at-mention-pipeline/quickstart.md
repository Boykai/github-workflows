# Quickstart: @ Mention in Chat to Select Agent Pipeline Configuration

**Feature**: 030-at-mention-pipeline | **Date**: 2026-03-08

## Prerequisites

- Node.js 20+ and npm
- Python 3.12+
- The repository cloned and on the feature branch

```bash
git checkout 030-at-mention-pipeline
```

## Setup

### Backend

```bash
cd backend
pip install -e ".[dev]"
uvicorn src.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
# App available at http://localhost:5173
```

## New Files to Create

### Frontend Files

| File | Purpose |
|------|---------|
| `frontend/src/components/chat/MentionInput.tsx` | contentEditable div replacing textarea; supports inline mention tokens |
| `frontend/src/components/chat/MentionAutocomplete.tsx` | Floating dropdown listing pipelines matching @mention filter |
| `frontend/src/components/chat/MentionToken.tsx` | Styled chip/tag for resolved @mention inline in input |
| `frontend/src/components/chat/PipelineIndicator.tsx` | "Using pipeline: [name]" badge near the submit button |
| `frontend/src/hooks/useMentionAutocomplete.ts` | Autocomplete state management: trigger, filter, navigate, select, validate |

### Files to Modify

| File | Changes |
|------|---------|
| `backend/src/models/chat.py` | Add optional `pipeline_id: str \| None` field to `ChatMessageRequest` |
| `backend/src/api/chat.py` | Read `pipeline_id` from request; validate pipeline exists; pass to issue creation flow |
| `frontend/src/components/chat/ChatInterface.tsx` | Replace textarea with `MentionInput`; wire `MentionAutocomplete` and `PipelineIndicator`; update submit to include `pipeline_id` |
| `frontend/src/types/index.ts` | Add `MentionToken`, `MentionInputState`, `MentionFilterResult` interfaces |

## Implementation Order

### Phase 1: Backend — Accept Pipeline ID

1. **Model update** (`backend/src/models/chat.py`)
   - Add `pipeline_id: str | None = Field(default=None, ...)` to `ChatMessageRequest`
   - This is backward-compatible — no existing tests or clients affected

2. **Endpoint update** (`backend/src/api/chat.py`)
   - In `send_message`, read `chat_request.pipeline_id`
   - If provided, validate the pipeline exists via the pipeline service
   - Pass `pipeline_id` to the issue creation flow when routing through agent commands

### Phase 2: Frontend Types

1. **Types** (`frontend/src/types/index.ts`)
   - Add `MentionToken`, `MentionInputState`, `MentionFilterResult` interfaces
   - Update `ChatMessageRequest` to include `pipeline_id?: string`

### Phase 3: Frontend Components (Bottom-Up)

1. **MentionToken** component (leaf component, no dependencies)
   - Styled `<span>` with valid/invalid visual states
   - Carries `data-pipeline-id` and `data-pipeline-name` attributes

2. **MentionAutocomplete** component (depends on `MentionFilterResult` type)
   - Floating dropdown with keyboard navigation
   - Follow `CommandAutocomplete.tsx` ARIA pattern
   - Display pipeline name, description, and updated date

3. **PipelineIndicator** component (standalone)
   - Badge showing active pipeline name
   - Warning state for invalid mentions

4. **MentionInput** component (depends on `MentionToken`)
   - contentEditable div with auto-resize
   - "@" trigger detection
   - Token insertion and atomic deletion

### Phase 4: Hook

1. **useMentionAutocomplete** hook (depends on components and types)
   - Pipeline list fetching via `pipelinesApi.list()`
   - Client-side filtering with 150ms debounce
   - Token lifecycle management
   - Keyboard navigation state
   - Active pipeline tracking (last valid mention)
   - Validation and submission helpers

### Phase 5: Integration

1. **ChatInterface modifications**
   - Replace `<textarea>` with `<MentionInput>`
   - Add `<MentionAutocomplete>` overlay
   - Add `<PipelineIndicator>` near submit button
   - Wire `useMentionAutocomplete` hook
   - Update `doSubmit` to include `pipeline_id` from hook
   - Ensure slash-command and @mention autocompletes don't conflict
   - Retain all existing functionality

## Key Patterns to Follow

### Autocomplete Pattern (from existing `CommandAutocomplete.tsx`)

```typescript
// ARIA-compliant listbox pattern
<div role="listbox" aria-label="Pipeline suggestions">
  {pipelines.map((pipeline, index) => (
    <div
      key={pipeline.id}
      role="option"
      id={`mention-option-${index}`}
      aria-selected={index === highlightedIndex}
      onClick={() => onSelect(pipeline)}
      onMouseEnter={() => onHighlightChange(index)}
    >
      <span className="font-medium">{pipeline.name}</span>
      <span className="text-muted-foreground text-sm">{pipeline.description}</span>
    </div>
  ))}
</div>
```

### contentEditable Input Pattern

```typescript
// MentionInput core structure
<div
  ref={inputRef}
  contentEditable
  role="textbox"
  aria-multiline="true"
  aria-label="Chat input"
  onInput={handleInput}
  onKeyDown={handleKeyDown}
  onPaste={handlePaste}
  className="mention-input min-h-[44px] max-h-[400px] overflow-y-auto ..."
/>
```

### Token Insertion Pattern

```typescript
// Insert a mention token at the current cursor position
function insertMentionToken(pipelineId: string, pipelineName: string) {
  const span = document.createElement('span');
  span.contentEditable = 'false';
  span.setAttribute('data-pipeline-id', pipelineId);
  span.setAttribute('data-pipeline-name', pipelineName);
  span.className = 'mention-token mention-token--valid ...';
  span.textContent = `@${pipelineName}`;

  // Replace the "@query" text with the token span
  const selection = window.getSelection();
  // ... range manipulation to replace trigger text with span ...
}
```

### Hook Pattern (from existing `useChat.ts`)

```typescript
function useMentionAutocomplete({ projectId, inputRef }: Props) {
  const [state, setState] = useState<MentionInputState>(initialState);

  // Fetch pipelines lazily on first "@" trigger
  const { data: pipelineData, isLoading } = useQuery({
    queryKey: ['pipelines', projectId],
    queryFn: () => pipelinesApi.list(projectId),
    enabled: state.isAutocompleteOpen, // Only fetch when needed
    staleTime: 30_000,
  });

  // Filter pipelines client-side
  const filteredPipelines = useMemo(() => {
    if (!pipelineData?.pipelines) return [];
    const query = state.filterQuery.toLowerCase();
    return pipelineData.pipelines
      .filter(p => p.name.toLowerCase().includes(query))
      .slice(0, 10); // Show max 10 items
  }, [pipelineData, state.filterQuery]);

  // ... keyboard handlers, token management, validation ...
}
```

## Verification

After implementation, verify:

1. **Trigger**: Type "@" in the chat input → autocomplete dropdown appears with pipeline names
2. **Filter**: Type additional characters after "@" → dropdown filters in real-time (case-insensitive)
3. **Select (keyboard)**: Arrow down → Enter → pipeline inserted as a styled chip token
4. **Select (mouse)**: Click a pipeline name → token inserted
5. **Dismiss**: Press Escape → dropdown closes, "@" remains as plain text
6. **Token deletion**: Backspace into a token → entire token removed as one unit
7. **Indicator**: Insert a valid @mention → "Using pipeline: [name]" badge appears near submit
8. **Invalid mention**: Type "@nonexistent" → warning state on the text
9. **Submit with @mention**: Send message with a valid @mention → backend receives `pipeline_id`
10. **Submit without @mention**: Send message without @mention → existing behavior preserved
11. **Multiple @mentions**: Insert two @mentions → last one is used, notification shown
12. **Empty state**: Type "@" with no saved pipelines → "No pipelines found" message in dropdown
13. **Slash-command coexistence**: Type "/" → slash autocomplete works as before, no conflict
