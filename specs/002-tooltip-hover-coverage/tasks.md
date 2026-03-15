# Tasks: Deep UI/UX Tooltip & Hover Coverage

**Input**: Design documents from `/specs/002-tooltip-hover-coverage/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Unit tests are required for the two new UI primitives (hover-card, popover) per spec FR-027 and plan Phase 1 item 5. Phase 2+ component changes rely on existing test infrastructure and manual verification per quickstart.md.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing. User Story 1 (tooltips) and User Story 2 (hover cards) share the new `hover-card.tsx` infrastructure; User Story 3 (popovers) depends on `popover.tsx`. User Stories 4 (hover styling) and 5 (registry audit) are cross-cutting but can proceed independently after Setup completes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Frontend app**: `solune/frontend/src/`
- **Frontend tests**: colocated `solune/frontend/src/**/*.test.ts(x)`
- **UI primitives**: `solune/frontend/src/components/ui/`
- **Tooltip registry**: `solune/frontend/src/constants/tooltip-content.ts`
- **Feature artifacts**: `specs/002-tooltip-hover-coverage/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install new Radix dependencies and bootstrap the development environment.

- [x] T001 Install `@radix-ui/react-hover-card` and `@radix-ui/react-popover` in `solune/frontend/package.json` via `npm install` per `specs/002-tooltip-hover-coverage/quickstart.md`
- [x] T002 Run baseline validation commands (`npx vitest run`, `npm run type-check`, `npm run lint`) in `solune/frontend/` to record any pre-existing failures before making source changes

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the two new Radix UI wrapper components and extend the tooltip registry with all missing keys. MUST complete before ANY user story implementation can begin.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T003 Create `solune/frontend/src/components/ui/hover-card.tsx` — Radix HoverCard wrapper exporting `HoverCard`, `HoverCardTrigger`, and styled `HoverCardContent` with `forwardRef`, `openDelay={300}`, `closeDelay={150}`, fade+slide animation gated behind `motion-safe:` Tailwind modifier, portal rendering, and collision detection per `specs/002-tooltip-hover-coverage/contracts/hover-card-component-contract.md`
- [x] T004 [P] Create `solune/frontend/src/components/ui/popover.tsx` — Radix Popover wrapper exporting `Popover`, `PopoverTrigger`, `PopoverContent`, `PopoverAnchor`, `PopoverClose`, and `PopoverArrow` with `forwardRef`, focus trap, Escape-to-close, outside-click-to-close, focus-return-to-trigger, `aria-haspopup`/`aria-expanded`, and `motion-safe:` animation per `specs/002-tooltip-hover-coverage/contracts/popover-component-contract.md`
- [x] T005 [P] Create unit tests in `solune/frontend/src/components/ui/hover-card.test.tsx` — renders without crashing, shows content on hover trigger, hides content on mouse leave, applies custom className, respects `side`/`align` props, no animation under `prefers-reduced-motion` per plan Phase 1 item 5
- [x] T006 [P] Create unit tests in `solune/frontend/src/components/ui/popover.test.tsx` — renders without crashing, shows content on click, hides on Escape, hides on outside click, traps focus, returns focus to trigger, applies custom className per plan Phase 1 item 5
- [x] T007 Extend `solune/frontend/src/constants/tooltip-content.ts` registry with all 40 new entries identified in `specs/002-tooltip-hover-coverage/research.md` RT-003 plus `agents.card.icon` from plan 2.2: pipeline keys (`pipeline.agent.dragHandle`, `pipeline.agent.clone`, `pipeline.group.dragHandle`, `pipeline.group.label`, `pipeline.stage.dragHandle`, `pipeline.analytics.complexity`), agents keys (`agents.card.icon`, `agents.card.expand`, `agents.tools.moveUp`, `agents.tools.moveDown`, `agents.tools.remove`, `agents.bulk.scope`), chat keys (`chat.voice.stop`, `chat.mention.agentPreview`, `chat.command.description`), board keys (`board.filter.button`, `board.sort.button`, `board.column.addAgent`, `board.column.settings`, `board.column.collapse`), tools keys (`tools.card.resync`, `tools.config.repoUrl`, `tools.config.branch`, `tools.config.serverCommand`, `tools.generator.copy`, `tools.search.input`), settings keys (`settings.ai.temperature`, `settings.ai.provider`, `settings.theme.toggle`, `settings.signal.qr`, `settings.reset.danger`, `settings.reset.cache`, `settings.reset.all`), and nav keys (`nav.projects`, `nav.agents`, `nav.pipeline`, `nav.chores`, `nav.tools`, `nav.settings`, `nav.sidebar.toggle`)
- [x] T008 Extend `solune/frontend/src/test/test-utils.tsx` to include any required providers for HoverCard and Popover rendering in test contexts, ensuring `tooltipAwareRender` supports the new primitives per plan Phase 1 item 6

