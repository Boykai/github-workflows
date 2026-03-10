# Quickstart: Audit Pipelines Page for UI Consistency, Quality & UX

**Feature**: 033-audit-pipelines-ux | **Date**: 2026-03-10

## Prerequisites

- Node.js 20+ and npm
- Python 3.13+
- The repository cloned and on the feature branch

```bash
git checkout 033-audit-pipelines-ux
```

## Setup

### Backend

```bash
cd backend
pip install -e ".[dev]"
# Database migrations run automatically on startup
uvicorn src.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# App available at http://localhost:5173
```

## Files to Modify

### PIPE-004: Validation Accessibility

| File | Changes |
|------|---------|
| `frontend/src/components/pipeline/PipelineBoard.tsx` | Add `aria-invalid`, `aria-describedby`, and `id` on error paragraph for both compact and full layout name inputs |

### PIPE-005: Skeleton Upgrade

| File | Changes |
|------|---------|
| `frontend/src/components/pipeline/SavedWorkflowsList.tsx` | Replace generic pulse blocks with structured card skeletons using `celestial-panel`-aligned styling |

### PIPE-006: Activity Overflow

| File | Changes |
|------|---------|
| `frontend/src/pages/AgentsPipelinePage.tsx` | Add conditional overflow text with anchor link below Recent Activity section when pipeline count exceeds 3 |

### No Backend Changes Required

All audit findings are frontend-only. The backend API and data models are unchanged.

## Implementation Order

### Phase 1: PIPE-004 — Accessibility Remediation (Medium Severity)

1. **Open `PipelineBoard.tsx`** and locate the name input sections (compact layout ~line 124 and full layout ~line 218)

2. **Add ARIA attributes to both input instances**:
   - `aria-invalid={validationErrors.name ? "true" : undefined}`
   - `aria-describedby={validationErrors.name ? "pipeline-name-error" : undefined}`

3. **Add `id` to both error paragraph instances**:
   - `id="pipeline-name-error"` on the `<p>` element showing `validationErrors.name`

4. **Verify**:
   - Open the Pipelines page → create a new pipeline → clear the name → tab away
   - Inspect the input element: should have `aria-invalid="true"` and `aria-describedby="pipeline-name-error"`
   - Use a screen reader: error message should be announced when input receives focus

### Phase 2: PIPE-005 — Skeleton Visual Upgrade (Low Severity)

1. **Open `SavedWorkflowsList.tsx`** and locate the loading skeleton section (~line 61)

2. **Replace the flat `h-32` blocks** with structured card skeletons:
   - Use `rounded-[1.3rem]` to match loaded card border radius
   - Use `bg-card/80` background with `border-border/50`
   - Add placeholder shapes: name bar (h-4 w-2/3), description lines (h-3), stats row (h-3)

3. **Verify**:
   - Trigger a loading state (slow network or dev tools throttling)
   - Skeleton cards should preview the structure of the loaded cards
   - Transition from skeleton to loaded should feel smooth

### Phase 3: PIPE-006 — Activity Overflow Indicator (Low Severity)

1. **Open `AgentsPipelinePage.tsx`** and locate the Recent Activity section

2. **Add conditional overflow text** after the `.slice(0, 3).map()`:
   - Show "Showing 3 of {total} — see all in Saved Pipelines" when count > 3
   - "Saved Pipelines" links to `#saved-pipelines`
   - Style: `text-xs text-muted-foreground`

3. **Verify**:
   - Create more than 3 pipelines
   - The overflow text should appear below the recent activity cards
   - Clicking "Saved Pipelines" should scroll to the saved pipelines section

## Validation Commands

### Lint

```bash
cd frontend
npm run lint
```

### Type Check

```bash
cd frontend
npm run type-check
```

### Tests

```bash
cd frontend
npm run test
```

### Targeted Tests

```bash
cd frontend
npx vitest run src/components/pipeline/PipelineBoard.test.tsx
npx vitest run src/components/pipeline/SavedWorkflowsList.test.tsx
npx vitest run src/pages/AgentsPipelinePage.test.tsx
```

### Accessibility Audit

```bash
# Run jest-axe tests (included in existing test suite)
cd frontend
npx vitest run --grep "a11y\|accessibility\|axe"
```

## Audit Verification Checklist

After all remediation is complete, verify the full audit report:

- [ ] All 6 findings in `audit-report.md` are accounted for
- [ ] PIPE-001 (High): Fixed — hero CTA routes through `handleNewPipeline()`
- [ ] PIPE-002 (Medium): Fixed — `#saved-pipelines` section ID exists with `aria-labelledby`
- [ ] PIPE-003 (Medium): Fixed — long pipeline names show tooltip on hover/focus
- [ ] PIPE-004 (Medium): Remediated — name input has `aria-invalid`/`aria-describedby`
- [ ] PIPE-005 (Low): Remediated — skeleton cards match loaded card structure
- [ ] PIPE-006 (Low): Remediated — overflow text with anchor link when count > 3
- [ ] No unexpected console errors in development mode
- [ ] `npm run lint` passes
- [ ] `npm run type-check` passes
- [ ] `npm run test` passes
