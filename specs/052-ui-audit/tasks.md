# Tasks: UI Audit — Page-Level Quality & Consistency

**Input**: Design documents from `/specs/052-ui-audit/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are explicitly requested in the spec (User Stories 6 and 7, FR-031 through FR-033). Test tasks are included in Phase 9 (US6).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. Within each user story, tasks are ordered by page audit priority (largest/highest-risk pages first).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/frontend/src/` at repository root
- Pages: `solune/frontend/src/pages/`
- Feature components: `solune/frontend/src/components/[feature]/`
- Hooks: `solune/frontend/src/hooks/`
- API service: `solune/frontend/src/services/api.ts`
- Types: `solune/frontend/src/types/`
- Shared UI: `solune/frontend/src/components/ui/`
- Shared common: `solune/frontend/src/components/common/`
- Tests: Co-located with source files (`.test.ts` / `.test.tsx`)

## Page Inventory (Audit Priority Order)

| # | Page | Lines | Feature Dir | Key Hooks | Exceeds 250? |
|---|------|-------|-------------|-----------|---------------|
| 1 | AppsPage | 707 | `src/components/apps/` | useApps | ⚠️ Yes (2.8x) |
| 2 | ProjectsPage | 629 | `src/components/board/` | useProjects, useProjectBoard | ⚠️ Yes (2.5x) |
| 3 | AgentsPipelinePage | 417 | `src/components/pipeline/` | usePipelineConfig, useSelectedPipeline, usePipelineReducer | ⚠️ Yes (1.7x) |
| 4 | AgentsPage | 230 | `src/components/agents/` | useAgents, useAgentConfig | ✅ No |
| 5 | ChoresPage | 166 | `src/components/chores/` | useChores | ✅ No |
| 6 | HelpPage | 195 | `src/components/help/` | — | ✅ No |
| 7 | SettingsPage | 107 | `src/components/settings/` | useSettings, useSettingsForm | ✅ No |
| 8 | ToolsPage | 87 | `src/components/tools/` | useTools | ✅ No |
| 9 | AppPage | 141 | `src/components/chat/` | useChat, useChatHistory | ✅ No |
| 10 | LoginPage | 119 | `src/components/auth/` | useAuth | ✅ No |
| 11 | NotFoundPage | 29 | — | — | ✅ No |

---

## Phase 1: Setup (Audit Infrastructure)

**Purpose**: Create the audit process infrastructure and findings directory structure

- [ ] T001 Create findings report directory at `specs/052-ui-audit/findings/`
- [ ] T002 [P] Run initial line-count assessment on all 11 pages in `solune/frontend/src/pages/`
- [ ] T003 [P] Run initial ESLint check on all pages: `cd solune/frontend && npx eslint src/pages/`
- [ ] T004 [P] Run initial TypeScript check: `cd solune/frontend && npx tsc --noEmit`
- [ ] T005 [P] Run existing test suite: `cd solune/frontend && npx vitest run`

---

## Phase 2: Foundational (Page Discovery & Findings Reports)

**Purpose**: Execute discovery phase for each page — read source, score 60 checklist items, produce findings report. MUST complete before remediation begins.

**⚠️ CRITICAL**: No remediation work can begin until discovery is complete for all pages. Findings reports drive all subsequent phases.

