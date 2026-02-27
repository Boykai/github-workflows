# Data Model: Move Chat Experience to Project-Board Page as Pop-Up Module & Simplify Homepage

**Date**: 2026-02-26 | **Branch**: `011-chat-popup-homepage` | **Plan**: [plan.md](plan.md)

## Overview

This feature is a frontend-only UI refactor. No backend schema, API, or data model changes are required. The existing chat data model (messages, proposals, status changes, recommendations) is unchanged. The only new "model" is the UI state for the chat pop-up toggle.

## UI State Model

### ChatPopup Component State

| Field | Type | Default | Scope | Description |
|-------|------|---------|-------|-------------|
| `isOpen` | `boolean` | `false` | Local (`useState`) | Whether the chat pop-up panel is visible |

**Lifecycle**:
- Initialized to `false` when `ProjectBoardPage` mounts (pop-up starts closed).
- Toggled by user clicking the chat toggle button.
- Persists across re-renders while `ProjectBoardPage` remains mounted.
- Resets to `false` when user navigates away from the board view (component unmounts) and returns.

### Existing Entities (Unchanged)

The following existing data entities are consumed by the chat pop-up but are not modified:

| Entity | Source | Used By |
|--------|--------|---------|
| `ChatMessage[]` | `useChat()` hook → `GET /api/v1/chat/messages` | `ChatInterface` (inside `ChatPopup`) |
| `Map<string, AITaskProposal>` | `useChat()` hook (local state) | `ChatInterface` → `TaskPreview` |
| `Map<string, StatusChangeProposal>` | `useChat()` hook (local state) | `ChatInterface` → `StatusChangePreview` |
| `Map<string, IssueCreateActionData>` | `useChat()` hook (local state) | `ChatInterface` → `IssueRecommendationPreview` |

### View State Model (App.tsx)

The existing `activeView` state in `App.tsx` gains a semantic change but no type change:

| Field | Type | Values | Change |
|-------|------|--------|--------|
| `activeView` | `'chat' \| 'board' \| 'settings'` | `'chat'`, `'board'`, `'settings'` | The `'chat'` view now renders the simplified homepage instead of the chat interface. The nav button label changes from "Chat" to "Home". |

**Note**: The `activeView` type union may be updated to `'home' | 'board' | 'settings'` for clarity, but this is optional and does not affect functionality.

## Relationships

```
App.tsx (activeView state)
├── 'home'/'chat' → Homepage (static: nav + CTA only, no data fetching)
├── 'board' → ProjectBoardPage
│   ├── useChat() → ChatMessage[], proposals, etc.
│   ├── useWorkflow() → confirmRecommendation, rejectRecommendation
│   ├── useProjects() → project selection (already present)
│   └── ChatPopup (isOpen state)
│       └── ChatInterface (receives all chat props)
└── 'settings' → SettingsPage (unchanged)
```

## Validation Rules

- `isOpen` is always a boolean — no validation needed beyond TypeScript type safety.
- All existing chat data validation (message content, proposal IDs, etc.) is unchanged and handled by the existing `useChat` hook and backend API.

## Schema Changes

**None.** No database migrations, no API contract changes, no new backend endpoints.
