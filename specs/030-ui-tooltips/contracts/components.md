# Component Contracts: Comprehensive Tooltips Across App UI for Feature Explainability and UX Guidance

**Feature**: 030-ui-tooltips | **Date**: 2026-03-08

## New Components

### Tooltip

**Location**: `frontend/src/components/ui/tooltip.tsx`
**Purpose**: Reusable tooltip wrapper component that provides consistent, accessible tooltips across the application. Built on `@radix-ui/react-tooltip` for positioning, accessibility, and interaction handling. Resolves content from the centralized registry by key or accepts direct content.

```typescript
interface TooltipProps {
  contentKey?: string;                    // Registry key to look up tooltip content
  content?: string;                       // Direct tooltip text (escape hatch)
  title?: string;                         // Direct title (used with content prop)
  learnMoreUrl?: string;                  // Direct learnMoreUrl (used with content prop)
  side?: 'top' | 'right' | 'bottom' | 'left';  // Preferred placement (default: 'top')
  align?: 'start' | 'center' | 'end';    // Alignment (default: 'center')
  delayDuration?: number;                 // Override delay in ms (default: 300)
  children: React.ReactNode;             // Trigger element
}
```

**Behavior**:

- **Registry lookup**: When `contentKey` is provided, looks up `tooltipContent[contentKey]`. If not found, renders children without tooltip (FR-012 graceful fallback). Logs a `console.warn` in development mode.
- **Direct content**: When `content` is provided (no `contentKey`), uses the string directly as the summary. Optional `title` and `learnMoreUrl` props augment the direct content.
- **Neither provided**: Renders children without tooltip wrapper. Logs a `console.warn` in development.
- **Trigger delay**: Default 300ms (FR-005). Overridable via `delayDuration` prop. When user moves between tooltips within the `skipDelayDuration` window (300ms), the next tooltip shows instantly.
- **Positioning**: Prefers `side` placement (default: `'top'`). Automatically flips to opposite side when clipped by viewport edge (FR-003). Shifts horizontally to stay within viewport bounds.
- **Portal rendering**: Tooltip content renders in a React portal outside the DOM hierarchy to avoid overflow clipping from scrollable containers.
- **Dismiss**: Dismisses on mouse-out, touch-end, Escape key, or focus loss (FR-006).
- **Accessibility**: Trigger element gets `aria-describedby` pointing to the tooltip. Tooltip has `role="tooltip"`. Tooltip appears on keyboard focus (Tab) for keyboard users (FR-008).
- **Progressive disclosure**: When the resolved content has a `title`, renders it as a bold heading above the summary. When `learnMoreUrl` is present, renders a "Learn more →" link below the summary (FR-007).
- **Animation**: Fade-in/zoom-in on appear, fade-out/zoom-out on dismiss. Respects `prefers-reduced-motion` via Tailwind's `motion-reduce:` variant (FR-013).

**Styling**:

```text
┌───────────────────────────────────────┐
│ ▲ (arrow pointing to trigger)         │
│                                       │
│  **Model Selection**                  │  ← title (bold, optional)
│  Choose which language model powers   │  ← summary
│  this pipeline stage.                 │
│                                       │
│  Learn more →                         │  ← learnMoreUrl (optional)
│                                       │
└───────────────────────────────────────┘
max-width: 280px
min-font-size: 13px
background: hsl(var(--popover))
text: hsl(var(--popover-foreground))
border: 1px solid hsl(var(--border) / 0.6)
border-radius: 0.5rem (rounded-lg)
padding: 8px 12px (py-2 px-3)
shadow: shadow-md
z-index: 50
```

**Exported Members**:

```typescript
// High-level wrapper (primary usage)
export function Tooltip(props: TooltipProps): JSX.Element;

// Re-exported Radix primitives (for advanced use cases)
export { TooltipProvider } from '@radix-ui/react-tooltip';

// Subcomponents for fine-grained control
export { TooltipTrigger, TooltipContent, TooltipArrow } from './tooltip-internals';
```

---

### TooltipProvider (App-Level Wrapper)

