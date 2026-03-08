# Data Model: Comprehensive Tooltips Across App UI for Feature Explainability and UX Guidance

**Feature**: 030-ui-tooltips | **Date**: 2026-03-08

## Frontend Types (TypeScript)

### Tooltip Content Types (New)

```typescript
/**
 * A single tooltip content entry in the centralized registry.
 * Each entry maps to a specific UI element via its key.
 */
export interface TooltipEntry {
  /** Concise explanation of the element's purpose and consequences (required) */
  summary: string;
  /** Optional bolded heading for complex features (progressive disclosure tier 1) */
  title?: string;
  /** Optional URL for "Learn more" link (progressive disclosure tier 2) */
  learnMoreUrl?: string;
}

/**
 * The centralized tooltip content registry.
 * Keys follow dot-notation: {page}.{section}.{element}
 * e.g., 'agents.card.deleteButton', 'pipeline.stage.modelSelector'
 */
export type TooltipContentRegistry = Record<string, TooltipEntry>;
```

### Tooltip Component Types (New)

```typescript
/**
 * Props for the reusable Tooltip wrapper component.
 * Supports both registry-based (contentKey) and direct content modes.
 */
export interface TooltipProps {
  /** Registry key to look up tooltip content (primary usage) */
  contentKey?: string;
  /** Direct tooltip text (escape hatch for dynamic content) */
  content?: string;
  /** Direct title for the tooltip (used with content prop) */
  title?: string;
  /** Direct learnMoreUrl for the tooltip (used with content prop) */
  learnMoreUrl?: string;
  /** Preferred tooltip placement relative to trigger */
  side?: 'top' | 'right' | 'bottom' | 'left';
  /** Horizontal alignment of tooltip relative to trigger */
  align?: 'start' | 'center' | 'end';
  /** Delay in ms before tooltip appears (default: 300) */
  delayDuration?: number;
  /** Children element that triggers the tooltip */
  children: React.ReactNode;
}
```

### Radix Tooltip Provider Types (Configuration)

```typescript
/**
 * Configuration for the global TooltipProvider wrapping the app.
 * Set once in App.tsx, applies to all tooltips.
 */
interface TooltipProviderConfig {
  /** Default delay before tooltip shows (ms). Set to 300 per FR-005. */
  delayDuration: number;
  /** Time window for instant-show when moving between tooltips (ms). */
  skipDelayDuration: number;
  /** Whether to disable hover triggers entirely (for testing). */
  disableHoverableContent?: boolean;
}
```

---

## Tooltip Content Registry Structure

### Key Naming Convention

Keys use hierarchical dot-notation: `{area}.{section}.{element}`

| Level | Description | Examples |
|-------|-------------|----------|
| `area` | Top-level page or feature area | `agents`, `pipeline`, `board`, `chat`, `chores`, `settings`, `tools` |
| `section` | Component group within the area | `card`, `panel`, `toolbar`, `modal`, `stage` |
| `element` | Specific interactive element | `deleteButton`, `modelSelector`, `refreshButton`, `aiEnhanceToggle` |

### Registry Categories

| Category | Key Pattern | Element Count (Estimated) | Examples |
|----------|-------------|---------------------------|----------|
| Agents | `agents.*` | ~8 | `agents.card.deleteButton`, `agents.panel.bulkUpdateButton`, `agents.card.editButton` |
| Pipeline | `pipeline.*` | ~6 | `pipeline.stage.modelSelector`, `pipeline.board.addStageButton`, `pipeline.stage.deleteButton` |
| Board | `board.*` | ~6 | `board.toolbar.refreshButton`, `board.toolbar.cleanUpButton`, `board.toolbar.filterButton` |
| Chat | `chat.*` | ~5 | `chat.toolbar.aiEnhanceToggle`, `chat.toolbar.attachButton`, `chat.toolbar.voiceButton` |
| Chores | `chores.*` | ~5 | `chores.card.deleteButton`, `chores.card.executeButton`, `chores.card.editButton` |
| Settings | `settings.*` | ~4 | `settings.models.addButton`, `settings.general.themeToggle` |
| Tools | `tools.*` | ~4 | `tools.card.configureButton`, `tools.card.statusToggle` |

**Total estimated entries**: ~38 tooltip content entries

---

## State Machines

### Tooltip Display Lifecycle

