# Contract: Global Keyboard Shortcuts (Phase 5)

**Feature**: 050-frontend-ux-improvements  
**Requirements**: FR-022 through FR-027

## Component Contracts

### `useGlobalShortcuts` Hook (NEW)

**Location**: `solune/frontend/src/hooks/useGlobalShortcuts.ts`

```tsx
interface UseGlobalShortcutsOptions {
  chatInputRef?: React.RefObject<HTMLInputElement | HTMLTextAreaElement>;
  onOpenShortcutModal: () => void;
}

function useGlobalShortcuts(options: UseGlobalShortcutsOptions): void;
```

**Behavior**:
1. Registers a single `keydown` event listener on `document` via `useEffect`.
2. Checks `event.target` to determine if a text input is focused.
3. Dispatches actions based on key combinations:

```tsx
const isTextInput = (target: EventTarget | null): boolean => {
  if (!target || !(target instanceof HTMLElement)) return false;
  const tagName = target.tagName.toLowerCase();
  return tagName === 'input' || tagName === 'textarea' || target.isContentEditable;
};

const handleKeyDown = (event: KeyboardEvent) => {
  const inInput = isTextInput(event.target);

  // Always active (FR-026 exceptions):
  if (event.key === 'Escape') {
    // Close topmost modal — handled by individual modal components
    return;
  }
  if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
    event.preventDefault();
    // FR-023: Focus chat input (open chat panel if closed)
    options.chatInputRef?.current?.focus();
    return;
  }

  // Guard: skip when in text input (FR-026)
  if (inInput) return;

  if (event.key === '?') {
    event.preventDefault();
    options.onOpenShortcutModal();
    return;
  }

  // FR-024: Number key navigation
  const sectionMap: Record<string, string> = {
    '1': '/dashboard',
    '2': '/board',
    '3': '/agents',
    '4': '/pipeline',
    '5': '/settings',
  };
  if (sectionMap[event.key]) {
    event.preventDefault();
    navigate(sectionMap[event.key]);
  }
};
```

4. Cleans up listener on unmount via `useEffect` return.

### `ShortcutModal.tsx` (NEW)

**Location**: `solune/frontend/src/components/ui/shortcut-modal.tsx`

```tsx
interface ShortcutModalProps {
  isOpen: boolean;
  onClose: () => void;
}

function ShortcutModal({ isOpen, onClose }: ShortcutModalProps) {
  // FR-022: Display all available shortcuts
  // FR-025: Close on Escape
}
```

**Layout**:
```
┌─────────────────────────────────────┐
│  Keyboard Shortcuts            [✕]  │
├─────────────────────────────────────┤
│  NAVIGATION                         │
│  1         Go to Dashboard          │
│  2         Go to Board              │
│  3         Go to Agents             │
│  4         Go to Pipeline           │
│  5         Go to Settings           │
│                                     │
│  ACTIONS                            │
│  Ctrl+K    Focus chat input         │
│  Escape    Close modal              │
│                                     │
│  HELP                               │
│  ?         Show this modal          │
└─────────────────────────────────────┘
```

**Styling**: `celestial-panel` background, `celestial-fade-in` animation, modal with backdrop overlay.

### AppLayout.tsx Integration

**Location**: `solune/frontend/src/layout/AppLayout.tsx`  
**Action**: Add `useGlobalShortcuts` and `ShortcutModal` state.

```tsx
import { useGlobalShortcuts } from '@/hooks/useGlobalShortcuts';
import { ShortcutModal } from '@/components/ui/shortcut-modal';

// Inside AppLayout:
const [shortcutModalOpen, setShortcutModalOpen] = useState(false);
const chatInputRef = useRef<HTMLInputElement>(null);

useGlobalShortcuts({
  chatInputRef,
  onOpenShortcutModal: () => setShortcutModalOpen(true),
});

// In JSX:
<ShortcutModal
  isOpen={shortcutModalOpen}
  onClose={() => setShortcutModalOpen(false)}
/>
```

### Tooltip Enhancement

**Location**: Sidebar nav items and toolbar buttons  
**Action**: Append shortcut hints to existing tooltip text (FR-027).

```tsx
// Example in Sidebar nav item:
<Tooltip content="Board (2)">    {/* Was: "Board" */}
  <NavLink to="/board">...</NavLink>
</Tooltip>

// Example in toolbar:
<Tooltip content="Focus chat (Ctrl+K)">
  <Button>...</Button>
</Tooltip>
```

## Accessibility

- FR-022: Modal uses `role="dialog"` with `aria-modal="true"` and `aria-labelledby` pointing to the title.
- FR-025: Escape closes topmost modal (handled by modal's own `onKeyDown` handler calling `event.stopPropagation()`).
- FR-026: Text input guard prevents shortcuts from firing during typing.
- Focus management: When modal opens, focus moves to the close button. When modal closes, focus returns to the previously focused element.