- [ ] T006 Audit discovery for AppsPage — read `solune/frontend/src/pages/AppsPage.tsx`, `solune/frontend/src/components/apps/`, `solune/frontend/src/hooks/useApps*.ts`, score all 60 checklist items per `specs/052-ui-audit/contracts/audit-checklist.md`, produce findings report at `specs/052-ui-audit/findings/AppsPage.md`
- [ ] T007 [P] Audit discovery for ProjectsPage — read `solune/frontend/src/pages/ProjectsPage.tsx`, `solune/frontend/src/components/board/`, `solune/frontend/src/hooks/useProject*.ts`, score all 60 checklist items, produce findings report at `specs/052-ui-audit/findings/ProjectsPage.md`
- [ ] T008 [P] Audit discovery for AgentsPipelinePage — read `solune/frontend/src/pages/AgentsPipelinePage.tsx`, `solune/frontend/src/components/pipeline/`, `solune/frontend/src/hooks/usePipeline*.ts`, score all 60 checklist items, produce findings report at `specs/052-ui-audit/findings/AgentsPipelinePage.md`
- [ ] T009 [P] Audit discovery for AgentsPage — read `solune/frontend/src/pages/AgentsPage.tsx`, `solune/frontend/src/components/agents/`, `solune/frontend/src/hooks/useAgent*.ts`, score all 60 checklist items, produce findings report at `specs/052-ui-audit/findings/AgentsPage.md`
- [ ] T010 [P] Audit discovery for ChoresPage — read `solune/frontend/src/pages/ChoresPage.tsx`, `solune/frontend/src/components/chores/`, `solune/frontend/src/hooks/useChores*.ts`, score all 60 checklist items, produce findings report at `specs/052-ui-audit/findings/ChoresPage.md`
- [ ] T011 [P] Audit discovery for HelpPage — read `solune/frontend/src/pages/HelpPage.tsx`, `solune/frontend/src/components/help/`, score all 60 checklist items, produce findings report at `specs/052-ui-audit/findings/HelpPage.md`
- [ ] T012 [P] Audit discovery for SettingsPage — read `solune/frontend/src/pages/SettingsPage.tsx`, `solune/frontend/src/components/settings/`, `solune/frontend/src/hooks/useSettings*.ts`, score all 60 checklist items, produce findings report at `specs/052-ui-audit/findings/SettingsPage.md`
- [ ] T013 [P] Audit discovery for ToolsPage — read `solune/frontend/src/pages/ToolsPage.tsx`, `solune/frontend/src/components/tools/`, `solune/frontend/src/hooks/useTools*.ts`, score all 60 checklist items, produce findings report at `specs/052-ui-audit/findings/ToolsPage.md`
- [ ] T014 [P] Audit discovery for AppPage — read `solune/frontend/src/pages/AppPage.tsx`, `solune/frontend/src/components/chat/`, `solune/frontend/src/hooks/useChat*.ts`, score all 60 checklist items, produce findings report at `specs/052-ui-audit/findings/AppPage.md`
- [ ] T015 [P] Audit discovery for LoginPage — read `solune/frontend/src/pages/LoginPage.tsx`, `solune/frontend/src/components/auth/`, `solune/frontend/src/hooks/useAuth*.ts`, score all 60 checklist items, produce findings report at `specs/052-ui-audit/findings/LoginPage.md`
- [ ] T016 [P] Audit discovery for NotFoundPage — read `solune/frontend/src/pages/NotFoundPage.tsx`, score all 60 checklist items, produce findings report at `specs/052-ui-audit/findings/NotFoundPage.md`

**Checkpoint**: All 11 findings reports produced. Review findings to confirm remediation priorities before proceeding.

---

## Phase 3: User Story 1 — Consistent Loading & Error Feedback (Priority: P1) 🎯 MVP

**Goal**: Every page shows clear loading indicators during data fetch, user-friendly error messages with retry on failure, and meaningful empty states when collections are empty. No blank screens. Independent sections handle their own loading/error states.

**Independent Test**: Navigate to each audited page under three conditions — (a) normal load, (b) simulated slow network, (c) simulated API failure — and verify loading indicator appears, error message with retry appears on failure, and empty state appears for empty collections.

**Related FRs**: FR-004 (loading indicator), FR-005 (error + retry + rate limit), FR-006 (empty state), FR-007 (partial loading per section)

### Implementation for User Story 1

- [ ] T017 [US1] Add/fix loading state in `solune/frontend/src/pages/AppsPage.tsx` — use `<CelestialLoader size="md" />` from `@/components/common/CelestialLoader` for all `isLoading`/`isPending` branches; ensure no blank screen during fetch
- [ ] T018 [US1] Add/fix error state in `solune/frontend/src/pages/AppsPage.tsx` — display user-friendly error message with retry button on API failure; use `isRateLimitApiError()` for rate limit detection; no raw error codes
- [ ] T019 [US1] Add/fix empty state in `solune/frontend/src/pages/AppsPage.tsx` — show meaningful empty state with guidance when app list is empty (e.g., "No apps found. Create your first app to get started.")
- [ ] T020 [P] [US1] Add/fix loading state in `solune/frontend/src/pages/ProjectsPage.tsx` — use `<CelestialLoader size="md" />` for all loading branches
- [ ] T021 [P] [US1] Add/fix error state in `solune/frontend/src/pages/ProjectsPage.tsx` — user-friendly error with retry and rate limit detection
- [ ] T022 [P] [US1] Add/fix empty state in `solune/frontend/src/pages/ProjectsPage.tsx` — meaningful empty state when project list is empty
- [ ] T023 [US1] Ensure partial loading in `solune/frontend/src/pages/ProjectsPage.tsx` — if page has multiple data sources, each section shows independent loading/error states per FR-007
- [ ] T024 [P] [US1] Add/fix loading state in `solune/frontend/src/pages/AgentsPipelinePage.tsx` — use `<CelestialLoader size="md" />` for pipeline config loading
- [ ] T025 [P] [US1] Add/fix error state in `solune/frontend/src/pages/AgentsPipelinePage.tsx` — user-friendly error with retry for pipeline fetch failures
- [ ] T026 [P] [US1] Add/fix empty state in `solune/frontend/src/pages/AgentsPipelinePage.tsx` — meaningful empty state when no pipeline configurations exist
- [ ] T027 [P] [US1] Add/fix loading, error, and empty states in `solune/frontend/src/pages/AgentsPage.tsx` — CelestialLoader during fetch, error with retry, empty state for no agents
- [ ] T028 [P] [US1] Add/fix loading, error, and empty states in `solune/frontend/src/pages/ChoresPage.tsx` — CelestialLoader during fetch, error with retry, empty state for no chores
- [ ] T029 [P] [US1] Add/fix loading, error, and empty states in `solune/frontend/src/pages/HelpPage.tsx` — CelestialLoader during fetch, error with retry (if applicable)
- [ ] T030 [P] [US1] Add/fix loading, error, and empty states in `solune/frontend/src/pages/SettingsPage.tsx` — CelestialLoader during fetch, error with retry for settings data
- [ ] T031 [P] [US1] Add/fix loading, error, and empty states in `solune/frontend/src/pages/ToolsPage.tsx` — CelestialLoader during fetch, error with retry, empty state for no tools
- [ ] T032 [P] [US1] Add/fix loading state in `solune/frontend/src/pages/AppPage.tsx` — CelestialLoader for chat/conversation data loading
- [ ] T033 [P] [US1] Add/fix loading state in `solune/frontend/src/pages/LoginPage.tsx` — CelestialLoader during authentication checks (if applicable)
- [ ] T034 [US1] Verify all `useMutation` calls across all pages have `onError` handlers that surface user-visible feedback (toast or inline error) — check hooks in `solune/frontend/src/hooks/`