**Checkpoint**: Foundation ready — `npm run test` passes, both new primitives are available, registry has all keys, user story implementation can begin.

---

## Phase 3: User Story 1 — Icon-Only Button Discoverability (Priority: P1) 🎯 MVP

**Goal**: Every icon-only button across all 8 pages displays a descriptive tooltip on hover and keyboard focus, sourced from the centralized registry. All `title=` attributes on interactive elements are replaced with `<Tooltip contentKey="...">`.

**Independent Test**: Navigate to each page, hover over every icon-only button, and verify a tooltip appears with accurate text within 300ms. Tab-navigate to verify keyboard focus triggers the same tooltip. Grep for `title=` on interactive elements should return zero results.

### Implementation for User Story 1

#### 2.7 — Sidebar Navigation

- [x] T009 [US1] Replace all `title=` attributes on icon-only nav items in `solune/frontend/src/layout/Sidebar.tsx` with `<Tooltip contentKey="nav.{page}">` wrappers for Projects, Agents, Pipeline, Chores, Tools, Settings and add collapse/expand toggle tooltip using `nav.sidebar.toggle` per plan Phase 2.7
- [x] T010 [P] [US1] Add `aria-label` matching tooltip summary to every icon-only nav button in `solune/frontend/src/layout/Sidebar.tsx` per spec FR-024

#### 2.1 — Pipeline Builder

- [x] T011 [P] [US1] Add tooltip with `contentKey="pipeline.agent.dragHandle"` to the drag handle on `AgentNode` in `solune/frontend/src/components/pipeline/AgentNode.tsx` and set matching `aria-label`
- [x] T012 [P] [US1] Add tooltip with `contentKey="pipeline.agent.clone"` to the clone button on `AgentNode` in `solune/frontend/src/components/pipeline/AgentNode.tsx` and set matching `aria-label`
- [ ] T013 [P] [US1] Add tooltip with `contentKey="pipeline.group.dragHandle"` to the drag handle on `ExecutionGroupCard` in `solune/frontend/src/components/pipeline/ExecutionGroupCard.tsx` and set matching `aria-label`
- [ ] T014 [P] [US1] Add tooltip with `contentKey="pipeline.group.label"` to the group label badge on `ExecutionGroupCard` in `solune/frontend/src/components/pipeline/ExecutionGroupCard.tsx`
- [x] T015 [P] [US1] Add tooltip with `contentKey="pipeline.stage.dragHandle"` to the drag handle on `StageCard` in `solune/frontend/src/components/pipeline/StageCard.tsx` and set matching `aria-label`
- [ ] T016 [P] [US1] Add tooltip with `contentKey="pipeline.analytics.complexity"` to the complexity badge on `PipelineAnalytics` in `solune/frontend/src/components/pipeline/PipelineAnalytics.tsx`
- [ ] T017 [P] [US1] Replace `title=` attribute on truncated workflow names in `SavedWorkflowsList` in `solune/frontend/src/components/pipeline/SavedWorkflowsList.tsx` with `<Tooltip>` using direct `content` prop

#### 2.2 — Agents Page

