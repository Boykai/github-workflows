# Research: Deep UI/UX Tooltip & Hover Coverage

**Feature**: `002-tooltip-hover-coverage` | **Date**: 2026-03-15 | **Plan**: [plan.md](plan.md)

## Research Tasks

### RT-001: Radix HoverCard Best Practices for React 19

**Decision**: Use `@radix-ui/react-hover-card` as the foundation for all rich entity preview overlays (agent nodes, agent cards, issue cards, mention chips). The wrapper component (`hover-card.tsx`) will follow the exact pattern established by the existing `tooltip.tsx` — export named parts (Root, Trigger, Content) and provide a convenience wrapper with sensible defaults.

**Rationale**: Radix HoverCard provides built-in open/close delay management (`openDelay`, `closeDelay`), collision detection for viewport edge repositioning, portal rendering to avoid z-index stacking issues, and `prefers-reduced-motion` compatibility via CSS. The existing codebase already uses `@radix-ui/react-tooltip@^1.2.8` and `@radix-ui/react-slot@^1.2.4`, so adding another Radix primitive maintains architectural consistency and avoids introducing a new design system library.

**Alternatives considered**:
- **Custom hover card from scratch**: Rejected because it would duplicate Radix's delay management, collision detection, portal rendering, and ARIA attribute handling — violating YAGNI and DRY principles.
- **Using Tooltip with JSX content**: Rejected because Radix Tooltip is designed for simple text and does not support interactive content inside the tooltip body. Hover cards need to support clickable links, lists, and badges.
- **Floating UI (Popper successor)**: Rejected as a lower-level positioning library that would require manual implementation of delays, ARIA attributes, and animation — Radix provides a higher-level, opinionated solution that matches the existing codebase's approach.

**Key Implementation Details**:
- `@radix-ui/react-hover-card` does NOT require a global provider (unlike Tooltip). No `App.tsx` changes needed.
- Default `openDelay={300}` matches the existing tooltip delay; `closeDelay={150}` gives users time to move cursor into the card content.
- Content component uses `forwardRef` + `React.ComponentPropsWithoutRef` pattern for full TypeScript inference, consistent with `tooltip.tsx`.
- Animation: `data-[state=open]:animate-in data-[state=closed]:animate-out` with `fade-in-0`/`fade-out-0` and `zoom-in-95`/`zoom-out-95`, gated behind `motion-safe:` Tailwind modifier for `prefers-reduced-motion` compliance.

---

### RT-002: Radix Popover Migration Strategy for Manual Overlays

**Decision**: Use `@radix-ui/react-popover` to create a shared `popover.tsx` wrapper, then incrementally migrate the three identified manual popover implementations (AddAgentPopover, ModelSelector, AgentPresetSelector) in Phase 2/4. Migration preserves all existing features (search, filtering, recent tracking, presets) while replacing only the overlay mechanics (positioning, focus management, keyboard handling).

**Rationale**: The three existing manual popover implementations collectively total ~1,200 lines of code, each independently re-implementing viewport collision detection, Escape key handling, outside click detection, and portal rendering. Radix Popover provides all of these as built-in behaviors with correct ARIA attribute management (`aria-haspopup`, `aria-expanded`), focus trapping, and focus restoration on close — addressing FR-013 through FR-017 and User Story 3.

**Alternatives considered**:
- **Keep manual implementations and add ARIA attributes**: Rejected because the manual implementations have inconsistent keyboard behavior and would require per-component fixes for focus trapping and focus restoration — essentially rebuilding what Radix provides.
- **Use Headless UI Popover**: Rejected to avoid mixing component libraries. The codebase is standardized on Radix UI; introducing Headless UI would fragment the dependency tree.
- **Big-bang migration (all at once)**: Rejected in favor of incremental migration. Each component has unique features (ModelSelector: recent tracking, cost badges; AgentPresetSelector: confirmation dialogs, localStorage). Migrating one at a time allows focused testing and reduces risk.

