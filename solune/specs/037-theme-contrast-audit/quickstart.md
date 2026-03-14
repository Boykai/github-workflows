# Quickstart: Frontend Theme Audit — Light/Dark Mode Contrast & Style Consistency

**Feature**: `037-theme-contrast-audit` | **Date**: 2026-03-12

## Overview

This guide provides the essential context and steps needed to begin implementing the theme contrast audit. The audit covers ~146 component files, 11 pages, and 9 layout files across the frontend, ensuring all color usage adheres to the Celestial design system and meets WCAG 2.1 AA contrast standards.

## Prerequisites

- Node.js (latest LTS)
- Access to the repository: `Boykai/github-workflows`
- Branch: `037-theme-contrast-audit` (or child branch from `copilot/speckit-specify-audit-light-dark-theme`)

## Setup

```bash
cd frontend
npm install
npm run dev          # Start dev server on localhost:5173
```

## Key Files

| File | Purpose |
|------|---------|
| `frontend/src/index.css` | **Primary audit target** — all theme tokens (`:root` + `.dark`), `@theme` block, solar-* utility classes |
| `frontend/src/components/ThemeProvider.tsx` | Theme context provider — toggle mechanism, transition handling |
| `frontend/src/layout/Sidebar.tsx` | Theme toggle button (Sun/Moon icon) |
| `frontend/src/components/ui/button.tsx` | Button variants (CVA) — all interactive states |
| `frontend/src/components/ui/input.tsx` | Input component — focus/disabled states |
| `frontend/src/components/ui/card.tsx` | Card component — surface/border tokens |
| `frontend/src/components/ui/tooltip.tsx` | Tooltip — portal-rendered, theme inheritance |
| `frontend/src/components/board/colorUtils.ts` | GitHub status color mappings (hardcoded) |
| `frontend/src/components/board/IssueCard.tsx` | Issue cards with dynamic label colors |
| `frontend/src/components/agents/AgentAvatar.tsx` | SVG avatar icons with hardcoded fills |
| `frontend/src/test/a11y-helpers.ts` | Accessibility test utilities (jest-axe) |

## Architecture Quick Reference

### Theme System

```
ThemeProvider (React Context)
  ↓ sets class on <html>
  ├── .light → :root CSS vars active
  └── .dark  → .dark CSS vars active
       ↓ CSS inheritance
       All components receive theme via hsl(var(--token))
```

### Token Flow

```
index.css :root / .dark
  → --background: 41 82% 95% / 236 28% 7%
    → @theme block: --color-background: hsl(var(--background))
      → Tailwind class: bg-background
        → Component: className="bg-background text-foreground"
```

### Audit Categories

1. **Token compliance** (FR-001): Scan for hardcoded colors → replace with tokens
2. **Contrast verification** (FR-002, FR-003): Check all foreground/background pairs against WCAG AA
3. **Interactive states** (FR-004): Verify hover/focus/active/disabled in both themes
4. **Component consistency** (FR-005): Visual review of all variant × theme combinations
5. **Token alignment** (FR-006, FR-007, FR-008): No pure black/white; remove stale tokens
6. **Theme-switch stability** (FR-009): Toggle without FOUC or layout shift
7. **Third-party audit** (FR-010): Radix UI components inherit theme
8. **Token documentation** (FR-011): Update token-registry.md with changes

## Testing Commands

```bash
# Type checking
npm run type-check

# Linting (includes jsx-a11y plugin)
npm run lint

# Run all tests
npx vitest run

# Run accessibility-focused tests
npm run test:a11y

# Run specific component tests
npx vitest run src/components/ui/button.test.tsx
```

## Contrast Checking

The WCAG 2.1 contrast ratio formula:

```
Relative luminance: L = 0.2126 * R_linear + 0.7152 * G_linear + 0.0722 * B_linear
Where R_linear = (R/255)^2.2 (simplified gamma)

Contrast ratio = (L_lighter + 0.05) / (L_darker + 0.05)

Thresholds:
  Normal text (< 18px or < 14px bold): ≥ 4.5:1
  Large text (≥ 18px or ≥ 14px bold):  ≥ 3.0:1
  UI component boundaries:              ≥ 3.0:1
```

## Known Issues to Address

1. **Shadow tokens** (`@theme` block): Use hardcoded `rgba()` — not theme-aware
2. **Priority tokens** (P0-P3): Identical in Light and Dark — may need lightness adjustment
3. **colorUtils.ts**: GitHub status colors are hardcoded — verify contrast in both themes
4. **IssueCard.tsx**: Pipeline/Agent badge colors hardcoded — verify contrast

## Implementation Order (recommended)

1. Start with `index.css` token corrections (shadows, any token value adjustments)
2. Scan and fix component files for hardcoded colors
3. Verify contrast ratios programmatically for all token pairs
4. Manual review of interactive states per component
5. Theme-switch stability testing across all pages
6. Document all changes in token-registry.md

## Related Artifacts

- [Specification](./spec.md) — Full requirements and acceptance criteria
- [Plan](./plan.md) — Implementation plan and technical context
- [Research](./research.md) — Research decisions and rationale
- [Data Model](./data-model.md) — Entity definitions and relationships
- [Audit Checklist](./contracts/audit-checklist.md) — Systematic audit procedure
- [Token Registry](./contracts/token-registry.md) — Living token reference