**Checkpoint**: At this point, every page should show loading → content/error/empty states correctly. No blank screens. User Story 1 is independently testable.

---

## Phase 4: User Story 2 — Full Keyboard & Screen Reader Accessibility (Priority: P1)

**Goal**: Every interactive element on every page is reachable via keyboard (Tab, Enter, Space, Escape), dialogs trap focus and return focus on close, all controls have ARIA attributes, form fields have labels, status indicators don't rely on color alone, and focus-visible styles are present.

**Independent Test**: Navigate each audited page using only keyboard. Verify Tab reaches all interactive elements, Enter/Space activates them, Escape closes dialogs, and screen reader announces control names and states.

**Related FRs**: FR-008 (keyboard accessible), FR-009 (focus trapping), FR-010 (ARIA attributes), FR-011 (form labels), FR-012 (color + icon/text), FR-013 (focus-visible styles)

### Implementation for User Story 2

- [ ] T035 [US2] Audit and fix ARIA attributes on custom controls (dropdowns, toggles, tabs) in `solune/frontend/src/pages/AppsPage.tsx` and `solune/frontend/src/components/apps/` — add `role`, `aria-label`, `aria-expanded`, `aria-selected` where missing
- [ ] T036 [US2] Verify focus management in all dialogs triggered from `solune/frontend/src/pages/AppsPage.tsx` — ensure `<ConfirmationDialog>` and modals trap focus while open and return focus to trigger element on close
- [ ] T037 [US2] Add `aria-label` to all form inputs without visible labels in `solune/frontend/src/pages/AppsPage.tsx` and `solune/frontend/src/components/apps/`
- [ ] T038 [P] [US2] Audit and fix ARIA attributes and keyboard accessibility in `solune/frontend/src/pages/ProjectsPage.tsx` and `solune/frontend/src/components/board/` — ensure board interactions are keyboard-accessible
- [ ] T039 [P] [US2] Audit and fix ARIA attributes and keyboard accessibility in `solune/frontend/src/pages/AgentsPipelinePage.tsx` and `solune/frontend/src/components/pipeline/` — ensure pipeline builder drag-and-drop has keyboard alternatives
- [ ] T040 [P] [US2] Audit and fix ARIA attributes and keyboard accessibility in `solune/frontend/src/pages/AgentsPage.tsx` and `solune/frontend/src/components/agents/`
- [ ] T041 [P] [US2] Audit and fix ARIA attributes and keyboard accessibility in `solune/frontend/src/pages/ChoresPage.tsx` and `solune/frontend/src/components/chores/`
- [ ] T042 [P] [US2] Audit and fix ARIA attributes and keyboard accessibility in `solune/frontend/src/pages/HelpPage.tsx` and `solune/frontend/src/components/help/`
- [ ] T043 [P] [US2] Audit and fix ARIA attributes and keyboard accessibility in `solune/frontend/src/pages/SettingsPage.tsx` and `solune/frontend/src/components/settings/`
- [ ] T044 [P] [US2] Audit and fix ARIA attributes and keyboard accessibility in `solune/frontend/src/pages/ToolsPage.tsx` and `solune/frontend/src/components/tools/`
- [ ] T045 [P] [US2] Audit and fix ARIA attributes and keyboard accessibility in `solune/frontend/src/pages/AppPage.tsx` and `solune/frontend/src/components/chat/`
- [ ] T046 [P] [US2] Audit and fix keyboard accessibility in `solune/frontend/src/pages/LoginPage.tsx` and `solune/frontend/src/components/auth/` — ensure login form is fully keyboard-operable
- [ ] T047 [US2] Add `aria-hidden="true"` to all decorative icons and `aria-label` to all meaningful icons across all pages and feature components — check `lucide-react` icon usage
- [ ] T048 [US2] Verify all interactive elements have `focus-visible:` ring or `celestial-focus` class — audit all pages and feature components for missing focus styles
- [ ] T049 [US2] Verify status indicators across all pages don't rely on color alone — ensure icon + text accompanies all status colors (check badge/status components in `solune/frontend/src/components/`)

