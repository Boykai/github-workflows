# Implementation Plan: Move Chat Experience to Project-Board Page as Pop-Up Module & Simplify Homepage

**Branch**: `011-chat-popup-homepage` | **Date**: 2026-02-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/011-chat-popup-homepage/spec.md`

## Summary

Relocate the chat interface from the homepage to the project-board page as a floating pop-up module, and simplify the homepage to display only the navigation bar and a centered "Create Your App Here" CTA. The chat pop-up is a self-contained component with toggle state, smooth open/close animation, and responsive layout. No new backend changes are required — this is a frontend-only refactor affecting `App.tsx`, `ProjectBoardPage.tsx`, and introducing a new `ChatPopup` component.

## Technical Context

**Language/Version**: TypeScript ~5.4, React 18.3  
**Primary Dependencies**: React 18.3, TanStack Query v5, Vite 5, socket.io-client 4.7  
**Storage**: N/A (no backend/storage changes)  
**Testing**: vitest ≥4.0 (frontend unit), Playwright ≥1.58 (E2E)  
**Target Platform**: Browser SPA (desktop + mobile)  
**Project Type**: Web application (frontend-only changes)  
**Performance Goals**: Chat pop-up toggle animation < 300ms, no chat-related API calls on homepage  
**Constraints**: Must not break existing chat functionality, responsive across 320px–1920px viewports  
**Scale/Scope**: ~5 frontend source files modified/created, 1 new CSS file

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | `spec.md` created with 4 prioritized user stories (P1, P2), GWT acceptance scenarios, edge cases, and success criteria |
| II. Template-Driven | ✅ PASS | Using canonical `plan.md` template, all artifacts follow `.specify/templates/` |
| III. Agent-Orchestrated | ✅ PASS | Plan phase produces plan.md, research.md, data-model.md, contracts/, quickstart.md |
| IV. Test Optionality | ✅ PASS | Tests not explicitly mandated in spec — existing tests should continue to pass. New tests optional but recommended for ChatPopup toggle behavior. |
| V. Simplicity and DRY | ✅ PASS | Extracting chat into a self-contained `ChatPopup` component reuses the existing `ChatInterface` directly — no new abstractions, no premature generalization. CSS transitions used instead of adding an animation library. |

**Gate result: PASS** — no violations, no complexity justification needed.

### Post-Design Re-Evaluation

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | All design artifacts trace back to spec.md FRs (FR-001 through FR-011). No scope creep. |
| II. Template-Driven | ✅ PASS | All artifacts (plan.md, research.md, data-model.md, contracts/, quickstart.md) follow canonical templates. |
| III. Agent-Orchestrated | ✅ PASS | Phase 0 and Phase 1 complete with clear handoff to Phase 2 (tasks). |
| IV. Test Optionality | ✅ PASS | No tests mandated. Existing vitest and Playwright suites cover regression. Optional unit test for ChatPopup toggle state noted in quickstart. |
| V. Simplicity and DRY | ✅ PASS | ChatPopup wraps existing ChatInterface — zero duplication of chat logic. Homepage simplification removes code rather than adding it. CSS transitions (no new library) for animation. Local `useState` for toggle — simplest possible state management. |

**Post-design gate result: PASS**

## Project Structure

### Documentation (this feature)

```text
specs/011-chat-popup-homepage/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── App.tsx                              # FR-001, FR-002, FR-011: Remove chat from homepage view, add "Create Your App Here" CTA, remove chat API calls on homepage
│   ├── App.css                              # FR-002: Add homepage hero styles
│   ├── components/
│   │   └── chat/
│   │       ├── ChatPopup.tsx                # FR-003, FR-004, FR-005, FR-006, FR-007, FR-008: New floating chat pop-up wrapper component
│   │       ├── ChatPopup.css                # FR-003, FR-007, FR-008, FR-010: Pop-up positioning, animation, responsive styles
│   │       └── ChatInterface.tsx            # No changes — reused inside ChatPopup
│   ├── pages/
│   │   └── ProjectBoardPage.tsx             # FR-003: Integrate ChatPopup component
│   └── hooks/
│       └── useChat.ts                       # No changes — reused by ChatPopup via prop drilling from ProjectBoardPage
```

**Structure Decision**: Web application (existing `frontend/` structure). One new component file (`ChatPopup.tsx`) and one new CSS file (`ChatPopup.css`). All other changes are modifications to existing files. No backend changes required.

## Complexity Tracking

> No constitution violations detected. No complexity justification needed.
