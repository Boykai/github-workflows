# Implementation Plan: Fix Screen Scrolling Getting Stuck Intermittently

**Branch**: `030-fix-scroll-stuck` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/030-fix-scroll-stuck/spec.md`

## Summary

Users experience intermittent scroll freezing across the application. Investigation reveals the primary root cause is a **modal scroll-lock race condition**: multiple modal components independently set `document.body.style.overflow = 'hidden'` on open and unconditionally reset it to `''` on close. When modals are opened/closed in sequence or nested, the last modal to close resets overflow to empty string even if another modal is still open — or conversely, leaves overflow as `hidden` after all modals are closed if the cleanup order is wrong. The fix introduces a centralized `useScrollLock` hook with a reference-counting mechanism, ensuring `document.body.style.overflow` is only restored when all scroll-locking consumers have released their lock. Additionally, capture-phase scroll event listeners used for popover repositioning should use `passive: true` to avoid blocking scroll input.

## Technical Context

**Language/Version**: TypeScript / Node.js 22 (frontend), Python 3.13 (backend — no changes needed)
**Primary Dependencies**: React 19, Tailwind CSS, @dnd-kit (drag-and-drop), @radix-ui/react-tooltip, @radix-ui/react-slot
**Storage**: N/A (frontend-only fix)
**Testing**: Vitest (frontend)
**Target Platform**: Web browser (Chrome, Firefox, Safari — desktop and mobile)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: 60 fps scrolling; zero perceptible lag during scroll
**Constraints**: Must not break existing scroll-dependent UI (dropdowns, drag-and-drop, infinite scroll, modals); must work across Chrome, Firefox, Safari, and mobile touch devices
**Scale/Scope**: ~11 frontend files modified (new shared hook + 6 modal components + 4 scroll-listener components) plus associated test files, 0 new dependencies, 0 backend changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | spec.md complete with 4 prioritized user stories, Given-When-Then acceptance scenarios, edge cases |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated Execution | ✅ PASS | Bug fix within existing frontend components; no new agents needed |
| IV. Test Optionality with Clarity | ✅ PASS | Tests not explicitly mandated in spec; existing Vitest suite covers modal components — unit tests for the new `useScrollLock` hook should be added to validate the reference-counting logic |
| V. Simplicity and DRY | ✅ PASS | Centralizes duplicated scroll-lock logic from 6 components into one shared hook — reduces duplication, not premature abstraction |

**Gate result**: ✅ PASS — No violations. Proceed to Phase 0.

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | All user stories have corresponding implementation tasks mapped |
| II. Template-Driven Workflow | ✅ PASS | All artifacts generated from canonical templates |
| III. Agent-Orchestrated Execution | ✅ PASS | No new agents; existing component structure preserved |
| IV. Test Optionality with Clarity | ✅ PASS | Unit tests for `useScrollLock` hook validate reference-counting logic; existing modal tests remain valid |
| V. Simplicity and DRY | ✅ PASS | Single `useScrollLock` hook replaces 6 independent scroll-lock implementations; no over-abstraction |

**Gate result**: ✅ PASS — No violations post-design.

## Project Structure

### Documentation (this feature)

```text
specs/030-fix-scroll-stuck/
├── plan.md              # This file
├── research.md          # Phase 0 output — research decisions
├── data-model.md        # Phase 1 output — behavioral model changes
├── quickstart.md        # Phase 1 output — developer guide
├── contracts/
│   └── components.md    # Phase 1 output — frontend component behavior changes
├── checklists/
│   └── requirements.md  # Specification quality checklist (already exists)
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── hooks/
│   │   └── useScrollLock.ts           # NEW: Centralized scroll-lock hook with ref-counting
│   ├── components/
│   │   ├── board/
│   │   │   ├── IssueDetailModal.tsx   # MODIFY: Replace manual scroll lock with useScrollLock
│   │   │   ├── CleanUpConfirmModal.tsx # MODIFY: Replace manual scroll lock with useScrollLock
│   │   │   ├── CleanUpSummary.tsx      # MODIFY: Replace manual scroll lock with useScrollLock
│   │   │   ├── CleanUpAuditHistory.tsx # MODIFY: Replace manual scroll lock with useScrollLock
│   │   │   └── AddAgentPopover.tsx     # MODIFY: Add passive option to scroll listener
│   │   ├── agents/
│   │   │   └── AgentIconPickerModal.tsx # MODIFY: Replace manual scroll lock with useScrollLock
│   │   └── pipeline/
│   │       ├── PipelineToolbar.tsx      # MODIFY: Replace manual scroll lock with useScrollLock
│   │       ├── ModelSelector.tsx        # MODIFY: Add passive option to scroll listener
│   │       └── StageCard.tsx            # MODIFY: Add passive option to scroll listener
│   └── layout/
│       └── NotificationBell.tsx         # MODIFY: Add passive option to scroll listener
└── tests/
```

**Structure Decision**: Web application structure. Changes are frontend-only, concentrated in the `frontend/src/` directory. A new shared hook (`useScrollLock.ts`) centralizes the scroll-lock logic currently duplicated across 6 modal components.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.
