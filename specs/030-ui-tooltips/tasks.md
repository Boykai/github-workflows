# Tasks: Comprehensive Tooltips Across App UI for Feature Explainability and UX Guidance

**Input**: Design documents from `/specs/030-ui-tooltips/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/components.md, quickstart.md

**Tests**: Not explicitly requested in the feature specification. Existing tests must continue to pass.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/` for all frontend changes (no backend changes for this feature)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install the new dependency and prepare the project for tooltip development

- [x] T001 Install `@radix-ui/react-tooltip` (latest stable v1.x) dependency in frontend/package.json
- [x] T002 Create `frontend/src/constants/` directory for static data modules

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the core Tooltip component, content registry, and app-level provider that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Define `TooltipEntry` interface (`summary: string`, `title?: string`, `learnMoreUrl?: string`) and `TooltipContentRegistry` type, and create the registry scaffold with key naming convention (`{area}.{section}.{element}`) in frontend/src/constants/tooltip-content.ts
- [x] T004 Populate the tooltip content registry with all ~38 entries organized by area (board, chat, agents, pipeline, chores, settings, tools) with concise summary text for each interactive element in frontend/src/constants/tooltip-content.ts
- [x] T005 Create reusable `Tooltip` wrapper component built on `@radix-ui/react-tooltip` with `contentKey` and `content` props, registry lookup, graceful fallback for missing keys (render children only, `console.warn` in dev), and portal rendering in frontend/src/components/ui/tooltip.tsx
- [x] T006 Apply theme-aware styling to the Tooltip component using existing CSS custom properties (`bg-popover`, `text-popover-foreground`, `border-border/60`), directional arrow via `<TooltipArrow>`, max-width 280px, min font size 13px, `animate-in`/`animate-out` with `motion-reduce:animate-none` in frontend/src/components/ui/tooltip.tsx
- [x] T007 Re-export `TooltipProvider` from the Tooltip component module for use in App.tsx in frontend/src/components/ui/tooltip.tsx
- [x] T008 Wrap application root with `<TooltipProvider delayDuration={300} skipDelayDuration={300}>` around the existing `QueryClientProvider` in frontend/src/App.tsx

**Checkpoint**: Foundation ready — app builds without errors, TypeScript compiles, no visual changes yet (tooltips not wired to elements). User story implementation can now begin.

---

## Phase 3: User Story 1 — Tooltip on Interactive Elements (Priority: P1) 🎯 MVP

**Goal**: Display an informative tooltip on hover (desktop), long-press (mobile), and keyboard focus for every interactive UI element across the application, communicating each element's purpose and consequences.

**Independent Test**: Hover over any interactive element (button, toggle, dropdown, form field, icon, or slider) in the app and verify a tooltip appears after ~300ms with the element's name, purpose, and consequence description. Verify tooltip dismisses on mouse-out, touch-end, or Escape key.

### Implementation for User Story 1

- [x] T009 [P] [US1] Wrap refresh button with `<Tooltip contentKey="board.toolbar.refreshButton">` in frontend/src/components/board/RefreshButton.tsx
- [x] T010 [P] [US1] Wrap clean-up button with `<Tooltip contentKey="board.toolbar.cleanUpButton">` in frontend/src/components/board/CleanUpButton.tsx
- [x] T011 [P] [US1] Wrap filter, sort, and group controls with `<Tooltip>` using appropriate content keys in frontend/src/components/board/BoardToolbar.tsx
- [x] T012 [P] [US1] Wrap AI Enhance toggle, attach, voice, and send buttons with `<Tooltip>` using appropriate content keys in frontend/src/components/chat/ChatToolbar.tsx
- [x] T013 [P] [US1] Wrap history toggle and message actions with `<Tooltip>` using appropriate content keys in frontend/src/components/chat/ChatInterface.tsx
- [x] T014 [P] [US1] Wrap edit, delete, and model selector actions with `<Tooltip>` using appropriate content keys in frontend/src/components/agents/AgentCard.tsx
- [x] T015 [P] [US1] Wrap search input, sort, bulk update, and add agent controls with `<Tooltip>` using appropriate content keys in frontend/src/components/agents/AgentsPanel.tsx
- [x] T016 [P] [US1] Wrap system prompt field, tools editor, and model selection fields with `<Tooltip>` using appropriate content keys in frontend/src/components/agents/AddAgentModal.tsx
- [x] T017 [P] [US1] Wrap model selector and delete button with `<Tooltip>` using appropriate content keys in frontend/src/components/pipeline/StageCard.tsx
- [x] T018 [P] [US1] Wrap add stage, save, and delete pipeline buttons with `<Tooltip>` using appropriate content keys in frontend/src/components/pipeline/PipelineBoard.tsx
- [x] T019 [P] [US1] Wrap model dropdown with `<Tooltip>` using appropriate content key in frontend/src/components/pipeline/ModelSelector.tsx
- [x] T020 [P] [US1] Wrap execute, edit, delete, and AI Enhance toggle with `<Tooltip>` using appropriate content keys in frontend/src/components/chores/ChoreCard.tsx
- [x] T021 [P] [US1] Wrap theme toggle and model management controls with `<Tooltip>` using appropriate content keys in frontend/src/pages/SettingsPage.tsx and frontend/src/components/settings/ components
- [x] T022 [P] [US1] Wrap tool configure and status toggle controls with `<Tooltip>` using appropriate content keys in frontend/src/pages/ToolsPage.tsx and frontend/src/components/tools/ToolCard.tsx

