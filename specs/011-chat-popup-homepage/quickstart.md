# Quickstart: Chat Pop-Up & Homepage Simplification Implementation Guide

**Date**: 2026-02-26 | **Branch**: `011-chat-popup-homepage`

## Prerequisites

- Node.js 18+
- Clone and checkout: `git checkout 011-chat-popup-homepage`
- Install frontend dependencies: `cd frontend && npm install`

## Environment Variables

No new environment variables required. This is a frontend-only change.

## Running Locally

```bash
cd frontend && npm run dev
# Frontend: http://localhost:5173
```

For full-stack (chat functionality requires backend):
```bash
docker compose up --build
# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

## Implementation Order

Work through these phases sequentially. Each phase is independently verifiable.

### Phase A — New ChatPopup Component (Foundation)

1. **`frontend/src/components/chat/ChatPopup.css`** — Create pop-up styles: fixed positioning, toggle button, panel layout, open/close animation, responsive breakpoints.
2. **`frontend/src/components/chat/ChatPopup.tsx`** — Create `ChatPopup` component that wraps `ChatInterface` with toggle state and floating panel UI.

**Verify**: Import `ChatPopup` in a test harness or Storybook (if available). Confirm toggle button renders, panel opens/closes with animation, and `ChatInterface` displays correctly inside the panel.

### Phase B — Integrate ChatPopup into ProjectBoardPage

3. **`frontend/src/pages/ProjectBoardPage.tsx`** — Add `useChat()` and `useWorkflow()` hooks. Wire up all chat callbacks. Render `<ChatPopup />` at the end of the component JSX.

**Verify**: Navigate to the project-board page. Confirm the chat toggle button appears in the bottom-right corner. Open the pop-up, send a message (requires backend running), close the pop-up. Confirm the pop-up does not obstruct board columns.

### Phase C — Simplify Homepage

4. **`frontend/src/App.tsx`** — Remove `useChat()`, `useWorkflow()`, and all chat-related state/callbacks from `AppContent`. Remove `ProjectSidebar` and `ChatInterface` from the chat view. Replace with a centered "Create Your App Here" hero section. Update the "Chat" nav button label to "Home".
5. **`frontend/src/App.css`** — Add homepage hero styles (centered layout, prominent heading, CTA button).

**Verify**: Navigate to the homepage. Confirm only the nav bar and "Create Your App Here" heading are visible. Confirm no chat-related network requests fire on the homepage (check browser DevTools Network tab). Click the CTA — confirm navigation to the project-board page.

### Phase D — Cleanup & Polish

6. Remove any unused imports from `App.tsx` (chat-related imports that are no longer needed).
7. Verify responsive layout on mobile viewports (320px, 375px, 768px).
8. Verify keyboard accessibility: Tab to toggle button, Enter to open, Tab through chat input, Escape to close (optional).

**Verify**: Run `npm run type-check` — no TypeScript errors. Run `npm run lint` — no linting errors.

### Phase E — Testing & Confirmation

9. Run `npm run test` — all existing unit tests pass.
10. Run `npm run build` — production build succeeds.
11. (Optional) Run `npm run test:e2e` — Playwright E2E tests pass.

## Key Testing Commands

```bash
# Type checking
cd frontend && npm run type-check

# Linting
cd frontend && npm run lint

# Unit tests
cd frontend && npm run test

# Build
cd frontend && npm run build

# E2E tests (requires backend)
cd frontend && npm run test:e2e
```

## Verification Checklist

- [ ] Homepage shows only navigation bar and "Create Your App Here" CTA
- [ ] No chat input, message history, or chat UI visible on homepage
- [ ] No chat-related API calls on homepage (check Network tab)
- [ ] Project-board page has floating chat toggle button (bottom-right)
- [ ] Clicking toggle opens chat pop-up with smooth animation
- [ ] Chat pop-up contains full chat interface (messages, input, send button)
- [ ] Sending a message works correctly in the pop-up
- [ ] Closing the pop-up animates smoothly
- [ ] Pop-up open/closed state persists during project-board session
- [ ] Pop-up does not obstruct board columns/headers when open
- [ ] "Create Your App Here" CTA navigates to project-board page
- [ ] Layout is responsive on mobile (320px–768px)
- [ ] Toggle button is keyboard-accessible (focusable, activatable with Enter/Space)
- [ ] Toggle button has appropriate aria-label
- [ ] `npm run type-check` passes
- [ ] `npm run lint` passes
- [ ] `npm run test` passes
- [ ] `npm run build` succeeds
