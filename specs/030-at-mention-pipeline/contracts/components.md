# Component Contracts: @ Mention in Chat to Select Agent Pipeline Configuration

**Feature**: 030-at-mention-pipeline | **Date**: 2026-03-08

## New Components

### MentionInput

**Location**: `frontend/src/components/chat/MentionInput.tsx`
**Purpose**: Replaces the existing `<textarea>` in `ChatInterface`. A `contentEditable` div that supports both plain text and inline @mention token spans.

```typescript
interface MentionInputProps {
  value: string;                            // Plain text content (tokens represented as placeholders)
  mentionTokens: MentionToken[];            // Currently inserted mention tokens
  placeholder?: string;                     // Placeholder text when empty
  disabled?: boolean;                       // Disable input during send
  maxHeight?: number;                       // Max height in px before scrolling (default: 400)
  onTextChange: (text: string) => void;     // Called when plain text content changes
  onMentionTrigger: (query: string, offset: number) => void;  // Called when "@" detected with filter text
  onMentionDismiss: () => void;             // Called when mention autocomplete should close
  onTokenRemove: (pipelineId: string) => void;  // Called when a token is deleted via backspace
  onSubmit: () => void;                     // Called on Enter (without Shift)
  onNavigateHistory: (direction: 'up' | 'down') => void;  // Arrow key history navigation
  onKeyDown?: (e: React.KeyboardEvent) => void;  // Pass-through for autocomplete keyboard handling
  inputRef?: React.RefObject<HTMLDivElement>;     // Ref to the contentEditable div
}
```

**Behavior**:

- Renders a `contentEditable` div with auto-resize behavior (matches current textarea behavior)
- Detects "@" trigger condition: preceded by space, newline, or at position 0 (R2)
- Inserts mention tokens as `<span contentEditable="false" data-pipeline-id="..." data-pipeline-name="...">` elements
- Handles backspace into a token by removing the entire token as a single unit (FR-011)
- Fires `onSubmit` on Enter (without Shift); Shift+Enter inserts newline (matches current textarea)
- Fires `onNavigateHistory` on ArrowUp/ArrowDown when cursor is at start/end (matches current history nav)
- Preserves paste behavior: pasted text with "@name" patterns remains as plain text (no auto-resolve on paste for simplicity; spec says "SHOULD attempt" — deferred to follow-up)
- Exposes `focus()` and `clear()` methods via ref

---

### MentionAutocomplete

**Location**: `frontend/src/components/chat/MentionAutocomplete.tsx`
**Purpose**: Dropdown overlay listing pipelines matching the current @mention filter query. Positioned above the input at the "@" trigger location.

```typescript
interface MentionAutocompleteProps {
  pipelines: MentionFilterResult[];         // Filtered pipeline list with match highlighting
  highlightedIndex: number;                 // Currently highlighted item index
  isLoading: boolean;                       // Pipeline list is being fetched
  isVisible: boolean;                       // Whether the dropdown is shown
  anchorOffset: number;                     // Character offset for positioning
  onSelect: (pipeline: PipelineConfigSummary) => void;  // User selected a pipeline
  onDismiss: () => void;                    // User pressed Escape or clicked outside
  onHighlightChange: (index: number) => void;  // Highlight changed via keyboard/mouse
}
```

**Behavior**:

- Renders a floating panel positioned above/below the "@" trigger position in the input (FR-001)
- Displays up to 10 visible items in a scrollable list (FR-015, Edge Case: 50+ pipelines)
- Each item shows pipeline name (with highlighted match ranges), and optionally description or updated date (FR-014)
- Keyboard navigation: ArrowUp/ArrowDown to highlight, Enter/Tab to select, Escape to dismiss (FR-003, FR-012)
- Mouse hover highlights item, click selects item (FR-003)
- Auto-scrolls highlighted item into view
- Shows empty state "No pipelines found" when filter matches nothing (Edge Case: no saved pipelines)
- Shows loading skeleton while `isLoading` is true
- Shows error state "Unable to load pipelines" on fetch failure (Edge Case: no network)
- ARIA-compliant: `role="listbox"` on container, `role="option"` on items, `aria-activedescendant` for highlighted item
- Follows the structural pattern of `CommandAutocomplete.tsx`

---

### MentionToken

**Location**: `frontend/src/components/chat/MentionToken.tsx`
**Purpose**: Visual chip/tag representing a resolved @mention inline in the input.

```typescript
interface MentionTokenProps {
  pipelineId: string;                       // UUID of the referenced pipeline
  pipelineName: string;                     // Display name
  isValid: boolean;                         // Whether the pipeline exists (controls styling)
}
```

**Behavior**:

- Renders a `<span>` element with `contentEditable="false"` for atomic behavior (FR-011)
- Carries `data-pipeline-id` and `data-pipeline-name` attributes for DOM-based extraction (FR-005)
- Valid state: blue chip styling (`bg-blue-100 text-blue-800` light, `bg-blue-900 text-blue-200` dark) (FR-004)
- Invalid state: amber/red chip styling with warning icon (FR-010)
- Displays "@[pipeline name]" as the visible text
- Not directly clickable or editable — cursor skips over the token
- This component is rendered by `MentionInput` when inserting tokens into the contentEditable div