**Location**: Used in `frontend/src/App.tsx`
**Purpose**: Wraps the entire application to provide shared tooltip delay management across all tooltip instances.

```typescript
// In App.tsx
import { TooltipProvider } from '@/components/ui/tooltip';

<TooltipProvider delayDuration={300} skipDelayDuration={300}>
  <QueryClientProvider client={queryClient}>
    {/* ... existing app structure ... */}
  </QueryClientProvider>
</TooltipProvider>
```

**Behavior**:

- `delayDuration={300}`: Default 300ms hover delay for all tooltips (FR-005).
- `skipDelayDuration={300}`: When moving between tooltip triggers within 300ms, the next tooltip appears instantly (no delay). Provides smooth scanning experience.
- Single provider wraps the entire app — no per-page providers needed.

---

## Modified Components

### App.tsx

**Location**: `frontend/src/App.tsx`
**Purpose**: Application root — modified to wrap the app tree with `TooltipProvider`.

**Changes**:

1. Import `TooltipProvider` from `@/components/ui/tooltip`
2. Wrap the outermost layer (around `QueryClientProvider`) with `<TooltipProvider delayDuration={300} skipDelayDuration={300}>`
3. No structural changes to routing, error boundaries, or query client

### Board Components

**RefreshButton.tsx**: Wrap the refresh button with `<Tooltip contentKey="board.toolbar.refreshButton">`
**CleanUpButton.tsx**: Wrap the clean-up button with `<Tooltip contentKey="board.toolbar.cleanUpButton">`
**BoardToolbar.tsx**: Add tooltips to filter, sort, and group controls

### Chat Components

**ChatToolbar.tsx**: Add tooltips to AI Enhance toggle, attach, voice, and send buttons
**ChatInterface.tsx**: Add tooltips to history toggle and message actions

### Agent Components

**AgentCard.tsx**: Add tooltips to edit, delete, and model selector actions
**AgentsPanel.tsx**: Add tooltips to search, sort, bulk update, and featured agents controls
**AddAgentModal.tsx**: Add tooltips to configuration fields (system prompt, tools, model)

### Pipeline Components

**StageCard.tsx**: Add tooltips to stage actions and model selector
**PipelineBoard.tsx**: Add tooltips to add stage, save, and pipeline-level actions
**ModelSelector.tsx**: Add tooltip to model dropdown explaining selection impact

### Chores Components

**ChoreCard.tsx**: Add tooltips to execute, edit, and delete actions

### Settings Components

Add tooltips to theme toggles, model management, and configuration options

### Tools Components

Add tooltips to tool configuration, status toggles, and management actions

---

## Tooltip Content Registry Contract

### File: `frontend/src/constants/tooltip-content.ts`

