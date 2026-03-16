# Quickstart: Pipeline Page Audit

**Feature Branch**: `043-pipeline-page-audit`
**Date**: 2026-03-16

## Prerequisites

- Node.js 20+ and npm
- Python 3.12+ and `uv` (for backend, if running locally)
- A GitHub token configured in `.env` for API access

## Setup

```bash
# Clone and checkout
git checkout 043-pipeline-page-audit

# Install frontend dependencies
cd solune/frontend
npm install

# Verify existing tests pass
npx vitest run
npm run lint
npm run type-check
```

## Development Workflow

### 1. Run the Frontend Dev Server

```bash
cd solune/frontend
npm run dev
```

The Pipeline page is available at `http://localhost:5173/pipeline` (or the port shown in terminal).

### 2. Run the Backend (if testing with live data)

```bash
cd solune/backend
uv run --extra dev uvicorn src.main:app --reload --port 8000
```

### 3. Audit Checklist

Work through the audit in priority order matching the spec:

#### P1: Bug-Free and Complete Page States (User Story 1)

- [ ] Test loading state — CelestialLoader while pipeline data fetches, never a blank screen
- [ ] Test no-project-selected state — ProjectSelectionEmptyState renders correctly
- [ ] Test empty pipeline board — empty state with "Create Pipeline" CTA and illustrative icon
- [ ] Test populated board — stages, agent nodes, execution groups render correctly
- [ ] Test save error — user-friendly message "Could not save pipeline. [Reason]. [Next step]."
- [ ] Test rate limit error — specific rate-limit message with retry guidance using `isRateLimitApiError()`
- [ ] Test deleted pipeline fallback — graceful handling when selected pipeline is deleted externally
- [ ] Test partial section failures — pipeline list, assignment, and analytics fail independently
- [ ] Test rapid save clicks — save button disabled during `isSaving` state

#### P1: Accessible Pipeline Page (User Story 2)

- [ ] Tab through all interactive elements — toolbar buttons, stage name inputs, agent picker, model selector, saved workflow cards, analytics
- [ ] Verify visible focus indicators on every interactive element (`.celestial-focus` or `focus-visible:ring-*`)
- [ ] Add `aria-expanded` to ModelSelector and PipelineModelDropdown triggers
- [ ] Add `role="listbox"` to ModelSelector and PipelineModelDropdown option lists
- [ ] Add `role="region"` with `aria-label` to PipelineAnalytics section
- [ ] Add `role="img"` with `aria-label` to PipelineFlowGraph (or `aria-hidden` if decorative)
- [ ] Add `aria-label` to inline stage name edit inputs in StageCard
- [ ] Verify focus trap in UnsavedChangesDialog and PipelineToolbar copy dialog
- [ ] Verify focus restoration on dialog/modal close
- [ ] Test Escape key on all dropdowns (ModelSelector, PipelineModelDropdown) and dialogs
- [ ] Verify screen reader announces saved workflow card content (name, stage count, status)
- [ ] Run contrast checker on all `text-muted-foreground` with opacity reductions

#### P2: Consistent and Polished User Experience (User Story 3)

- [ ] Compare typography, spacing, color usage against other pages (Agents, Projects, Settings)
- [ ] Verify all text is final meaningful copy — no "TODO", "Lorem ipsum", placeholder text
- [ ] Verify consistent terminology — "pipeline" not "workflow" in user-facing text, "stage" not "step"
- [ ] Verify all destructive actions use confirmation dialog — delete pipeline, remove stage, remove agent, discard changes
- [ ] Verify success feedback for save, create, duplicate, delete operations
- [ ] Test light mode and dark mode — all elements render correctly in both themes
- [ ] Replace `text-white` and `bg-red-500` in PipelineToolbar notification badge with design tokens
- [ ] Verify long text truncation with tooltip — pipeline names, agent names, model names
- [ ] Verify timestamps use relative format for recent, absolute for older
- [ ] Verify action button labels are verb phrases — "Save Pipeline", "Delete Pipeline", "Discard Changes"

#### P2: Reliable Pipeline Editing and Navigation Guards (User Story 4)

