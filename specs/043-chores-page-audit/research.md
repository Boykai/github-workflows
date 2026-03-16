# Research: Chores Page Audit — Modern Best Practices, Modular Design, and Zero Bugs

**Feature Branch**: `043-chores-page-audit`
**Date**: 2026-03-16

## Research Tasks

### R1: Component Decomposition Strategy for Oversized Files

**Decision**: Decompose the three oversized components (ChoresPanel at 543 lines, ChoreCard at 584 lines, AddChoreModal at 356 lines) into focused sub-components within `src/components/chores/`, each under 250 lines with a single clear responsibility.

**Rationale**: The spec mandates ≤250 lines per component file (FR-011). ChoresPanel contains search controls, sort controls, the chore grid, add-chore button, cleanup integration, and save-all logic — at least 4 extractable sections. ChoreCard bundles schedule display, action buttons (trigger, pause, delete), inline editor toggle, pipeline selector, AI enhancement toggle, and stats display — at least 5 extractable sections. AddChoreModal combines template selection, chat flow, auto-merge confirmation, and form validation — at least 3 extractable sections. Each extracted sub-component should be placed in `src/components/chores/` following existing naming conventions (PascalCase `.tsx`).

**Alternatives Considered**:

- Leaving large files intact with clear section comments — Rejected because the spec explicitly requires ≤250 lines per file (FR-011), and large files increase merge conflict risk and reduce maintainability
- Extracting into a nested folder structure (`chores/ChoreCard/`) — Rejected because the existing convention is flat files within `src/components/chores/` with no nested component folders

**Proposed Decomposition**:

**ChoresPanel.tsx** (543 → ~150 main + sub-components):
- `ChoresToolbar.tsx` — Search input, sort controls, add-chore button
- `ChoresGrid.tsx` — Grid layout rendering ChoreCard items
- `ChoresSaveAllBar.tsx` — Save-all action bar for batch dirty edits
- Main `ChoresPanel.tsx` — Composition of above with state management

**ChoreCard.tsx** (584 → ~180 main + sub-components):
- `ChoreCardActions.tsx` — Trigger, pause/resume, delete action buttons
- `ChoreCardHeader.tsx` — Name, status badge, template path
- `ChoreCardStats.tsx` — Execution count, last triggered, next checkpoint
- `ChoreCardSettings.tsx` — Schedule config, pipeline selector, AI toggle
- Main `ChoreCard.tsx` — Composition of above sections

**AddChoreModal.tsx** (356 → ~180 main + sub-components):
- `TemplateSelector.tsx` — Template list with search and selection
- `ChoreCreationForm.tsx` — Name input, content editor, submission
- Main `AddChoreModal.tsx` — Modal shell with step flow

---

### R2: Celestial Design System Token Compliance for Chores Page

**Decision**: All Chores page components must exclusively use CSS custom properties defined in `frontend/src/index.css` via the Tailwind v4 `@theme` block and custom utility classes. No hardcoded hex/rgb/hsl values should appear in component code.