**Checkpoint**: All pages are fully keyboard-navigable, screen reader-accessible, and ARIA-compliant. User Story 2 is independently testable.

---

## Phase 5: User Story 3 — Accurate, Polished Copy & Consistent UX Patterns (Priority: P2)

**Goal**: All text is final (no placeholders), terminology is consistent, action buttons use verb labels, destructive actions require confirmation, mutations show success feedback, error messages are user-friendly, long text is truncated with tooltip.

**Independent Test**: Review all visible text on each page for placeholder strings and terminology consistency. Attempt every destructive action and verify confirmation dialog appears. Trigger mutations and verify success feedback.

**Related FRs**: FR-014 (no placeholder text), FR-015 (consistent terminology), FR-016 (confirmation on destructive), FR-017 (success feedback), FR-018 (user-friendly errors), FR-019 (truncation + tooltip)

### Implementation for User Story 3

- [ ] T050 [US3] Scan and fix placeholder text in `solune/frontend/src/pages/AppsPage.tsx` and `solune/frontend/src/components/apps/` — remove any "TODO", "Lorem ipsum", "Test" strings; replace with final copy
- [ ] T051 [US3] Add `<ConfirmationDialog>` for all destructive actions (delete/remove/stop) in `solune/frontend/src/pages/AppsPage.tsx` and `solune/frontend/src/components/apps/` — use `useConfirmation` hook from `@/hooks/useConfirmation`
- [ ] T052 [US3] Ensure all `useMutation` `onSuccess` handlers in AppsPage-related hooks show user-visible success feedback (toast, status change, or inline message)
- [ ] T053 [US3] Add `<Tooltip>` for truncated text (app names, descriptions, URLs) in `solune/frontend/src/components/apps/` — use `text-ellipsis` + `<Tooltip>` from `@/components/ui/tooltip`
- [ ] T054 [P] [US3] Scan and fix placeholder text, add confirmation dialogs for destructive actions, and add truncation tooltips in `solune/frontend/src/pages/ProjectsPage.tsx` and `solune/frontend/src/components/board/`
- [ ] T055 [P] [US3] Scan and fix placeholder text, add confirmation dialogs for destructive actions, and add truncation tooltips in `solune/frontend/src/pages/AgentsPipelinePage.tsx` and `solune/frontend/src/components/pipeline/`
- [ ] T056 [P] [US3] Scan and fix placeholder text, add confirmation dialogs for destructive actions, and add truncation tooltips in `solune/frontend/src/pages/AgentsPage.tsx` and `solune/frontend/src/components/agents/`
- [ ] T057 [P] [US3] Scan and fix placeholder text, add confirmation dialogs for destructive actions, and add truncation tooltips in `solune/frontend/src/pages/ChoresPage.tsx` and `solune/frontend/src/components/chores/`
- [ ] T058 [P] [US3] Scan and fix copy and UX patterns in `solune/frontend/src/pages/HelpPage.tsx` and `solune/frontend/src/components/help/`
- [ ] T059 [P] [US3] Scan and fix copy and UX patterns in `solune/frontend/src/pages/SettingsPage.tsx` and `solune/frontend/src/components/settings/`
- [ ] T060 [P] [US3] Scan and fix copy and UX patterns in `solune/frontend/src/pages/ToolsPage.tsx` and `solune/frontend/src/components/tools/`
- [ ] T061 [P] [US3] Scan and fix copy and UX patterns in `solune/frontend/src/pages/AppPage.tsx` and `solune/frontend/src/components/chat/`
- [ ] T062 [P] [US3] Scan and fix copy and UX patterns in `solune/frontend/src/pages/LoginPage.tsx` and `solune/frontend/src/components/auth/`
- [ ] T063 [US3] Cross-page terminology review — verify consistent terms across all 11 pages (e.g., "pipeline" not "workflow", "chore" not "task"); ensure action button labels are verb-based ("Create Agent" not "New Agent", "Save Settings" not "Settings")
- [ ] T064 [US3] Verify all error messages across pages follow the format: "Could not [action]. [Reason, if known]. [Suggested next step]." — check `onError` handlers in hooks under `solune/frontend/src/hooks/`

**Checkpoint**: All text is final and consistent, destructive actions require confirmation, mutations show feedback. User Story 3 is independently testable.

---

## Phase 6: User Story 4 — Modular, Maintainable Page Structure (Priority: P2)

**Goal**: Page files stay within 250 lines, feature components live in dedicated directories, complex state is extracted into hooks, no deep prop drilling, no business logic in JSX.

**Independent Test**: Verify line counts of all page files (≤250), feature components exist in `src/components/[feature]/`, and custom hooks encapsulate complex state logic.

**Related FRs**: FR-020 (≤250 lines), FR-021 (feature directory), FR-022 (no deep prop drilling), FR-023 (hook extraction), FR-024 (no business logic in JSX)

### Implementation for User Story 4

