# Data Model: Solune Frontend UX Improvements

**Feature**: 050-frontend-ux-improvements  
**Date**: 2026-03-19

## Entity Definitions

### E1: Toast Notification (Phase 1)

**Source**: FR-001 through FR-005

```typescript
// Sonner handles internal state. These are the call-site types.
type ToastSeverity = 'success' | 'error' | 'warning' | 'info';

// Usage: toast.success("Pipeline saved") — no custom type needed.
// Sonner manages: id, message, duration, dismissible, stacking, ARIA.

// Toaster configuration (set once in AppLayout.tsx):
interface ToasterConfig {
  position: 'bottom-right';          // FR-003: stacking position
  visibleToasts: 3;                  // Edge case: max 3 visible
  duration: 5000;                    // FR-002: default 5s auto-dismiss
  richColors: false;                 // Use custom celestial theme instead
  toastOptions: {
    classNames: {
      toast: string;                 // celestial-panel styling
      title: string;                 // text-foreground
      description: string;          // text-muted-foreground
      success: string;              // success-specific styling
      error: string;                // destructive-specific styling
      warning: string;              // warning-specific styling
    };
  };
}
```

**Validation Rules**: None (toast messages are system-generated strings).  
**State Transitions**: Created → Visible → Auto-dismissed | User-dismissed.

---

### E2: Rendered Message (Phase 2)

**Source**: FR-006 through FR-010

```typescript
// Existing ChatMessage type (no changes needed):
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;                   // Raw markdown (AI) or plain text (user)
  timestamp: string;
  status?: 'sending' | 'sent' | 'failed';
}

// New: Code block rendering props
interface CodeBlockProps {
  children: string;                  // Code content
  className?: string;               // Language class (e.g., "language-typescript")
  inline?: boolean;                  // Inline vs block code
}

// New: Copy action state
interface CopyState {
  copied: boolean;                   // True for ~2s after successful copy
  onCopy: () => void;               // Triggers navigator.clipboard.writeText
}

// Rendering decision (in MessageBubble.tsx):
// if (message.role === 'assistant') → <ReactMarkdown> with GFM + custom code renderer
// if (message.role === 'user')      → plain text (FR-009)
// if (message.role === 'system')    → system message styling (unchanged)
```

**Validation Rules**:
- FR-010: HTML in AI markdown is stripped by default (react-markdown behavior). `rehype-raw` must NOT be added.

**State Transitions**: None (messages are immutable after creation).

---

### E3: Board Card DnD State (Phase 3)

**Source**: FR-011 through FR-017

```typescript
// Existing BoardItem type (from useProjectBoard hook):
interface BoardItem {
  id: string;                        // GitHub node ID
  title: string;
  number: number;
  status: string;                    // Current column/status name
  labels: Label[];
  assignees: Assignee[];
  priority?: string;
  // ... other existing fields
}

// New: DnD context state (managed by useBoardDnd hook)
interface BoardDndState {
  activeCardId: string | null;       // Currently dragged card ID
  activeCard: BoardItem | null;      // Data for DragOverlay rendering
  sourceColumn: string | null;       // Original column before drag
  overColumn: string | null;         // Column currently being hovered
}

// New: DnD event handlers
interface BoardDndHandlers {
  onDragStart: (event: DragStartEvent) => void;
  onDragOver: (event: DragOverEvent) => void;
  onDragEnd: (event: DragEndEvent) => void;
  onDragCancel: () => void;
}

// Optimistic update shape (TanStack Query mutation):
interface MoveCardMutation {
  itemId: string;                    // Board item node ID
  fromColumn: string;                // Source status name
  toColumn: string;                  // Target status name
}

// API request (to backend):
interface UpdateBoardItemStatusRequest {
  project_id: string;                // GitHub project node ID
  item_id: string;                   // Project item node ID
  status: string;                    // Target status column name
}
```

**Validation Rules**:
- FR-016: If `fromColumn === toColumn`, the drop is a no-op (no API call, no toast).
- Card must have a valid node ID to be draggable.

**State Transitions**: Idle → Dragging → Over Target → Dropped (Optimistic) → Confirmed | Rolled Back.

---

### E4: Skeleton Placeholder (Phase 4)

**Source**: FR-018 through FR-021