- [ ] T018 [P] [US1] Add tooltip with `contentKey="agents.card.icon"` to the icon area on `AgentCard` in `solune/frontend/src/components/agents/AgentCard.tsx` and set matching `aria-label`
- [ ] T019 [P] [US1] Add tooltip with `contentKey="agents.card.expand"` to the expand/collapse toggle on `AgentCard` in `solune/frontend/src/components/agents/AgentCard.tsx` with dynamic `aria-label` ("Expand agent details" / "Collapse agent details") per spec acceptance scenario 3
- [x] T020 [P] [US1] Add tooltips with `contentKey="agents.tools.moveUp"` and `contentKey="agents.tools.moveDown"` to the move-up/move-down buttons in `ToolsEditor` in `solune/frontend/src/components/agents/ToolsEditor.tsx` and set matching `aria-label`
- [x] T021 [P] [US1] Add tooltip with `contentKey="agents.tools.remove"` to the remove-tool button in `ToolsEditor` in `solune/frontend/src/components/agents/ToolsEditor.tsx` and set matching `aria-label`
- [ ] T022 [P] [US1] Add tooltip with `contentKey="agents.bulk.scope"` to the scope selector in `BulkModelUpdateDialog` in `solune/frontend/src/components/agents/BulkModelUpdateDialog.tsx`

#### 2.3 — Chat Interface

- [x] T023 [P] [US1] Verify/add tooltip with `contentKey="chat.voice.stop"` to the stop-recording state of `VoiceInputButton` in `solune/frontend/src/components/chat/VoiceInputButton.tsx` and set matching `aria-label`

#### 2.4 — Board / Projects

- [ ] T024 [P] [US1] Add tooltips with `contentKey="board.filter.button"` and `contentKey="board.sort.button"` to filter/sort toolbar buttons in the board component(s) under `solune/frontend/src/components/board/` and set matching `aria-label`
- [ ] T025 [P] [US1] Add tooltips with `contentKey="board.column.addAgent"`, `contentKey="board.column.settings"`, and `contentKey="board.column.collapse"` to column header icon-only actions under `solune/frontend/src/components/board/` and set matching `aria-label`

#### 2.5 — Tools Page

- [ ] T026 [P] [US1] Verify/add tooltip with `contentKey="tools.card.resync"` to the re-sync button on `ToolCard` in `solune/frontend/src/components/tools/ToolCard.tsx` and set matching `aria-label`
- [ ] T027 [P] [US1] Add field-help tooltips using `contentKey="tools.config.repoUrl"`, `tools.config.branch`, `tools.config.serverCommand` to inputs in `RepoConfigPanel` in `solune/frontend/src/components/tools/RepoConfigPanel.tsx`
- [x] T028 [P] [US1] Add tooltip with `contentKey="tools.generator.copy"` to the copy button in `GitHubMcpConfigGenerator` in `solune/frontend/src/components/tools/GitHubMcpConfigGenerator.tsx` and set matching `aria-label`
- [ ] T029 [P] [US1] Add tooltip with `contentKey="tools.search.input"` to the search input in the tools page search component under `solune/frontend/src/components/tools/`

#### 2.6 — Settings Page

- [ ] T030 [P] [US1] Add tooltip with `contentKey="settings.ai.temperature"` to the temperature slider in settings component(s) under `solune/frontend/src/components/settings/`
- [ ] T031 [P] [US1] Add tooltip with `contentKey="settings.ai.provider"` to the provider toggle in settings component(s) under `solune/frontend/src/components/settings/`
- [ ] T032 [P] [US1] Replace `title=` with `<Tooltip contentKey="settings.theme.toggle">` on the theme toggle in settings component(s) under `solune/frontend/src/components/settings/`
- [ ] T033 [P] [US1] Add tooltip with `contentKey="settings.signal.qr"` to the Signal QR button in settings component(s) under `solune/frontend/src/components/settings/`
- [ ] T034 [P] [US1] Add warning tooltips with `contentKey="settings.reset.danger"`, `settings.reset.cache`, `settings.reset.all` to destructive reset actions in settings component(s) under `solune/frontend/src/components/settings/`

**Checkpoint**: At this point, every icon-only button across all 8 pages has a tooltip, all `title=` on interactive elements are replaced, and `aria-label` attributes match tooltip text. User Story 1 is fully functional and testable independently.

---

## Phase 4: User Story 2 — Rich Entity Previews via Hover Cards (Priority: P2)

**Goal**: Agent nodes, agent cards, issue cards, and @agent-name mention chips display rich hover card previews with structured entity data — without clicking or navigating away.

