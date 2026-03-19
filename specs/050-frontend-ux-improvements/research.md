# Research: Solune Frontend UX Improvements

**Feature**: 050-frontend-ux-improvements  
**Date**: 2026-03-19  
**Status**: Complete — all NEEDS CLARIFICATION resolved

## R1: Toast Notification Library Selection

**Decision**: Use `sonner` for toast notifications.

**Rationale**: Sonner is the lightest accessible toast library at ~4KB gzipped. It provides built-in stacking, auto-dismiss, keyboard dismissal, and screen reader announcements out of the box. It works with React 19 and requires minimal setup — a single `<Toaster />` provider component in the layout. It supports custom styling via CSS classes, making it straightforward to match the celestial theme with existing design tokens (`--glow`, `--gold`, `--panel`).

**Alternatives Considered**:
- `react-hot-toast` (~5KB): Similar API but less accessible by default. No built-in ARIA live regions. Requires manual screen reader support.
- `react-toastify` (~8KB): Feature-rich but heavier. Includes its own CSS bundle that would conflict with the Tailwind-first approach.
- Custom implementation: Would require building stacking logic, auto-dismiss timers, ARIA announcements, and animation management from scratch. Higher effort, higher bug surface.

## R2: Markdown Rendering for Chat Messages

**Decision**: Use the already-installed `react-markdown` (^10.1.0) with `remark-gfm` (^4.0.1) for AI message rendering.

**Rationale**: Both packages are already in `package.json` and code-split into the `markdown-vendor` chunk (see `vite.config.ts`). They are simply not wired into `MessageBubble.tsx`. The implementation requires wrapping AI message content in `<ReactMarkdown remarkPlugins={[remarkGfm]}>` and providing custom component renderers for code blocks (with a copy button) and links (with `target="_blank"`).

**Alternatives Considered**:
- `marked` + `DOMPurify`: Would require a raw HTML approach with `dangerouslySetInnerHTML`, losing React component composition for code blocks and copy buttons.
- `mdx-js/react`: Overkill for rendering static markdown content. Designed for MDX (markdown with JSX) authoring, not display.
- Custom parser: Unnecessary complexity when a battle-tested solution is already installed.

**Security Note**: `react-markdown` does NOT render raw HTML by default — it strips HTML tags. This satisfies FR-010 (HTML sanitization) without additional configuration. The `rehype-raw` plugin (which would enable HTML) should NOT be added.

## R3: Drag-and-Drop for Kanban Board

**Decision**: Use the already-installed `@dnd-kit/core` (^6.3.1) and `@dnd-kit/sortable` (^10.0.0) for board card drag-and-drop.

**Rationale**: `@dnd-kit` is already installed and actively used in the pipeline builder. `AgentDragOverlay.tsx` provides an existing pattern for rendering drag overlays. The library supports keyboard accessibility (Enter/Space to activate, arrow keys to move, Enter to drop) which satisfies FR-017. The code-split chunk `dnd-vendor` already bundles all `@dnd-kit` packages, so there is zero bundle impact.

**Key Implementation Pattern (from AgentDragOverlay.tsx)**:
1. Wrap container with `<DndContext>` and provide `onDragStart`, `onDragOver`, `onDragEnd` handlers
2. Make cards draggable with `useDraggable` hook from `@dnd-kit/core`
3. Make columns droppable with `useDroppable` hook from `@dnd-kit/core`
4. Render ghost card in `<DragOverlay>` portal during drag
5. Use `@dnd-kit/modifiers` (already installed at ^9.0.0) for movement constraints

**Alternatives Considered**:
- `react-beautiful-dnd`: Deprecated, no React 19 support.
- `react-dnd`: Heavier, requires separate backend packages. Would add a second DnD library.
- Custom Pointer Events: Would require building the full drag lifecycle, keyboard support, and overlay rendering. Existing library already handles edge cases.

**Backend Integration**: The backend already exposes `update_project_item_field` and `update_item_status_by_name` methods in `solune/backend/src/services/github_projects/projects.py`. A frontend API function will call the existing endpoint to update the Status field when a card is dropped on a new column. No new backend endpoints needed.

## R4: Skeleton Loading Component Pattern

**Decision**: Create a `Skeleton` primitive in `src/components/ui/skeleton.tsx` using Tailwind's `animate-pulse` with the existing `celestial-shimmer` keyframe as an optional sweep variant.

**Rationale**: The project already has a `celestial-shimmer` animation defined in `index.css` (shimmer keyframe: `background-position` sweep at 2s interval). A Skeleton primitive using `animate-pulse bg-muted rounded` provides the base, with an optional `variant="shimmer"` that applies the `celestial-shimmer` class for the gold-tinted sweep effect. Composite skeletons (BoardColumnSkeleton, IssueCardSkeleton, ChatMessageSkeleton, AgentCardSkeleton) will match the dimensions of their real counterparts to prevent layout shift (FR-019).