```typescript
import type { TooltipEntry } from '@/components/ui/tooltip';

export const tooltipContent: Record<string, TooltipEntry> = {
  // Board
  'board.toolbar.refreshButton': {
    summary: 'Refresh the board to show the latest project data from GitHub.',
  },
  'board.toolbar.cleanUpButton': {
    summary: 'Remove completed items from the board to reduce visual clutter.',
  },
  'board.toolbar.filterButton': {
    summary: 'Filter board items by label, assignee, milestone, or other criteria.',
  },
  'board.toolbar.sortButton': {
    summary: 'Change the order of items within each column.',
  },
  'board.toolbar.groupButton': {
    summary: 'Group board items by label, assignee, or milestone.',
  },

  // Chat
  'chat.toolbar.aiEnhanceToggle': {
    title: 'AI Enhance',
    summary: 'When enabled, your message is refined by AI before creating a task. Disable for literal task creation from your exact text.',
  },
  'chat.toolbar.attachButton': {
    summary: 'Attach a file to your message for context.',
  },
  'chat.toolbar.voiceButton': {
    summary: 'Use voice input to dictate your message.',
  },
  'chat.toolbar.sendButton': {
    summary: 'Send your message to create a new task or issue.',
  },
  'chat.interface.historyToggle': {
    summary: 'View your recent message history and past interactions.',
  },

  // Agents
  'agents.card.editButton': {
    summary: 'Edit this agent\'s configuration including name, system prompt, tools, and model. Changes create a pull request.',
  },
  'agents.card.deleteButton': {
    summary: 'Permanently delete this agent configuration. This action cannot be undone.',
  },
  'agents.card.modelSelector': {
    title: 'AI Model',
    summary: 'Select which language model powers this agent. Different models vary in speed, cost, and capability.',
  },
  'agents.panel.searchInput': {
    summary: 'Search agents by name, description, or slug.',
  },
  'agents.panel.sortButton': {
    summary: 'Sort agents by name, creation date, or usage count.',
  },
  'agents.panel.bulkUpdateButton': {
    title: 'Bulk Model Update',
    summary: 'Update the AI model for all agents at once. Opens a confirmation dialog before applying changes.',
  },
  'agents.panel.addAgentButton': {
    summary: 'Create a new agent with a custom system prompt, tools, and model selection.',
  },
  'agents.modal.systemPrompt': {
    title: 'System Prompt',
    summary: 'Instructions that define this agent\'s behavior, expertise, and response style. This is sent to the AI model with every interaction.',
    learnMoreUrl: 'https://docs.github.com/en/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot',
  },
  'agents.modal.toolsEditor': {
    title: 'Agent Tools',
    summary: 'Tools this agent can use during task execution. Order matters — tools listed first are preferred. At least one tool is required.',
  },

  // Pipeline
  'pipeline.stage.modelSelector': {
    title: 'Stage Model',
    summary: 'Choose the AI model for this pipeline stage. Consider speed vs. capability tradeoffs for your workflow.',
  },
  'pipeline.stage.deleteButton': {
    summary: 'Remove this stage from the pipeline. Remaining stages will adjust their order automatically.',
  },
  'pipeline.board.addStageButton': {
    summary: 'Add a new stage to the pipeline workflow.',
  },
  'pipeline.board.savePipelineButton': {
    title: 'Save Pipeline',
    summary: 'Save the current pipeline configuration. This persists all stage settings and model selections.',
  },
  'pipeline.board.deletePipelineButton': {
    summary: 'Delete this entire pipeline configuration. This action cannot be undone.',
  },

  // Chores
  'chores.card.executeButton': {
    title: 'Execute Chore',
    summary: 'Trigger this chore to run immediately. The execution count will be incremented.',
  },
  'chores.card.deleteButton': {
    summary: 'Permanently delete this chore. This action cannot be undone.',
  },
  'chores.card.editButton': {
    summary: 'Edit this chore\'s name, description, schedule, and configuration.',
  },
  'chores.card.aiEnhanceToggle': {
    title: 'AI Enhance',
    summary: 'When enabled, AI refines the chore\'s task description before execution for better results.',
  },

  // Settings
  'settings.models.addButton': {
    summary: 'Add a new AI model configuration to your available models list.',
  },
  'settings.general.themeToggle': {
    summary: 'Switch between light and dark theme. Your preference is saved locally.',
  },

  // Tools
  'tools.card.configureButton': {
    summary: 'Open the configuration panel for this tool to adjust its settings.',
  },
  'tools.card.statusToggle': {
    summary: 'Enable or disable this tool. Disabled tools are not available to agents.',
  },
};
```

---

## Integration Pattern

### Standard Integration (for each component)

```tsx
// Before (no tooltip)
<Button variant="destructive" onClick={handleDelete}>
  <Trash2 className="h-4 w-4" />
</Button>

// After (with tooltip)
import { Tooltip } from '@/components/ui/tooltip';

<Tooltip contentKey="agents.card.deleteButton">
  <Button variant="destructive" onClick={handleDelete}>
    <Trash2 className="h-4 w-4" />
  </Button>
</Tooltip>
```

### Dynamic Content Integration

```tsx
// For tooltips with runtime-computed text
<Tooltip content={`${selectedCount} agents will be updated to ${modelName}`}>
  <Button onClick={handleBulkUpdate}>Confirm</Button>
</Tooltip>
```

---

## No API Contracts Needed

This feature is entirely frontend. No REST API endpoints are added, modified, or consumed beyond what already exists. The tooltip content registry is a static TypeScript module bundled with the frontend application.
