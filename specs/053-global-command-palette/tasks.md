# Tasks: Global Search / Command Palette

**Input**: Design documents from `/specs/053-global-command-palette/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted per Principle IV (Test Optionality with Clarity).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/frontend/src/` (frontend module within monorepo)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create new files and directories required by the command palette feature

- [x] T001 Create command palette component directory at `solune/frontend/src/components/command-palette/`
- [x] T002 [P] Define `CommandPaletteItem`, `CommandCategory`, and `CommandPaletteState` TypeScript types in `solune/frontend/src/hooks/useCommandPalette.ts` per data-model.md entities (id, label, category, icon, description, keywords, action)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core hook and shortcut wiring that MUST be complete before ANY user story UI can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Implement `useCommandPalette` hook skeleton in `solune/frontend/src/hooks/useCommandPalette.ts` with state management: `query`, `selectedIndex`, `filteredResults`, `isLoading`, conditional data fetching (entity hooks enabled only when `isOpen` is true), `setQuery()`, `moveUp()`, `moveDown()`, `selectCurrent()`, and focus save/restore via `useRef` for `document.activeElement`
- [x] T004 [P] Modify `useGlobalShortcuts` in `solune/frontend/src/hooks/useGlobalShortcuts.ts` to dispatch `'solune:open-command-palette'` custom event on Ctrl+K / Cmd+K instead of `'solune:focus-chat'`, with `isModalOpen()` guard to prevent opening over existing dialogs (FR-012)
- [x] T005 Add `solune:open-command-palette` event listener in `solune/frontend/src/layout/AppLayout.tsx` with `isCommandPaletteOpen` state (`useState(false)`), toggling on event, and pass `isOpen` / `onClose` / `projectId` props to `CommandPalette` component render site (below `KeyboardShortcutModal`)

**Checkpoint**: Foundation ready — Ctrl+K dispatches new event, AppLayout listens and manages open state

---

## Phase 3: User Story 1 — Open and Navigate via Command Palette (Priority: P1) 🎯 MVP

**Goal**: Users press Ctrl+K to open a command palette overlay, type to filter navigation pages from `NAV_ROUTES`, select a result via keyboard or click, and navigate to the target page

**Independent Test**: Press Ctrl+K → palette opens with auto-focused input → type "set" → "Settings" page result appears → press Enter → navigated to `/settings` → palette closes

### Implementation for User Story 1

- [x] T006 [US1] Wire `NAV_ROUTES` (from `solune/frontend/src/constants.ts`) as the Pages search source in `useCommandPalette` hook (`solune/frontend/src/hooks/useCommandPalette.ts`): transform each route to `CommandPaletteItem` with `id: page-{path}`, `label: route.label`, `icon: route.icon`, `category: 'pages'`, `action: () => navigate(route.path)` using `useNavigate` from react-router
- [x] T007 [US1] Implement case-insensitive substring search filter in `useCommandPalette` (`solune/frontend/src/hooks/useCommandPalette.ts`): match `query` against `item.label` and `item.keywords`, reset `selectedIndex` to 0 on query change, return empty results when query is empty
- [x] T008 [US1] Create `CommandPalette` component in `solune/frontend/src/components/command-palette/CommandPalette.tsx` with: fixed backdrop overlay (`fixed inset-0 z-50`), centered dialog panel (`role="dialog"`, `aria-modal="true"`, `aria-label="Command palette"`), auto-focused search input (`aria-label="Search commands"`), results list (`role="listbox"`), result items (`role="option"`, `aria-selected` for highlighted item), category headers (`role="presentation"`), click-to-select on result items, backdrop click to close
- [x] T009 [US1] Wire keyboard event handlers in `CommandPalette` component (`solune/frontend/src/components/command-palette/CommandPalette.tsx`): ArrowDown → `moveDown()`, ArrowUp → `moveUp()`, Enter → `selectCurrent()` then `onClose()`, Escape → `onClose()`, with `preventDefault()` on all handled keys

**Checkpoint**: User Story 1 complete — Ctrl+K opens palette, typing filters NAV_ROUTES pages, arrow keys navigate, Enter/click selects and navigates, Escape/backdrop closes