**Migration Approach**:
1. The `popover.tsx` wrapper exports: `Popover`, `PopoverTrigger`, `PopoverContent`, `PopoverAnchor`, `PopoverClose`, `PopoverArrow`.
2. Each manual popover retains its existing internal logic (search, filtering, selection) but replaces its outer shell (useState toggle, absolute positioning, portal rendering, event listeners) with Radix Popover primitives.
3. Migration order: AddAgentPopover (simplest, 298 lines) → ModelSelector (medium, 365 lines) → AgentPresetSelector (most complex, 540 lines with confirmation dialogs).

---

### RT-003: Tooltip Registry Extension Strategy

**Decision**: Extend the existing `tooltip-content.ts` registry with ~40 new entries following the established `{area}.{section}.{element}` naming convention. New entries cover all gaps identified in the per-component audit (Phase 2 of the issue): pipeline drag handles, agent card actions, tools editor actions, board toolbar/column actions, settings controls, and sidebar navigation.

**Rationale**: The existing registry contains 54 entries across 7 areas (board, chat, agents, pipeline, chores, settings, tools). The spec identifies ~40 additional elements that lack tooltips. Extending the existing registry (rather than creating a parallel system) maintains the single-source-of-truth pattern, preserves i18n readiness, and keeps the `contentKey=` lookup mechanism unchanged.

**Alternatives considered**:
- **Per-component inline tooltip text**: Rejected because it scatters tooltip copy across ~30+ component files, making terminology consistency checks and future localization much harder.
- **Separate registry per area**: Rejected because it fragments the lookup mechanism and introduces import complexity. The flat registry with dot-notation keys already handles namespacing.

**New Registry Keys** (organized by area):

| Area | New Keys | Count |
|------|----------|-------|
| **pipeline** | `pipeline.agent.dragHandle`, `pipeline.agent.clone`, `pipeline.group.dragHandle`, `pipeline.group.label`, `pipeline.stage.dragHandle`, `pipeline.analytics.complexity` | 6 |
| **agents** | `agents.card.expand`, `agents.tools.moveUp`, `agents.tools.moveDown`, `agents.tools.remove`, `agents.bulk.scope` | 5 |
| **chat** | `chat.voice.stop`, `chat.mention.agentPreview`, `chat.command.description` | 3 |
| **board** | `board.filter.button`, `board.sort.button`, `board.column.addAgent`, `board.column.settings`, `board.column.collapse` | 5 |
| **tools** | `tools.card.resync`, `tools.config.repoUrl`, `tools.config.branch`, `tools.config.serverCommand`, `tools.generator.copy`, `tools.search.input` | 6 |
| **settings** | `settings.ai.temperature`, `settings.ai.provider`, `settings.theme.toggle`, `settings.signal.qr`, `settings.reset.danger`, `settings.reset.cache`, `settings.reset.all` | 7 |
| **nav** | `nav.projects`, `nav.agents`, `nav.pipeline`, `nav.chores`, `nav.tools`, `nav.settings`, `nav.sidebar.toggle` | 7 |
| **Total** | | **39** |

**Note**: Some keys (e.g., `settings.ai.temperature`, `tools.card.resync`) may already exist in the registry with different naming. The implementation phase will reconcile existing vs. new entries and avoid duplicates.

---

### RT-004: Title Attribute Migration Strategy

**Decision**: Systematically replace all `title=` attributes on interactive elements (buttons, links, toggles) with `<Tooltip contentKey="...">` wrappers sourced from the registry. Retain `title=` only on non-interactive elements displaying truncated text where a styled tooltip would be overkill (e.g., `<span>` with `text-overflow: ellipsis`).

**Rationale**: The codebase contains ~94 `title=` attribute instances across `.tsx` files. Browser-native title tooltips have several UX problems: inconsistent appearance across browsers, no styling control, delayed appearance (~500ms in most browsers vs. our 300ms target), no keyboard trigger, and no `prefers-reduced-motion` respect. The centralized registry pattern already exists and is proven; migration is mechanical.

**Alternatives considered**:
- **Keep `title=` alongside `<Tooltip>`**: Rejected because dual tooltips (browser native + Radix) would create a confusing double-tooltip experience.
- **Remove `title=` without replacement**: Rejected because it would remove discoverability for icon-only buttons, violating User Story 1.
- **Replace all `title=` including on truncated text**: Considered but rejected for non-interactive `<span>` elements where `title=` provides lightweight truncation hints without the overhead of a Radix Tooltip portal.

