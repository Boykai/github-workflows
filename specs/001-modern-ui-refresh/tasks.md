# Tasks: Modern UI Refresh

**Input**: Design documents from `/specs/001-modern-ui-refresh/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/theme.ts, quickstart.md

**Tests**: Tests are OPTIONAL for this UI refresh feature as per the plan. Existing E2E tests must pass.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for Tailwind and Shadcn UI.

- [x] T001 Install Tailwind CSS, PostCSS, Autoprefixer in `frontend/package.json`
- [x] T002 Initialize Tailwind configuration in `frontend/tailwind.config.js`
- [x] T003 Install Shadcn UI dependencies (`class-variance-authority`, `clsx`, `tailwind-merge`, `lucide-react`) in `frontend/package.json`
- [x] T004 Initialize Shadcn UI configuration in `frontend/components.json`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

- [x] T005 Implement ThemeProvider context in `frontend/src/components/ThemeProvider.tsx` based on `contracts/theme.ts`
- [x] T006 Add theme toggle hook in `frontend/src/hooks/useTheme.ts`
- [x] T007 Wrap application with ThemeProvider in `frontend/src/main.tsx`
- [x] T008 Setup global CSS variables for light/dark themes in `frontend/src/index.css`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Distinctive Visual Identity (Priority: P1) 🎯 MVP

**Goal**: Establish the core visual language (colors, typography, spacing) to address the "NOT AI vibe coded" requirement.

**Independent Test**: Can be fully tested by reviewing the global stylesheet, typography choices, and color palette implementation across a representative sample page.

### Implementation for User Story 1

- [x] T009 [US1] Update `frontend/tailwind.config.js` with custom typography scale and developer-focused color palette
- [x] T010 [US1] Update `frontend/src/index.css` with specific color variables for the new palette
- [x] T011 [US1] Update `frontend/index.html` to include the new modern font (e.g., Inter or Geist)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. The app should have a new font and base colors.

---

## Phase 4: User Story 2 - Refined Layout and Spacing (Priority: P2)

**Goal**: Navigate an interface with intentional whitespace and structured layouts.

**Independent Test**: Can be fully tested by inspecting the grid system, margins, and padding on core pages across different screen sizes.

### Implementation for User Story 2

- [x] T012 [US2] Refactor main layout container in `frontend/src/App.tsx` to use new spacing scale and responsive layout
- [x] T013 [US2] Update Dashboard/Project view layout in `frontend/src/App.tsx` (or main view component) to use CSS Grid/Flexbox with generous gaps
- [x] T014 [US2] Update Navigation/Header component in `frontend/src/App.tsx` (or dedicated component) for better spacing and responsive design

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. The app should look structurally sound with good whitespace.

---

## Phase 5: User Story 3 - Polished Interactive Elements (Priority: P3)

**Goal**: Buttons, forms, and interactive elements have subtle, high-quality feedback.

**Independent Test**: Can be fully tested by interacting with forms, buttons, and navigation menus to observe hover, focus, and active states.

### Implementation for User Story 3

- [x] T015 [P] [US3] Add Shadcn Button component in `frontend/src/components/ui/button.tsx`
- [x] T016 [P] [US3] Add Shadcn Input component in `frontend/src/components/ui/input.tsx`
- [x] T017 [P] [US3] Add Shadcn Card component in `frontend/src/components/ui/card.tsx`
- [x] T018 [US3] Replace legacy buttons with new Button component in `frontend/src/App.tsx` and other core components
- [x] T019 [US3] Replace legacy inputs with new Input component in `frontend/src/App.tsx` and other core components
- [x] T020 [US3] Replace legacy containers with new Card component in `frontend/src/App.tsx`

**Checkpoint**: All user stories should now be independently functional. The app should feel polished and interactive.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [ ] T021 Audit accessibility (color contrast, aria labels) across updated components
- [ ] T022 Verify dark mode toggle works across all updated components
- [x] T023 Clean up unused legacy CSS in `frontend/src/App.css` and `frontend/src/index.css`
- [x] T024 Run existing E2E tests (`npm run test:e2e`) to ensure no regressions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 visual identity
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Integrates with US1 and US2 layouts

### Parallel Opportunities

- All Setup tasks can run sequentially as they build on each other.
- Foundational tasks T005 and T006 can run in parallel.
- UI Component creation tasks (T015, T016, T017) marked [P] can run in parallel.

---

## Parallel Example: User Story 3

```bash
# Launch all UI component creations for User Story 3 together:
Task: "Add Shadcn Button component in frontend/src/components/ui/button.tsx"
Task: "Add Shadcn Input component in frontend/src/components/ui/input.tsx"
Task: "Add Shadcn Card component in frontend/src/components/ui/card.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Visual Identity)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories
