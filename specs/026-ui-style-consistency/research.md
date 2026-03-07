# Research: Audit & Update UI Components for Style Consistency

**Feature Branch**: `026-ui-style-consistency`  
**Date**: 2026-03-07

## R1: Current Theme Token Inventory

**Decision**: The existing theme system in `index.css` is complete and correct — no token additions or changes needed.  
**Rationale**: The app uses HSL CSS custom properties in `:root` (light) and `.dark` (dark) selectors. The token set covers all required categories: backgrounds (`--background`, `--card`, `--popover`, `--panel`), foregrounds (`--foreground`, `--card-foreground`, `--muted-foreground`), accent/brand colors (`--primary`, `--secondary`, `--accent`, `--gold`, `--glow`), destructive (`--destructive`), borders (`--border`, `--input`), and shadows (`--shadow-sm` through `--shadow-lg`). The `--radius: 1rem` base is established. Priority colors (`--priority-p0` through `--priority-p3`) are defined for both modes. The token architecture is sound and maps cleanly to Tailwind's `bg-*`, `text-*`, `border-*` utilities via `hsl(var(--token))`.  
**Alternatives considered**:
- Adding new tokens for status colors (connected/disconnected/warning) — Rejected because Tailwind's built-in semantic colors (green, yellow, red) with `dark:` prefixes are the established pattern in the codebase for status indicators, and the volume is small enough to centralize in constants rather than CSS variables.

## R2: cn() Utility Adoption Strategy

**Decision**: Adopt `cn()` (from `lib/utils.ts`) across all components that use conditional or composed class names. Leave components with purely static class strings unchanged.  
**Rationale**: The `cn()` utility (clsx + tailwind-merge) is already the standard in the base UI components (`button.tsx`, `card.tsx`, `input.tsx`) and in `ChatInterface.tsx`. However, ~94 of 98 component files use raw template literals (`` `${condition ? 'class-a' : 'class-b'}` ``) for conditional classes. Template literals can produce Tailwind conflicts (e.g., two `bg-*` classes both being applied) and are harder to read. `cn()` resolves conflicts automatically and improves readability. The migration is mechanical: replace `` className={`...${ternary}...`} `` with `className={cn('base-classes', condition && 'conditional-class')}`.  
**Alternatives considered**:
- clsx only (without tailwind-merge) — Insufficient; doesn't resolve Tailwind class conflicts.
- CVA for all components — Overkill for components without variant systems. CVA is appropriate for the base UI kit (button, card, input) but not for domain components with simple conditional styling.

## R3: Centralized Status/State Color Constants

**Decision**: Add centralized color constant maps to `constants.ts` for recurring status and state patterns: signal connection status, agent source type, chore status, sync status, and general operational states.  
**Rationale**: The audit found 18+ files with duplicated hardcoded color classes for the same semantic concepts. For example, "connected" status uses `bg-green-500/10 text-green-600 dark:text-green-400` in SignalConnection.tsx, McpSettings.tsx, and CleanUpSummary.tsx. "Warning" uses `bg-yellow-500/10 text-yellow-600 dark:text-yellow-400` across 5+ files. Centralizing these into named constants (e.g., `STATUS_COLORS.success`, `STATUS_COLORS.warning`, `STATUS_COLORS.error`) eliminates duplication and ensures changes propagate automatically.  
**Alternatives considered**:
- CSS custom properties for status colors — The existing HSL token system works for the core theme, but status colors are Tailwind utility combinations (bg + text + dark variants), not single HSL values. Keeping them as string constants in TypeScript is simpler and consistent with how `PRIORITY_COLORS` is already implemented.
- Tailwind @apply directives — Would require creating custom CSS classes for each status color combination. This adds indirection without meaningful benefit over TypeScript constants.

## R4: Handling Third-Party Component Styles

