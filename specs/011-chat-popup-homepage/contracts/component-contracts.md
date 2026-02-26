# Component Contracts: Move Chat to Project-Board Pop-Up

**Date**: 2026-02-26 | **Branch**: `011-chat-popup-homepage` | **Plan**: [plan.md](plan.md)

## Overview

This feature involves no backend API changes. All contracts are frontend component interfaces (React props). The existing REST API contract for chat (`GET /api/v1/chat/messages`, `POST /api/v1/chat/messages`, etc.) is unchanged.

## Component Contracts

### ChatPopup

**File**: `frontend/src/components/chat/ChatPopup.tsx`

```typescript
interface ChatPopupProps {
  /** Chat messages from useChat() */
  messages: ChatMessage[];
  /** Pending task creation proposals */
  pendingProposals: Map<string, AITaskProposal>;
  /** Pending status change proposals */
  pendingStatusChanges: Map<string, StatusChangeProposal>;
  /** Pending issue creation recommendations */
  pendingRecommendations: Map<string, IssueCreateActionData>;
  /** Whether a message is currently being sent */
  isSending: boolean;
  /** Callback to send a chat message */
  onSendMessage: (content: string) => void;
  /** Callback to confirm a task creation proposal */
  onConfirmProposal: (proposalId: string) => void;
  /** Callback to confirm a status change proposal */
  onConfirmStatusChange: (proposalId: string) => void;
  /** Callback to confirm an issue recommendation */
  onConfirmRecommendation: (recommendationId: string) => Promise<WorkflowResult>;
  /** Callback to reject a task creation proposal */
  onRejectProposal: (proposalId: string) => void;
  /** Callback to reject an issue recommendation */
  onRejectRecommendation: (recommendationId: string) => Promise<void>;
  /** Callback to start a new chat session */
  onNewChat: () => void;
}
```

**Behavior**:
- Renders a fixed-position toggle button (bottom-right corner).
- On toggle click: opens/closes the chat panel with CSS transition animation.
- Panel contains `<ChatInterface />` with all props forwarded.
- Manages `isOpen: boolean` state internally.
- Toggle button has `aria-label="Open chat"` / `"Close chat"` for accessibility.
- Panel uses `z-index: 1000` to float above board content.
- Responsive: full-width on mobile viewports.

### ProjectBoardPage (Modified)

**File**: `frontend/src/pages/ProjectBoardPage.tsx`

```typescript
interface ProjectBoardPageProps {
  /** Currently selected project ID (shared with chat page) */
  selectedProjectId?: string | null;
  /** Callback when user selects a project (persists to session) */
  onProjectSelect?: (projectId: string) => void;
}
```

**Changes**:
- Now internally calls `useChat()` and `useWorkflow()` hooks.
- Renders `<ChatPopup />` with chat props at the end of its JSX tree.
- No prop interface changes — chat is fully self-contained within the page.

### AppContent (Modified)

**File**: `frontend/src/App.tsx`

**Changes**:
- `activeView` default value changes from `'chat'` to `'chat'` (remains same type, but the `'chat'` view now renders the simplified homepage).
- Removes `useChat()` and `useWorkflow()` hook calls.
- Removes `ChatInterface`, `ProjectSidebar` imports for chat view.
- Homepage view (`activeView === 'chat'`) renders only:
  ```tsx
  <div className="homepage-hero">
    <h2>Create Your App Here</h2>
    <button onClick={() => setActiveView('board')}>Get Started</button>
  </div>
  ```

## API Contracts (Unchanged)

No backend API changes. The following existing endpoints continue to be consumed, now from within `ProjectBoardPage` instead of `App.tsx`:

| Method | Endpoint | Consumer |
|--------|----------|----------|
| `GET` | `/api/v1/chat/messages` | `useChat()` in `ProjectBoardPage` |
| `POST` | `/api/v1/chat/messages` | `useChat()` in `ProjectBoardPage` |
| `POST` | `/api/v1/chat/proposals/{id}/confirm` | `useChat()` in `ProjectBoardPage` |
| `POST` | `/api/v1/chat/proposals/{id}/cancel` | `useChat()` in `ProjectBoardPage` |
| `DELETE` | `/api/v1/chat/messages` | `useChat()` in `ProjectBoardPage` |