**Alternatives Considered**:
- Radix UI Skeleton: Radix does not provide a skeleton component.
- `react-loading-skeleton`: Adds ~3KB and its own CSS. Unnecessary when Tailwind + existing keyframes provide the same result.
- CSS-only approach without component: Would lead to duplicated markup across all loading states.

## R5: Global Keyboard Shortcuts Architecture

**Decision**: Create a `useGlobalShortcuts` hook that registers a single `keydown` listener on `document` and dispatches actions based on key combinations.

**Rationale**: A single centralized listener avoids multiple competing handlers. The hook will check `event.target` to skip shortcuts when text inputs are focused (FR-026), except for `Escape` and `Ctrl+K` which should always work. The hook uses `useNavigate` from react-router-dom for section navigation and a ref/callback pattern for focusing the chat input. The shortcut help modal is a new component in `src/components/ui/shortcut-modal.tsx`.

**Key Bindings**:
| Key | Action | Guard |
|-----|--------|-------|
| `?` | Open shortcut help modal | Not in text input |
| `Ctrl+K` / `Cmd+K` | Focus chat input | Always |
| `1`–`5` | Navigate to section | Not in text input |
| `Escape` | Close topmost modal | Always |

**Alternatives Considered**:
- `react-hotkeys-hook`: Adds ~2KB dependency. The use case is simple enough for a custom hook with < 60 lines of code.
- `mousetrap`: Legacy library, no React integration. Would require manual cleanup.
- Per-component key handlers: Would fragment shortcut logic across files, making it hard to maintain the shortcut help modal's content.

## R6: Toast Integration Points (Mutation Hooks Audit)

**Decision**: Add `toast()` calls to all existing mutation hooks at their success/error callbacks.

**Audit of mutation hooks requiring toast integration**:

| Hook | File | Mutations | Toast Messages |
|------|------|-----------|----------------|
| `usePipelineConfig` | `src/hooks/usePipelineConfig.ts` | save, saveAsCopy, duplicate, delete, assign | "Pipeline saved", "Pipeline duplicated", "Pipeline deleted", "Pipeline assigned", + error variants |
| `useAgentConfig` | `src/hooks/useAgentConfig.ts` | save, addAgent, removeAgent, cloneAgent, moveAgentToColumn | "Agent configuration saved", "Agent added", "Agent removed", + error variants |
| `useChores` | `src/hooks/useChores.ts` | create, update, delete, trigger, inlineUpdate, createWithAutoMerge | "Chore created", "Chore updated", "Chore deleted", "Chore triggered", + error variants |
| `useSettings` | `src/hooks/useSettings.ts` | save | "Settings saved", + error variant |
| `usePipelineBoardMutations` | `src/hooks/usePipelineBoardMutations.ts` | board-specific pipeline mutations | "Pipeline updated", + error variants |
| `useChat` | `src/hooks/useChat.ts` | send message (error only) | "Failed to send message" |
| `useWorkflow` | `src/hooks/useWorkflow.ts` | trigger, stop | "Workflow started", "Workflow stopped", + error variants |
| `useApps` | `src/hooks/useApps.ts` | create, update, delete | "App created", "App updated", "App deleted", + error variants |

**Pattern**: Import `toast` from `sonner` in each hook. Call `toast.success(msg)` in `.onSuccess` callbacks and `toast.error(msg)` in `.onError` / catch blocks of TanStack Query mutations.

## R7: Board Status Update API

**Decision**: Add a `updateBoardItemStatus(projectId, itemId, statusName)` function to `src/services/api.ts` that calls the existing backend endpoint.

**Rationale**: The backend service `update_item_status_by_name` in `projects.py:575` accepts a project node ID, item node ID, and status column name. The frontend needs a thin API wrapper to invoke this. The chat system already has a `_handle_status_change` function in `chat.py:609` that demonstrates the pattern. A new REST endpoint may need to be exposed, or the existing chat-based status change flow can be adapted. Research confirms the backend has the capability; a simple PATCH/POST endpoint wrapping `update_item_status_by_name` is the cleanest approach.

**Alternatives Considered**:
- Using the chat interface to change status: Too indirect for drag-and-drop UX.
- Direct GraphQL from frontend: Would require exposing GitHub tokens to the frontend, which is a security anti-pattern.

## R8: Sonner Theming for Celestial Design

**Decision**: Style Sonner toasts using Tailwind utility classes and the existing celestial design tokens.

**Rationale**: Sonner's `<Toaster />` accepts `toastOptions.classNames` for custom styling. Toast styles will use:
- Background: `celestial-panel` class (gradient backgrounds matching the theme)
- Border: `border border-border` (uses the `--border` CSS variable)
- Text: `text-foreground` (adapts to light/dark mode)
- Success icon: `text-green-500` (or `--sync-connected` token)
- Error icon: `text-destructive`
- Animation: `celestial-fade-in` class for enter, CSS transition for exit

**Alternatives Considered**:
- Custom toast component from scratch: Higher effort, duplicates Sonner's stacking/timing/accessibility logic.
- Unstyled Sonner: Would not match the celestial theme. Styling is necessary for visual consistency.