**Decision**: Document third-party style conflicts as known exceptions. Do not modify third-party library CSS. Apply wrapper-level theme alignment where needed.  
**Rationale**: The app uses `@dnd-kit` for drag-and-drop, which injects its own inline styles for drag overlays and transforms. These are functional (position, transform, opacity) not decorative, so they don't conflict with the theme system. The `@radix-ui/react-slot` is headless (no styles). Lucide icons inherit `currentColor` and scale with `font-size`, so they automatically adapt to the theme. No third-party style conflicts were identified that require remediation.  
**Alternatives considered**:
- Wrapping dnd-kit with custom styled components — Unnecessary; dnd-kit styles are transform-based and don't affect colors/typography.

## R5: Arbitrary Tailwind Values Assessment

**Decision**: Preserve existing arbitrary values (e.g., `rounded-[1.75rem]`, `w-[280px]`) where they serve intentional one-off design purposes. Document them as intentional exceptions.  
**Rationale**: The spec's edge cases section explicitly states that "inline styles for a legitimate one-off visual treatment should be explicitly documented as intentional exceptions." Arbitrary Tailwind values in `LoginPage.tsx` (`rounded-[1.75rem]`, `w-[280px]`, `bottom-[7.4rem]`) and `ProjectsPage.tsx` (`rounded-[1.75rem]`, `rounded-[1.25rem]`) are for specific layout needs that don't have standard Tailwind equivalents. These are semantically equivalent to using the Tailwind utility system (just with custom values) and don't represent theme token violations.  
**Alternatives considered**:
- Extending the Tailwind theme with custom spacing/radius values — Adds configuration complexity for values used in only 1-2 places each. Violates YAGNI.

## R6: Visual Regression Verification Strategy

**Decision**: Manual visual verification against before/after screenshots, supplemented by existing Vitest + Playwright tests.  
**Rationale**: The spec requires "no visual regressions" (FR-008, SC-004) but does not mandate automated visual regression testing tools. The existing test suite (Vitest unit tests, Playwright E2E) verifies functional behavior. Visual verification is done by: (1) capturing screenshots of all 6 pages in both light and dark modes before changes, (2) applying remediation changes page by page, (3) comparing the updated rendering against baseline screenshots. Since changes are limited to token replacement (not layout restructuring), visual differences should be minimal to none.  
**Alternatives considered**:
- Percy or Chromatic for automated visual regression — Adds a new dependency and service integration, which is out of scope. The change volume is manageable with manual verification.
- Playwright screenshot comparison — Feasible but requires baseline management infrastructure. Worth considering for future features but not justified for this audit-only scope.

## R7: Deprecated/Unused Component Identification

**Decision**: Identify components with zero import references and flag them for removal. Run tree-shaking analysis via build to confirm no dynamic imports.  
**Rationale**: The spec requires removal of deprecated or unused components (FR-009, US5). The approach is: (1) For each component file in `frontend/src/components/`, search the codebase for import statements referencing it. (2) Any file with zero import references is flagged. (3) Before deletion, run `npm run build` to verify no missing-module errors. (4) After deletion, run existing tests to confirm no breakage. The preliminary audit did not identify obviously dead components (all components in `components/` directories appear to have active imports), but the formal audit in implementation will do a complete reference scan.  
**Alternatives considered**:
- Static analysis tools (e.g., ts-unused-exports) — Could be used as a supplement, but a manual import search is more reliable for this codebase size and catches dynamic imports.

## R8: Dark Mode Verification Approach

**Decision**: Verify every remediated component in both light and dark modes by toggling the theme during visual review.  
**Rationale**: The theme system uses the `.dark` class on `document.documentElement`, toggled by `ThemeProvider.tsx` via `localStorage('vite-ui-theme')`. All semantic Tailwind classes (`bg-primary`, `text-foreground`, etc.) automatically adapt. The `dark:` prefix classes (e.g., `dark:bg-accent/20`) provide explicit dark-mode overrides. The risk area is components where hardcoded colors are replaced with theme tokens — the dark-mode equivalent must be verified. The ThemeProvider supports `"dark"`, `"light"`, and `"system"` modes, so testing should cover explicit dark/light toggles.  
**Alternatives considered**:
- Automated dark mode screenshot testing — Same considerations as R6; manual is sufficient for this scope.