**Checkpoint**: All interactive elements across the application have tooltips. Hovering over any button, toggle, dropdown, or control displays a contextual tooltip after ~300ms. Tooltips dismiss on mouse-out, touch-end, or Escape. User Story 1 is fully functional and testable independently.

---

## Phase 4: User Story 2 — Consistent Visual Design and Intelligent Positioning (Priority: P1)

**Goal**: Ensure all tooltips share a consistent visual design (dark/theme-aware background, light text, directional arrow, max-width ~280px, min 13px font) and automatically reposition (flip/shift) when they would be clipped by viewport edges.

**Independent Test**: Trigger tooltips on elements positioned near each viewport edge (top, bottom, left, right) and verify they flip to remain fully visible. Compare tooltip appearance across different UI sections — all should share identical styling. Toggle between light and dark theme and verify theme-aware colors.

### Implementation for User Story 2

- [x] T023 [US2] Verify and tune tooltip visual design consistency — ensure all tooltip instances render with `bg-popover`, `text-popover-foreground`, `border-border/60`, `max-w-[280px]`, `text-[13px]`, `rounded-lg`, `shadow-md`, and directional arrow across both light and dark themes in frontend/src/components/ui/tooltip.tsx
- [x] T024 [US2] Verify intelligent positioning — confirm Radix Tooltip `side` and `align` props produce correct flip behavior when tooltips are triggered near top, bottom, left, and right viewport edges; adjust `sideOffset` and `collisionPadding` values if needed in frontend/src/components/ui/tooltip.tsx
- [x] T025 [US2] Verify tooltips do not obstruct adjacent interactive elements — ensure z-index (50), portal rendering, and spacing prevent overlap with nearby clickable elements; adjust `sideOffset` or `collisionPadding` if needed in frontend/src/components/ui/tooltip.tsx

**Checkpoint**: Tooltips look identical across all pages and sections. Tooltips near viewport edges flip and shift correctly. No visual clipping or overlap issues. Theme toggle produces correct color adaptation.

---

## Phase 5: User Story 3 — Accessibility-Compliant Tooltips (Priority: P1)

**Goal**: Ensure all tooltips are fully accessible to keyboard-only and assistive-technology users with proper ARIA attributes, keyboard focus triggers, Escape dismiss, and WCAG 2.1 AA color contrast compliance.

**Independent Test**: Tab through the UI with a keyboard — tooltips should appear on focus. Press Escape — tooltips should dismiss. Inspect DOM for `aria-describedby` on trigger elements and `role="tooltip"` on tooltip content. Verify text-to-background contrast ratio meets 4.5:1 minimum.

### Implementation for User Story 3

- [x] T026 [US3] Verify Radix Tooltip provides `aria-describedby` on trigger elements and `role="tooltip"` on content automatically; add any missing ARIA attributes if needed in frontend/src/components/ui/tooltip.tsx
- [x] T027 [US3] Audit keyboard navigation across all pages — confirm tooltips appear when interactive elements receive keyboard focus via Tab and dismiss on Escape or focus loss; fix any focus-related issues in frontend/src/components/ui/tooltip.tsx
- [x] T028 [US3] Verify color contrast ratios meet WCAG 2.1 AA (minimum 4.5:1) for tooltip text on tooltip background in both light theme (`--popover-foreground` on `--popover`: ~10.2:1) and dark theme (~12.8:1); adjust CSS custom property usage if contrast is insufficient in frontend/src/components/ui/tooltip.tsx and frontend/src/index.css

**Checkpoint**: Full keyboard navigation works — tooltips trigger on Tab focus and dismiss on Escape. All ARIA attributes are present. Color contrast meets WCAG 2.1 AA in both themes. Automated accessibility audit returns zero critical violations from tooltip elements.

