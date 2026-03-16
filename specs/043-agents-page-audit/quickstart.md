# Quickstart: Agents Page Audit

**Feature**: 043-agents-page-audit | **Date**: 2026-03-16

## Setup

```bash
git checkout 043-agents-page-audit
cd solune/frontend && npm install
npx vitest run && npm run lint && npm run type-check
npm run dev  # http://localhost:5173/agents
```

## File Map

### Page Entry Point
- `src/pages/AgentsPage.tsx` — 251 lines — Page orchestrator

### Catalog Components (`src/components/agents/`)
| File | Lines | Status | Action |
|------|-------|--------|--------|
| AgentsPanel.tsx | 565 | ❌ OVER | Decompose → AgentSearch, AgentSortControls, SpotlightSection, AgentList, PendingAgentsSection |
| AddAgentModal.tsx | 520 | ❌ OVER | Decompose → AgentForm, AgentFormFields, AgentToolsSection |
| AgentCard.tsx | 286 | ❌ OVER | Decompose → AgentCardActions, AgentCardMetadata |
| AgentInlineEditor.tsx | 272 | ❌ OVER | Decompose → AgentEditForm |
| AgentAvatar.tsx | 210 | ✅ OK | Verify a11y + dark mode |
| AgentChatFlow.tsx | 199 | ✅ OK | Verify error states |
| BulkModelUpdateDialog.tsx | 165 | ✅ OK | Verify confirmation + error handling |
| ToolsEditor.tsx | 132 | ✅ OK | Verify a11y + type safety |
| AgentIconPickerModal.tsx | 117 | ✅ OK | **Fix ARIA role** (role="dialog" + aria-modal) |
| AgentIconCatalog.tsx | 70 | ✅ OK | Verify keyboard navigation |

### Board Components (`src/components/board/`)
| File | Lines | Status | Action |
|------|-------|--------|--------|
| AgentPresetSelector.tsx | 519 | ❌ OVER | Decompose → PresetButtons, SavedPipelinesDropdown |
| AgentConfigRow.tsx | 480 | ❌ OVER | Decompose → ColumnMappingGrid, DnDOrchestrator |
| AgentTile.tsx | 295 | ❌ OVER | Decompose → ConstellationSVG, TileActions |
| AddAgentPopover.tsx | 208 | ✅ OK | Fix ARIA roles + design tokens |
| AgentColumnCell.tsx | 168 | ✅ OK | Add role="list" |
| AgentDragOverlay.tsx | 69 | ✅ OK | Verify dark mode |
| AgentSaveBar.tsx | 49 | ✅ OK | Add aria-live |

### Hooks (`src/hooks/`)
| File | Lines | Action |
|------|-------|--------|
| useAgentConfig.ts | 349 | Add staleTime, add tests |
| useAgents.ts | 108 | Configure staleTime (30s), add tests |
| useAgentTools.ts | 39 | Add tests if missing |

### Existing Tests
- `src/components/agents/__tests__/AddAgentModal.test.tsx`
- `src/components/agents/__tests__/AgentsPanel.test.tsx`
- `src/components/board/AgentSaveBar.test.tsx`
- `src/components/board/AgentTile.test.tsx`
- `src/components/common/ThemedAgentIcon.test.tsx`

## Audit Checklist (by Priority)

### P1 — Modular Component Architecture (US1)
- [ ] AgentsPanel.tsx ≤250 lines with sub-components extracted
- [ ] AddAgentModal.tsx ≤250 lines with form components extracted
- [ ] AgentCard.tsx ≤250 lines with actions/metadata extracted
- [ ] AgentInlineEditor.tsx ≤250 lines with form extracted
- [ ] AgentPresetSelector.tsx ≤250 lines with sub-components extracted
- [ ] AgentConfigRow.tsx ≤250 lines with grid/DnD extracted
- [ ] AgentTile.tsx ≤250 lines with SVG/actions extracted
- [ ] Complex state logic (>15 lines useState/useEffect) extracted into hooks
- [ ] useAvailableAgents separated from useAgentConfig (if combined)

### P1 — Loading, Error, and Empty States (US2)
- [ ] Loading state: CelestialLoader or skeleton for each data source
- [ ] Error state: User-friendly message + retry for API errors
- [ ] Rate limit: Detected via isRateLimitApiError() with specific message
- [ ] Empty state: Meaningful CTA when no agents exist
- [ ] Independent sections: One failure doesn't block other sections
- [ ] ErrorBoundary wraps page content