---

## Phase 4: User Story 4 — Keyboard-Driven Navigation Within the Palette (Priority: P1)

**Goal**: Full keyboard-only workflow: open palette, search, navigate results with arrow keys showing visible highlight, select with Enter, dismiss with Escape

**Independent Test**: Open palette → type query → Down arrow moves highlight visually → Up arrow wraps from first to last → Enter executes highlighted action → Escape dismisses cleanly and restores focus

### Implementation for User Story 4

- [x] T010 [US4] Add visible focus highlight styling to the selected result item in `CommandPalette` component (`solune/frontend/src/components/command-palette/CommandPalette.tsx`): apply distinct background/ring style to `results[selectedIndex]` item, ensure `aria-selected="true"` only on highlighted item, auto-scroll highlighted item into view using `scrollIntoView({ block: 'nearest' })`
- [x] T011 [US4] Implement wrap-around navigation in `useCommandPalette` (`solune/frontend/src/hooks/useCommandPalette.ts`): `moveUp()` on index 0 wraps to `results.length - 1`, `moveDown()` on last index wraps to 0, both are no-ops when results are empty
- [x] T012 [US4] Implement focus restore on palette close in `useCommandPalette` (`solune/frontend/src/hooks/useCommandPalette.ts`): capture `document.activeElement` into `previousFocusRef` when palette opens (via `useEffect` on `isOpen`), call `previousFocusRef.current?.focus()` on close if element still exists in DOM

**Checkpoint**: User Stories 1 AND 4 complete — full keyboard-driven workflow with visual highlight, wrap-around, and focus restore

---

## Phase 5: User Story 2 — Search Across Entities (Priority: P2)

**Goal**: Users search the palette and see categorized results from agents, pipelines, tools, chores, and apps alongside page results

**Independent Test**: Open palette → type an agent name → see result under "Agents" category → type a query matching items across multiple types → see grouped results with category headers and icons → type nonsense → see "No results found"

### Implementation for User Story 2

- [x] T013 [P] [US2] Add agents search source to `useCommandPalette` (`solune/frontend/src/hooks/useCommandPalette.ts`): call `useAgentsList(projectId)` from `solune/frontend/src/hooks/useAgents.ts`, transform `AgentConfig[]` to `CommandPaletteItem[]` with `id: agent-{name}`, `label: agent.name`, `icon: Bot`, `category: 'agents'`, `action: () => navigate('/agents')`
- [x] T014 [P] [US2] Add pipelines search source to `useCommandPalette` (`solune/frontend/src/hooks/useCommandPalette.ts`): access `pipelines` array from `usePipelineConfig()` (from `solune/frontend/src/hooks/usePipelineConfig.ts`), transform to `CommandPaletteItem[]` with `id: pipeline-{name}`, `label: pipeline.name`, `icon: GitBranch`, `category: 'pipelines'`, `action: () => navigate('/pipeline')`
- [x] T015 [P] [US2] Add tools search source to `useCommandPalette` (`solune/frontend/src/hooks/useCommandPalette.ts`): access `tools` from `useToolsList(projectId)` (from `solune/frontend/src/hooks/useTools.ts`), transform to `CommandPaletteItem[]` with `id: tool-{name}`, `label: tool.name`, `icon: Wrench`, `category: 'tools'`, `action: () => navigate('/tools')`
- [x] T016 [P] [US2] Add chores search source to `useCommandPalette` (`solune/frontend/src/hooks/useCommandPalette.ts`): call `useChoresList(projectId)` from `solune/frontend/src/hooks/useChores.ts`, transform `Chore[]` to `CommandPaletteItem[]` with `id: chore-{name}`, `label: chore.name`, `icon: ListChecks`, `category: 'chores'`, `action: () => navigate('/chores')`
- [x] T017 [P] [US2] Add apps search source to `useCommandPalette` (`solune/frontend/src/hooks/useCommandPalette.ts`): call `useApps()` from `solune/frontend/src/hooks/useApps.ts`, transform `App[]` to `CommandPaletteItem[]` with `id: app-{name}`, `label: app.name`, `icon: Boxes`, `category: 'apps'`, `action: () => navigate('/apps')`
- [x] T018 [US2] Add category headers with icons to the results list in `CommandPalette` component (`solune/frontend/src/components/command-palette/CommandPalette.tsx`): group results by `category` field, render category label and icon (from `CommandCategory` mapping) before each group, display order: Pages, Agents, Pipelines, Tools, Chores, Apps, Actions
- [x] T019 [P] [US2] Add "No results found" empty state in `CommandPalette` component (`solune/frontend/src/components/command-palette/CommandPalette.tsx`): when `query` is non-empty and `results.length === 0` and `isLoading === false`, display friendly message (FR-010)
- [x] T020 [P] [US2] Add loading indicator in `CommandPalette` component (`solune/frontend/src/components/command-palette/CommandPalette.tsx`): when `isLoading === true`, display a spinner or skeleton in the results area while entity data is being fetched