---

## Phase 6: User Story 4 — Progressive Disclosure for Complex Features (Priority: P2)

**Goal**: Support a two-tier progressive disclosure pattern where complex or high-impact features (agent configuration, pipeline decision nodes, irreversible settings) show a bolded title line + concise summary on first hover, with an optional "Learn more" link for deeper explanation.

**Independent Test**: Hover over a complex feature element (e.g., agent system prompt field, pipeline model selector, bulk model update button) — tooltip should show a bold title, summary text, and "Learn more" link. Hover over a simple element (e.g., refresh button) — tooltip should show only summary text with no title or "Learn more" link.

### Implementation for User Story 4

- [x] T029 [US4] Implement progressive disclosure rendering in the Tooltip component — render `title` field as bold `<p className="font-semibold">` heading above summary, render `learnMoreUrl` as a "Learn more →" link below summary, skip title/link when fields are absent in frontend/src/components/ui/tooltip.tsx
- [x] T030 [US4] Add `title` and `learnMoreUrl` fields to complex feature tooltip entries in the content registry — ensure entries for `agents.modal.systemPrompt`, `agents.modal.toolsEditor`, `agents.card.modelSelector`, `agents.panel.bulkUpdateButton`, `pipeline.stage.modelSelector`, `pipeline.board.savePipelineButton`, `chores.card.executeButton`, `chores.card.aiEnhanceToggle`, and `chat.toolbar.aiEnhanceToggle` include a bold title and optional learn more URL in frontend/src/constants/tooltip-content.ts
- [x] T031 [US4] Verify simple tooltip entries (e.g., `board.toolbar.refreshButton`, `agents.card.deleteButton`) in frontend/src/constants/tooltip-content.ts display only summary text without title or "Learn more" link

**Checkpoint**: Complex feature tooltips show bold title + summary + optional "Learn more" link. Simple tooltips show only summary text. Progressive disclosure pattern works correctly for all designated complex features.

---

## Phase 7: User Story 5 — Centralized Tooltip Content Management (Priority: P2)

**Goal**: Ensure all tooltip text is sourced from the centralized content registry (`frontend/src/constants/tooltip-content.ts`) with no hardcoded tooltip strings in component files, enabling easy auditing, updating, and future localization.

**Independent Test**: Search all component files for hardcoded tooltip strings — none should exist. Change a tooltip string in the registry — the corresponding UI tooltip should reflect the update without any other code changes. Review the registry and verify each entry has a unique key mappable to a specific UI element.

### Implementation for User Story 5

- [x] T032 [US5] Audit all instrumented component files to ensure no inline tooltip text is hardcoded — all tooltips must use `contentKey` prop referencing the centralized registry in frontend/src/constants/tooltip-content.ts
- [x] T033 [US5] Verify registry key naming consistency — all keys follow the `{area}.{section}.{element}` dot-notation convention and each key uniquely maps to one UI element in frontend/src/constants/tooltip-content.ts
- [x] T034 [US5] Verify `TooltipEntry` type is exported from the tooltip component module so the registry can import it for type safety in frontend/src/components/ui/tooltip.tsx and frontend/src/constants/tooltip-content.ts

**Checkpoint**: All tooltip content is sourced from a single registry file. No hardcoded tooltip strings in component files. Registry keys follow consistent naming convention. Changing a registry entry updates the UI tooltip.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, motion preferences, edge case handling, and cleanup

- [x] T035 [P] Verify `prefers-reduced-motion` media query support — tooltip appear/disappear animations should be disabled or reduced when the user has motion reduction enabled, using Tailwind's `motion-reduce:animate-none` variant in frontend/src/components/ui/tooltip.tsx
- [x] T036 [P] Verify rapid cursor scanning behavior — moving quickly between tooltip triggers should dismiss the previous tooltip and show the next one without delay lag (leveraging `skipDelayDuration={300}` on `TooltipProvider` configured in frontend/src/App.tsx)
- [x] T037 [P] Verify graceful handling of missing registry keys — hovering over an element with a `contentKey` that has no entry in the registry should render children only (no empty or broken tooltip) and log a `console.warn` in development mode in frontend/src/components/ui/tooltip.tsx
- [x] T038 Run `npx tsc --noEmit` to confirm zero TypeScript errors after all tooltip changes
- [x] T039 Run `npx vitest run` to confirm all existing tests pass with no regressions from tooltip changes
- [x] T040 Run quickstart.md validation — follow all 16 verification steps from specs/030-ui-tooltips/quickstart.md to confirm end-to-end tooltip behavior

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion
- **User Story 2 (Phase 4)**: Depends on Foundational phase completion (can run in parallel with US1)
- **User Story 3 (Phase 5)**: Depends on Foundational phase completion (can run in parallel with US1)
- **User Story 4 (Phase 6)**: Depends on Foundational phase completion (can run in parallel with US1–US3)
- **User Story 5 (Phase 7)**: Depends on US1 completion (audit requires tooltips to be wired up)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — bulk of implementation work; wires tooltips to all elements
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — visual design is built into the Tooltip component; verification can run alongside US1
- **User Story 3 (P1)**: Can start after Foundational (Phase 2) — accessibility is built into Radix Tooltip; verification can run alongside US1
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) — progressive disclosure rendering in Tooltip component; content registry entries can be added alongside US1
- **User Story 5 (P2)**: Requires US1 to be complete — audit verifies all tooltips are registry-sourced, which requires tooltips to be wired up first