**Independent Test**: Hover over each entity type and verify the hover card displays correct, complete data per data-model.md entities (AgentHoverCardData, IssueHoverCardData, MentionHoverCardData). Verify cards close after 150ms on mouse leave. Verify no animations under `prefers-reduced-motion`.

### Implementation for User Story 2

- [x] T035 [US2] Create `AgentHoverCardContent` preview component (reusable across AgentNode and AgentCard hover cards) rendering `AgentHoverCardData` fields — name, description (truncated ~100 chars), model badge, tools list (max 5, "+N more"), last-run status badge — in a new file or inline in `solune/frontend/src/components/pipeline/AgentNode.tsx` per `specs/002-tooltip-hover-coverage/data-model.md` and `contracts/hover-card-component-contract.md`
- [x] T036 [P] [US2] Wrap `AgentNode` in `solune/frontend/src/components/pipeline/AgentNode.tsx` with `<HoverCard openDelay={300} closeDelay={150}>` + `<HoverCardTrigger asChild>` + `<HoverCardContent>` rendering `AgentHoverCardContent` per spec FR-009 and contract usage pattern "Agent Node Hover Card"
- [x] T037 [P] [US2] Wrap `AgentCard` name/avatar in `solune/frontend/src/components/agents/AgentCard.tsx` with `<HoverCard>` rendering `AgentHoverCardContent` showing description snippet, active tools, and run count per spec FR-010
- [x] T038 [US2] Create `IssueHoverCardContent` preview component rendering `IssueHoverCardData` fields — full title, number, assignees (max 3 avatars, "+N"), labels as colored badges, pipeline stage, status — in `solune/frontend/src/components/board/IssueCard.tsx` or a shared location per `specs/002-tooltip-hover-coverage/data-model.md`
- [x] T039 [P] [US2] Wrap `IssueCard` in `solune/frontend/src/components/board/IssueCard.tsx` with `<HoverCard>` rendering `IssueHoverCardContent` showing full title (if truncated), assignees, labels, pipeline stage per spec FR-011 and contract usage pattern "Issue Card Hover Card"
- [ ] T040 [US2] Create `MentionHoverCardContent` preview component rendering `MentionHoverCardData` fields — agent name, description, tools (max 3, overflow) — in `solune/frontend/src/components/chat/` per `specs/002-tooltip-hover-coverage/data-model.md`
- [ ] T041 [P] [US2] Wrap `@agent-name` mention chips in chat composer in `solune/frontend/src/components/chat/MentionAutocomplete.tsx` (or the component rendering mention chips) with `<HoverCard>` rendering `MentionHoverCardContent` per spec FR-012
- [ ] T042 [US2] Add loading skeleton placeholder inside each hover card content component for async data states per spec edge case "hover cards when the underlying data is still loading"

**Checkpoint**: At this point, all 4 entity types show rich hover cards with correct data. User Story 2 is fully functional and testable independently.

---

## Phase 5: User Story 3 — Accessible Popover Menus (Priority: P2)

**Goal**: All manual dropdown/overlay menus are migrated to the standardized Radix popover component with correct focus trapping, Escape-to-close, outside-click-to-close, and ARIA attributes.

**Independent Test**: Click each popover trigger, verify focus is trapped inside, press Escape to close and confirm focus returns to trigger. Verify `aria-haspopup` and `aria-expanded` on all triggers. Run automated accessibility scan for zero violations.

### Implementation for User Story 3

- [x] T043 [US3] Migrate `ModelSelector` in `solune/frontend/src/components/pipeline/ModelSelector.tsx` from manual useState + absolute-positioned dropdown to `<Popover>` + `<PopoverTrigger>` + `<PopoverContent>` per `specs/002-tooltip-hover-coverage/contracts/popover-component-contract.md` migration pattern — retain existing search, filtering, recent tracking, and cost badge logic; remove manual Escape/outside-click/portal handlers
- [x] T044 [P] [US3] Migrate `AddAgentPopover` in `solune/frontend/src/components/board/AddAgentPopover.tsx` from manual overlay to `<Popover>` + `<PopoverTrigger>` + `<PopoverContent>` — retain existing agent filtering and selection logic; remove manual overlay mechanics per contract migration pattern
- [x] T045 [P] [US3] Migrate `AgentPresetSelector` in `solune/frontend/src/components/board/AgentPresetSelector.tsx` from manual overlay to `<Popover>` + `<PopoverTrigger>` + `<PopoverContent>` — retain existing preset logic, confirmation dialogs, and localStorage; remove manual overlay mechanics per research RT-002
- [ ] T046 [US3] Grep codebase (`solune/frontend/src/`) for remaining manual open/close toggle patterns (useState + absolute-positioned div) and migrate each to `popover.tsx` per spec FR-017 and plan Phase 4
- [ ] T047 [US3] Verify all migrated popovers have correct `aria-haspopup="dialog"` on trigger, `aria-expanded` toggling, focus trapping, and focus restoration per `specs/002-tooltip-hover-coverage/contracts/popover-component-contract.md` migration checklist

