# Quickstart: Move Chat Experience to Project-Board Page as Pop-Up Module & Simplify Homepage

**Feature**: 011-chat-popup-homepage  
**Date**: 2026-02-26

## Prerequisites

- Node.js (for frontend development)
- Repository cloned and on branch `011-chat-popup-homepage`

## Setup

```bash
cd frontend
npm install    # No new dependencies to install
```

## Development

```bash
cd frontend
npm run dev    # Start Vite dev server
```

## What Changed (Summary)

### Files Modified
1. **`frontend/src/App.tsx`** — Replaced "chat" view with "home" hero CTA; removed chat imports and hook usage; updated navigation
2. **`frontend/src/App.css`** — Added `.homepage-hero` styles; cleanup of unused chat-section styles
3. **`frontend/src/pages/ProjectBoardPage.tsx`** — Added `ChatPopup` component import and render

### Files Created
4. **`frontend/src/components/chat/ChatPopup.tsx`** — New self-contained chat pop-up component with toggle, animation, and local state
5. **`frontend/src/components/chat/ChatPopup.css`** — Popup positioning, animation transitions, responsive styles

### Files Unchanged
- `frontend/src/components/chat/ChatInterface.tsx` — Existing chat UI, no modifications
- `frontend/src/components/chat/ChatInterface.css` — Existing chat styles, no modifications
- `frontend/src/hooks/useChat.ts` — Existing chat hook, no modifications
- `frontend/src/hooks/useWorkflow.ts` — Existing workflow hook, no modifications
- All backend files — Zero backend changes

## Verification Steps

### 1. Homepage is minimal
```
Navigate to the app → default view should be "Home"
Only navigation bar and "Create Your App Here" centered heading visible
No chat input, message history, or chat-related elements
```

### 2. Chat pop-up on project board
```
Click "Project Board" in navigation
Look for floating chat bubble icon at bottom-right
Click it → chat panel should animate open
Full chat interface (messages, input, send) visible in panel
Click toggle again → panel animates closed
```

### 3. No chat network requests on homepage
```
Open browser DevTools → Network tab
Load the homepage
Filter for API requests → no /chat/ requests should appear
Navigate to project board → chat requests appear only when popup is opened
```

### 4. Responsive check
```
Resize browser to mobile width (< 768px)
Homepage: CTA title adjusts to smaller font
Project board: Chat popup expands to near-full-width on mobile
Toggle button remains accessible for touch
```

## Build & Test

```bash
cd frontend
npm run build         # TypeScript compilation + Vite build
npm run type-check    # TypeScript type checking only
npm run lint          # ESLint
npm run test          # Vitest unit tests
```
