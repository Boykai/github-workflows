# Research: Full Frontend Responsiveness & Mobile-Friendly Audit

**Feature**: 031-frontend-responsive-audit | **Date**: 2026-03-09

## R1: Mobile Navigation Pattern — Sidebar Drawer vs. Bottom Nav vs. Hamburger Menu

**Task**: Determine the best mobile navigation pattern for the existing sidebar-based navigation, given 7 navigation routes and a collapsible sidebar that currently always occupies screen space on mobile.

**Decision**: Convert the existing `Sidebar.tsx` into a mobile drawer overlay on viewports below 768px (`md:` breakpoint). On mobile, the sidebar is hidden by default and opens as a full-height slide-out drawer from the left, triggered by a hamburger menu icon (☰) in the `TopBar`. A semi-transparent backdrop behind the drawer dismisses it on tap. On tablet and desktop (≥768px), the sidebar retains its current collapsible behavior (toggle between 240px and 64px). The `useSidebarState` hook gains a `isMobileOpen` state and `openMobile`/`closeMobile` methods, with automatic close on route change via `useLocation`.

**Rationale**: The codebase already has a well-structured `Sidebar.tsx` with navigation items, project selector, recent interactions, and collapse logic. Converting it to a drawer on mobile (rather than building a separate mobile navigation component) ensures:

1. **DRY**: Navigation items, project selector, and recent interactions are defined once — no duplication between a mobile nav and desktop sidebar.
2. **Consistency**: Users see the same navigation structure across breakpoints, maintaining mental model.
3. **Simplicity**: One component handles both modes via CSS (`hidden md:flex` for desktop sidebar) and JavaScript state (`isMobileOpen` for drawer).
4. **Alignment with FR-003**: The hamburger + drawer pattern is the most widely recognized mobile navigation paradigm (Material Design, Apple HIG, Bootstrap, Tailwind UI all use this pattern).

The hamburger icon in TopBar is visible only on `<768px` via `md:hidden`. On `≥768px`, the existing sidebar toggle button controls the collapse state.

**Alternatives Considered**:

- **Bottom navigation bar**: Considered — works well for 3–5 top-level items. With 7 navigation routes plus project selector and recent interactions, a bottom bar would be overcrowded. Also violates the codebase's current visual language (no bottom nav exists in the celestial theme).
- **Separate `MobileNav` component**: Rejected — duplicates all navigation content from Sidebar.tsx. Maintaining parity between two navigation components across 7 routes + project selector + recent interactions is error-prone and violates DRY.
- **Always-visible collapsed sidebar on mobile (current behavior)**: Rejected — even collapsed, the sidebar consumes 64px of horizontal space on a 320px viewport, which is 20% of the screen width. This causes content cramping and potential horizontal overflow (violates FR-001).
- **Tab bar with "More" overflow**: Rejected — adds complexity for a non-standard pattern. The 7-item nav doesn't naturally group into primary (tab) and secondary (overflow) categories.

---

## R2: Responsive Breakpoint Token Strategy — CSS Custom Properties vs. Tailwind-Only

**Task**: Determine how to centralize responsive breakpoint values as tokens/variables per FR-009, given that Tailwind v4 uses implicit breakpoints with no explicit configuration file.

**Decision**: Define CSS custom properties in `frontend/src/index.css` within the existing `@theme` block for breakpoint values:

```css
@theme {
  --bp-xs: 320px;
  --bp-sm: 640px;
  --bp-md: 768px;
  --bp-lg: 1024px;
  --bp-xl: 1280px;
  --bp-2xl: 1440px;
}
```

Also define a TypeScript `BREAKPOINTS` constant in `frontend/src/constants.ts` for programmatic access:

```typescript
export const BREAKPOINTS = {
  xs: 320,
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1440,
} as const;
```

Tailwind class utilities (`sm:`, `md:`, `lg:`, etc.) remain the primary mechanism for responsive styles. The CSS custom properties serve as documentation and are available to JavaScript via `getComputedStyle`. The TypeScript constant is used by the `useMediaQuery` hook and E2E test viewport definitions.

**Rationale**: Tailwind v4 does not use a `tailwind.config.js` file — breakpoints are built-in defaults. Adding CSS custom properties creates a visible, documented, single source of truth for breakpoint values without fighting Tailwind's architecture. The TypeScript constant mirrors these values for JavaScript consumption (e.g., `useMediaQuery`, E2E viewport definitions). Both sources reference the same values, and a comment in `constants.ts` links to the CSS definitions. This satisfies FR-009 ("consistent responsive breakpoint tokens/variables across the codebase").

**Alternatives Considered**:

