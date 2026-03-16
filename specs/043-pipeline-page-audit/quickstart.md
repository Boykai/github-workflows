# Quickstart: Pipeline Page Audit

**Feature**: `043-pipeline-page-audit` | **Date**: 2026-03-16

## Prerequisites

- Node.js 20+ with npm
- Python 3.12+ (for backend, if running full stack)
- GitHub personal access token (for API integration)

## Setup

```bash
# Clone and install frontend dependencies
cd solune/frontend
npm install

# Verify tests pass before making changes
npx vitest run

# Verify type checking passes
npm run type-check

# Verify linting passes
npm run lint
```

## Development Workflow

```bash
# Start frontend dev server
cd solune/frontend
npm run dev

# In a separate terminal, start backend (optional, for full API testing)
cd solune/backend
pip install -e ".[dev]"
uvicorn src.main:app --reload --port 8000
```

## Audit Checklist by Priority

### P1: Bug-Free Page States (User Story 1)

- [ ] Loading state displays CelestialLoader — no blank screen
- [ ] No-project-selected shows ProjectSelectionEmptyState
- [ ] Empty pipeline board shows meaningful empty state with CTA
- [ ] Save errors show user-friendly messages (FR-004 format)
- [ ] Rate limit errors detected and displayed specifically (FR-005)
- [ ] Deleted pipeline handled gracefully without crash
- [ ] Each section (pipeline list, assignment, analytics) has independent error states (FR-006)

### P1: Accessibility (User Story 2)

- [ ] All interactive elements reachable via Tab with visible focus indicator
- [ ] Saved workflow cards are proper interactive elements, not styled divs (FR-026)
- [ ] All dialogs trap focus, close on Escape, return focus to trigger (FR-014)
- [ ] Status indicators use icon + text, not color alone (FR-015)
- [ ] All form inputs have labels or aria-label (FR-016)
- [ ] Execution mode toggle has proper ARIA attributes
- [ ] Validation errors programmatically associated with inputs

### P2: Consistent UX (User Story 3)

- [ ] All visual elements use Celestial design tokens — no hardcoded colors
- [ ] All text is final meaningful copy — no placeholders (FR terminology)
- [ ] Consistent terminology ("pipeline" not "workflow" in user-facing text)
- [ ] All destructive actions require confirmation dialog (FR-007)
- [ ] All mutations provide success feedback (FR-008)
- [ ] Light/dark mode switching works correctly for all elements
- [ ] Long text truncated with ellipsis + tooltip (FR-018)
- [ ] Button labels are verb phrases (FR-019)
- [ ] Timestamps use relative format for recent

### P2: Editing Guards (User Story 4)

- [ ] Unsaved changes guard activates on navigation away (FR-009)
- [ ] Browser beforeunload warning on tab close (FR-009)
- [ ] Unsaved changes guard on loading different pipeline (FR-009)
- [ ] Unsaved changes guard on creating new pipeline (FR-009)
- [ ] Dialog offers Save/Discard/Cancel (FR-010)
- [ ] Discard reverts to last saved snapshot
- [ ] Save from dialog continues pending action on success
- [ ] Name conflict error handled with user-friendly message (FR-012)

### P2: Responsive Layout (User Story 5)

- [ ] Desktop (1920px): effective use of space
- [ ] Standard laptop (1280px): all sections visible and functional
- [ ] Minimum width (768px): sections stack, controls accessible
- [ ] Smooth layout transitions across breakpoints

### P3: Code Quality (User Story 6)

- [ ] Page file ≤250 lines (FR-021) — currently 417 lines
- [ ] No prop drilling >2 levels (FR-022)
- [ ] All data fetching via React Query (FR-023)
- [ ] Zero linting warnings (FR-024)
- [ ] Zero type errors (FR-024)
- [ ] Key interactive components have test files (FR-025)
- [ ] No `any` types, no unsafe type assertions
- [ ] No dead code, unused imports, console.log

## Running Tests

```bash
# Run all pipeline-related tests
cd solune/frontend
npx vitest run src/components/pipeline/ src/hooks/usePipeline* src/pages/AgentsPipelinePage*

# Run with coverage
npx vitest run --coverage src/components/pipeline/

# Run lint on pipeline files
npx eslint src/pages/AgentsPipelinePage.tsx src/components/pipeline/ src/hooks/usePipeline*

# Run type check
npm run type-check

# Run full test suite
npx vitest run
```