**Rationale**: The Celestial design system defines a comprehensive token set covering colors (`--color-background`, `--color-primary`, `--color-muted-foreground`, etc.), spacing (Tailwind's default scale), typography (`--font-display`, `--font-sans`), shadows (`--shadow-sm` through `--shadow-lg`), radii (`--radius-sm`, `--radius-md`, `--radius-lg`), and motion (`--transition-cosmic-*`). Both light and dark themes are supported by applying `.light` / `.dark` classes to the `<html>` element via the ThemeProvider, with HSL-based token overrides. Using these tokens ensures visual consistency across pages and automatic theme switching support.

**Alternatives Considered**:

- Creating a separate design token JSON file — Rejected because Tailwind v4's native `@theme` block already serves this purpose and is the established convention
- Using CSS-in-JS for theming — Rejected because the project uses Tailwind CSS exclusively with utility classes and the `cn()` helper

**Key Tokens to Audit Against**:

- Colors: `primary`, `secondary`, `muted`, `accent`, `destructive`, `background`, `foreground`, `border`, `card`, `panel`, `popover`, `glow`, `gold`, `night`
- Custom CSS classes: `.celestial-panel`, `.celestial-fade-in`, `.moonwell`, `.solar-chip`, `.solar-chip-*`
- Spacing: Tailwind standard scale (`gap-4`, `p-6`) — no arbitrary values like `p-[13px]`

---

### R3: Accessibility Best Practices for Chores Page Interactive Elements

**Decision**: Follow WAI-ARIA Authoring Practices for all interactive elements on the Chores page, ensuring keyboard navigability, screen reader announcements, proper focus management in modals, and WCAG AA contrast compliance.

**Rationale**: WCAG AA requires that all interactive content be operable via keyboard (2.1.1), has visible focus indicators (2.4.7), has appropriate names and roles (4.1.2), and meets contrast ratios (1.4.3 normal text 4.5:1, 1.4.11 UI components 3:1). The Chores page has complex interactive elements — inline editors (ChoreInlineEditor), schedule configuration modals (ChoreScheduleConfig), pipeline selector popups (PipelineSelector), confirmation dialogs (ConfirmChoreModal), filter controls, toggle switches (status, AI enhance), and chat flows (ChoreChatFlow) — that all require careful keyboard and screen reader support.

**Alternatives Considered**:

- Using a dedicated accessibility testing library like axe-core during development — Recommended as supplementary; focus on manual keyboard testing and ARIA compliance
- Implementing full WAI-ARIA grid pattern for the chore catalog — Rejected as overly complex; the catalog uses a simpler grid-of-cards pattern

**Key Accessibility Audit Points**:

1. **Focus management**: AddChoreModal and ConfirmChoreModal must trap focus and return focus on close
2. **Keyboard navigation**: All buttons, toggles, selectors, and inline editors must be reachable via Tab; modals must support Escape to close
3. **ARIA labels**: PipelineSelector dropdown, schedule type selector, status toggles, AI enhancement toggles need complete ARIA labeling
4. **Contrast ratios**: Verify all `text-muted-foreground` variants meet minimum 4.5:1 against their backgrounds
5. **Focus indicators**: Ensure `celestial-focus` class or `focus-visible:ring-*` classes are present on all interactive elements
6. **Status not color-only**: Chore status badges (active/paused), schedule indicators, and trigger states must communicate via icon + text

---

### R4: Data Fetching and Query Key Patterns for Chores

**Decision**: The existing `useChores.ts` hook already follows TanStack React Query patterns with proper `choreKeys` factory. Audit should verify staleTime configuration, mutation error handling with user feedback, and absence of duplicate API calls between parent/child components.

**Rationale**: The Chores page fetches from multiple endpoints: chores list, templates, board data (for parent issue count), pipeline options, and polls evaluate-triggers every 60 seconds. The `useChores.ts` hook provides 11 exports covering queries and mutations. The `choreKeys` factory follows the established `[feature].all / .list(id)` convention. Key areas to audit include: whether all mutations have `onError` handlers with toast/inline feedback (FR-015), whether `staleTime` is configured appropriately, whether the evaluate-triggers polling is efficient, and whether any data is fetched redundantly.

**Alternatives Considered**:

- Moving to a different state management pattern (Zustand, signals) — Rejected; TanStack Query is the established pattern and works well for the Chores page
- Adding optimistic updates for all mutations — Considered for create/delete operations but query invalidation is simpler and sufficient for the current use case

**Key Data Fetching Audit Points**:

1. **Query keys**: Verify `choreKeys.all`, `choreKeys.list(projectId)`, `choreKeys.templates(projectId)` follow convention
2. **staleTime**: Chores list should have reasonable staleTime (30s); templates can be longer (60s)
3. **Mutation error handling**: All 8 mutations (`useCreateChore`, `useUpdateChore`, `useDeleteChore`, `useTriggerChore`, `useChoreChat`, `useInlineUpdateChore`, `useCreateChoreWithAutoMerge`, seed presets) need `onError` with user-visible feedback
4. **Duplicate calls**: Verify chores list is fetched once at ChoresPanel level and not again in ChoreCard children
5. **Polling efficiency**: evaluate-triggers polling (60s) should respect component unmount

---

### R5: Responsive Design Patterns for Chore Catalog Layout

**Decision**: Use Tailwind's responsive prefixes (`sm:`, `md:`, `lg:`) to adapt the Chores page layout across three breakpoints: desktop (1280px+), tablet (768px–1279px), and mobile (below 768px). The chore catalog grid should reduce columns and stack vertically on smaller screens.

**Rationale**: The Chores page uses a catalog-style grid layout with ChoreCard items, a FeaturedRitualsPanel spotlight section, a CelestialCatalogHero header, and toolbar controls. The grid must reflow correctly at different breakpoints — from 3-4 columns on desktop to 2 on tablet to 1 on mobile. Touch targets must be at minimum 44×44px on touch screens per WCAG 2.5.5. The inline editor (ChoreInlineEditor) must remain usable on smaller screens.

**Alternatives Considered**:

- Using a completely different layout for mobile (e.g., list view) — Deferred as future enhancement; audit focuses on ensuring the current card layout adapts correctly
- Using CSS Container Queries instead of viewport breakpoints — Rejected; Tailwind breakpoints are the established convention

**Key Responsive Audit Points**:

1. **Chore catalog grid**: Needs responsive column count (3-4 desktop, 2 tablet, 1 mobile)
2. **FeaturedRitualsPanel**: Three-card spotlight should wrap on smaller screens
3. **ChoreCard actions**: Trigger, edit, delete buttons need adequate touch targets on mobile
4. **Modals**: AddChoreModal, ConfirmChoreModal, and ChoreScheduleConfig must be full-width on mobile
5. **Toolbar**: Search input and sort controls should stack vertically on mobile

---

### R6: Error Handling and Edge Case Patterns for Chores Page

**Decision**: Each data section on the Chores page must handle its own loading, error, and empty states independently. Error messages must follow the "Could not [action]. [Reason]. [Next step]." format per FR-017. All destructive actions must use `ConfirmationDialog` per FR-016.

**Rationale**: The Chores page has multiple independent data sources: chores list, chore templates, board data (for parent issue count), pipeline options, and evaluate-triggers polling. A failure in one should not block others (FR-003). Current implementation needs audit for: seed-presets error handling, evaluate-triggers polling error handling, template loading in AddChoreModal, and inline update errors.

**Alternatives Considered**:

- Implementing a global error boundary for all Chores errors — Already exists at app level; page-level inline error handling is more informative
- Using toast-only error handling — Rejected for errors that block the view; inline banners provide persistent visibility

**Key Error Handling Audit Points**:

1. **Chores list loading failure**: Should show error state with retry
2. **Rate limit detection**: Must use `isRateLimitApiError()` for specific handling
3. **Seed presets failure**: Should not crash the page; log and continue
4. **Trigger mutation rapid-click**: Button should be disabled during mutation (edge case from spec)
5. **Inline update conflict**: File SHA mismatch should show clear conflict message
6. **Partial save failure**: "Save All" should indicate which saves succeeded and which failed
7. **Chat flow network error**: ChoreChatFlow should allow retry without losing context

---

## Research Summary

| Topic | Status | Key Finding |
|-------|--------|-------------|
| Component decomposition | ✅ Resolved | 3 files exceed 250 lines; decompose ChoresPanel, ChoreCard, AddChoreModal into focused sub-components |
| Design system tokens | ✅ Resolved | Comprehensive Celestial token set in `index.css`; audit for hardcoded values |
| Accessibility (WCAG AA) | ✅ Resolved | Complex interactive elements (modals, toggles, selectors, inline editors) need focus management, ARIA labels, and keyboard nav audit |
| Data fetching patterns | ✅ Resolved | TanStack Query well-established; audit mutation error handlers, staleTime, and duplicate call prevention |
| Responsive design | ✅ Resolved | Three breakpoints; catalog grid needs responsive columns; touch targets need validation |
| Error handling | ✅ Resolved | Multiple data sources need independent error states; destructive actions need confirmation dialogs |

All NEEDS CLARIFICATION items have been resolved through codebase analysis. No external research dependencies remain.