### Within Each User Story

- All tasks marked [P] can run in parallel (different files, no dependencies)
- Registry-based content (tooltip-content.ts) should be created before component integration
- Component wrapping order does not matter — each component is independent

### Parallel Opportunities

- All US1 component integration tasks (T009–T022) can run in parallel — each modifies a different file
- US2, US3, and US4 foundational work (T023, T026, T029) can run in parallel with US1 component integration
- Within US1: All 14 component tasks are parallelizable (different files, no dependencies on each other)

---

## Parallel Example: User Story 1

```text
# Launch all component integration tasks for US1 together (all [P] — different files):
Task T009: Wrap refresh button in frontend/src/components/board/RefreshButton.tsx
Task T010: Wrap clean-up button in frontend/src/components/board/CleanUpButton.tsx
Task T011: Wrap board toolbar controls in frontend/src/components/board/BoardToolbar.tsx
Task T012: Wrap chat toolbar controls in frontend/src/components/chat/ChatToolbar.tsx
Task T013: Wrap chat interface controls in frontend/src/components/chat/ChatInterface.tsx
Task T014: Wrap agent card actions in frontend/src/components/agents/AgentCard.tsx
Task T015: Wrap agents panel controls in frontend/src/components/agents/AgentsPanel.tsx
Task T016: Wrap add agent modal fields in frontend/src/components/agents/AddAgentModal.tsx
Task T017: Wrap stage card controls in frontend/src/components/pipeline/StageCard.tsx
Task T018: Wrap pipeline board actions in frontend/src/components/pipeline/PipelineBoard.tsx
Task T019: Wrap model selector in frontend/src/components/pipeline/ModelSelector.tsx
Task T020: Wrap chore card actions in frontend/src/components/chores/ChoreCard.tsx
Task T021: Wrap settings controls in frontend/src/pages/SettingsPage.tsx
Task T022: Wrap tools controls in frontend/src/pages/ToolsPage.tsx
```

---

## Implementation Strategy

### MVP First (User Stories 1–3 Together)

1. Complete Phase 1: Setup (install dependency)
2. Complete Phase 2: Foundational (Tooltip component + registry + provider)
3. Complete Phase 3: User Story 1 (wire tooltips to all elements)
4. Complete Phase 4: User Story 2 (visual design verification)
5. Complete Phase 5: User Story 3 (accessibility verification)
6. **STOP and VALIDATE**: Test all tooltips — hover, keyboard, viewport edges, themes
7. Deploy/demo if ready — MVP delivers full tooltip coverage with consistent design and accessibility

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Full tooltip coverage → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Visual consistency verified → Deploy/Demo
4. Add User Story 3 → Accessibility verified → Deploy/Demo
5. Add User Story 4 → Progressive disclosure for complex features → Deploy/Demo
6. Add User Story 5 → Centralized management audit → Deploy/Demo
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (component integration — bulk work)
   - Developer B: User Story 2 + User Story 3 (visual design + accessibility verification)
   - Developer C: User Story 4 (progressive disclosure)
3. After US1 completes: Developer A handles User Story 5 (content audit)
4. All: Polish phase

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Tests are NOT explicitly requested — only ensure existing tests continue to pass
- No backend changes — this feature is entirely frontend
- Total task count: 40 tasks
- Task count per user story: US1 (14), US2 (3), US3 (3), US4 (3), US5 (3)
- Setup: 2 tasks, Foundational: 6 tasks, Polish: 6 tasks
- Parallel opportunities: 14 tasks in US1, 3 across US2/US3/US4 foundational work
- Suggested MVP scope: US1 + US2 + US3 (all P1 — delivers full tooltip coverage with visual consistency and accessibility)
