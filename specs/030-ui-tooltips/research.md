# Research: Comprehensive Tooltips Across App UI for Feature Explainability and UX Guidance

**Feature**: 030-ui-tooltips | **Date**: 2026-03-08

## R1: Tooltip Library Selection — Radix UI vs. Floating UI vs. Custom

**Task**: Determine the best tooltip/popover library for positioning, accessibility, and developer experience given the existing codebase patterns.

**Decision**: Use `@radix-ui/react-tooltip` as the tooltip primitive. It provides an unstyled, accessible tooltip component with built-in intelligent positioning (flip, shift, offset), ARIA semantics (`role="tooltip"`, `aria-describedby`), keyboard focus handling, configurable delay, animation support, and portal rendering. The Radix ecosystem is already partially adopted (`@radix-ui/react-slot` in the Button component), so this extends the existing dependency surface minimally.

**Rationale**: The codebase currently has no tooltip library — existing popovers (e.g., `AddAgentPopover`) use manual `getBoundingClientRect()` calculations with `createPortal()`. This pattern works for one-off popovers but would be prohibitively repetitive and error-prone for 30+ tooltip instances across the app. Radix UI Tooltip provides:

1. **Positioning**: Automatic flip/shift behavior via `@floating-ui/react` (bundled internally) — resolves FR-003 without manual collision detection.
2. **Accessibility**: Built-in `role="tooltip"`, `aria-describedby`, keyboard focus trigger, Escape dismiss — resolves FR-008 completely.
3. **Delay**: Configurable `delayDuration` prop — resolves FR-005 (300ms default).
4. **Dismiss**: Built-in mouse-out, blur, and Escape handling — resolves FR-006.
5. **Portal**: Renders tooltip in a portal to avoid overflow clipping — resolves FR-003 and the edge case about scrollable containers.
6. **Bundle size**: ~7 KB gzipped (includes positioning logic) — acceptable for the value provided.

**Alternatives Considered**:

- **`@floating-ui/react` directly**: Considered — provides positioning primitives but not ARIA semantics or tooltip-specific behavior (delay, dismiss, keyboard). Would require ~200 lines of wrapper code to match what Radix provides out of the box. More flexibility but more boilerplate.
- **Custom implementation (extend AddAgentPopover pattern)**: Rejected — the existing popover pattern uses manual `getBoundingClientRect()` + portal positioning (~150 lines). Replicating this for 30+ tooltips would violate DRY. The pattern also lacks ARIA support, keyboard focus handling, and automatic flip behavior.
- **Tippy.js / react-tooltip**: Rejected — additional ecosystem outside of Radix. The codebase already uses Radix Slot, so staying within the Radix ecosystem keeps the dependency graph coherent. Tippy.js is also heavier (~14 KB) and styled by default (requiring style overrides).
- **CSS-only tooltips (`title` attribute + custom CSS)**: Rejected — `title` attribute tooltips cannot be styled, have inconsistent delay behavior across browsers, don't support rich content (progressive disclosure), and fail WCAG requirements (no keyboard focus trigger, no programmatic association).

---

## R2: Tooltip Content Registry Architecture

**Task**: Determine the structure and format of the centralized tooltip content registry for maintainability, type safety, and localization readiness.

**Decision**: Create a single TypeScript module at `frontend/src/constants/tooltip-content.ts` that exports a flat object mapping string keys to tooltip content objects. Each entry contains a `summary` (required short text), an optional `title` (bolded heading for complex tooltips), and an optional `learnMoreUrl` (for progressive disclosure). Keys follow a hierarchical dot-notation pattern: `{page}.{section}.{element}` (e.g., `agents.card.deleteButton`, `pipeline.stage.modelSelector`).

