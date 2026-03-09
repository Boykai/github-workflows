# Component Contracts: Update User Chat Helper Text for Comprehensive UX Guidance

**Feature**: 031-chat-helper-text | **Date**: 2026-03-08

## New Modules

### chat-placeholders.ts

**Location**: `frontend/src/constants/chat-placeholders.ts`
**Purpose**: Centralized registry of all chat input placeholder copy, providing consistent, auditable, and maintainable text across all chat entry points.

```typescript
export interface ChatPlaceholderConfig {
  /** Full placeholder text for viewports at Tailwind `sm` and above (≥640px) */
  desktop: string;
  /** Shortened placeholder text for mobile viewports below Tailwind `sm` (<640px) */
  mobile: string;
  /** Accessible label for screen readers */
  ariaLabel: string;
}

export const CHAT_PLACEHOLDERS: Record<string, ChatPlaceholderConfig> = {
  main: {
    desktop: "Ask a question, describe a task, use / for commands, or @ to select a pipeline…",
    mobile: "Ask anything or use / and @ for more…",
    ariaLabel: "Chat input — ask questions, describe tasks, use slash commands, or mention pipelines",
  },
  agentFlow: {
    desktop: "Describe what you'd like your agent to do…",
    mobile: "Describe your agent…",
    ariaLabel: "Agent creation chat input",
  },
  choreFlow: {
    desktop: "Add details or refine your request…",
    mobile: "Add details…",
    ariaLabel: "Chore template chat input",
  },
};

/** P3: Example prompts for cycling placeholder animation in main chat */
export const CYCLING_EXAMPLES: string[] = [
  "Try: 'Summarize the open issues for this sprint'",
  "Try: 'Create an issue for updating the login page'",
  "Try: '/ to see available commands'",
  "Try: '@ to select a pipeline and run it'",
  "Try: 'What's the status of my project?'",
];
```

**Traces to**: FR-001, FR-002, FR-003, FR-005, FR-007, FR-008

### useCyclingPlaceholder.ts (P3 — optional)

**Location**: `frontend/src/hooks/useCyclingPlaceholder.ts`
**Purpose**: React hook that cycles through an array of placeholder strings at a configurable interval, respecting `prefers-reduced-motion`.

```typescript
export function useCyclingPlaceholder(
  prompts: string[],
  options?: {
    intervalMs?: number;   // default: 5000
    enabled?: boolean;     // default: true — set false when input is focused or non-empty
  }
): string;
```

**Behavior:**
- Returns `prompts[0]` when `prefers-reduced-motion: reduce` is active or `enabled` is `false`.
- Cycles through `prompts` at `intervalMs` intervals when enabled and motion is allowed.
- Cleans up interval on unmount or when disabled.
- Does NOT trigger any ARIA live announcements.

**Traces to**: FR-009

---

## Modified Components

### MentionInput.tsx

**Location**: `frontend/src/components/chat/MentionInput.tsx`
**Change summary**: Accept responsive placeholder props; render dual-span with Tailwind responsive visibility; update `aria-label`.

**Interface change:**

```typescript
// BEFORE
interface MentionInputProps {
  placeholder?: string;
  // ... other props unchanged
}

// AFTER
interface MentionInputProps {
  placeholder?: string;          // Desktop placeholder (kept for backward compatibility)
  placeholderMobile?: string;    // Mobile placeholder variant (new, optional)
  ariaLabel?: string;            // Override for aria-label attribute (new, optional — defaults to "Chat input")
  // ... other props unchanged
}
```

**Rendering change (placeholder overlay):**

```tsx
// BEFORE (lines 247-250)
{isEmpty && !disabled && placeholder && (
  <div className="absolute top-0 left-0 p-3 text-sm text-muted-foreground pointer-events-none select-none">
    {placeholder}
  </div>
)}

// AFTER
{isEmpty && !disabled && placeholder && (
  <div className="absolute top-0 left-0 p-3 text-sm text-muted-foreground pointer-events-none select-none">
    {placeholderMobile ? (
      <>
        <span className="max-sm:hidden">{placeholder}</span>
        <span className="hidden max-sm:inline">{placeholderMobile}</span>
      </>
    ) : (
      placeholder
    )}
  </div>
)}
```

