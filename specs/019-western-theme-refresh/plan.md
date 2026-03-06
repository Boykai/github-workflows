# Implementation Plan: Western/Cowboy UI Theme Refresh

**Branch**: `019-western-theme-refresh` | **Date**: 2026-03-05 | **Spec**: [spec.md](specs/019-western-theme-refresh/spec.md)
**Input**: Feature specification from `/specs/019-western-theme-refresh/spec.md`

## Summary

Replace the default slate/blue shadcn/ui theme with a Western/Cowboy-inspired design system. The core approach: redefine CSS custom properties in `index.css` (light and dark modes) with warm cream, dark brown, sunset-gold, and terra-cotta values — this propagates automatically to ~80% of components via shadcn/ui's `cssVariables: true` configuration. Then add a slab-serif display font (Rye) for headings, update Tailwind config with warm shadows and convenience colors, refine button/card/input primitives with tactile interactions, and audit ~20 component files containing hardcoded Tailwind color classes for palette harmony. No backend, API, or business logic changes.

## Technical Context

**Language/Version**: TypeScript 5.8.0, React 18.3.1, Vite 5.4.0  
**Primary Dependencies**: Tailwind CSS 3.4.19, shadcn/ui (cssVariables: true, baseColor: slate), class-variance-authority, lucide-react 0.575.0, Radix UI  
**Storage**: N/A (frontend-only changes)  
**Testing**: Vitest 4.0.18, @testing-library/react, jest-axe 10.0.0, Playwright 1.58.1  
**Target Platform**: Web (desktop + mobile responsive)  
**Project Type**: Web application (frontend/ only — no backend changes)  
**Performance Goals**: Zero net bundle size increase; no new JS dependencies; font loaded via Google Fonts CDN with `display=swap`  
**Constraints**: CSS/Tailwind-only visual changes; no business logic or API alterations; WCAG AA contrast compliance required; existing tests must pass unchanged  
**Scale/Scope**: Frontend global style overhaul — 3 config files, 3 UI primitives, ~20 component files with hardcoded colors, 2 page files, 1 favicon

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | `spec.md` completed with 5 prioritized user stories, Given-When-Then acceptance scenarios, clear scope boundaries, and out-of-scope declarations |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates (`spec-template.md`, `plan-template.md`); no custom sections added |
| **III. Agent-Orchestrated** | ✅ PASS | Following specify → plan → tasks → implement phase chain with explicit handoffs |
| **IV. Test Optionality** | ✅ PASS | Tests not explicitly requested in spec; existing jest-axe and Vitest tests serve as regression guards. No new test creation required. SC-004 mandates existing tests continue to pass. |
| **V. Simplicity/DRY** | ✅ PASS | CSS variable propagation handles ~80% of changes automatically; manual edits only where hardcoded colors exist. No new abstractions, no new components, no premature patterns. |

**Gate result**: ALL PASS — proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/019-western-theme-refresh/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (design token definitions)
├── quickstart.md        # Phase 1 output (implementation quick-start)
├── contracts/           # Phase 1 output (token interface contracts)
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── index.html                          # Google Fonts link (add Rye)
├── tailwind.config.js                  # Font families, warm shadows, convenience colors
├── public/
│   └── favicon.svg                     # Western-themed favicon (replace vite.svg)
├── src/
│   ├── index.css                       # CSS custom properties (:root + .dark)
│   ├── App.tsx                         # Header branding font, SignalBannerBar colors
│   ├── pages/
│   │   ├── ProjectBoardPage.tsx        # Warning banner colors, heading font
│   │   └── SettingsPage.tsx            # Heading font
│   ├── components/
│   │   ├── ui/
│   │   │   ├── button.tsx              # Press animation, optional western variant
│   │   │   ├── card.tsx                # Warm shadow
│   │   │   └── input.tsx               # Gold focus border
│   │   ├── board/
│   │   │   ├── IssueCard.tsx           # Sub-issue state icon colors
│   │   │   ├── IssueDetailModal.tsx    # State indicator colors
│   │   │   ├── AddAgentPopover.tsx     # Status badge colors
│   │   │   ├── AgentTile.tsx           # Amber accent
│   │   │   ├── AgentColumnCell.tsx     # Amber accent
│   │   │   ├── CleanUpSummary.tsx      # Success indicator colors
│   │   │   ├── CleanUpConfirmModal.tsx # Success indicator colors
│   │   │   └── CleanUpAuditHistory.tsx # Status indicator colors
│   │   ├── agents/
│   │   │   └── AgentCard.tsx           # Status badge colors (green/yellow/red)
│   │   ├── chores/
│   │   │   └── ChoreCard.tsx           # Status indicator colors
│   │   ├── chat/
│   │   │   ├── MessageBubble.tsx       # Success indicator
│   │   │   ├── TaskPreview.tsx         # Confirm button colors
│   │   │   ├── StatusChangePreview.tsx # Confirm button colors
│   │   │   └── IssueRecommendationPreview.tsx # Multi-color badges/buttons
│   │   └── settings/
│   │       ├── SettingsSection.tsx      # Success text color
│   │       ├── SignalConnection.tsx     # Connection status colors
│   │       ├── McpSettings.tsx         # Status indicator colors
│   │       └── DynamicDropdown.tsx     # Warning styling
│   └── hooks/
│       └── useAppTheme.ts             # No changes (theme mechanism preserved)
```

**Structure Decision**: Frontend-only web application. All changes are in the `frontend/` directory. No backend modifications. The design system lives in 3 config/style files (`index.css`, `tailwind.config.js`, `index.html`); component-level changes target hardcoded colors in ~20 `.tsx` files.

## Complexity Tracking

> No violations detected — all constitution principles pass. No complexity justification needed.