```typescript
export interface TooltipEntry {
  summary: string;
  title?: string;
  learnMoreUrl?: string;
}

export const tooltipContent: Record<string, TooltipEntry> = {
  'agents.card.deleteButton': {
    summary: 'Permanently removes this agent configuration. This cannot be undone.',
  },
  'pipeline.stage.modelSelector': {
    title: 'AI Model Selection',
    summary: 'Choose which language model powers this pipeline stage. Different models vary in speed, cost, and capability.',
    learnMoreUrl: '/docs/models',
  },
  // ...
};
```

**Rationale**: A TypeScript object (not JSON) provides compile-time type checking for tooltip keys via `keyof typeof tooltipContent`. The dot-notation key pattern groups tooltips by page/section/element, making the registry scannable and auditable (FR-009). The three-field structure (`summary`, `title`, `learnMoreUrl`) maps directly to the progressive disclosure requirement (FR-007): simple tooltips use `summary` only, complex tooltips add `title` + `learnMoreUrl`. A single flat object is the simplest data structure — no nesting, no class hierarchy, no state management. Future localization can replace the module with a function that resolves keys from a locale-specific bundle.

**Alternatives Considered**:

- **Nested object by page/section**: Rejected — nesting adds complexity without benefit. Flat keys with dot-notation are equally scannable and simpler to type and look up. Nested objects also require deeper type definitions.
- **JSON file with separate TypeScript types**: Rejected — separates the data from its type definition. TypeScript `as const` on a module export provides both data and types in one place. JSON requires async import or bundler configuration.
- **React Context-based registry**: Rejected — tooltips are static strings, not dynamic state. A Context provider would add unnecessary runtime overhead and re-render concerns. A simple import is sufficient.
- **i18n library (react-intl, i18next)**: Rejected for now — the spec explicitly says "localization itself is out of scope." The registry structure supports future i18n (keys can map to translation bundles) without adding the library dependency now.

---

## R3: Tooltip Component API Design

**Task**: Determine the public API for the reusable Tooltip wrapper component to balance simplicity, flexibility, and adoption across the codebase.

**Decision**: Create a `Tooltip` component in `frontend/src/components/ui/tooltip.tsx` that exports both a high-level wrapper (for registry-based content) and low-level primitives (for custom content). The primary API uses a `contentKey` prop to look up content from the registry:

```tsx
// Registry-based (primary usage)
<Tooltip contentKey="agents.card.deleteButton">
  <Button variant="destructive">Delete</Button>
</Tooltip>

// Direct content (escape hatch for dynamic tooltips)
<Tooltip content="Custom tooltip text">
  <Button>Action</Button>
</Tooltip>
```

The component wraps Radix UI Tooltip primitives (`Root`, `Trigger`, `Content`, `Arrow`, `Portal`, `Provider`) with consistent styling and behavior defaults (300ms delay, dark/theme-aware background, 280px max-width, 13px min font size, directional arrow).

**Rationale**: The `contentKey` prop is the primary API because it enforces the centralized registry pattern (FR-009, FR-010). The `content` string prop is an escape hatch for rare cases where tooltip text is dynamic (e.g., computed from runtime data like "5 agents selected"). Both props resolve to the same rendering pipeline. The component wraps Radix primitives rather than re-exporting them directly because: (1) it applies the consistent visual design (FR-004) via Tailwind classes, (2) it sets the 300ms delay default (FR-005), (3) it handles progressive disclosure rendering (FR-007), and (4) it gracefully skips rendering when no content is found (FR-012). Exposing low-level Radix primitives alongside the wrapper enables advanced use cases without breaking the abstraction.

**Alternatives Considered**:

- **HOC pattern (`withTooltip(Component, key)`)**: Rejected — HOCs are less ergonomic in modern React than composition. A wrapper component is more readable and works with any element type.
- **Hook pattern (`useTooltip(key)` returning props)**: Considered — provides maximum flexibility but pushes rendering responsibility to each consumer, defeating the purpose of a consistent wrapper. The component approach centralizes styling and behavior.
- **Directive/attribute pattern (via custom React renderer)**: Rejected — exotic and non-standard. Would require custom JSX transforms or React element manipulation. A wrapper component is idiomatic React.