**Checkpoint**: User Stories 1, 4, AND 2 complete — cross-entity search with categorized results, no-results state, and loading indicator

---

## Phase 6: User Story 3 — Quick Actions from the Palette (Priority: P3)

**Goal**: Users search and invoke quick actions (Toggle Theme, Focus Chat) directly from the command palette without navigating to a page

**Independent Test**: Open palette → type "theme" → "Toggle Theme" action appears → select it → theme toggles → open palette → type "chat" → "Focus Chat" appears → select it → chat input receives focus

### Implementation for User Story 3

- [x] T021 [US3] Add quick actions search source to `useCommandPalette` (`solune/frontend/src/hooks/useCommandPalette.ts`): define static `CommandPaletteItem[]` for "Toggle Theme" (`icon: SunMoon`, `category: 'actions'`, `action: toggleTheme` from `useAppTheme`), "Focus Chat" (`icon: MessageSquare`, `category: 'actions'`, `action: () => window.dispatchEvent(new CustomEvent('solune:focus-chat'))`), and "Help" (`icon: HelpCircle`, `category: 'actions'`, `action: () => navigate('/help')`) per data-model.md Quick Action definitions
- [x] T022 [US3] Add clickable search trigger button to `TopBar` in `solune/frontend/src/layout/TopBar.tsx`: render a `Search` icon button (from `lucide-react`) with tooltip "Search (Ctrl+K)" or "Search (⌘K)" on macOS, `onClick` dispatches `'solune:open-command-palette'` custom event, `aria-label="Open command palette"`, positioned near existing action buttons (FR-013)
- [x] T023 [US3] Update keyboard shortcut modal description in `solune/frontend/src/components/ui/keyboard-shortcut-modal.tsx`: change the Ctrl+K / Cmd+K shortcut description from `'Focus chat input'` to `'Command Palette'` (FR-015)

**Checkpoint**: All user stories (1, 4, 2, 3) complete — quick actions work, UI trigger opens palette, shortcut modal updated

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases, performance, and accessibility improvements that span multiple user stories

