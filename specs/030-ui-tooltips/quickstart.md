# Quickstart: Comprehensive Tooltips Across App UI for Feature Explainability and UX Guidance

**Feature**: 030-ui-tooltips | **Date**: 2026-03-08

## Prerequisites

- Node.js 20+ and npm
- The repository cloned and on the feature branch

```bash
git checkout 030-ui-tooltips
```

## Setup

### Frontend

```bash
cd frontend
npm install
npm run dev
# App available at http://localhost:5173
```

No backend changes are needed for this feature. If you need the full app experience (data in the UI), also start the backend:

```bash
cd backend
pip install -e ".[dev]"
uvicorn src.main:app --reload --port 8000
```

## New Files to Create

### New Frontend Files

| File | Purpose |
|------|---------|
| `frontend/src/components/ui/tooltip.tsx` | NEW: Reusable Tooltip wrapper component built on @radix-ui/react-tooltip |
| `frontend/src/constants/tooltip-content.ts` | NEW: Centralized tooltip content registry mapping keys to tooltip strings |

## Files to Modify

| File | Changes |
|------|---------|
| `frontend/package.json` | Add `@radix-ui/react-tooltip` dependency |
| `frontend/src/App.tsx` | Wrap app with `TooltipProvider` (300ms delay, 300ms skipDelay) |
| `frontend/src/components/agents/AgentCard.tsx` | Wrap edit, delete, and model selector with `<Tooltip>` |
| `frontend/src/components/agents/AgentsPanel.tsx` | Wrap search, sort, bulk update, and add agent controls with `<Tooltip>` |
| `frontend/src/components/agents/AddAgentModal.tsx` | Wrap system prompt, tools, and model fields with `<Tooltip>` |
| `frontend/src/components/board/RefreshButton.tsx` | Wrap refresh button with `<Tooltip>` |
| `frontend/src/components/board/CleanUpButton.tsx` | Wrap clean-up button with `<Tooltip>` |
| `frontend/src/components/board/BoardToolbar.tsx` | Wrap filter, sort, and group controls with `<Tooltip>` |
| `frontend/src/components/chat/ChatToolbar.tsx` | Wrap AI Enhance toggle, attach, voice, and send buttons with `<Tooltip>` |
| `frontend/src/components/chat/ChatInterface.tsx` | Wrap history toggle and message actions with `<Tooltip>` |
| `frontend/src/components/chores/ChoreCard.tsx` | Wrap execute, edit, and delete buttons with `<Tooltip>` |
| `frontend/src/components/pipeline/StageCard.tsx` | Wrap stage actions and model selector with `<Tooltip>` |
| `frontend/src/components/pipeline/PipelineBoard.tsx` | Wrap pipeline-level actions with `<Tooltip>` |
| `frontend/src/components/pipeline/ModelSelector.tsx` | Wrap model dropdown with `<Tooltip>` |
| `frontend/src/pages/SettingsPage.tsx` | Wrap settings controls with `<Tooltip>` |
| `frontend/src/pages/ToolsPage.tsx` | Wrap tools management controls with `<Tooltip>` |

## Implementation Order

### Phase 1: Foundation — Tooltip Component + Content Registry (FR-003, FR-004, FR-005, FR-006, FR-008, FR-009, FR-010, FR-012, FR-013)

1. **Install dependency**

   ```bash
   cd frontend && npm install @radix-ui/react-tooltip
   ```

2. **tooltip.tsx** (new) — `frontend/src/components/ui/tooltip.tsx`
   - Import Radix UI Tooltip primitives (`Root`, `Trigger`, `Content`, `Arrow`, `Portal`, `Provider`)
   - Create `Tooltip` component with `contentKey` and `content` props
   - Apply consistent styling: `bg-popover`, `text-popover-foreground`, `border-border/60`, `max-w-[280px]`, `text-[13px]`, `rounded-lg`, `shadow-md`
   - Add directional arrow via `<TooltipArrow>`
   - Handle progressive disclosure: render `title` as bold heading, `summary` as body, `learnMoreUrl` as "Learn more →" link
   - Graceful fallback: render children only when no content resolved (FR-012)
   - Animation: `animate-in fade-in-0 zoom-in-95` with `motion-reduce:animate-none`
   - Re-export `TooltipProvider` for use in App.tsx

3. **tooltip-content.ts** (new) — `frontend/src/constants/tooltip-content.ts`
   - Define `TooltipEntry` interface: `{ summary: string; title?: string; learnMoreUrl?: string }`
   - Export `tooltipContent` record with all tooltip entries
   - Organize by area: board, chat, agents, pipeline, chores, settings, tools
   - Start with ~38 entries covering all interactive elements

4. **App.tsx** — Wrap with `TooltipProvider`
   - Import `TooltipProvider` from `@/components/ui/tooltip`
   - Wrap around `QueryClientProvider` (outermost wrapper after error boundary)
   - Set `delayDuration={300}` and `skipDelayDuration={300}`

**Verify**: App builds without errors. TypeScript compiles. No visual changes yet (tooltips not wired to elements).

### Phase 2: Board & Chat Tooltips (FR-001, FR-002)

1. **RefreshButton.tsx** — Wrap with `<Tooltip contentKey="board.toolbar.refreshButton">`
2. **CleanUpButton.tsx** — Wrap with `<Tooltip contentKey="board.toolbar.cleanUpButton">`
3. **BoardToolbar.tsx** — Wrap filter, sort, and group buttons with `<Tooltip>`
4. **ChatToolbar.tsx** — Wrap AI Enhance toggle, attach, voice, and send buttons with `<Tooltip>`
5. **ChatInterface.tsx** — Wrap history toggle with `<Tooltip>`

