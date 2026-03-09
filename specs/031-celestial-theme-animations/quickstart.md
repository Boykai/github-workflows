# Quickstart: Frontend Style Audit & Celestial/Cosmic Theme Animation Enhancement

**Feature**: 031-celestial-theme-animations | **Date**: 2026-03-09

## Prerequisites

- Node.js (latest LTS)
- Repository cloned with `frontend/` directory accessible
- Working knowledge of Tailwind CSS v4, React 19, and CSS custom properties

## Development Setup

```bash
cd frontend
npm install
npm run dev     # Start Vite dev server
```

## Implementation Phases

### Phase 1: Extend Design Token System (index.css)

**Goal**: Add new tokens, keyframes, and utility classes needed for the feature.

**Files**: `frontend/src/index.css`

1. Add `--transition-theme-shift` and `--animate-celestial-loader` tokens to `@theme` block
2. Add `theme-shift` keyframe to `@theme` block
3. Add `.theme-transitioning` utility class and `::after` overlay to `@layer base`
4. Update `@media (prefers-reduced-motion: reduce)` block to include new classes

**Verification**:
```bash
npm run build   # Ensure CSS compiles without errors
```

### Phase 2: Create CelestialLoader Component

**Goal**: Build the reusable celestial-themed loading component.

**Files**: `frontend/src/components/common/CelestialLoader.tsx`

1. Create component with `size`, `label`, `className` props
2. Render orbital animation using existing CSS classes (`celestial-orbit-spin-fast`, `celestial-pulse-glow`)
3. Include `role="status"` and `aria-label` for accessibility
4. Export from component file

**Verification**:
```bash
npm run type-check   # TypeScript compilation
npm run lint         # ESLint check
```

### Phase 3: Update ThemeProvider for Smooth Transitions

**Goal**: Add cosmic gradient transition effect when toggling themes.

**Files**: `frontend/src/components/ThemeProvider.tsx`

1. In the `setTheme` function (inside `useEffect`), add `theme-transitioning` class before toggling
2. Set 600ms `setTimeout` to remove the class
3. Clean up timeout on component unmount

**Verification**:
- Toggle theme in the app and observe smooth gradient overlay
- Enable `prefers-reduced-motion: reduce` in dev tools and verify instant switch (no animation)

### Phase 4: UI Primitives Audit (components/ui/)

**Goal**: Ensure base UI components use design tokens and celestial animation classes.

**Files**: `button.tsx`, `card.tsx`, `input.tsx`, `tooltip.tsx`, `confirmation-dialog.tsx`

1. Add `celestial-focus` class to button and input focus states
2. Add `solar-action` class to primary button hover states
3. Add `celestial-panel` and `celestial-fade-in` to card component
4. Add `celestial-fade-in` to confirmation dialog
5. Audit all hard-coded color/spacing values → replace with tokens

**Verification**:
```bash
npm run test         # Existing UI component tests still pass
npm run type-check
```

### Phase 5: Component-by-Component Audit (by directory)

**Goal**: Systematically audit each component directory for token compliance, text casing, and animation application.

**Order of directories** (dependencies first):
1. `layout/` — Sidebar, TopBar, Breadcrumb (already partially themed)
2. `pages/` — All 9 page components
3. `components/board/` — Board, columns, cards
4. `components/agents/` — Agent cards, panels, modals
5. `components/chat/` — Chat interface, messages, toolbar
6. `components/pipeline/` — Pipeline board, nodes, stages
7. `components/chores/` — Chore cards, panels, modals
8. `components/settings/` — Settings sections, preferences
9. `components/tools/` — Tool cards, panels, modals
10. `components/common/` — Shared components

**Per-component checklist**:
- [ ] No hard-coded colors (`#hex`, `rgb()`, arbitrary `hsl()`) — use design tokens
- [ ] No hard-coded spacing outside Tailwind scale
- [ ] No hard-coded border-radius — use `rounded-sm/md/lg` or token
- [ ] No hard-coded shadows — use `shadow-sm/default/md/lg`
- [ ] Headings use Title Case
- [ ] Body/descriptions use sentence case
- [ ] Badges/labels use ALL CAPS (`uppercase` class)
- [ ] Interactive elements have `celestial-focus` for focus ring
- [ ] Cards/panels have `celestial-panel` for hover effect
- [ ] Buttons have `solar-action` for hover enhancement (where appropriate)
- [ ] Entry animations use `celestial-fade-in` (where appropriate)
- [ ] Add inline comment documenting changes made