```typescript
// Skeleton primitive props:
interface SkeletonProps {
  className?: string;                // Tailwind classes for dimensions
  variant?: 'pulse' | 'shimmer';    // Animation type (default: 'pulse')
}

// Composite skeleton shapes (dimension-matched to real content):

// BoardColumnSkeleton: Matches BoardColumn (h-[72rem], w-full)
// - Header skeleton: h-6 w-24 (status name) + h-4 w-8 (count badge)
// - 3–4 IssueCardSkeleton placeholders

// IssueCardSkeleton: Matches IssueCard approximate dimensions
// - Title line: h-4 w-3/4
// - Description lines: h-3 w-full, h-3 w-2/3
// - Label pills: h-5 w-16 (×2)
// - Footer: h-6 w-20 (assignee avatars)

// ChatMessageSkeleton: Matches MessageBubble dimensions
// - Avatar: h-8 w-8 rounded-full
// - Content lines: h-3 w-full (×3), h-3 w-1/2

// AgentCardSkeleton: Matches agent card dimensions
// - Icon: h-10 w-10 rounded-full
// - Name: h-4 w-32
// - Model: h-3 w-24
// - Tools count: h-3 w-16
```

**Validation Rules**:
- FR-019: Skeleton dimensions MUST approximate real content to prevent layout shift.
- FR-021: Shimmer variant uses the existing `celestial-shimmer` class from `index.css`.

**State Transitions**: Visible (loading) → Hidden (data loaded). Replaces CelestialLoader in data-loading contexts (FR-020: CelestialLoader retained for route suspense only).

---

### E5: Keyboard Shortcut (Phase 5)

**Source**: FR-022 through FR-027

```typescript
// Shortcut definition:
interface KeyboardShortcut {
  key: string;                       // Key identifier (e.g., '?', 'k', '1')
  modifiers?: ('ctrl' | 'meta')[];  // Modifier keys
  description: string;              // Human-readable description
  category: 'navigation' | 'action' | 'help';
  action: () => void;               // Callback to execute
  guard?: 'always' | 'not-in-input'; // When shortcut fires
}

// Shortcut registry (static, defined in useGlobalShortcuts):
const SHORTCUTS: KeyboardShortcut[] = [
  { key: '?', description: 'Show keyboard shortcuts', category: 'help', guard: 'not-in-input' },
  { key: 'k', modifiers: ['ctrl'], description: 'Focus chat input', category: 'action', guard: 'always' },
  { key: '1', description: 'Go to Dashboard', category: 'navigation', guard: 'not-in-input' },
  { key: '2', description: 'Go to Board', category: 'navigation', guard: 'not-in-input' },
  { key: '3', description: 'Go to Agents', category: 'navigation', guard: 'not-in-input' },
  { key: '4', description: 'Go to Pipeline', category: 'navigation', guard: 'not-in-input' },
  { key: '5', description: 'Go to Settings', category: 'navigation', guard: 'not-in-input' },
  { key: 'Escape', description: 'Close modal', category: 'action', guard: 'always' },
];

// Shortcut modal state:
interface ShortcutModalState {
  isOpen: boolean;
  open: () => void;
  close: () => void;
}
```

**Validation Rules**:
- FR-026: Shortcuts with `guard: 'not-in-input'` must check `event.target` is not `<input>`, `<textarea>`, or `[contenteditable]`.
- FR-025: Only the topmost modal responds to Escape (handled by React's event bubbling — the modal component calls `event.stopPropagation()`).

**State Transitions**: None (shortcuts are stateless event handlers). Modal: Closed → Open → Closed.

---

### E6: Quick Win Entities (Phase 6)

**Source**: FR-028 through FR-033

```typescript
// Board filter state (extends existing useBoardControls):
interface BoardFilterState {
  labels: string[];                  // Selected label names
  assignees: string[];               // Selected assignee logins
  milestones: string[];              // Selected milestone titles
  pipelineConfig: string | null;     // Selected pipeline config ID
  priority: string | null;           // NEW: Selected priority level (P0–P3)
}

// Tour progress (extends SpotlightTooltip):
interface TourProgress {
  currentStep: number;               // 1-based step index
  totalSteps: number;                // Total steps (currently 9)
}

// Chat date separator:
interface DateSeparator {
  date: string;                      // ISO date string (YYYY-MM-DD)
  label: string;                     // Display label (e.g., "Today", "Yesterday", "Mar 17")
}

// Notification bell animation state:
interface NotificationBellState {
  unreadCount: number;
  shouldPulse: boolean;              // true when unreadCount > 0
}

// Ctrl+Enter send (no new types — extends existing keyboard handler in ChatInterface)
```

**Validation Rules**:
- FR-028: Filter returns empty state with "Clear filters" action when no matches.
- FR-032: Empty columns show illustration + suggestion (e.g., "Create your first issue").