- [ ] T065 [US4] Extract sub-components from `solune/frontend/src/pages/AppsPage.tsx` (707 lines) into `solune/frontend/src/components/apps/` — identify 3–4 self-contained sections (e.g., app list, app detail, app creation form, app actions) and extract each into a dedicated component file
- [ ] T066 [US4] Extract complex state logic from AppsPage into `solune/frontend/src/hooks/useApps.ts` or new hook files — move >15-line stateful blocks (useState/useEffect/useCallback chains) into dedicated custom hooks
- [ ] T067 [US4] Remove inline business logic from AppsPage render tree — move data transformations (sorting, filtering, mapping) into hooks or helper functions
- [ ] T068 [US4] Verify AppsPage has no prop drilling >2 levels — refactor to use composition, context, or hook extraction if needed
- [ ] T069 [P] [US4] Extract sub-components from `solune/frontend/src/pages/ProjectsPage.tsx` (629 lines) into `solune/frontend/src/components/board/` — identify 3–4 self-contained sections and extract each into a dedicated component file
- [ ] T070 [P] [US4] Extract complex state logic from ProjectsPage into hooks under `solune/frontend/src/hooks/useProject*.ts` — move >15-line stateful blocks into custom hooks
- [ ] T071 [US4] Remove inline business logic from ProjectsPage render tree and fix prop drilling >2 levels
- [ ] T072 [P] [US4] Extract sub-components from `solune/frontend/src/pages/AgentsPipelinePage.tsx` (417 lines) into `solune/frontend/src/components/pipeline/` — identify 1–2 self-contained sections and extract each into a dedicated component file
- [ ] T073 [P] [US4] Extract complex state logic from AgentsPipelinePage into hooks under `solune/frontend/src/hooks/usePipeline*.ts`
- [ ] T074 [US4] Remove inline business logic from AgentsPipelinePage render tree and fix prop drilling >2 levels
- [ ] T075 [US4] Verify remaining 8 pages (AgentsPage, ChoresPage, HelpPage, SettingsPage, ToolsPage, AppPage, LoginPage, NotFoundPage) are within 250-line limit and have no inline business logic in JSX — fix any violations found in findings reports

**Checkpoint**: All page files are ≤250 lines, feature components are in dedicated directories, state logic is in hooks. User Story 4 is independently testable.

---

## Phase 7: User Story 5 — Dark Mode & Responsive Layout (Priority: P2)

**Goal**: Every page renders correctly in light and dark themes using Tailwind dark: variants, no hardcoded colors. Pages adapt from 768px to 1920px viewport with no clipping, scrolling, or overlapping.

**Independent Test**: View each page in light mode and dark mode at viewport widths of 768px, 1024px, 1440px, and 1920px. Verify no invisible text, broken contrast, clipped content, or overlapping elements.

**Related FRs**: FR-025 (dark mode), FR-026 (responsive 768px–1920px)

### Implementation for User Story 5

- [ ] T076 [US5] Fix dark mode violations in `solune/frontend/src/pages/AppsPage.tsx` and `solune/frontend/src/components/apps/` — replace hardcoded colors (`bg-white`, `text-black`, `#fff`, `#000`) with Tailwind `dark:` variants or CSS variables
- [ ] T077 [US5] Fix responsive layout issues in `solune/frontend/src/pages/AppsPage.tsx` and `solune/frontend/src/components/apps/` — ensure grid/flex layouts adapt at 768px, 1024px, 1440px, 1920px; no horizontal scrolling or clipped content
- [ ] T078 [P] [US5] Fix dark mode and responsive layout in `solune/frontend/src/pages/ProjectsPage.tsx` and `solune/frontend/src/components/board/`
- [ ] T079 [P] [US5] Fix dark mode and responsive layout in `solune/frontend/src/pages/AgentsPipelinePage.tsx` and `solune/frontend/src/components/pipeline/`
- [ ] T080 [P] [US5] Fix dark mode and responsive layout in `solune/frontend/src/pages/AgentsPage.tsx` and `solune/frontend/src/components/agents/`
- [ ] T081 [P] [US5] Fix dark mode and responsive layout in `solune/frontend/src/pages/ChoresPage.tsx` and `solune/frontend/src/components/chores/`
- [ ] T082 [P] [US5] Fix dark mode and responsive layout in `solune/frontend/src/pages/HelpPage.tsx` and `solune/frontend/src/components/help/`
- [ ] T083 [P] [US5] Fix dark mode and responsive layout in `solune/frontend/src/pages/SettingsPage.tsx` and `solune/frontend/src/components/settings/`
- [ ] T084 [P] [US5] Fix dark mode and responsive layout in `solune/frontend/src/pages/ToolsPage.tsx` and `solune/frontend/src/components/tools/`
- [ ] T085 [P] [US5] Fix dark mode and responsive layout in `solune/frontend/src/pages/AppPage.tsx` and `solune/frontend/src/components/chat/`
- [ ] T086 [P] [US5] Fix dark mode and responsive layout in `solune/frontend/src/pages/LoginPage.tsx` and `solune/frontend/src/components/auth/`
- [ ] T087 [P] [US5] Fix dark mode and responsive layout in `solune/frontend/src/pages/NotFoundPage.tsx`
- [ ] T088 [US5] Fix inline `style={}` attributes across all pages — replace with Tailwind utility classes and `cn()` helper from `solune/frontend/src/lib/utils.ts`
- [ ] T089 [US5] Fix arbitrary spacing values across all pages — replace `p-[Npx]`, `m-[Npx]` with standard Tailwind spacing scale (`gap-4`, `p-6`, etc.)