**Aria-label change:**

```tsx
// BEFORE
aria-label="Chat input"

// AFTER
aria-label={ariaLabel || "Chat input"}
```

**Traces to**: FR-001, FR-002, FR-003, FR-005, FR-010

### ChatInterface.tsx

**Location**: `frontend/src/components/chat/ChatInterface.tsx`
**Change summary**: Import placeholder config from centralized constants; pass desktop, mobile, and aria-label props to MentionInput.

```tsx
// BEFORE (line ~489)
<MentionInput
  placeholder="Describe a task, type / for commands, or @ for pipelines..."
  // ...
/>

// AFTER
import { CHAT_PLACEHOLDERS } from '@/constants/chat-placeholders';
// ...
<MentionInput
  placeholder={CHAT_PLACEHOLDERS.main.desktop}
  placeholderMobile={CHAT_PLACEHOLDERS.main.mobile}
  ariaLabel={CHAT_PLACEHOLDERS.main.ariaLabel}
  // ...
/>
```

**Traces to**: FR-001, FR-002, FR-003, FR-005, FR-007

### AgentChatFlow.tsx

**Location**: `frontend/src/components/agents/AgentChatFlow.tsx`
**Change summary**: Import placeholder config; update `<input placeholder>` and add `aria-label`.

```tsx
// BEFORE (line ~176)
<input placeholder="Type your response…" ... />

// AFTER
import { CHAT_PLACEHOLDERS } from '@/constants/chat-placeholders';
// ...
<input
  placeholder={CHAT_PLACEHOLDERS.agentFlow.desktop}
  aria-label={CHAT_PLACEHOLDERS.agentFlow.ariaLabel}
  ...
/>
```

**Note**: AgentChatFlow uses a standard `<input>` element inside a small modal. The mobile variant is not needed here because the modal has its own responsive layout and the agent flow placeholder is already short enough for mobile viewports.

**Traces to**: FR-005, FR-007, FR-008

### ChoreChatFlow.tsx

**Location**: `frontend/src/components/chores/ChoreChatFlow.tsx`
**Change summary**: Import placeholder config; update `<input placeholder>` and add `aria-label`.

```tsx
// BEFORE (line ~172)
<input placeholder="Type your response…" ... />

// AFTER
import { CHAT_PLACEHOLDERS } from '@/constants/chat-placeholders';
// ...
<input
  placeholder={CHAT_PLACEHOLDERS.choreFlow.desktop}
  aria-label={CHAT_PLACEHOLDERS.choreFlow.ariaLabel}
  ...
/>
```

**Note**: Same rationale as AgentChatFlow — small modal input with short enough copy for all viewports.

**Traces to**: FR-005, FR-007, FR-008

---

## Unchanged Components

| Component | Reason |
|-----------|--------|
| ChatPopup.tsx | Wraps ChatInterface; does not own the input — no placeholder changes needed |
| ChatToolbar.tsx | Toolbar controls only — no text input |
| MessageBubble.tsx | Message display only — no text input |
| CommandAutocomplete.tsx | Command suggestion dropdown — no placeholder text |
| MentionAutocomplete.tsx | Pipeline mention dropdown — no placeholder text |
| VoiceInputButton.tsx | Voice input toggle — no text input |
| FilePreviewChips.tsx | File display — no text input |

---

## Dependency Impact

| Dependency | Change | Version Impact |
|-----------|--------|----------------|
| None | No new dependencies for P1/P2 | N/A |

**P3 note**: The cycling placeholder hook (P3) requires no new npm dependencies. It uses `window.matchMedia`, `setInterval`, and `useState`/`useEffect` — all built-in browser and React APIs.