- **Tailwind v4 `@theme` breakpoint overrides**: Considered — Tailwind v4 supports `@theme { --breakpoint-sm: 640px; }` to override breakpoints. However, the default values are already correct for this project. Overriding them adds no value and risks breaking existing responsive classes if values are changed inadvertently.
- **JavaScript-only constants (no CSS properties)**: Rejected — CSS custom properties are accessible to both CSS (via `var()`) and JavaScript (via `getComputedStyle`), making them more versatile. JavaScript-only constants don't help with CSS-side media queries.
- **Design token JSON file**: Rejected — adds build-time processing complexity. The project has no design token pipeline. CSS custom properties + TypeScript constants are simpler and directly usable.

---

## R3: Touch Target Sizing Strategy — Utility Class vs. Component Variant

**Task**: Determine the best approach to ensure all interactive elements meet the 44×44px minimum touch target size on mobile (FR-002, WCAG 2.5.8).

**Decision**: Use a two-pronged approach:

1. **Add a `touch` size variant to the `Button` component** via CVA: `size: 'touch'` applies `min-h-[44px] min-w-[44px]` with appropriate padding. This variant is conditionally applied on mobile using `sm:size-default` pattern or via the `useMediaQuery` hook.

2. **Add a CSS utility class `.touch-target`** in `index.css` that applies `min-height: 44px; min-width: 44px;` and can be applied to any interactive element (links, icon buttons, menu items) that isn't a Button component.

3. **For icon-only buttons** (common in the codebase — delete, edit, settings icons), ensure the clickable area is at least 44×44px even if the visible icon is smaller. This is achieved by adding sufficient padding (`p-2.5` = 10px padding on a 24px icon = 44px total) or using the `.touch-target` utility.

**Rationale**: The codebase uses CVA-based `Button` component with existing size variants (`default`, `sm`, `lg`, `icon`). Adding a `touch` variant follows the established pattern. The CSS utility class handles non-Button interactive elements (links, menu items, custom components). The 44×44px minimum is the WCAG 2.5.8 Level AAA recommendation and the standard used by Apple HIG and Material Design. The approach is additive — it doesn't change existing desktop button sizes, only ensures mobile sizes meet the minimum.

**Alternatives Considered**:

- **Global minimum size on all buttons**: Rejected — would increase desktop button sizes unnecessarily. Many icon buttons in toolbars are intentionally compact on desktop. The mobile-specific approach preserves desktop aesthetics.
- **Wrapper component (`<TouchTarget>`)**: Rejected — adds a DOM element around every interactive target. The utility class approach is lighter and more idiomatic with Tailwind.
- **JavaScript-based resize on mobile**: Rejected — CSS-only solutions are simpler, more performant, and don't cause layout shift from JavaScript-driven resizing.

---

## R4: Modal and Drawer Mobile Behavior — Full-Screen vs. Scaled

**Task**: Determine how modals and drawers should adapt on mobile viewports, given 16 modal components in the codebase.

**Decision**: Modals use a responsive pattern: on viewports below 640px (`sm:` breakpoint), modals expand to full-screen with the following behavior:

- `max-sm:w-screen max-sm:h-screen max-sm:rounded-none max-sm:m-0` — fills the viewport
- Content area scrolls vertically (the modal itself does not scroll — its body does)
- Close button (X) is always visible in the top-right corner with a touch-friendly 44×44px target
- No backdrop tap-to-close on mobile (prevents accidental dismissal on touch)

On tablet (768px+) and desktop, modals retain their current centered overlay behavior with backdrop dismissal.

This pattern already partially exists in `ChatPopup.tsx` (`max-sm:!w-screen max-sm:!h-[70vh]`) and is extended to all modal components.

**Rationale**: Full-screen modals on mobile are the industry standard (iOS sheets, Material Design full-screen dialogs). They prevent content overflow, eliminate edge-clipping, and provide maximum space for form inputs and content. The ChatPopup already implements a variant of this pattern. Extending it to all modals creates consistency (FR-008). The scrollable content area ensures long forms remain accessible without the modal itself causing viewport overflow.

**Alternatives Considered**:

- **Scaled modals (smaller but not full-screen)**: Rejected — on 320px viewports, even a 90% width modal is 288px, which is too narrow for form inputs, dropdowns, and content. Full-screen is simpler and more usable.
- **Bottom sheet pattern**: Considered — provides a mobile-native feel. However, converting 16 modals to bottom sheets requires significant refactoring (different animation, drag-to-dismiss, snap points). Full-screen is achievable with CSS-only changes to existing modal components. Bottom sheets could be a future enhancement.
- **No modal changes (let modals overflow)**: Rejected — violates FR-008 and creates horizontal scrollbars on mobile.

