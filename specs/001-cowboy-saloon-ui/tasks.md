# Tasks: Cowboy Saloon UI

**Input**: Design documents from `/specs/001-cowboy-saloon-ui/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/ui-only.md
**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup

**Purpose**: Project initialization and basic structure

- [x] T001 Find or create 3 fallback generic SVG cowboy avatars (e.g. Sheriff, Bandit, generic) in `frontend/src/assets/avatars/sheriff.svg`, `frontend/src/assets/avatars/bandit.svg`, and `frontend/src/assets/avatars/generic.svg`

---

## Phase 2: Foundational

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [x] T002 Update Tailwind configuration in `frontend/tailwind.config.js` to ensure the correct theme variable usage and add any new western fonts or colors if conceptually needed.

---

## Phase 3: User Story 1 - Enjoyable & Western-Themed Visuals (Priority: P1) 🎯 MVP

**Goal**: Update the visual colors, backgrounds, and themes to a warm rustic "Cowboy Saloon" aesthetic supporting dynamic dark mode.

**Independent Test**: Can be safely tested by opening the app locally, viewing the main containers, and manually switching the theme toggle to see light and dark variants.

### Implementation for User Story 1

- [x] T003 [US1] Update light mode css variables (`:root`) in `frontend/src/index.css` to warm rustic browns and golds instead of the default shadcn variables.
- [x] T004 [US1] Update dark mode css variables (`.dark`) in `frontend/src/index.css` to an appropriate high-contrast dark western look.
- [x] T005 [US1] Inject custom western web-safe fonts globally within `frontend/src/index.css`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. You should see the colors applied system-wide.

---

## Phase 4: User Story 2 - Distinct Cowboy Agent Avatars (Priority: P2)

**Goal**: Agent slugs map directly to stylized distinct cowboy icon avatars across the UI.

**Independent Test**: Agent list items in the system display a sheriff, bandit, or generic vector avatar instead of any plain fallback.

### Implementation for User Story 2

- [x] T006 [P] [US2] Abstract a small localized `<CowboyAvatar slug={slug} />` component in `frontend/src/components/CowboyAvatar.tsx`.
- [x] T007 [P] [US2] Integrate `<CowboyAvatar />` layout in `frontend/src/components/board/AgentTile.tsx`.
- [x] T008 [P] [US2] Integrate `<CowboyAvatar />` layout in `frontend/src/components/board/AgentConfigRow.tsx`.
- [x] T009 [P] [US2] Integrate `<CowboyAvatar />` layout in `frontend/src/components/board/AgentColumnCell.tsx`.

**Checkpoint**: Agents now load visually with cowboy avatars instead of standard avatars.

---

## Phase 5: User Story 3 - Responsive and Dynamic Interaction Elements (Priority: P3)

**Goal**: Components remain fluid, attractive, and responsive with interactive bouncy animations mirroring saloon-like reactions.

**Independent Test**: Resizing UI on the page adapts elements properly, and hovering interactable elements shows dynamic scale/bounciness.

### Implementation for User Story 3

- [x] T010 [P] [US3] Add interactive hover/active states (e.g. `hover:scale-105 active:scale-95 transition-transform duration-200`) to the Button component in `frontend/src/components/ui/button.tsx`.
- [x] T011 [P] [US3] Add hover motion adjustments to Agent Tiles in `frontend/src/components/board/AgentTile.tsx`.
- [x] T012 [P] [US3] Validate and apply responsive flex/grid wrappers correctly if needed in `frontend/src/pages/ProjectBoardPage.tsx` to handle narrower viewport scales properly for the new aesthetics.

**Checkpoint**: Application flows dynamically and reacts distinctly to hovers. No overlaps on mobile viewing.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T013 Verify execution aligns with no bundle-bloat parameters.
- [x] T014 Run validation quickstart locally `npm run dev`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed sequentially in priority order (P1 → P2 → P3), or parallel if developers have specific boundaries.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Color configuration mapping.
- **User Story 2 (P2)**: UI Avatar injection logic (Requires Layout updates).
- **User Story 3 (P3)**: Interactive states applied correctly over the colored layouts.

### Parallel Opportunities

- Components mapping the Cowboy Avatar (T007, T008, T009) can run in parallel since they touch isolated files in the board.
- Interaction additions (T010, T011) can run parallel to Avatar injections safely without structural conflicts.

---

## Parallel Example: User Story 2

```bash
# Launch generic avatar integration concurrently:
Task: "Integrate <CowboyAvatar /> in frontend/src/components/board/AgentTile.tsx"
Task: "Integrate <CowboyAvatar /> in frontend/src/components/board/AgentConfigRow.tsx"
Task: "Integrate <CowboyAvatar /> in frontend/src/components/board/AgentColumnCell.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1 (Base Styles updated)
4. **STOP and VALIDATE**: Test CSS variables manually on elements using Vite's live server.
