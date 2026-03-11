# Tasks: Audit & Polish the Projects Page

**Feature Branch**: `033-projects-page-audit`
**Date**: 2026-03-10

## Phase 1 — Accessibility Fixes (P1/P2)

- [X] T-001: Add focus trap to IssueDetailModal (Tab cycles within modal, Escape closes, focus returns to trigger)
- [X] T-002: Add `aria-labelledby` to IssueDetailModal dialog referencing the heading element
- [X] T-003: Add `focus-visible` ring to IssueDetailModal close button
- [X] T-004: Add `aria-expanded` to IssueCard sub-issues toggle button
- [X] T-005: Add `disabled` and `aria-disabled` to BoardColumn "Coming soon" placeholder button
- [X] T-006: Add `role="region"` and `aria-label` to ProjectBoard container
- [X] T-007: Add `aria-expanded` to BlockingChainPanel toggle button
- [X] T-008: Add `aria-label` to BlockingChainPanel close button
- [X] T-009: Update IssueDetailModal test to match new `aria-labelledby` attribute

## Phase 2 — Responsive Layout Fixes

- [X] T-010: Fix ProjectBoard grid `minmax(14rem, 1fr)` to `minmax(min(14rem, 85vw), 1fr)` for mobile
- [X] T-011: Fix ProjectSelector `min-w-[20rem]` to `min-w-[min(20rem,calc(100vw-3rem))]` for mobile
- [X] T-012: Fix pipeline stages grid to use responsive `minmax(min(14rem, 85vw), 1fr)` for mobile

## Phase 3 — Visual Consistency (Design Tokens)

- [X] T-013: Add `--sync-connected/polling/connecting/disconnected` CSS custom properties with light/dark variants
- [X] T-014: Replace hardcoded sync status indicator colors with `hsl(var(--sync-*))` references
- [X] T-015: Replace blocking toggle `bg-amber-500`/`text-amber-500` with `bg-gold`/`text-gold` design tokens

## Phase 4 — Performance Optimizations

- [X] T-016: Memoize `SubIssueRow` component in IssueCard with `memo()`

## Phase 5 — Validation

- [X] T-017: Verify all 597 tests pass
- [X] T-018: Verify TypeScript type-check clean
- [X] T-019: Verify ESLint lint clean (no new warnings)
