# Quickstart: Update User Chat Helper Text for Comprehensive UX Guidance

**Feature**: 031-chat-helper-text | **Date**: 2026-03-08

## What This Feature Does

Updates the chat input placeholder/helper text across all chat entry points in the Solune UI. The generic "Type your response…" and the existing main chat placeholder are replaced with descriptive, responsive copy that guides users on what they can do in each chat context. The text adapts between desktop and mobile viewports, and all accessibility attributes are kept in sync.

## Quick Setup (for implementer)

### Prerequisites

- Node.js and npm (already configured in the frontend workspace)
- No new dependencies required for P1/P2 stories
- No backend changes

### Implementation Steps

#### Step 1: Create centralized constants file

```bash
# Create the constants file for chat placeholder copy
touch frontend/src/constants/chat-placeholders.ts
```

Populate with the `ChatPlaceholderConfig` interface and `CHAT_PLACEHOLDERS` registry as defined in [data-model.md](data-model.md) and [contracts/components.md](contracts/components.md).

#### Step 2: Update MentionInput.tsx

1. Add `placeholderMobile?: string` and `ariaLabel?: string` props to the `MentionInputProps` interface.
2. Update the placeholder overlay to render dual `<span>` elements with Tailwind responsive classes when `placeholderMobile` is provided.
3. Update the `aria-label` attribute on the contentEditable div to use the new `ariaLabel` prop with a fallback to `"Chat input"`.

#### Step 3: Update ChatInterface.tsx

1. Import `CHAT_PLACEHOLDERS` from `@/constants/chat-placeholders`.
2. Replace the hardcoded `placeholder` prop on `<MentionInput>` with `CHAT_PLACEHOLDERS.main.desktop`.
3. Add `placeholderMobile={CHAT_PLACEHOLDERS.main.mobile}` and `ariaLabel={CHAT_PLACEHOLDERS.main.ariaLabel}`.

#### Step 4: Update AgentChatFlow.tsx

1. Import `CHAT_PLACEHOLDERS` from `@/constants/chat-placeholders`.
2. Replace `placeholder="Type your response…"` with `placeholder={CHAT_PLACEHOLDERS.agentFlow.desktop}`.
3. Add `aria-label={CHAT_PLACEHOLDERS.agentFlow.ariaLabel}`.

#### Step 5: Update ChoreChatFlow.tsx

1. Import `CHAT_PLACEHOLDERS` from `@/constants/chat-placeholders`.
2. Replace `placeholder="Type your response…"` with `placeholder={CHAT_PLACEHOLDERS.choreFlow.desktop}`.
3. Add `aria-label={CHAT_PLACEHOLDERS.choreFlow.ariaLabel}`.

#### Step 6 (P3 — optional): Create useCyclingPlaceholder hook

Only if P3 is in scope:
1. Create `frontend/src/hooks/useCyclingPlaceholder.ts` with the hook implementation.
2. Integrate with MentionInput's placeholder overlay for the main chat context.

### Verification

```bash
# Build frontend to verify no TypeScript errors
cd frontend && npm run build

# Run existing tests to verify no regressions
cd frontend && npx vitest run

# Manual checks:
# 1. Open the chat popup on desktop — verify new descriptive placeholder text
# 2. Resize browser to <640px — verify shortened mobile placeholder
# 3. Open Agent creation modal — verify "Describe what you'd like your agent to do…"
# 4. Open Chore creation modal — verify "Add details or refine your request…"
# 5. Use a screen reader to navigate to chat input — verify announced label matches visible text
# 6. Type text, clear it — verify placeholder reappears
# 7. Submit a message — verify chat functionality unchanged
```

## Key Files

| File | Status | Purpose |
|------|--------|---------|
| `frontend/src/constants/chat-placeholders.ts` | NEW | Centralized placeholder copy registry |
| `frontend/src/components/chat/MentionInput.tsx` | MODIFIED | Responsive placeholder rendering + aria-label |
| `frontend/src/components/chat/ChatInterface.tsx` | MODIFIED | Import from constants, pass new props |
| `frontend/src/components/agents/AgentChatFlow.tsx` | MODIFIED | Update placeholder from constants |
| `frontend/src/components/chores/ChoreChatFlow.tsx` | MODIFIED | Update placeholder from constants |
| `frontend/src/hooks/useCyclingPlaceholder.ts` | NEW (P3) | Cycling animation hook (optional) |

## Spec Traceability

| Requirement | Implementation |
|------------|---------------|
| FR-001: Comprehensive placeholder | `CHAT_PLACEHOLDERS.main.desktop` copy communicates 4 interaction types |
| FR-002: Desktop fit | Copy ≤80 chars; fits within standard chat input width |
| FR-003: Mobile variant | `CHAT_PLACEHOLDERS.main.mobile` displayed via Tailwind `max-sm:` classes |
| FR-004: WCAG contrast | Existing `text-muted-foreground` meets 4.5:1 (verified in research.md R3) |
| FR-005: Aria attributes | `ariaLabel` prop on MentionInput; `aria-label` on AgentChatFlow/ChoreChatFlow inputs |
| FR-006: No functionality change | Copy-only changes; no input behavior modifications |
| FR-007: Consistent across app | All 3 chat inputs use `CHAT_PLACEHOLDERS` constants |
| FR-008: Solune tone | Approachable, action-oriented copy |
| FR-009: Cycling placeholder | P3 `useCyclingPlaceholder` hook with `prefers-reduced-motion` fallback |
| FR-010: Zoom/scaling tolerance | Tailwind responsive classes + text-sm font-size handles browser zoom |