- [ ] Test unsaved changes + navigate away → confirmation dialog appears
- [ ] Test unsaved changes + close browser tab → native warning displayed
- [ ] Test unsaved changes + load different pipeline → confirmation dialog before loading
- [ ] Test unsaved changes + create new pipeline → confirmation dialog before creating
- [ ] Test "Discard" in dialog → state reverts to last saved snapshot, no residual dirty state
- [ ] Test "Save" in dialog → save completes, pending action continues
- [ ] Test pipeline name conflict on save → clear error message identifying the conflict

#### P2: Responsive Layout (User Story 5)

- [ ] Test at 1920px (large desktop) — layout uses space effectively
- [ ] Test at 1280px (standard laptop) — all sections visible, stage board adapts
- [ ] Test at 768px (minimum supported) — sections stack, stage board scrollable, all controls accessible
- [ ] Test browser resize transitions — no broken intermediate states
- [ ] Verify pipeline flow graph scales at different viewport widths
- [ ] Verify no horizontal scrolling at supported widths (768px+)
- [ ] Verify toolbar controls remain accessible at narrow widths

#### P3: Maintainable and Well-Tested Pipeline Code (User Story 6)

- [ ] Review AgentsPipelinePage.tsx line count (currently 417 — target ≤250 via extraction)
- [ ] Review prop drilling depth — verify no props drilled >2 levels
- [ ] Verify all hooks have explicit or inferrable return types, no `any` types
- [ ] Verify no unsafe type assertions (`as`) in pipeline-related code
- [ ] Run linter on all pipeline files — zero warnings
- [ ] Run type checker — zero errors in pipeline-related files
- [ ] Verify existing tests pass and cover key interactive components

### 4. Running Tests

```bash
# All tests
cd solune/frontend && npx vitest run

# Pipeline-specific tests only
npx vitest run --reporter=verbose PipelineBoard StageCard AgentNode SavedWorkflowsList PipelineFlowGraph usePipelineConfig usePipelineReducer useSelectedPipeline

# Type checking
npm run type-check

# Linting
npm run lint
```

### 5. Accessibility Scanning

```bash
# jest-axe is available — add axe tests to verify components
# Example in test:
# import { axe, toHaveNoViolations } from 'jest-axe'
# expect(await axe(container)).toHaveNoViolations()
```

## Key Files Reference

| File | Lines | Purpose |
|------|-------|---------|
| `pages/AgentsPipelinePage.tsx` | 417 | Main page — pipeline editor layout |
| `pipeline/PipelineBoard.tsx` | 299 | Stage grid canvas |
| `pipeline/StageCard.tsx` | 362 | Stage card with inline editing, agent picker |
| `pipeline/ExecutionGroupCard.tsx` | 223 | Execution group with mode toggle |
| `pipeline/AgentNode.tsx` | 187 | Agent node with model selection |
| `pipeline/ModelSelector.tsx` | 290 | Agent-level model dropdown |
| `pipeline/PipelineAnalytics.tsx` | 295 | Analytics dashboard |
| `pipeline/SavedWorkflowsList.tsx` | 237 | Saved pipelines list |
| `pipeline/PipelineToolbar.tsx` | 172 | Save/create/copy/delete toolbar |
| `pipeline/PipelineFlowGraph.tsx` | 235 | Visual flow diagram |
| `pipeline/PipelineModelDropdown.tsx` | 117 | Pipeline-level model override |
| `pipeline/UnsavedChangesDialog.tsx` | 69 | Unsaved changes confirmation |
| `hooks/usePipelineConfig.ts` | 232 | Primary pipeline orchestration hook |
| `hooks/usePipelineBoardMutations.ts` | 418 | Board-level CRUD mutations |
| `hooks/usePipelineReducer.ts` | 115 | Pipeline state reducer |
| `hooks/usePipelineModelOverride.ts` | 98 | Model override derivation |
| `hooks/usePipelineValidation.ts` | 38 | Validation state management |

## PR Guidelines

- Reference the spec: `specs/043-pipeline-page-audit/spec.md`
- Organize commits by user story priority (P1 first, then P2, then P3)
- Each commit should address one component or one category of fix
- Run `npx vitest run` before each PR update to verify no regressions
- Include before/after screenshots for visual changes