- [x] T024 [P] Handle Ctrl+K when palette is already open in `solune/frontend/src/hooks/useGlobalShortcuts.ts` or `solune/frontend/src/hooks/useCommandPalette.ts`: if palette is open, select all text in search input (no-op or select-all behavior)
- [x] T025 [P] Cap visible results at 15 items with scrollable overflow in `CommandPalette` component (`solune/frontend/src/components/command-palette/CommandPalette.tsx`): set `max-height` on results container, ensure `overflow-y: auto` for scrolling (spec: max 15 visible results)
- [x] T026 [P] Handle rapid typing smoothly in `useCommandPalette` (`solune/frontend/src/hooks/useCommandPalette.ts`): ensure search filtering runs synchronously with `useMemo` or deferred with `requestAnimationFrame` to prevent UI jank on fast input (<200ms result update target per SC-003)
- [x] T027 [P] Prevent default browser Ctrl+K behavior (browser search bar) in `solune/frontend/src/hooks/useGlobalShortcuts.ts`: ensure `e.preventDefault()` is called in the Ctrl+K handler to suppress browser-native search behavior
- [x] T028 Run quickstart.md verification: execute `npx tsc --noEmit` type-check and `npx eslint` lint in `solune/frontend/` to confirm all changes compile and lint cleanly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 — core palette overlay and page navigation
- **User Story 4 (Phase 4)**: Depends on Phase 3 — keyboard navigation refinements build on Phase 3 component
- **User Story 2 (Phase 5)**: Depends on Phase 2 — entity search can start after foundation; independent of US4 polish
- **User Story 3 (Phase 6)**: Depends on Phase 2 — quick actions and UI trigger are independent of US2 entity search
- **Polish (Phase 7)**: Depends on Phases 3–6 — cross-cutting refinements across all stories

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Phase 2 (Foundational) — No dependencies on other stories
- **User Story 4 (P1)**: Depends on User Story 1 — keyboard navigation refinements build on the palette component
- **User Story 2 (P2)**: Depends on Phase 2 (Foundational) — Can run in parallel with US4; adds entity sources to existing hook
- **User Story 3 (P3)**: Depends on Phase 2 (Foundational) — Can run in parallel with US2 and US4; touches different files (TopBar, shortcut modal)

### Within Each User Story

- Hook logic before component UI
- Component structure before styling refinements
- Core implementation before edge case handling

### Parallel Opportunities

- **Phase 1**: T001 and T002 can run in parallel (directory creation + type definitions)
- **Phase 2**: T004 (shortcut modification) and T003 (hook skeleton) can run in parallel
- **Phase 5 (US2)**: T013, T014, T015, T016, T017 (all entity sources) can run in parallel — each adds a different data source to the same hook
- **Phase 5 (US2)**: T019, T020 (no-results + loading) can run in parallel — different UI sections
- **Phase 6 (US3)**: T021, T022, T023 can all run in parallel — quick actions (hook), TopBar trigger (layout), shortcut modal (UI component) are different files
- **Phase 7**: T024, T025, T026, T027 can all run in parallel — independent edge case fixes in different files/sections

---

## Parallel Example: User Story 2

```bash
# Launch all entity source tasks together (different data hooks, same target file but different sections):
Task T013: "Add agents search source to useCommandPalette"
Task T014: "Add pipelines search source to useCommandPalette"
Task T015: "Add tools search source to useCommandPalette"
Task T016: "Add chores search source to useCommandPalette"
Task T017: "Add apps search source to useCommandPalette"

# Launch UI states in parallel (different render branches in CommandPalette):
Task T019: "Add 'No results found' empty state"
Task T020: "Add loading indicator"
```

## Parallel Example: User Story 3

```bash
# All three tasks touch different files — fully parallelizable:
Task T021: "Add quick actions to useCommandPalette" (hook file)
Task T022: "Add search trigger button to TopBar" (layout file)
Task T023: "Update keyboard shortcut modal description" (UI component file)
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 4 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003–T005)
3. Complete Phase 3: User Story 1 (T006–T009)
4. Complete Phase 4: User Story 4 (T010–T012)
5. **STOP and VALIDATE**: Ctrl+K opens palette, page search works, full keyboard navigation, focus restore
6. Deploy/demo if ready — palette is useful with page navigation alone

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 + 4 → Palette opens, pages searchable, keyboard works → Deploy/Demo (MVP!)
3. Add User Story 2 → Cross-entity search → Deploy/Demo
4. Add User Story 3 → Quick actions + UI trigger → Deploy/Demo
5. Polish → Edge cases, performance, accessibility → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 → User Story 4 (sequential — US4 depends on US1)
   - Developer B: User Story 2 (parallel with A — independent entity sources)
   - Developer C: User Story 3 (parallel with A and B — different files entirely)
3. All developers: Polish phase together

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- All source paths are relative to repository root (e.g., `solune/frontend/src/...`)
- No new npm dependencies required — built with existing React, Radix patterns, Tailwind, Lucide
- No backend changes — entirely frontend, client-side search against cached TanStack Query data
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