**Checkpoint**: All popovers close on Escape, trap focus, return focus to trigger, and have correct ARIA attributes. User Story 3 is fully functional and testable independently.

---

## Phase 6: User Story 4 — Consistent Hover Styling Across All Cards (Priority: P3)

**Goal**: All interactive card surfaces display uniform hover states, drag handles appear on hover with grab cursor, and drop zones provide visual feedback during drag operations.

**Independent Test**: Hover over each card type (AgentCard, IssueCard, ToolCard, ChoreCard, AgentNode, StageCard) and verify identical ring highlight + background accent shift. Hover over draggable items and verify drag handle appears. Drag items over drop zones and verify visual highlight.

### Implementation for User Story 4

#### Uniform Hover State Token

- [x] T048 [P] [US4] Apply consistent `hover:ring-1 hover:ring-border hover:bg-accent/50 transition-all` classes to `AgentCard` in `solune/frontend/src/components/agents/AgentCard.tsx` per research RT-005
- [x] T049 [P] [US4] Apply consistent `hover:ring-1 hover:ring-border hover:bg-accent/50 transition-all` classes to `IssueCard` in `solune/frontend/src/components/board/IssueCard.tsx` per research RT-005
- [x] T050 [P] [US4] Apply consistent `hover:ring-1 hover:ring-border hover:bg-accent/50 transition-all` classes to `ToolCard` in `solune/frontend/src/components/tools/ToolCard.tsx` per research RT-005
- [x] T051 [P] [US4] Apply consistent `hover:ring-1 hover:ring-border hover:bg-accent/50 transition-all` classes to `ChoreCard` (or chore row component) under `solune/frontend/src/components/chores/` per research RT-005
- [x] T052 [P] [US4] Apply consistent `hover:ring-1 hover:ring-border hover:bg-accent/50 transition-all` classes to `AgentNode` in `solune/frontend/src/components/pipeline/AgentNode.tsx` per research RT-005
- [x] T053 [P] [US4] Apply consistent `hover:ring-1 hover:ring-border hover:bg-accent/50 transition-all` classes to `StageCard` in `solune/frontend/src/components/pipeline/StageCard.tsx` per research RT-005

#### Drag Handle Affordance

- [ ] T054 [P] [US4] Add `opacity-0 group-hover:opacity-100 cursor-grab transition-opacity` to drag handle icon on `AgentNode` in `solune/frontend/src/components/pipeline/AgentNode.tsx` per research RT-005 drag handle pattern
- [ ] T055 [P] [US4] Add `opacity-0 group-hover:opacity-100 cursor-grab transition-opacity` to drag handle icon on `ExecutionGroupCard` in `solune/frontend/src/components/pipeline/ExecutionGroupCard.tsx` per research RT-005
- [ ] T056 [P] [US4] Add `opacity-0 group-hover:opacity-100 cursor-grab transition-opacity` to drag handle icon on `StageCard` in `solune/frontend/src/components/pipeline/StageCard.tsx` per research RT-005
- [ ] T057 [P] [US4] Add `opacity-0 group-hover:opacity-100 cursor-grab transition-opacity` to drag handle on chore rows under `solune/frontend/src/components/chores/` per research RT-005

#### Droppable Zone Feedback

- [ ] T058 [US4] Apply `isOver` state-driven `ring-2 ring-primary/50 bg-primary/5` classes to all `@dnd-kit` drop targets in pipeline builder (`solune/frontend/src/components/pipeline/`) and board (`solune/frontend/src/components/board/`) per research RT-005 drop zone pattern