---

## R5: Data-Heavy Component Strategy — Pipeline Board, Kanban Board, Chat

**Task**: Determine how to handle complex, data-heavy components (pipeline boards, kanban boards, chat panels) on mobile where horizontal space is severely limited.

**Decision**: Use a context-specific strategy for each component type:

1. **Kanban Board (ProjectBoard)**: Horizontal scroll container on mobile. Board columns stack in a scrollable horizontal strip (`overflow-x-auto snap-x snap-mandatory`). Each column takes ~85% of viewport width on mobile, creating a "card swipe" pattern. Column count indicator shows position (e.g., "2/5").

2. **Pipeline Board (PipelineBoard)**: Similar horizontal scroll for stages. Pipeline stages render in a scrollable container on mobile. The flow graph (`PipelineFlowGraph`) uses `overflow-x-auto` with pinch-to-zoom disabled (CSS `touch-action: pan-x pan-y`).

3. **Chat Interface**: Already mostly responsive via ChatPopup's mobile optimizations. Message bubbles use `max-w-[85%]` on mobile (already implemented). Input area uses full width. File preview chips wrap to new lines.

**Rationale**: Horizontal scrolling for board-like components is an established mobile pattern (Trello, Jira, GitHub Projects all use this). Snap scrolling (`snap-x snap-mandatory`) provides a native-feeling swipe experience. The alternative — vertical stacking of board columns — would create extremely long pages and break the mental model of a kanban board. For pipelines, horizontal scrolling preserves the left-to-right flow that is semantically meaningful (pipeline stages execute in order).

**Alternatives Considered**:

- **Vertical stacking of board columns**: Rejected — a 5-column kanban board would become an extremely long vertical list. Users lose the overview that makes kanban boards valuable. Horizontal scroll preserves the board paradigm.
- **Accordion/collapsible columns**: Considered — each column collapses to a header, expandable on tap. This saves space but adds interaction cost and makes it impossible to see multiple columns simultaneously. Horizontal scroll is simpler and more standard.
- **"Select column" dropdown**: Rejected — requires users to select a column from a dropdown, then view its cards. This is functional but slow and non-standard for board UIs.

---

## R6: Responsive Typography and Spacing Scale

**Task**: Determine the approach for ensuring typography and spacing scale appropriately across breakpoints (FR-010, SC-007).

**Decision**: Use Tailwind's built-in responsive modifiers to apply context-specific typography scaling. Do not introduce a global responsive typography scale (like `clamp()` or fluid type) — instead, audit each page and component to ensure:

1. **Body text**: Minimum 16px (`text-base`) on all viewports. The existing codebase already uses `text-sm` (14px) extensively — instances on mobile viewports are bumped to `text-base` using `max-sm:text-base` where readability is critical.

2. **Headings**: Scale down on mobile using existing responsive modifiers (e.g., `text-3xl sm:text-4xl lg:text-5xl`). The CelestialCatalogHero already implements this pattern well.

3. **Spacing**: Reduce horizontal padding on mobile (`px-2` instead of `px-6`) to maximize content area. Vertical spacing remains consistent or increases slightly for touch-friendly scrolling.

4. **Line heights**: Ensure `leading-relaxed` (1.625) or `leading-normal` (1.5) on body text for mobile readability. The default Tailwind line heights are appropriate.

**Rationale**: The codebase already uses Tailwind responsive modifiers for typography in key areas (CelestialCatalogHero: `text-[2.7rem] sm:text-5xl xl:text-[4.6rem]`). Extending this pattern to remaining components is consistent with the established approach. A global fluid type system (`clamp()`) would require a significant CSS refactor and could break the existing design system's spacing rhythm. The targeted approach — auditing and fixing specific components — is lower risk and more aligned with the audit's remediation nature (fixing what's broken, not redesigning the type system).

**Alternatives Considered**:

- **CSS `clamp()` fluid typography**: Considered — provides smooth scaling between breakpoints without media queries. Rejected because: (1) requires replacing all existing `text-*` utilities with `clamp()` values, which is a massive change; (2) the existing design system uses discrete size steps that are intentional; (3) fluid scaling can produce awkward intermediate sizes that haven't been designed for.
- **Tailwind `@apply` base styles**: Rejected — overriding Tailwind's base styles globally risks unintended cascading effects. Component-level responsive classes are safer and more traceable.
- **Viewport-relative units (`vw`, `vh`)**: Rejected — not recommended for body text (accessibility concern — users can't zoom effectively). Fixed `rem`/`px` with responsive breakpoints is the standard approach.