**Verify**: Hover over board refresh button → tooltip appears after ~300ms with "Refresh the board to show the latest project data from GitHub." Tab to button → same tooltip. Press Escape → tooltip dismisses. Verify tooltip flips when near viewport edge.

### Phase 3: Agent Tooltips (FR-001, FR-002, FR-007)

1. **AgentCard.tsx** — Wrap edit, delete, and model selector with `<Tooltip>`
2. **AgentsPanel.tsx** — Wrap search input, sort, bulk update, and add agent controls with `<Tooltip>`
3. **AddAgentModal.tsx** — Wrap system prompt field, tools editor, and model field with `<Tooltip>` (these use the progressive disclosure pattern with `title` + `learnMoreUrl`)

**Verify**: Open Agents page → hover over delete button → tooltip shows "Permanently delete this agent configuration. This action cannot be undone." Hover over system prompt field → rich tooltip with bold title "System Prompt" and "Learn more →" link.

### Phase 4: Pipeline Tooltips (FR-001, FR-002, FR-007)

1. **StageCard.tsx** — Wrap model selector and delete button with `<Tooltip>`
2. **PipelineBoard.tsx** — Wrap add stage, save, and delete pipeline buttons with `<Tooltip>`
3. **ModelSelector.tsx** — Wrap model dropdown with `<Tooltip>` (progressive disclosure)

**Verify**: Open Pipeline page → hover over model selector → rich tooltip with "Stage Model" title.

### Phase 5: Chores, Settings & Tools Tooltips (FR-001, FR-002)

1. **ChoreCard.tsx** — Wrap execute, edit, and delete buttons with `<Tooltip>`
2. **SettingsPage.tsx** — Wrap theme toggle and model management controls with `<Tooltip>`
3. **ToolsPage.tsx** — Wrap configure and status toggle with `<Tooltip>`

**Verify**: All pages have tooltips on interactive elements. No broken or empty tooltips.

### Phase 6: Accessibility & Polish (FR-008, FR-013)

1. **Keyboard navigation audit**
    - Tab through every page → verify tooltips appear on focus
    - Escape key dismisses any visible tooltip
    - Screen reader announces tooltip content

2. **Motion preferences**
    - Enable `prefers-reduced-motion` in browser dev tools
    - Verify tooltip animations are disabled/reduced

3. **Viewport edge testing**
    - Trigger tooltips on elements near all viewport edges
    - Verify tooltips flip and shift to remain visible

**Verify**: Run `npx vitest run` → all existing tests pass. Run accessibility audit → no critical violations from tooltips.

## Key Patterns to Follow

### Registry-Based Tooltip (Primary)

```tsx
import { Tooltip } from '@/components/ui/tooltip';

<Tooltip contentKey="agents.card.deleteButton">
  <Button variant="destructive">
    <Trash2 className="h-4 w-4" />
  </Button>
</Tooltip>
```

### Direct Content Tooltip (Escape Hatch)

```tsx
<Tooltip content={`Updating ${count} agents to ${modelName}`}>
  <Button>Confirm</Button>
</Tooltip>
```

### Progressive Disclosure Tooltip (Complex Features)

Registry entry:

```typescript
'agents.modal.systemPrompt': {
  title: 'System Prompt',
  summary: 'Instructions that define this agent\'s behavior...',
  learnMoreUrl: 'https://docs.github.com/...',
},
```

Component usage:

```tsx
<Tooltip contentKey="agents.modal.systemPrompt">
  <label>System Prompt</label>
</Tooltip>
```

### Adding a New Tooltip

1. Add entry to `frontend/src/constants/tooltip-content.ts`:

   ```typescript
   'area.section.element': {
     summary: 'Concise description of what this does and why it matters.',
   },
   ```

2. Wrap the element in the component file:

   ```tsx
   <Tooltip contentKey="area.section.element">
     <ExistingElement />
   </Tooltip>
   ```

3. No other changes needed — the Tooltip component handles all rendering, positioning, and accessibility.

## Verification

After implementation, verify:

1. **Hover tooltip**: Hover over any button → tooltip appears after ~300ms → move away → tooltip dismisses.
2. **Keyboard tooltip**: Tab to any button → tooltip appears → Shift+Tab away → tooltip dismisses.
3. **Escape dismiss**: With tooltip visible → press Escape → tooltip dismisses immediately.
4. **Viewport flip (top)**: Trigger tooltip on element near top edge → tooltip appears below.
5. **Viewport flip (right)**: Trigger tooltip on element near right edge → tooltip shifts left.
6. **Dark mode**: Toggle to dark theme → tooltips use dark-appropriate colors (theme-aware).
7. **Progressive disclosure**: Hover over agent system prompt field → see bold title + summary + "Learn more" link.
8. **Simple tooltip**: Hover over refresh button → see only summary text (no title, no "Learn more").
9. **No empty tooltip**: Hover over element with no registry entry → no tooltip appears, no broken UI.
10. **Consistent design**: All tooltips have same font size (13px+), max-width (~280px), arrow, border radius.
11. **Adjacent elements**: Tooltip does not cover nearby clickable elements.
12. **Rapid scanning**: Move quickly between tooltip triggers → previous dismisses, next appears without delay lag.
13. **Reduced motion**: Enable `prefers-reduced-motion` → tooltip appears/disappears without animation.
14. **Existing tests**: Run `npx vitest run` → all 358+ existing tests pass.
15. **TypeScript**: Run `npx tsc --noEmit` → no type errors.
16. **Content registry**: All tooltip strings come from `tooltip-content.ts` — no inline strings in components.