**Checkpoint**: All interactive cards have uniform hover styling, drag handles are visible on hover with grab cursor, and drop zones show visual feedback. User Story 4 is fully functional and testable independently.

---

## Phase 7: User Story 5 — Tooltip Registry Completeness and Accuracy (Priority: P3)

**Goal**: The tooltip registry has no orphaned keys, no interactive element uses native `title=`, and all tooltip copy matches exact UI terminology.

**Independent Test**: Run automated comparison of registry keys vs. `contentKey=` usages (zero orphans). Grep `title=` on interactive elements (zero results). Review tooltip text vs. UI labels for terminology consistency.

### Implementation for User Story 5

- [ ] T059 [US5] Audit and prune orphaned keys in `solune/frontend/src/constants/tooltip-content.ts` — find registry entries with no corresponding `contentKey=` usage in any component file under `solune/frontend/src/` per spec FR-021 and plan Phase 5 item 11
- [x] T060 [P] [US5] Grep `solune/frontend/src/` for remaining `title=` on interactive elements (buttons, links, toggles) and convert each to `<Tooltip>` wrapper per spec FR-022 and plan Phase 5 item 12; retain `title=` only on non-interactive truncated text `<span>` elements
- [ ] T061 [P] [US5] Perform terminology audit on all tooltip `summary` text in `solune/frontend/src/constants/tooltip-content.ts` — ensure exact match with UI labels (e.g., "execution group" not "group", "stage" not "column") per spec FR-023 and plan Phase 5 item 13

**Checkpoint**: Registry has zero orphaned keys, zero `title=` on interactive elements, and all terminology matches. User Story 5 is fully functional and testable independently.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Accessibility audit, motion compliance, keyboard reachability, and final verification across all user stories.

### Accessibility & Motion

- [ ] T062 [P] Audit every icon-only button across `solune/frontend/src/` for `aria-label` attribute matching its tooltip text per spec FR-024 and plan Phase 6 item 14
- [x] T063 [P] Verify `prefers-reduced-motion` compliance — confirm HoverCard and Popover animations in `solune/frontend/src/components/ui/hover-card.tsx` and `solune/frontend/src/components/ui/popover.tsx` use `motion-safe:` Tailwind modifier and produce no animation under reduced-motion per spec FR-003 and research RT-006
- [ ] T064 [P] Verify all tooltip triggers are reachable via keyboard Tab navigation and all popovers are focus-trapped and focus-returning per spec FR-025 and FR-026

### Chat Interface Inline Descriptions

- [ ] T065 [P] Add agent description inline preview to `MentionAutocomplete` items in `solune/frontend/src/components/chat/MentionAutocomplete.tsx` per plan Phase 2.3
- [ ] T066 [P] Add command description inline preview to `CommandAutocomplete` items in `solune/frontend/src/components/chat/CommandAutocomplete.tsx` per plan Phase 2.3

### Final Verification

- [x] T067 Run `npx vitest run` in `solune/frontend/` and verify all tests pass including new hover-card and popover tests
- [x] T068 Run `npm run type-check` in `solune/frontend/` and verify zero type errors
- [x] T069 Run `npm run lint` in `solune/frontend/` and verify zero lint errors
- [x] T070 Run `npm run build` in `solune/frontend/` and verify successful production build
- [ ] T071 Run quickstart.md manual verification walkthrough per `specs/002-tooltip-hover-coverage/quickstart.md` Verification section — every icon-only button shows tooltip ≤300ms; all truncated text shows full content; hover cards render correct data; all popovers close on Escape; no animation under `prefers-reduced-motion`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) — specifically T003 (hover-card.tsx not required for tooltips, but T007 registry extension is required)
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) — specifically T003 (hover-card.tsx) and T007 (registry)
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) — specifically T004 (popover.tsx)
- **User Story 4 (Phase 6)**: Depends on Setup (Phase 1) only — no dependency on new primitives
- **User Story 5 (Phase 7)**: Depends on User Stories 1–3 being complete (registry additions must stabilize before audit)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 — No dependencies on other stories
- **User Story 2 (P2)**: Can start after Phase 2 — No dependencies on other stories (uses hover-card.tsx from Phase 2)
- **User Story 3 (P2)**: Can start after Phase 2 — No dependencies on other stories (uses popover.tsx from Phase 2)
- **User Story 4 (P3)**: Can start after Phase 1 — No dependencies on other stories (CSS-only changes)
- **User Story 5 (P3)**: Should start after User Stories 1–3 are complete (registry and component changes must stabilize)