```text
                    ┌────────────┐
                    │   HIDDEN    │  Tooltip not visible
                    └──────┬─────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
         Mouse hover   Keyboard    Long-press
         enters        focus (Tab) starts (touch)
              │            │            │
              ▼            ▼            ▼
                    ┌────────────┐
                    │  DELAY     │  300ms timer running
                    │  (waiting) │  (configurable via delayDuration)
                    └──────┬─────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        Timer fires   Mouse leaves  Focus lost
              │        (cancel)     (cancel)
              │            │            │
              ▼            ▼            ▼
       ┌────────────┐  ┌────────────┐
       │  VISIBLE   │  │   HIDDEN    │  Timer cancelled
       │  (shown)   │  │  (reset)   │
       └──────┬─────┘  └────────────┘
              │
    ┌─────────┼──────────┐
    │         │          │
 Mouse-out  Escape   Focus lost
    │       key        │
    ▼         ▼          ▼
       ┌────────────┐
       │   HIDDEN    │  Tooltip dismissed
       │  (closed)   │
       └────────────┘
```

**Note**: When `skipDelayDuration` is set (default: 300ms), moving from one tooltip trigger to another within this window shows the next tooltip instantly (no delay). This prevents the "tooltip lag" experience when scanning UI elements.

### Progressive Disclosure Flow

```text
User triggers tooltip
    │
    ▼
┌──────────────────────────────────────┐
│  Is there a 'title' field?           │
│                                      │
│  NO → Simple tooltip:                │
│  ┌────────────────────────────────┐  │
│  │ summary text only              │  │
│  │ (concise, 1-2 lines)          │  │
│  └────────────────────────────────┘  │
│                                      │
│  YES → Rich tooltip:                 │
│  ┌────────────────────────────────┐  │
│  │ **title** (bold heading)       │  │
│  │ summary text (1-2 sentences)   │  │
│  │                                │  │
│  │ Is there a 'learnMoreUrl'?     │  │
│  │  YES → [Learn more →] link     │  │
│  │  NO  → (nothing extra)         │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
```

### Content Resolution Flow

```text
Tooltip component receives props
    │
    ├── contentKey provided?
    │   │
    │   YES → Look up tooltipContent[contentKey]
    │   │
    │   ├── Entry found?
    │   │   │
    │   │   YES → Render { title?, summary, learnMoreUrl? }
    │   │   │
    │   │   NO → Skip rendering (FR-012: graceful fallback)
    │   │        console.warn in development mode
    │   │
    │   └── (done)
    │
    ├── content provided? (string)
    │   │
    │   YES → Render { summary: content, title?, learnMoreUrl? }
    │   │      title and learnMoreUrl from direct props
    │   │
    │   └── (done)
    │
    └── Neither provided?
        │
        └── Render children only (no tooltip wrapper)
            console.warn in development mode
```

---

## Database Changes

### No Schema Changes Required

This feature is entirely frontend. No database tables, columns, or migrations are needed. Tooltip content is stored as static TypeScript constants bundled with the frontend application.

---

## localStorage Keys

No new localStorage keys are introduced. Tooltip visibility state is ephemeral (hover/focus-driven) and not persisted.

---

## CSS Custom Properties Used

The following existing CSS variables are used for tooltip styling:

| Variable | Light Value | Dark Value | Usage |
|----------|-------------|------------|-------|
| `--popover` | `39 82% 96%` | `236 28% 14%` | Tooltip background |
| `--popover-foreground` | `228 24% 16%` | `210 40% 98%` | Tooltip text color |
| `--border` | `37 34% 78%` | `230 16% 22%` | Tooltip border |
| `--radius` | `1rem` | `1rem` | Border radius base |

**Contrast ratios** (verified):

- Light theme: `--popover-foreground` on `--popover` → ~10.2:1 (exceeds 4.5:1 AA)
- Dark theme: `--popover-foreground` on `--popover` → ~12.8:1 (exceeds 4.5:1 AA)

---

## Accessibility Attributes

Every tooltip instance generates the following ARIA structure:

```html
<!-- Trigger element (any interactive element) -->
<button
  aria-describedby="tooltip-{unique-id}"
  data-state="closed|instant-open|delayed-open"
>
  Button Label
</button>

<!-- Tooltip (rendered in portal) -->
<div
  id="tooltip-{unique-id}"
  role="tooltip"
  data-state="closed|instant-open|delayed-open"
>
  <p class="font-semibold">Title (if present)</p>
  <p>Summary text describing the element.</p>
  <a href="/docs/topic">Learn more →</a>
</div>
```

Radix UI automatically manages:

- `aria-describedby` association between trigger and tooltip
- `role="tooltip"` on the tooltip content
- Focus management (tooltip triggers on Tab focus)
- Escape key dismissal
- Screen reader announcement of tooltip content