**Checkpoint**: All pages render correctly in light/dark mode and adapt from 768px–1920px. User Story 5 is independently testable.

---

## Phase 8: User Story 6 — Comprehensive Test Coverage for Audited Pages (Priority: P3)

**Goal**: Each page's custom hooks have test coverage for happy path, error, and empty states. Key interactive components have tests for user interactions. Edge cases (rate limits, null data, long strings) are covered.

**Independent Test**: Run `cd solune/frontend && npx vitest run` and verify tests exist and pass for all audited pages' hooks and key components.

**Related FRs**: FR-031 (hook tests), FR-032 (component tests), FR-033 (edge cases)

### Tests for User Story 6

> **NOTE: Write assertion-based tests (no snapshot tests). Follow existing test patterns: `vi.mock('@/services/api', ...)`, `renderHook`, `waitFor`, `createWrapper()`**

- [ ] T090 [P] [US6] Write/update hook tests for `solune/frontend/src/hooks/useApps.test.ts` — cover successful data fetch, error response (including rate limit), and empty data scenarios
- [ ] T091 [P] [US6] Write/update component tests for key interactive components in `solune/frontend/src/components/apps/*.test.tsx` — cover user interactions (clicks, form submissions, dialog confirmations)
- [ ] T092 [P] [US6] Write/update hook tests for `solune/frontend/src/hooks/useProjects.test.ts` and `solune/frontend/src/hooks/useProjectBoard.test.ts` — cover happy path, error, and empty states
- [ ] T093 [P] [US6] Write/update component tests for key interactive components in `solune/frontend/src/components/board/*.test.tsx`
- [ ] T094 [P] [US6] Write/update hook tests for pipeline hooks: `solune/frontend/src/hooks/usePipelineConfig.test.ts`, `solune/frontend/src/hooks/useSelectedPipeline.test.ts` — cover happy path, error, and empty states
- [ ] T095 [P] [US6] Write/update component tests for key interactive components in `solune/frontend/src/components/pipeline/*.test.tsx`
- [ ] T096 [P] [US6] Write/update hook tests for `solune/frontend/src/hooks/useAgents.test.ts` and `solune/frontend/src/hooks/useAgentConfig.test.ts` — cover happy path, error, and empty states
- [ ] T097 [P] [US6] Write/update hook tests for `solune/frontend/src/hooks/useChores.test.ts` — cover happy path, error, and empty states
- [ ] T098 [P] [US6] Write/update hook tests for `solune/frontend/src/hooks/useTools.test.ts` — cover happy path, error, and empty states
- [ ] T099 [P] [US6] Write/update hook tests for `solune/frontend/src/hooks/useSettings.test.ts` and `solune/frontend/src/hooks/useSettingsForm.test.ts` — cover happy path, error, and empty states
- [ ] T100 [P] [US6] Write/update hook tests for `solune/frontend/src/hooks/useChat.test.ts` and `solune/frontend/src/hooks/useChatHistory.test.ts` — cover happy path, error, and empty states
- [ ] T101 [P] [US6] Write/update hook tests for `solune/frontend/src/hooks/useAuth.test.ts` — cover login success, login failure, and authentication check states
- [ ] T102 [US6] Write edge-case tests across all pages — cover rate-limit errors (`isRateLimitApiError()`), null/missing data fields, long strings (truncation behavior), rapid state transitions

**Checkpoint**: All hooks and key components have assertion-based tests covering happy path, error, empty, and edge-case scenarios. All tests pass. User Story 6 is independently testable.

---

## Phase 9: User Story 7 — Clean, Type-Safe, Lint-Free Code (Priority: P3)

**Goal**: Zero `any` types, zero unused imports, zero `console.log`, zero commented-out code, all imports use `@/` alias, zero ESLint warnings, zero TypeScript errors across all audited pages.

**Independent Test**: Run ESLint and TypeScript checker on all pages and feature components — verify zero warnings and zero errors.

**Related FRs**: FR-029 (zero lint/type errors), FR-030 (no any, no dead code, no console.log)

### Implementation for User Story 7