### Within Each User Story

- Registry entries (T007) must exist before component tooltips can reference them
- Hover card content components (T035, T038, T040) must exist before wrapping components (T036, T037, T039, T041)
- Popover migration preserves existing internal logic; only overlay mechanics change
- All [P] tasks within a story can run in parallel (different files, no conflicts)

### Parallel Opportunities

- All Foundational tasks T003–T008 can proceed in parallel (different files)
- All Phase 3 US1 component tasks (T009–T034) are [P] and can run in parallel (different component files)
- All Phase 4 US2 hover card wrapping tasks (T036, T037, T039, T041) are [P] after their content component is created
- All Phase 5 US3 popover migrations (T043–T045) can run in parallel (different component files)
- All Phase 6 US4 hover styling tasks (T048–T058) are [P] (different component files)
- User Stories 1, 2, 3, and 4 can all proceed in parallel after Phase 2 completes

---

## Parallel Example: User Story 1

```bash
# After Phase 2 (Foundational) completes, all US1 component tasks run in parallel:
Task T009: "Replace title= on sidebar nav icons in Sidebar.tsx"
Task T011: "Add drag handle tooltip on AgentNode in AgentNode.tsx"
Task T013: "Add drag handle tooltip on ExecutionGroupCard in ExecutionGroupCard.tsx"
Task T018: "Add icon tooltip on AgentCard in AgentCard.tsx"
Task T024: "Add filter/sort tooltips on board toolbar"
Task T026: "Add re-sync tooltip on ToolCard in ToolCard.tsx"
Task T030: "Add temperature tooltip in settings"
# All target different files — safe to parallelize
```

## Parallel Example: User Story 2

```bash
# After hover card content components are created:
Task T036: "Wrap AgentNode with HoverCard in AgentNode.tsx"
Task T037: "Wrap AgentCard with HoverCard in AgentCard.tsx"
Task T039: "Wrap IssueCard with HoverCard in IssueCard.tsx"
Task T041: "Wrap mention chips with HoverCard in chat"
# All target different files — safe to parallelize
```

## Parallel Example: User Story 3

```bash
# After popover.tsx is created:
Task T043: "Migrate ModelSelector in ModelSelector.tsx"
Task T044: "Migrate AddAgentPopover in AddAgentPopover.tsx"
Task T045: "Migrate AgentPresetSelector in AgentPresetSelector.tsx"
# All target different files — safe to parallelize
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (install dependencies)
2. Complete Phase 2: Foundational (create primitives, extend registry)
3. Complete Phase 3: User Story 1 — Icon-Only Button Tooltips
4. **STOP and VALIDATE**: Hover over every icon-only button across all pages → tooltip appears
5. Deploy/demo if ready — immediate discoverability improvement

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (P1 tooltips) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (P2 hover cards) → Test independently → Deploy/Demo
4. Add User Story 3 (P2 popovers) → Test independently → Deploy/Demo
5. Add User Story 4 (P3 hover styling) → Test independently → Deploy/Demo
6. Add User Story 5 (P3 registry audit) → Test independently → Deploy/Demo
7. Complete Polish → Final accessibility/motion verification
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (tooltips — highest priority, broadest impact)
   - Developer B: User Story 2 (hover cards — depends on hover-card.tsx)
   - Developer C: User Story 3 (popovers — depends on popover.tsx)
   - Developer D: User Story 4 (hover styling — CSS-only, no primitive dependency)
3. After Stories 1–3 stabilize:
   - Any developer: User Story 5 (registry audit) + Polish

---

## Notes

- [P] tasks = different files, no dependencies — safe to parallelize
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group per quickstart.md workflow
- Stop at any checkpoint to validate story independently
- The 40 new registry entries (T007) are the single largest foundational task — complete this early as all US1 component work references it
- Avoid: vague tasks, same-file conflicts, cross-story dependencies that break independence