### P2 — Accessibility (US3)
- [ ] All interactive elements keyboard-accessible (Tab/Enter/Space)
- [ ] Focus trapped in dialogs/modals
- [ ] Focus returns to trigger on dialog close
- [ ] AgentIconPickerModal: Fix role="dialog" + aria-modal="true"
- [ ] AgentSaveBar: Add role="status" aria-live="polite"
- [ ] AgentConfigRow: Add role="region" aria-label
- [ ] AgentColumnCell: Add role="list", AgentTile: role="listitem"
- [ ] AddAgentPopover: Add role="listbox"/role="option"
- [ ] AgentPresetSelector: Add aria-expanded on dropdown
- [ ] All form fields have visible label or aria-label
- [ ] Status indicators use icon + text (not color alone)
- [ ] Focus-visible styles (celestial-focus or focus-visible:ring)

### P2 — Text, Copy, and UX Polish (US4)
- [ ] No placeholder text (TODO, Lorem ipsum, Test)
- [ ] Action buttons use verb labels ("Create Agent", "Delete Agent")
- [ ] All destructive actions use ConfirmationDialog
- [ ] Success feedback for all mutations (toast/inline)
- [ ] Error messages: "Could not [action]. [Reason]. [Suggestion]."
- [ ] Long text truncated with Tooltip
- [ ] Timestamps: relative for recent, absolute for older

### P3 — Styling and Responsive Layout (US5)
- [ ] No inline style={} — Tailwind only with cn()
- [ ] Responsive 768px–1920px without breaks
- [ ] Dark mode: No hardcoded colors (use dark: variants)
- [ ] Replace hardcoded colors: emerald, green, blue, amber → design tokens
- [ ] Consistent spacing (Tailwind scale only)
- [ ] Card component usage for content sections

### P3 — Test Coverage (US6)
- [ ] useAgents hook tests (renderHook with mock API)
- [ ] useAgentConfig hook tests (renderHook with mock API)
- [ ] useAgentTools hook tests (renderHook with mock API)
- [ ] AgentsPanel component test updates
- [ ] AddAgentModal component test updates
- [ ] AgentCard component tests
- [ ] Edge cases: empty, error, loading, rate limit, null data

### P3 — Performance and Code Hygiene (US7)
- [ ] Zero ESLint warnings on all agent files
- [ ] Zero any types or type assertions (as)
- [ ] No dead code (unused imports, commented blocks)
- [ ] No console.log statements
- [ ] All imports use @/ alias
- [ ] List keys use item.id (not index)
- [ ] Expensive computations in useMemo

## Validation Commands

```bash
# Lint
npx eslint src/pages/AgentsPage.tsx src/components/agents/ src/components/board/Agent*.tsx src/components/board/AddAgent*.tsx src/hooks/useAgent*.ts

# Type check
npm run type-check

# Tests
npx vitest run src/**/*agent* src/**/*Agent*

# All tests
npx vitest run

# Dev server
npm run dev
```

## Key Patterns

### Query Key Factory
```typescript
export const agentKeys = {
  all: ['agents'] as const,
  list: (projectId: string) => [...agentKeys.all, 'list', projectId] as const,
  pending: (projectId: string) => [...agentKeys.all, 'pending', projectId] as const,
};
```

### Error Message Format
```typescript
// FR-014: "Could not [action]. [Reason, if known]. [Suggested next step]."
toast.error(`Could not delete agent. ${error.message || 'Unknown error'}. Please try again.`);
```

### Mutation Pattern
```typescript
const mutation = useMutation({
  mutationFn: (data) => agentsApi.create(projectId, data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: agentKeys.all });
    toast.success('Agent created successfully');
  },
  onError: (error) => {
    if (isRateLimitApiError(error)) {
      toast.error('Rate limit reached. Please wait a moment and try again.');
    } else {
      toast.error(`Could not create agent. ${error.message}. Please try again.`);
    }
  },
});
```

### Component Decomposition Pattern
```typescript
// Before: AgentsPanel.tsx (565 lines)
// After:
// AgentsPanel.tsx (<=250 lines) — orchestrator
// AgentSearch.tsx — search input + filters
// AgentSortControls.tsx — sort buttons/dropdown
// SpotlightSection.tsx — featured agents grid
// AgentList.tsx — scrollable card list
// PendingAgentsSection.tsx — pending status cards
```