- [ ] T103 [US7] Remove all `any` types from `solune/frontend/src/pages/AppsPage.tsx`, `solune/frontend/src/components/apps/`, and related hooks — replace with specific types from `solune/frontend/src/types/`
- [ ] T104 [US7] Remove all `any` types from `solune/frontend/src/pages/ProjectsPage.tsx`, `solune/frontend/src/components/board/`, and related hooks
- [ ] T105 [P] [US7] Remove all `any` types from `solune/frontend/src/pages/AgentsPipelinePage.tsx`, `solune/frontend/src/components/pipeline/`, and related hooks
- [ ] T106 [P] [US7] Remove all `any` types from remaining pages (AgentsPage, ChoresPage, HelpPage, SettingsPage, ToolsPage, AppPage, LoginPage, NotFoundPage) and their feature components
- [ ] T107 [US7] Remove all `console.log` statements from all pages in `solune/frontend/src/pages/` and all feature components in `solune/frontend/src/components/`
- [ ] T108 [US7] Remove all dead code (unused imports, commented-out blocks, unreachable branches) from all pages and feature components
- [ ] T109 [US7] Fix all import paths to use `@/` alias — replace relative imports (`../../`) with `@/components/...`, `@/hooks/...`, `@/services/...` across all pages and feature components
- [ ] T110 [US7] Replace magic strings with constants — identify repeated strings (status values, route paths, query keys) across pages and define as constants in appropriate files
- [ ] T111 [US7] Run `cd solune/frontend && npx eslint src/pages/ src/components/ src/hooks/` and fix all remaining warnings to achieve zero warnings
- [ ] T112 [US7] Run `cd solune/frontend && npx tsc --noEmit` and fix all remaining type errors to achieve zero type errors

**Checkpoint**: All audited files are type-safe, lint-free, and free of dead code. User Story 7 is independently testable.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cross-cutting improvements that affect multiple user stories

- [ ] T113 [P] Verify `<ErrorBoundary>` wrapping for all page routes in `solune/frontend/src/App.tsx` — ensure all routes are protected at route level or page level
- [ ] T114 [P] Verify all `useQuery` calls have appropriate `staleTime` configured (30s for lists, 60s for settings) across all hooks in `solune/frontend/src/hooks/`
- [ ] T115 [P] Verify no duplicate API calls — check that the same data isn't fetched independently in both page and child component
- [ ] T116 [P] Verify array renders use stable keys (`key={item.id}`, never `key={index}`) across all pages and components
- [ ] T117 [P] Verify large lists (>50 items) are paginated or virtualized across all pages
- [ ] T118 [P] Verify expensive components are wrapped in `React.memo()` where props are stable and callbacks use `useCallback` only when passed to memoized children
- [ ] T119 Run full ESLint check: `cd solune/frontend && npx eslint src/pages/ src/components/ src/hooks/` — confirm 0 warnings
- [ ] T120 Run full TypeScript check: `cd solune/frontend && npx tsc --noEmit` — confirm 0 errors
- [ ] T121 Run full test suite: `cd solune/frontend && npx vitest run` — confirm all tests pass
- [ ] T122 Run theme validation: `cd solune/frontend && npm run audit:theme-*` (if available) — confirm no theme violations
- [ ] T123 Manual visual verification — check all 11 pages in light mode, dark mode, viewport widths 768px/1024px/1440px/1920px
- [ ] T124 Manual keyboard verification — Tab through all interactive elements on all 11 pages, Enter/Space to activate, Escape to close dialogs

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — discovery produces findings reports that drive all subsequent phases
- **User Stories (Phases 3–9)**: All depend on Foundational phase completion (findings reports)
  - **US1 (P1)** and **US2 (P1)** can proceed in parallel after Foundational
  - **US3 (P2)**, **US4 (P2)**, **US5 (P2)** can proceed in parallel after Foundational (no dependency on P1 stories)
  - **US4 (P2)** should ideally run before US1–US3 within each page (structural fixes first), but each story is independently testable
  - **US6 (P3)** depends on US1–US5 being complete (tests should verify fixes)
  - **US7 (P3)** can run in parallel with US6 (different files: source vs test files)
- **Polish (Phase 10)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **US2 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **US3 (P2)**: Can start after Foundational (Phase 2) — May touch same files as US1 (error messages) but independently testable
- **US4 (P2)**: Can start after Foundational (Phase 2) — Structural refactoring should ideally happen early; changes file organization that US1–US3 may reference
- **US5 (P2)**: Can start after Foundational (Phase 2) — Styling changes are independent of functional fixes
- **US6 (P3)**: Best started after US1–US5 are complete — tests should verify the fixes from earlier stories
- **US7 (P3)**: Can start after Foundational (Phase 2) — Code hygiene is independent of functional fixes, but benefits from structural clarity of US4

### Recommended Execution Order

For optimal results (structural fixes first, then functional, then polish):

1. Phase 1: Setup → Phase 2: Foundational
2. Phase 6: US4 (Modular Structure) — refactor oversized pages first
3. Phase 3: US1 (Loading/Error) + Phase 4: US2 (Accessibility) — in parallel
4. Phase 5: US3 (Copy/UX) + Phase 7: US5 (Dark Mode/Responsive) — in parallel
5. Phase 9: US7 (Code Hygiene) — clean up after all changes
6. Phase 8: US6 (Test Coverage) — lock in fixes with tests
7. Phase 10: Polish — final validation

### Within Each User Story