## Accessibility Testing Tools

```bash
# Automated a11y audit (if jest-axe is configured)
npx vitest run --grep "a11y\|accessibility\|axe"

# Manual testing:
# 1. Tab through entire Pipeline page — every interactive element reachable
# 2. Activate elements with Enter/Space
# 3. Open dialogs — verify focus trapping and Escape behavior
# 4. Use browser DevTools > Accessibility inspector
# 5. Chrome: Lighthouse > Accessibility audit
# 6. Chrome: axe DevTools extension
# 7. Chrome: Rendering > Emulate vision deficiencies
```

## Key Files to Audit

| Priority | File | Lines | Description |
|----------|------|-------|-------------|
| HIGH | `src/pages/AgentsPipelinePage.tsx` | ~417 | Main page — needs extraction to ≤250 lines |
| HIGH | `src/hooks/usePipelineBoardMutations.ts` | ~418 | Largest hook — verify all mutations handle errors |
| HIGH | `src/components/pipeline/StageCard.tsx` | ~362 | Complex component — verify a11y and decomposition |
| HIGH | `src/components/pipeline/PipelineBoard.tsx` | ~299 | Board grid — verify empty/error states |
| HIGH | `src/components/pipeline/PipelineAnalytics.tsx` | ~295 | Dashboard — verify independent error handling |
| HIGH | `src/components/pipeline/ModelSelector.tsx` | ~290 | Dropdown — verify keyboard nav and ARIA |
| MEDIUM | `src/components/pipeline/SavedWorkflowsList.tsx` | ~237 | List — verify cards are interactive elements |
| MEDIUM | `src/components/pipeline/PipelineFlowGraph.tsx` | ~235 | Graph — verify dark mode and responsiveness |
| MEDIUM | `src/hooks/usePipelineConfig.ts` | ~232 | Orchestrator — verify error handling |
| MEDIUM | `src/components/pipeline/ExecutionGroupCard.tsx` | ~223 | Group — verify mode toggle a11y |
| MEDIUM | `src/components/pipeline/PipelineToolbar.tsx` | ~172 | Toolbar — verify button labels and states |
| LOW | `src/hooks/usePipelineReducer.ts` | ~115 | State machine — verify transitions |
| LOW | `src/hooks/usePipelineModelOverride.ts` | ~98 | Model derivation — verify mode logic |
| LOW | `src/components/pipeline/PipelineModelDropdown.tsx` | ~117 | Dropdown variant |
| LOW | `src/components/pipeline/UnsavedChangesDialog.tsx` | ~69 | Dialog — verify focus management |
| LOW | `src/components/pipeline/PresetBadge.tsx` | ~55 | Badge — verify a11y |
| LOW | `src/hooks/usePipelineValidation.ts` | ~38 | Validation — may need extension |
| LOW | `src/components/pipeline/ParallelStageGroup.tsx` | ~30 | Layout wrapper |

## Design Token Reference

Key custom classes from `frontend/src/index.css`:

| Class | Usage |
|-------|-------|
| `.celestial-panel` | Content section containers |
| `.moonwell` | Recessed content areas |
| `.solar-chip` | Status badges and chips |
| `.nebula-glow` | Highlight effects |
| `.celestial-focus` | Focus indicator styles |
| `.glass-panel` | Transparent overlay panels |

Tailwind theme variables (use via `bg-*`, `text-*`, `border-*`):
- `background`, `foreground` — page base
- `card`, `card-foreground` — card surfaces
- `muted`, `muted-foreground` — secondary content
- `primary`, `primary-foreground` — primary actions
- `destructive`, `destructive-foreground` — destructive actions
- `border` — border colors
- `ring` — focus ring colors

## Output

After completing the audit, the following should be true:

1. `npx eslint src/pages/AgentsPipelinePage.tsx src/components/pipeline/ src/hooks/usePipeline*` — **0 warnings**
2. `npm run type-check` — **0 type errors** in pipeline-related files
3. `npx vitest run` — **all tests pass**
4. Browser: Pipeline page renders correctly in light mode, dark mode, at 768px, 1280px, and 1920px
5. Keyboard: All interactive elements reachable via Tab, activatable via Enter/Space
6. All user-visible text is final, meaningful copy with consistent terminology
7. All destructive actions require confirmation
8. All mutations provide success feedback
9. Page file is ≤250 lines with extracted sub-components