---

### PipelineIndicator

**Location**: `frontend/src/components/chat/PipelineIndicator.tsx`
**Purpose**: Contextual badge near the submit button showing which pipeline is active via @mention.

```typescript
interface PipelineIndicatorProps {
  activePipelineName: string | null;        // Name of the active (last valid) pipeline
  hasMultipleMentions: boolean;             // Whether multiple valid mentions exist
  hasInvalidMentions: boolean;              // Whether any invalid mentions exist
}
```

**Behavior**:

- Hidden when `activePipelineName` is `null` (no @mention in input) (FR-009)
- Shows "Using pipeline: [name]" badge when a valid pipeline is mentioned (FR-009, User Story 3)
- Shows info tooltip "Multiple pipelines mentioned — using last" when `hasMultipleMentions` is true (FR-007)
- Shows warning badge "Pipeline not found" when `activePipelineName` is null but `hasInvalidMentions` is true (FR-010)
- Uses existing `Badge` or styled `<span>` from the UI components
- Positioned between the input area and the submit button

---

## New Hook

### useMentionAutocomplete

**Location**: `frontend/src/hooks/useMentionAutocomplete.ts`
**Purpose**: Manages the full @mention autocomplete lifecycle: trigger detection, filtering, keyboard navigation, token insertion/removal, and active pipeline tracking.

```typescript
interface UseMentionAutocompleteProps {
  projectId: string;                        // For fetching pipeline list
  inputRef: React.RefObject<HTMLDivElement>; // Ref to the contentEditable input
}

interface UseMentionAutocompleteReturn {
  // Autocomplete state
  isAutocompleteOpen: boolean;
  filteredPipelines: MentionFilterResult[];
  highlightedIndex: number;
  isLoadingPipelines: boolean;

  // Token state
  mentionTokens: MentionToken[];
  activePipelineId: string | null;
  activePipelineName: string | null;
  hasMultipleMentions: boolean;
  hasInvalidMentions: boolean;

  // Event handlers (wire to MentionInput props)
  handleMentionTrigger: (query: string, offset: number) => void;
  handleMentionDismiss: () => void;
  handleSelect: (pipeline: PipelineConfigSummary) => void;
  handleTokenRemove: (pipelineId: string) => void;
  handleHighlightChange: (index: number) => void;
  handleKeyDown: (e: React.KeyboardEvent) => void;

  // Actions
  validateTokens: () => Promise<boolean>;   // Re-validate all tokens before submit
  getSubmissionPipelineId: () => string | null;  // Get the pipeline_id for submission
  reset: () => void;                        // Clear all tokens and state (after submit)
}

function useMentionAutocomplete(props: UseMentionAutocompleteProps): UseMentionAutocompleteReturn;
```

**Implementation Notes**:

- Uses TanStack Query to fetch `pipelinesApi.list(projectId)` on first "@" trigger (lazy fetch)
- Filters pipeline list client-side with case-insensitive substring match on `name`, debounced at 150ms (R3, FR-017)
- Tracks keyboard navigation index; resets to 0 on filter change
- `handleSelect` inserts a token `<span>` into the contentEditable div at the trigger offset and removes the "@query" text
- `activePipelineId` is computed as the last valid token's ID whenever tokens change (FR-007)
- `validateTokens` re-checks all token IDs against the pipeline list; updates `isValid` status on each token
- `reset` clears all tokens and internal state — called after successful submission

---

## Modified Components

### ChatInterface

**Location**: `frontend/src/components/chat/ChatInterface.tsx`
**Purpose**: Existing chat interface — modified to integrate @mention support.

**Changes**:

- Replace `<textarea>` element with `<MentionInput>` component
- Add `<MentionAutocomplete>` as a sibling overlay (same pattern as `CommandAutocomplete`)
- Add `<PipelineIndicator>` between the input area and the submit button row
- Wire `useMentionAutocomplete` hook for state management
- Update `doSubmit` function to include `pipeline_id` from `getSubmissionPipelineId()` in the `onSendMessage` call
- Update `onSendMessage` callback signature to accept optional `pipeline_id` parameter
- Ensure @mention autocomplete and slash-command autocomplete do not conflict:
  - Slash autocomplete activates on `/` at start of input
  - Mention autocomplete activates on `@` preceded by space/newline/start
  - Only one can be open at a time; opening one dismisses the other
- Retain all existing functionality: message history, voice input, file upload, AI enhance toggle

### ChatInterface `onSendMessage` callback

Updated signature:

```typescript
onSendMessage: (
  content: string,
  options?: {
    isCommand?: boolean;
    aiEnhance?: boolean;
    fileUrls?: string[];
    pipelineId?: string;          // NEW: from @mention selection
  }
) => void;
```

---

## Component Composition

```text
ChatInterface
├── MentionInput                    (replaces <textarea>)
│   └── MentionToken (×N)          (inline token spans within contentEditable)
├── MentionAutocomplete             (floating dropdown, shown on "@" trigger)
├── CommandAutocomplete             (existing, shown on "/" trigger)
├── PipelineIndicator               (badge near submit button)
├── [existing file upload UI]
├── [existing voice input button]
├── [existing AI enhance toggle]
└── [existing submit button]
```
