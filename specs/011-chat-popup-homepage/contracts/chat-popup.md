# Component Contracts: ChatPopup

**Feature**: 011-chat-popup-homepage  
**Date**: 2026-02-26

## ChatPopup Component

### Location
`frontend/src/components/chat/ChatPopup.tsx`

### Purpose
Self-contained chat pop-up module that wraps the existing `ChatInterface` component with toggle button, floating panel, open/close animation, and local state management.

### Props Interface

```typescript
interface ChatPopupProps {
  /** Currently selected project ID — controls whether chat is active */
  selectedProjectId?: string | null;
  /** Callback to refresh tasks after chat actions (proposal confirmations) */
  onTasksRefresh?: () => void;
}
```

### Internal State

```typescript
// Open/closed toggle (persists while component is mounted)
const [isOpen, setIsOpen] = useState(false);
```

### Internal Hook Usage

```typescript
// Chat hook — called inside ChatPopup, NOT in App.tsx
const {
  messages, pendingProposals, pendingStatusChanges,
  pendingRecommendations, isSending, sendMessage,
  confirmProposal, confirmStatusChange, rejectProposal,
  removePendingRecommendation, clearChat,
} = useChat();

// Workflow hook — for recommendation confirm/reject
const { confirmRecommendation, rejectRecommendation } = useWorkflow();
```

### Render Contract

```
When isOpen === false:
  - Render ONLY the toggle button (fixed position, bottom-right)
  - No ChatInterface rendered
  - No chat API calls beyond initial useChat() hook setup

When isOpen === true:
  - Render toggle button (changes to "close" appearance)
  - Render popup panel with ChatInterface inside
  - Panel animated in via CSS transition (transform + opacity)

When selectedProjectId is null/undefined:
  - Render toggle button (disabled or shows "Select a project" tooltip)
  - ChatInterface shows placeholder message if opened
```

### Accessibility

- Toggle button: `aria-label="Open chat"` / `"Close chat"` based on state
- Toggle button: `aria-expanded={isOpen}`
- Popup panel: `role="dialog"`, `aria-label="Chat"`
- Close on Escape key when popup is open
- Focus trap within popup panel when open (optional enhancement)

### CSS Contract (ChatPopup.css)

```css
/* Toggle button */
.chat-popup-toggle {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 1000;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  /* ... */
}

/* Popup panel */
.chat-popup-panel {
  position: fixed;
  bottom: 88px;  /* above toggle button */
  right: 24px;
  width: 400px;
  height: 600px;
  max-height: calc(100vh - 120px);
  z-index: 999;
  border-radius: 12px;
  overflow: hidden;
  /* Animation */
  transform: translateY(20px);
  opacity: 0;
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.chat-popup-panel.open {
  transform: translateY(0);
  opacity: 1;
}

/* Mobile (< 768px) */
@media (max-width: 767px) {
  .chat-popup-panel {
    width: calc(100vw - 16px);
    height: calc(100vh - 100px);
    bottom: 88px;
    right: 8px;
  }
}
```
