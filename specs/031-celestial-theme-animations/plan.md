# Implementation Plan: Frontend Style Audit & Celestial/Cosmic Theme Animation Enhancement

**Branch**: `031-celestial-theme-animations` | **Date**: 2026-03-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/031-celestial-theme-animations/spec.md`

## Summary

Conduct a full-scope audit of all ~117 frontend production components to enforce design token compliance (colors, typography, spacing, border-radius, shadows), standardize text casing conventions (Title Case for headings/nav, sentence case for body/descriptions, ALL CAPS for badges/labels), and layer a cohesive celestial/cosmic animation system across the application. The implementation extends the existing CSS-only animation foundation already established in `index.css` — including centralized motion tokens (`--transition-cosmic-fast/base/slow/drift`), keyframe definitions (`twinkle`, `pulse-glow`, `orbit-spin`, `shimmer`, `float`, `cosmic-fade-in`, `star-wink`), utility classes (`celestial-twinkle`, `celestial-panel`, `solar-action`, etc.), and `prefers-reduced-motion` overrides — to reach every component category: cards, buttons, modals, sidebars, navigation, tooltips, inputs, and loaders. No new JavaScript animation libraries are added; all enhancements use CSS `@keyframes`, custom properties, and the existing Tailwind v4 design token system. The `AppLayout` already includes a starfield background and decorative orbit elements; this work ensures consistent application of those patterns across remaining components and adds theme-transition gradient shifts, celestial loading states, and hover/focus micro-interactions where missing. All animations respect `prefers-reduced-motion`, maintain WCAG AA contrast ratios, and preserve focus-visible indicators. A style alignment report documents changes per component.

## Technical Context

**Language/Version**: TypeScript ~5.9 (frontend-only feature)
**Primary Dependencies**: React 19.2, Tailwind CSS v4, lucide-react 0.577, class-variance-authority 0.7, @radix-ui/react-tooltip, @radix-ui/react-slot
**Storage**: N/A — no database, localStorage, or API changes
**Testing**: Vitest 4 + Testing Library + jest-axe (accessibility)
**Target Platform**: Desktop browsers (Chrome, Firefox, Safari, Edge); mobile browsers (responsive, touch)
**Project Type**: Web application (frontend-only changes)
**Performance Goals**: Star-field background adds <100ms to initial page load; all animations maintain 30fps+ on mid-range devices; no layout shift from animation states
**Constraints**: Must use existing CSS custom properties and design tokens in `index.css`; must meet WCAG 2.1 AA (4.5:1 contrast ratio for normal text, 3:1 for large text); all animations must respect `prefers-reduced-motion: reduce`; no new JavaScript animation libraries (Framer Motion not in dep tree — use CSS-native only)
**Scale/Scope**: ~117 production component files across 12 directories, 9 pages, 1 layout system; 0 backend changes, 0 API changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 6 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, 16 functional requirements (FR-001–FR-016), 10 success criteria, edge cases, assumptions, and dependencies |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan → tasks → implement) |
| **IV. Test Optionality** | ✅ PASS | Tests not explicitly mandated in spec; existing tests should continue to pass; accessibility contrast checks recommended given WCAG requirements |
| **V. Simplicity/DRY** | ✅ PASS | Extends existing CSS animation token system rather than introducing new frameworks; centralized utility classes in `index.css`; no new dependencies added; reuses established `starfield`, `celestial-panel`, `solar-action` patterns already proven in `AppLayout` and `CelestialCatalogHero` |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace back to spec FRs (FR-001–FR-016); component audit scope derived from spec requirements |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 |
| **IV. Test Optionality** | ✅ PASS | Existing tests unaffected; accessibility checks recommended but not mandated |
| **V. Simplicity/DRY** | ✅ PASS | Zero new dependencies. All animations use the centralized `@theme` block tokens and `@keyframes` already in `index.css`. Utility classes (`celestial-panel`, `solar-action`, `celestial-focus`, `starfield`, etc.) are shared across all components — no per-component animation declarations. The `prefers-reduced-motion` block already covers all utility classes. New additions (theme-transition gradient, celestial loader) follow the same pattern and are added to the same centralized location. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/031-celestial-theme-animations/
├── plan.md              # This file
├── research.md          # Phase 0: Research decisions (R1–R6)
├── data-model.md        # Phase 1: Entity definitions, token catalog, audit structure
├── quickstart.md        # Phase 1: Developer onboarding guide
├── contracts/
│   └── components.md    # Phase 1: Component modification contracts
├── checklists/
│   └── requirements.md  # Specification quality checklist (complete)
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── index.css                              # MODIFIED: Extend @theme tokens, add new keyframes
│   │                                          #   (theme-transition gradient, celestial-loader orbit,
│   │                                          #    cosmic-glow-focus keyframe, additional utility classes,
│   │                                          #    prefers-reduced-motion updates)
│   ├── components/
│   │   ├── common/
│   │   │   └── CelestialLoader.tsx            # NEW: Celestial-themed loading spinner (orbital shimmer)
│   │   ├── ui/
│   │   │   ├── button.tsx                     # MODIFIED: Add celestial-focus, solar-action classes
│   │   │   ├── card.tsx                       # MODIFIED: Add celestial-panel, celestial-fade-in
│   │   │   ├── input.tsx                      # MODIFIED: Add celestial-focus class
│   │   │   ├── tooltip.tsx                    # MODIFIED: Ensure celestial theme alignment
│   │   │   └── confirmation-dialog.tsx        # MODIFIED: Add celestial-fade-in, backdrop styling
│   │   ├── agents/
│   │   │   ├── AgentCard.tsx                  # MODIFIED: celestial-panel, text casing audit
│   │   │   ├── AgentsPanel.tsx                # MODIFIED: Text casing, celestial-fade-in
│   │   │   ├── AddAgentModal.tsx              # MODIFIED: Modal celestial styling
│   │   │   ├── AgentIconCatalog.tsx           # MODIFIED: Grid item hover glow
│   │   │   └── [remaining agent components]   # MODIFIED: Token audit + text casing
│   │   ├── board/
│   │   │   ├── ProjectBoard.tsx               # MODIFIED: celestial-fade-in, token audit
│   │   │   ├── IssueCard.tsx                  # MODIFIED: celestial-panel hover
│   │   │   ├── BoardToolbar.tsx               # MODIFIED: Text casing, solar-action
│   │   │   └── [remaining board components]   # MODIFIED: Token audit + text casing
│   │   ├── chat/
│   │   │   ├── ChatInterface.tsx              # MODIFIED: Token audit, text casing
│   │   │   ├── MessageBubble.tsx              # MODIFIED: celestial-fade-in for messages
│   │   │   └── [remaining chat components]    # MODIFIED: Token audit + text casing
│   │   ├── chores/
│   │   │   ├── ChoreCard.tsx                  # MODIFIED: celestial-panel, text casing
│   │   │   └── [remaining chore components]   # MODIFIED: Token audit + text casing
│   │   ├── pipeline/
│   │   │   ├── StageCard.tsx                  # MODIFIED: celestial-panel, celestial-fade-in
│   │   │   ├── AgentNode.tsx                  # MODIFIED: Hover glow, token audit
│   │   │   └── [remaining pipeline components]# MODIFIED: Token audit + text casing
│   │   ├── settings/
│   │   │   ├── GlobalSettings.tsx             # MODIFIED: Text casing, section styling
│   │   │   └── [remaining settings components]# MODIFIED: Token audit + text casing
│   │   ├── tools/
│   │   │   ├── ToolCard.tsx                   # MODIFIED: celestial-panel, text casing
│   │   │   └── [remaining tools components]   # MODIFIED: Token audit + text casing
│   │   └── ThemeProvider.tsx                  # MODIFIED: Add theme-transition class during toggle
│   ├── layout/
│   │   ├── AppLayout.tsx                      # EXISTING: Already has starfield + celestial decorations
│   │   ├── Sidebar.tsx                        # MODIFIED: Text casing, celestial hover states
│   │   ├── TopBar.tsx                         # MODIFIED: Text casing, solar-action buttons
│   │   └── Breadcrumb.tsx                     # MODIFIED: Text casing audit
│   └── pages/
│       ├── LoginPage.tsx                      # MODIFIED: Celestial background, text casing
│       ├── NotFoundPage.tsx                   # MODIFIED: Celestial styling, text casing
│       └── [remaining pages]                  # MODIFIED: Token audit + text casing
```