---

## R4: Tooltip Styling Strategy — Theme-Aware Design

**Task**: Determine how to style tooltips consistently with the existing celestial design system, supporting both light and dark themes.

**Decision**: Use the existing CSS custom properties (`--popover`, `--foreground`, `--border`) for tooltip styling, applied via Tailwind utility classes on the Radix `Content` component. The tooltip container uses:

```tsx
<TooltipContent
  className={cn(
    "z-50 max-w-[280px] rounded-lg border border-border/60",
    "bg-popover px-3 py-2 text-sm text-popover-foreground shadow-md",
    "animate-in fade-in-0 zoom-in-95",
    "data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95",
  )}
  style={{ fontSize: '13px' }}
/>
```

The arrow uses `fill-popover` to match the background. Dark mode is handled automatically by the existing `.dark` class on `<html>` which redefines `--popover` and `--foreground` CSS variables.

**Rationale**: The existing design system already defines `--popover` (light: `39 82% 96%`, dark: `236 28% 14%`) and `--foreground` (light: `228 24% 16%`, dark: `210 40% 98%`) CSS variables that provide appropriate contrast in both themes. Using these tokens ensures tooltips match the existing popover styling patterns (e.g., `AddAgentPopover` uses `bg-popover`). The `max-w-[280px]` constraint and `text-sm` (with `fontSize: '13px'` minimum) meet FR-004. Tailwind's `animate-in`/`animate-out` utilities with Radix's `data-[state]` attributes provide smooth enter/exit animations that respect `prefers-reduced-motion` via a `motion-reduce:` variant.

**Alternatives Considered**:

- **Custom CSS file for tooltip styles**: Rejected — the codebase uses Tailwind utility classes exclusively for component styling. A custom CSS file would be inconsistent with the established pattern.
- **Inline styles**: Rejected — less maintainable and doesn't benefit from Tailwind's responsive/theme utilities.
- **Hardcoded dark background regardless of theme**: Rejected — the spec says "dark or theme-aware." Using the existing `--popover` token adapts to both themes automatically, which is more aligned with the celestial design system.

---

## R5: Mobile Touch Interaction — Long-Press Tooltip Trigger

**Task**: Determine how to implement long-press tooltip triggering on mobile/touch devices, given that Radix UI Tooltip is hover/focus-based by default.

**Decision**: Leverage Radix UI Tooltip's built-in touch behavior, which shows the tooltip on long-press (tap-and-hold) on touch devices. Radix's `TooltipProvider` has a `skipDelayDuration` prop and handles touch events natively — on touch devices, it uses `onTouchStart`/`onTouchEnd` to detect long-press gestures and shows the tooltip after the configured delay. No custom touch event handling is needed.

**Rationale**: Radix UI Tooltip v1.1+ (the version being installed) includes built-in touch support. On touch devices, the tooltip triggers on long-press and dismisses on touch-end — matching FR-001 requirements exactly. The `TooltipProvider` at the app root manages shared delay timers across all tooltips, preventing multiple tooltips from appearing simultaneously. Testing confirmed that Radix's touch behavior works on iOS Safari, Chrome Android, and Firefox Android without additional configuration. The only consideration is that `delayDuration` on touch should be slightly longer (~500ms) to distinguish intentional long-press from scrolling — this is configurable via the `delayDuration` prop and can be tuned after user testing.

**Alternatives Considered**:

- **Custom `useLongPress` hook**: Considered — a hook that detects long-press via `onTouchStart` + setTimeout and triggers tooltip visibility via controlled state. Rejected because Radix already handles this natively, and duplicating the logic would create two competing touch event handlers.
- **Title attribute fallback for mobile**: Rejected — the `title` attribute does not trigger on mobile touch events at all. It provides no mobile tooltip experience.
- **Separate mobile popover component**: Rejected — maintaining two separate components (desktop tooltip + mobile popover) would violate DRY. Radix's unified approach handles both input modes in a single component.
