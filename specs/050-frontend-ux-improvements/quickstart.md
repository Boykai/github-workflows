# Quickstart: Solune Frontend UX Improvements

**Feature**: 050-frontend-ux-improvements  
**Date**: 2026-03-19

## Prerequisites

- Node.js (version compatible with `package.json` engines)
- Git
- The Solune repository cloned locally

## Setup

```bash
# Navigate to the frontend directory
cd solune/frontend

# Install dependencies (includes existing react-markdown, dnd-kit, etc.)
npm install

# Install the one new dependency
npm install sonner

# Start the development server
npm run dev
# Frontend runs on http://localhost:5173
# Proxies /api to http://localhost:8000 (backend)
```

## Development Workflow

### Running Tests

```bash
# Run all unit/component tests
npm run test

# Run tests in watch mode (recommended during development)
npm run test:watch

# Run with coverage
npm run test:coverage

# Run accessibility-focused tests
npm run test:a11y

# Run E2E tests (requires backend running)
npm run test:e2e
```

### Linting

```bash
# Run ESLint
npm run lint

# Type checking
npx tsc -b --noEmit
```

### Theme Auditing

```bash
# Verify theme color usage
npm run audit:theme-colors

# Check contrast ratios
npm run audit:theme-contrast
```

## Implementation Order

Follow the phase order below. Each phase is independently deployable.

### Phase 1: Toast System (Critical)

1. `npm install sonner` — add toast dependency
2. Edit `src/layout/AppLayout.tsx` — add `<Toaster />` provider
3. Edit mutation hooks — add `toast.success()` / `toast.error()` calls
4. Verify: Trigger any mutation → themed toast appears

**Key files**: `AppLayout.tsx`, `usePipelineConfig.ts`, `useAgentConfig.ts`, `useChores.ts`, `useSettings.ts`, `useWorkflow.ts`, `useApps.ts`, `useChat.ts`

### Phase 2: Chat Markdown (High)

1. Edit `src/components/chat/MessageBubble.tsx` — wrap AI messages in `<ReactMarkdown>`
2. Create `src/components/chat/CodeBlock.tsx` — code block with copy button
3. Create `src/components/chat/CopyMessageAction.tsx` — hover copy action
4. Verify: Send markdown in chat → formatted rendering + copy works

**Key files**: `MessageBubble.tsx`, `CodeBlock.tsx` (new), `CopyMessageAction.tsx` (new)

### Phase 3: Kanban Drag-and-Drop (High)

1. Create `src/hooks/useBoardDnd.ts` — DnD state management hook
2. Edit `src/components/board/ProjectBoard.tsx` — wrap with `<DndContext>`
3. Edit `src/components/board/BoardColumn.tsx` — make droppable
4. Edit `src/components/board/IssueCard.tsx` — make draggable
5. Create `src/components/board/IssueDragOverlay.tsx` — drag preview
6. Add API function in `src/services/api.ts` — status update endpoint
7. Verify: Drag card between columns → status updates, rollback on error

**Key files**: `useBoardDnd.ts` (new), `ProjectBoard.tsx`, `BoardColumn.tsx`, `IssueCard.tsx`, `IssueDragOverlay.tsx` (new), `api.ts`  
**Reference**: `AgentDragOverlay.tsx` for existing dnd-kit pattern

### Phase 4: Skeleton Loading (Medium)

1. Create `src/components/ui/skeleton.tsx` — Skeleton primitive
2. Create composite skeletons: `BoardColumnSkeleton.tsx`, `IssueCardSkeleton.tsx`, `ChatMessageSkeleton.tsx`, `AgentCardSkeleton.tsx`
3. Replace `<CelestialLoader />` with skeletons in data-loading states
4. Verify: Throttle network → skeletons appear, no layout shift on load

**Key files**: `skeleton.tsx` (new), `*Skeleton.tsx` (new), pages/components that use CelestialLoader

### Phase 5: Keyboard Shortcuts (Medium)

1. Create `src/hooks/useGlobalShortcuts.ts` — global keydown listener
2. Create `src/components/ui/shortcut-modal.tsx` — shortcut help modal
3. Edit `src/layout/AppLayout.tsx` — wire hook and modal
4. Edit sidebar nav tooltips — add shortcut hints
5. Verify: Press `?` → modal opens; `Ctrl+K` → chat input focused

**Key files**: `useGlobalShortcuts.ts` (new), `shortcut-modal.tsx` (new), `AppLayout.tsx`

### Phase 6: Quick Wins (pick any order)

- **Board priority filter**: `BoardToolbar.tsx` + `useBoardControls.ts`
- **Tour progress**: `SpotlightTooltip.tsx`
- **Chat date separators**: `ChatInterface.tsx`
- **Notification pulse**: `NotificationBell.tsx` (may already work)
- **Empty states**: `BoardColumn.tsx` + `ProjectBoardContent.tsx`
- **Ctrl+Enter send**: `ChatInterface.tsx`

## Architecture Notes

- **State management**: TanStack Query for server state, local state via hooks
- **Styling**: Tailwind v4 with `@theme` block in `index.css` (no `tailwind.config.ts`)
- **Code splitting**: `@dnd-kit`, `react-markdown`, icons already in separate chunks
- **Accessibility**: jest-axe for unit a11y testing, @axe-core/playwright for E2E, `celestial-focus` class for focus rings
- **Animations**: All animations respect `prefers-reduced-motion` via existing `@media` block in `index.css`
- **Path alias**: `@/*` maps to `./src/*` (use in imports)

## Verification Checklist

| Phase | Test |
|-------|------|
| 1 | Trigger save/delete/error → toasts appear with correct severity and auto-dismiss |
| 2 | Send chat with markdown + code blocks → formatted rendering + copy button works |
| 3 | Drag issue card between columns → status updates in backend; rollback on API error |
| 4 | Throttle network → skeletons appear instead of spinners; no layout shift on load |
| 5 | Press `?` → shortcut modal opens; `Ctrl+K` → chat input receives focus |
| 6 | Each sub-item tested independently per FR-028 through FR-033 |