**Structure Decision**: Web application (frontend-only). This feature is entirely a frontend concern — no backend changes, no database changes, no API changes. All changes extend existing directories and component files. The single new component (`CelestialLoader.tsx`) lives in `frontend/src/components/common/` following the existing pattern for shared presentational components (`CelestialCatalogHero.tsx`, `ErrorBoundary.tsx`). All animation tokens, keyframes, and utility classes remain centralized in `frontend/src/index.css` within the `@theme` block and `@layer base` rules, extending the established architecture.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| CSS-only animations (no Framer Motion) | The existing `@theme` block already defines 7 keyframe animations, 4 motion transition tokens, and 12+ utility classes. Extending this CSS-native system is zero-dependency, maximally performant, and consistent with the established architecture. Framer Motion is not in the dependency tree. | Framer Motion (rejected: adds ~32KB gzipped dependency; introduces JavaScript-driven animations that compete with the existing CSS system; requires wrapping every animated element in `motion` components; overkill for the decorative/transitional animations needed here) |
| Single `index.css` for all animation tokens | Centralizes all keyframes, motion tokens, and utility classes in one file. Developers search one location for animation values. Matches the existing pattern where all design tokens live in the `@theme` block. | Separate `animations.css` or `theme/motion.ts` file (rejected: the spec suggests this as an option, but the existing codebase already has all animation tokens in `index.css`; splitting would fragment the token system and require new imports in every component file) |
| Utility-class-based animation application | Components apply animations via CSS classes (`celestial-panel`, `solar-action`, `celestial-focus`) rather than inline styles or component-level `@keyframes`. Classes are defined once and reused across all components. | Per-component animation definitions (rejected: violates DRY; makes the `prefers-reduced-motion` block unmaintainable; harder to audit for consistency) |
