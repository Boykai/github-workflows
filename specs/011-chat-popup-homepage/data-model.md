# Data Model: Move Chat Experience to Project-Board Page as Pop-Up Module & Simplify Homepage

**Feature**: 011-chat-popup-homepage  
**Date**: 2026-02-26  
**Status**: Complete

## Overview

This is a frontend-only layout refactor. No new data entities, database tables, or API endpoints are introduced. The existing chat data model (`ChatMessage`, `AITaskProposal`, `StatusChangeProposal`, `IssueCreateActionData`) remains unchanged. This document captures the UI state model and component interface contracts.

## UI State Entities

### ChatPopupState

Manages the open/closed state of the chat pop-up module on the project-board page.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `isOpen` | `boolean` | `false` | Whether the chat popup panel is currently visible |

**State Transitions**:
- `closed → open`: User clicks toggle button or presses Enter/Space on focused toggle
- `open → closed`: User clicks toggle button, clicks close control, or presses Escape

**Persistence**: React `useState` — persists while component is mounted (project-board view active). Resets to `false` when navigating away and back.

### ActiveView (modified)

Existing `activeView` state in `App.tsx` — modified to replace `'chat'` with `'home'`.

| Value | Before | After |
|-------|--------|-------|
| `'chat'` | Shows sidebar + chat interface | **Removed** |
| `'home'` | N/A | **New**: Shows centered "Create Your App Here" CTA |
| `'board'` | Shows project board | Shows project board + ChatPopup |
| `'settings'` | Shows settings page | No change |

**Note**: The `DefaultViewType` TypeScript type (`'chat' | 'board' | 'settings'`) in `frontend/src/types/index.ts` and the user settings `default_view` field may need updating to replace `'chat'` with `'home'` for consistency. However, since this is a user-settings type, backward compatibility should be maintained — `'chat'` can map to `'home'` in the view logic.

## Component Hierarchy

```
App (AppContent)
├── header (nav: Home | Project Board | Settings)
├── main
│   ├── [activeView === 'home']  → HomepageHero (new inline section)
│   ├── [activeView === 'board'] → ProjectBoardPage
│   │                               └── ChatPopup (NEW)
│   │                                   ├── ToggleButton (fixed position)
│   │                                   └── PopupPanel (conditionally rendered)
│   │                                       └── ChatInterface (existing, unchanged)
│   └── [activeView === 'settings'] → SettingsPage
```

## Existing Entities (unchanged)

The following types from `frontend/src/types/index.ts` are consumed by the chat components and remain unchanged:

- `ChatMessage` — Individual chat message with sender, content, action data
- `AITaskProposal` — Pending task creation proposal from AI
- `StatusChangeProposal` — Pending status change from AI
- `IssueCreateActionData` — Issue recommendation from AI
- `WorkflowResult` — Result of workflow operations

## Validation Rules

- The toggle button must always be visible and interactable when on the project-board page
- The popup panel must not render when `isOpen` is `false` (or render off-screen with `visibility: hidden` for animation purposes)
- Chat API calls (`useChat()` hook) must only be invoked within the `ChatPopup` component, not at the `App.tsx` level
- No chat-related query keys (`['chat', 'messages']`) should appear in the React Query cache when only the homepage has been visited