**Verification**:
```bash
npm run test         # All tests pass after each directory
npm run lint
npm run type-check
```

### Phase 6: Replace Loading States

**Goal**: Replace generic loading indicators with `CelestialLoader`.

**Files**: All pages and components with Suspense fallbacks or loading states

1. Find all `Loading...` text and spinner SVGs
2. Replace with `<CelestialLoader size="md" label="Loading {context}…" />`
3. Import `CelestialLoader` in each affected file

**Verification**:
- Navigate through app and trigger loading states
- Verify orbital animation appears and is themed correctly
- Verify `prefers-reduced-motion` stops the animation

### Phase 7: Accessibility & Polish

**Goal**: Final accessibility verification and visual polish pass.

1. **Contrast audit**: Check all text against backgrounds in both themes using browser dev tools
2. **Focus audit**: Tab through every interactive element — verify `celestial-focus` glow ring
3. **Reduced motion**: Enable `prefers-reduced-motion: reduce` — verify all animations stop
4. **Keyboard navigation**: Verify all functionality works without mouse
5. **Mobile responsiveness**: Test all animations on small viewports
6. **Performance**: Check animation FPS in Performance tab — verify 30fps+ maintained

**Verification**:
```bash
npm run test:a11y    # Accessibility test suite
npm run build        # Production build succeeds
```

### Phase 8: Style Alignment Report

**Goal**: Document all changes in a structured report.

1. Create inline code comments in each modified file documenting changes
2. Generate summary of all changes organized by component directory

## Key Patterns

### Adding Celestial Hover to a Card Component

```tsx
// Before
<div className="rounded-lg border bg-card p-4 shadow-sm">

// After — add celestial-panel for hover glow + celestial-fade-in for entry
<div className="celestial-panel celestial-fade-in rounded-lg border border-border bg-card p-4 shadow-sm">
```

### Adding Celestial Focus to an Input

```tsx
// Before
<input className="rounded-md border border-input bg-background px-3 py-2 focus:ring-2 focus:ring-primary" />

// After — replace focus ring with celestial-focus
<input className="celestial-focus rounded-md border border-input bg-background px-3 py-2" />
```

### Fixing Text Casing

```tsx
// Before (inconsistent)
<h2>agent configuration</h2>
<p>Configure your Agent settings here</p>
<span className="badge">active</span>

// After (correct conventions)
<h2>Agent Configuration</h2>           {/* Title Case for headings */}
<p>Configure your agent settings here</p>  {/* Sentence case for descriptions */}
<span className="uppercase tracking-wider badge">ACTIVE</span>  {/* ALL CAPS for badges */}
```

### Replacing a Loading Spinner

```tsx
// Before
{isLoading && <div className="flex items-center gap-2"><Loader2 className="animate-spin" /> Loading...</div>}

// After
{isLoading && <CelestialLoader size="sm" label="Loading agents…" />}
```

## Verification Checklist

- [ ] All CSS compiles without errors (`npm run build`)
- [ ] All existing tests pass (`npm run test`)
- [ ] TypeScript compiles without errors (`npm run type-check`)
- [ ] ESLint passes (`npm run lint`)
- [ ] `CelestialLoader` renders correctly at all 3 sizes
- [ ] Theme toggle shows smooth cosmic gradient transition
- [ ] `prefers-reduced-motion: reduce` disables all animations
- [ ] All headings use Title Case
- [ ] All body text uses sentence case
- [ ] All badges/labels use ALL CAPS
- [ ] Focus rings visible on all interactive elements via keyboard
- [ ] No hard-coded color values in component files
- [ ] Card hover shows subtle glow lift
- [ ] Button hover shows solar lift effect
- [ ] Loading states show celestial orbital animation
- [ ] Star-field background visible in AppLayout
- [ ] Animations maintain 30fps+ (checked in dev tools Performance tab)
- [ ] WCAG AA contrast ratios maintained in both themes
- [ ] Inline code comments document changes per component
- [ ] Mobile responsiveness preserved