**Migration Categories**:

| Category | Count (est.) | Action |
|----------|-------------|--------|
| Icon-only buttons (sidebar, toolbar) | ~20 | Replace with `<Tooltip contentKey="...">` |
| Card action buttons | ~15 | Replace with `<Tooltip contentKey="...">` |
| Status indicators | ~10 | Replace with `<Tooltip contentKey="...">` |
| Truncated text on non-interactive spans | ~25 | Keep `title=` (allowlisted) |
| Informational spans/divs | ~15 | Evaluate case-by-case; most migrate to `<Tooltip>` |
| Test files | ~5 | No changes |

---

### RT-005: Hover Styling Consistency Patterns

**Decision**: Establish two standardized Tailwind utility patterns for interactive hover states: (1) a card hover pattern (`hover:ring-1 hover:ring-border hover:bg-accent/50 transition-all`) applied to all interactive card surfaces, and (2) a drag handle pattern (`opacity-0 group-hover:opacity-100 cursor-grab transition-opacity`) applied to all draggable items' grip icons.

**Rationale**: Current hover styles are inconsistent across card types — some use `hover:bg-accent/14`, some use `hover:shadow-sm`, and some have no hover state at all. Standardizing on a single ring + background pattern reinforces learnability (User Story 4) and creates a predictable visual language. The `group-hover` pattern for drag handles is a well-established Tailwind idiom for progressive disclosure.

**Alternatives considered**:
- **CSS custom properties for hover states**: Rejected because the project uses Tailwind utility-first approach consistently; adding CSS variables would be inconsistent.
- **Shared className constant**: Considered (e.g., `const CARD_HOVER = "hover:ring-1 hover:ring-border hover:bg-accent/50"`), but rejected because Tailwind's JIT compiler needs to see full class strings in source. Instead, document the pattern in this plan and apply directly.

**Patterns**:

```tsx
// Card hover (apply to AgentCard, IssueCard, ToolCard, ChoreCard, AgentNode, StageCard)
className="... hover:ring-1 hover:ring-border hover:bg-accent/50 transition-all"

// Drag handle (apply to AgentNode, ExecutionGroupCard, StageCard, chore rows)
<GripVertical className="opacity-0 group-hover:opacity-100 cursor-grab transition-opacity" />

// Drop zone feedback (apply to @dnd-kit drop targets)
className={cn("...", isOver && "ring-2 ring-primary/50 bg-primary/5")}
```

---

### RT-006: Accessibility and Motion Compliance

**Decision**: All new components (hover-card, popover) will use Tailwind's `motion-safe:` and `motion-reduce:` modifiers to gate animations. Every icon-only button will receive both an `aria-label` matching its tooltip text and keyboard Tab reachability. All popovers will use Radix's built-in focus trapping.

**Rationale**: WCAG 2.1 AA compliance requires that animations respect `prefers-reduced-motion` (SC 2.3.3), all interactive elements be keyboard accessible (SC 2.1.1), and focus management be correct for modal/overlay content (SC 2.4.3). Radix components handle focus trapping and ARIA attributes by default; the wrapper components need only ensure animation classes respect the motion preference.

**Alternatives considered**:
- **JavaScript-based motion detection**: Rejected because Tailwind's `motion-safe:`/`motion-reduce:` modifiers handle this declaratively without JavaScript, matching the existing `tooltip.tsx` animation approach.
- **Global animation disable toggle**: Rejected as overly broad; `prefers-reduced-motion` is the standard mechanism and is per-user, per-OS.

**Implementation Details**:
- Animation classes in hover-card and popover: `motion-safe:data-[state=open]:animate-in motion-safe:data-[state=closed]:animate-out`
- Under `motion-reduce:`: components appear/disappear instantly (no transition classes applied)
- The existing `tooltip.tsx` already uses `animate-in` / `animate-out` — verify and add `motion-safe:` prefix if missing
- `aria-label` text sourced from the same registry entry as tooltip text to guarantee matching (FR-024)