- Read findings report for the page before starting fixes
- Fix highest-priority pages first (AppsPage → ProjectsPage → AgentsPipelinePage → ...)
- Tasks marked [P] within the same story can run in parallel (different files)
- Commit after each page is fixed within a story
- Validate fixes with lint + type-check after each page

### Parallel Opportunities

- All Phase 2 discovery tasks (T006–T016) can run in parallel — each page is independent
- Within each user story: Tasks for different pages marked [P] can run in parallel
- US1 and US2 can run in parallel (P1 stories, different quality dimensions)
- US3, US4, US5 can run in parallel (P2 stories, different quality dimensions)
- US6 and US7 can run in parallel (P3 stories, tests vs code hygiene)
- All Phase 10 verification tasks marked [P] can run in parallel

---

## Parallel Example: Phase 2 (Discovery)

```bash
# Launch all page discovery tasks together (all are [P]):
Task: T006 "Audit discovery for AppsPage"
Task: T007 "Audit discovery for ProjectsPage"
Task: T008 "Audit discovery for AgentsPipelinePage"
Task: T009 "Audit discovery for AgentsPage"
Task: T010 "Audit discovery for ChoresPage"
Task: T011 "Audit discovery for HelpPage"
Task: T012 "Audit discovery for SettingsPage"
Task: T013 "Audit discovery for ToolsPage"
Task: T014 "Audit discovery for AppPage"
Task: T015 "Audit discovery for LoginPage"
Task: T016 "Audit discovery for NotFoundPage"
```

## Parallel Example: User Story 1 (Loading & Error States)

```bash
# After AppsPage is done (T017–T019), launch remaining pages in parallel:
Task: T020 "Add/fix loading state in ProjectsPage"
Task: T024 "Add/fix loading state in AgentsPipelinePage"
Task: T027 "Add/fix loading, error, and empty states in AgentsPage"
Task: T028 "Add/fix loading, error, and empty states in ChoresPage"
Task: T029 "Add/fix loading, error, and empty states in HelpPage"
Task: T030 "Add/fix loading, error, and empty states in SettingsPage"
Task: T031 "Add/fix loading, error, and empty states in ToolsPage"
Task: T032 "Add/fix loading state in AppPage"
Task: T033 "Add/fix loading state in LoginPage"
```

## Parallel Example: User Story 6 (Test Coverage)

```bash
# All hook test tasks can run in parallel (different files):
Task: T090 "Hook tests for useApps"
Task: T092 "Hook tests for useProjects, useProjectBoard"
Task: T094 "Hook tests for pipeline hooks"
Task: T096 "Hook tests for useAgents, useAgentConfig"
Task: T097 "Hook tests for useChores"
Task: T098 "Hook tests for useTools"
Task: T099 "Hook tests for useSettings"
Task: T100 "Hook tests for useChat"
Task: T101 "Hook tests for useAuth"
```

---

## Implementation Strategy

### MVP First (User Story 1 + User Story 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (discovery for all 11 pages)
3. Complete Phase 3: User Story 1 — Loading & Error States (P1)
4. **STOP and VALIDATE**: Test all pages under normal/slow/error conditions
5. Complete Phase 4: User Story 2 — Accessibility (P1)
6. **STOP and VALIDATE**: Keyboard-navigate all pages, check screen reader labels
7. Deploy/demo if ready — all P1 stories complete

### Incremental Delivery

1. Complete Setup + Foundational → Findings reports for all 11 pages
2. Add US4 (Modular Structure) → Refactor oversized pages → Validate line counts ≤250
3. Add US1 (Loading/Error) → Fix all states → Validate no blank screens (MVP!)
4. Add US2 (Accessibility) → Fix keyboard/ARIA → Validate keyboard navigation
5. Add US3 (Copy/UX) → Fix text/dialogs → Validate consistency
6. Add US5 (Dark Mode/Responsive) → Fix themes/layouts → Validate visual
7. Add US7 (Code Hygiene) → Clean code → Validate lint/types
8. Add US6 (Test Coverage) → Write tests → Validate all tests pass
9. Polish → Final validation → Deploy

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US4 (Modular Structure) — pages 1–6
   - Developer B: US4 (Modular Structure) — pages 7–11, then US1 (Loading/Error) — all pages
   - Developer C: US2 (Accessibility) — all pages
3. After structural/functional fixes:
   - Developer A: US3 (Copy/UX) + US5 (Dark Mode)
   - Developer B: US7 (Code Hygiene)
   - Developer C: US6 (Test Coverage)
4. All developers: Polish and final validation

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks in the same story
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Page audits within each story follow priority order (AppsPage → ProjectsPage → ... → NotFoundPage)
- Commit after each page is fixed within a story
- Stop at any checkpoint to validate the story independently
- Findings reports (Phase 2) drive all remediation — don't skip discovery
- Tests (US6) are explicitly requested in spec (FR-031 through FR-033) — assertion-based only, no snapshots
- Avoid: vague tasks, same file conflicts across stories, cross-story dependencies that break independence
