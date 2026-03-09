# Implementation Plan: Update User Chat Helper Text for Comprehensive UX Guidance

**Branch**: `031-chat-helper-text` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/031-chat-helper-text/spec.md`

## Summary

Update the chat input placeholder/helper text across all chat entry points in the Solune UI to provide comprehensive, actionable guidance that communicates supported interaction types. The current placeholders are either generic ("Type your response…") or specific to one chat context ("Describe a task, type / for commands, or @ for pipelines..."). This plan replaces them with descriptive, responsive copy that adapts between desktop and mobile viewports, ensures WCAG AA contrast compliance, keeps accessibility attributes in sync, and optionally introduces a cycling placeholder animation for progressive capability discovery. The change is frontend-only, touching 3 components (ChatInterface, AgentChatFlow, ChoreChatFlow) and the MentionInput placeholder renderer.

## Technical Context

**Language/Version**: TypeScript ~5.9 (frontend-only feature)
**Primary Dependencies**: React 19.2, Tailwind CSS v4.2, class-variance-authority 0.7, lucide-react 0.577
**Storage**: N/A — placeholder text is static; no database or localStorage changes
**Testing**: Vitest 4 + Testing Library + jest-axe (accessibility)
**Target Platform**: Desktop browsers (Chrome, Firefox, Safari, Edge); mobile browsers (responsive)
**Project Type**: Web application (frontend-only changes)
**Performance Goals**: Zero performance impact; placeholder text is static DOM content. Cycling animation (if implemented) must use CSS transitions or `requestAnimationFrame` with <16ms frame budget and no layout shifts.
**Constraints**: Must meet WCAG AA 4.5:1 contrast ratio; placeholder must not overflow input boundary on any viewport ≥320px; must not interfere with existing chat functionality (commands, mentions, submission); must respect `prefers-reduced-motion` for any animation.
**Scale/Scope**: 3 chat input components to update, 1 shared placeholder overlay to modify (MentionInput), 0 backend changes, 0 new dependencies for P1/P2 stories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 5 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, 10 functional requirements (FR-001–FR-010), 8 success criteria, edge cases, and assumptions |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan → tasks → implement) |
| **IV. Test Optionality** | ✅ PASS | Tests not explicitly mandated in spec; existing MentionInput tests should continue to pass; accessibility contrast verification recommended but not required |
| **V. Simplicity/DRY** | ✅ PASS | Copy update with optional centralized constants; no new abstractions, no new dependencies for core stories (P1/P2). Cycling placeholder (P3) may use a lightweight custom hook but no external libraries. |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace back to spec FRs (FR-001–FR-010) |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 |
| **IV. Test Optionality** | ✅ PASS | Existing MentionInput tests unaffected; no new test infrastructure required |
| **V. Simplicity/DRY** | ✅ PASS | Placeholder strings centralized in a single constants module (`chat-placeholders.ts`). Responsive behavior handled via Tailwind's existing `max-sm:hidden` / `sm:hidden` pattern — no custom hooks for breakpoint detection needed for static text. Cycling animation (P3) contained in a single `useCyclingPlaceholder` hook with `prefers-reduced-motion` fallback. Zero new dependencies. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/031-chat-helper-text/
├── plan.md              # This file
├── research.md          # Phase 0: Research decisions (R1–R4)
├── data-model.md        # Phase 1: Placeholder string definitions, responsive variants, type contracts
├── quickstart.md        # Phase 1: Developer guide for updating placeholder text
├── contracts/
│   └── components.md    # Phase 1: Component interface changes
├── checklists/
│   └── requirements.md  # Specification quality checklist (pre-existing)
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── constants/
│   │   └── chat-placeholders.ts         # NEW: Centralized placeholder copy for all chat inputs
│   ├── hooks/
│   │   └── useCyclingPlaceholder.ts     # NEW (P3 only): Hook for animated cycling placeholders
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatInterface.tsx        # MODIFIED: Import placeholder from constants; pass responsive variant
│   │   │   ├── MentionInput.tsx         # MODIFIED: Support responsive placeholder prop; update aria attributes
│   │   │   └── MentionInput.test.tsx    # EXISTING: Verify no regressions
│   │   ├── agents/
│   │   │   └── AgentChatFlow.tsx        # MODIFIED: Update placeholder from constants
│   │   └── chores/
│   │       └── ChoreChatFlow.tsx        # MODIFIED: Update placeholder from constants
│   └── index.css                        # REVIEW: Verify --muted-foreground contrast ratio (no changes expected)
```

**Structure Decision**: Web application (frontend-only). This feature is entirely a frontend concern — no backend changes, no database changes, no API changes. All changes are copy/UX updates to existing components plus one new constants file for centralized copy management. The optional cycling hook (P3) is a single-file addition in `hooks/`.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| Centralized constants file (`chat-placeholders.ts`) | Single source of truth for all chat placeholder strings; easy to audit, update, and maintain consistency across components (FR-007) | Inline strings per component (rejected: harder to audit consistency; violates DRY for shared copy patterns) |
| Tailwind responsive classes for mobile variant | The codebase already uses `max-sm:` / `max-md:` Tailwind prefixes extensively (ChatPopup, board components); no custom hook needed for static responsive text | Custom `useMediaQuery` hook (rejected: over-engineering for static text display; adds React state/effect overhead for a CSS-solvable problem) |
| CSS `hidden` approach for responsive placeholder | Render both desktop and mobile placeholder variants; toggle visibility with `max-sm:hidden` / `sm:hidden` Tailwind classes | JavaScript-based viewport detection (rejected: causes hydration mismatch risk; adds unnecessary JS execution for a presentation concern) |
| Optional P3 cycling hook (not a dependency) | Cycling placeholders are P3 and only implemented if framework supports them without accessibility harm; standalone hook with `prefers-reduced-motion` check | CSS-only animation (rejected: contentEditable placeholder is a custom overlay div, not a native placeholder — CSS `::placeholder` animations don't apply; JavaScript is necessary for text content cycling) |
