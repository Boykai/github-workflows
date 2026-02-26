# Implementation Plan: Move Chat Experience to Project-Board Page as Pop-Up Module & Simplify Homepage

**Branch**: `011-chat-popup-homepage` | **Date**: 2026-02-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/011-chat-popup-homepage/spec.md`

## Summary

Relocate the chat interface from the homepage (currently the default "chat" view in `App.tsx`) to the project-board page as a floating pop-up module. The homepage becomes a minimal landing page showing only the navigation bar and a centered "Create Your App Here" CTA that links to the project board. The chat pop-up on the project-board page is a self-contained `ChatPopup` component with toggle button, open/close animation (CSS transitions), session-state persistence (React local state), and responsive/accessible design. No backend changes required — this is a frontend-only refactor.

## Technical Context

**Language/Version**: TypeScript ~5.4, React 18.3  
**Primary Dependencies**: React, @tanstack/react-query, socket.io-client, Vite 5.4  
**Storage**: N/A (no new storage; chat pop-up open/closed state is in-memory React state)  
**Testing**: Vitest (unit), Playwright (e2e)  
**Target Platform**: Web (desktop + mobile browsers)  
**Project Type**: Web application (frontend + backend)  
**Performance Goals**: Smooth 60fps open/close animation; no chat-related network requests on homepage  
**Constraints**: No new dependencies; use existing CSS transitions for animation; maintain all existing chat functionality  
**Scale/Scope**: ~6 files modified/created in frontend; 0 backend changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | `spec.md` exists with prioritized user stories, GWT scenarios, scope boundaries |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase produces plan.md, research.md, data-model.md, contracts/, quickstart.md |
| IV. Test Optionality | ✅ PASS | Tests not explicitly mandated in spec; will be included only if existing test infrastructure is impacted |
| V. Simplicity and DRY | ✅ PASS | Extract ChatPopup as single self-contained component; no premature abstractions; CSS transitions over new library |

**Gate Result**: ✅ ALL PASS — Proceed to Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/011-chat-popup-homepage/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (component contracts)
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── App.tsx                              # MODIFY: Replace chat view with homepage CTA; remove chat imports
│   ├── App.css                              # MODIFY: Add homepage-hero styles; remove chat-section styles if unused
│   ├── components/
│   │   └── chat/
│   │       ├── ChatInterface.tsx            # EXISTING: No changes needed
│   │       ├── ChatInterface.css            # EXISTING: No changes needed
│   │       ├── ChatPopup.tsx                # NEW: Self-contained chat pop-up with toggle, animation, state
│   │       └── ChatPopup.css                # NEW: Popup positioning, animation, responsive styles
│   └── pages/
│       └── ProjectBoardPage.tsx             # MODIFY: Import and render ChatPopup
```

**Structure Decision**: Web application layout (frontend + backend). Only the `frontend/` directory is modified. The backend requires zero changes since this is a purely presentational/layout refactor. The chat API integration remains identical — it's just rendered in a different location.

## Complexity Tracking

> No violations to justify — all changes follow simplicity principles.
