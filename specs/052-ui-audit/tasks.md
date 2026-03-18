# Tasks: UI Audit

**Input**: Design documents from `/specs/052-ui-audit/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are explicitly requested (US-8, FR-048 through FR-051). Test tasks are included for hook tests and component interaction tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing. Each user story phase targets all 11 pages in the application for that quality dimension.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app (frontend only)**: `solune/frontend/src/`
- **Pages**: `solune/frontend/src/pages/`
- **Feature components**: `solune/frontend/src/components/[feature]/`
- **Hooks**: `solune/frontend/src/hooks/`
- **Types**: `solune/frontend/src/types/`
- **UI primitives**: `solune/frontend/src/components/ui/`
- **Common components**: `solune/frontend/src/components/common/`
- **API service**: `solune/frontend/src/services/api.ts`
- **Audit checklists output**: `specs/052-ui-audit/checklists/`

## Pages Under Audit (11 total)

| Page | File | Lines | Extraction Needed | Primary Hook | Feature Components |
|------|------|-------|-------------------|-------------|-------------------|
| AgentsPage | `src/pages/AgentsPage.tsx` | 230 | No | `useAgents` | `src/components/agents/` |
| AgentsPipelinePage | `src/pages/AgentsPipelinePage.tsx` | 417 | Yes | `usePipelineConfig` | `src/components/pipeline/` |
| AppPage | `src/pages/AppPage.tsx` | 141 | No | `useApps` | `src/components/apps/` |
| AppsPage | `src/pages/AppsPage.tsx` | 709 | Yes | `useApps` | `src/components/apps/` |
| ChoresPage | `src/pages/ChoresPage.tsx` | 166 | No | `useChores` | `src/components/chores/` |
| HelpPage | `src/pages/HelpPage.tsx` | 195 | No | N/A | `src/components/help/` |
| LoginPage | `src/pages/LoginPage.tsx` | 119 | No | `useAuth` | `src/components/auth/` |
| NotFoundPage | `src/pages/NotFoundPage.tsx` | 29 | No | N/A | N/A |
| ProjectsPage | `src/pages/ProjectsPage.tsx` | 631 | Yes | `useProjects` | `src/components/board/` |
| SettingsPage | `src/pages/SettingsPage.tsx` | 107 | No | `useSettings` | `src/components/settings/` |
| ToolsPage | `src/pages/ToolsPage.tsx` | 87 | No | `useTools` | `src/components/tools/` |

---

## Phase 1: Setup (Audit Infrastructure)

**Purpose**: Establish the audit framework, scoring templates, and automated scanning tooling before any per-page work begins.

- [ ] T001 Create audit checklist template at `specs/052-ui-audit/checklists/page-audit-template.md` following the output format defined in `specs/052-ui-audit/contracts/audit-checklist.md` with all 10 categories and 65 checklist items
- [ ] T002 [P] Create automated scanning script at `specs/052-ui-audit/checklists/scan.sh` to run line count, ESLint, TypeScript type check, `any`-type grep, `console.log` grep, inline style grep, hardcoded color grep, index key grep, and relative import grep across all 11 pages
- [ ] T003 [P] Run initial `npx eslint src/pages/` in `solune/frontend/` and capture baseline ESLint warning/error count for all pages
- [ ] T004 [P] Run initial `npx tsc --noEmit` in `solune/frontend/` and capture baseline TypeScript error count
- [ ] T005 [P] Run initial `npm run test` in `solune/frontend/` and capture baseline test pass/fail count

---

## Phase 2: Foundational — Per-Page Discovery & Assessment (US1)

**Purpose**: Evaluate every page against all 10 audit categories and produce scored findings tables. This phase MUST complete before any remediation begins so that the full scope of work is known.

**⚠️ CRITICAL**: No remediation work (Phases 3–9) can begin until all 11 pages have been assessed.

### Discovery & Scoring for All Pages

- [ ] T006 [P] [US1] Audit AgentsPage: Read `solune/frontend/src/pages/AgentsPage.tsx`, `solune/frontend/src/components/agents/`, `solune/frontend/src/hooks/useAgents*.ts`, related types in `solune/frontend/src/types/`; run automated scans; score all 65 checklist items; produce findings at `specs/052-ui-audit/checklists/agents-page-audit.md`
- [ ] T007 [P] [US1] Audit AgentsPipelinePage: Read `solune/frontend/src/pages/AgentsPipelinePage.tsx`, `solune/frontend/src/components/pipeline/`, `solune/frontend/src/hooks/usePipelineConfig*.ts`, related types; run automated scans; score all 65 checklist items; produce findings at `specs/052-ui-audit/checklists/agents-pipeline-page-audit.md`
- [ ] T008 [P] [US1] Audit AppPage: Read `solune/frontend/src/pages/AppPage.tsx`, `solune/frontend/src/components/apps/`, `solune/frontend/src/hooks/useApps*.ts`, related types; run automated scans; score all 65 checklist items; produce findings at `specs/052-ui-audit/checklists/app-page-audit.md`
- [ ] T009 [P] [US1] Audit AppsPage: Read `solune/frontend/src/pages/AppsPage.tsx`, `solune/frontend/src/components/apps/`, `solune/frontend/src/hooks/useApps*.ts`, related types; run automated scans; score all 65 checklist items; produce findings at `specs/052-ui-audit/checklists/apps-page-audit.md`
- [ ] T010 [P] [US1] Audit ChoresPage: Read `solune/frontend/src/pages/ChoresPage.tsx`, `solune/frontend/src/components/chores/`, `solune/frontend/src/hooks/useChores*.ts`, related types; run automated scans; score all 65 checklist items; produce findings at `specs/052-ui-audit/checklists/chores-page-audit.md`
- [ ] T011 [P] [US1] Audit HelpPage: Read `solune/frontend/src/pages/HelpPage.tsx`, `solune/frontend/src/components/help/`, related types; run automated scans; score all 65 checklist items (Data Fetching items may be N/A for static content); produce findings at `specs/052-ui-audit/checklists/help-page-audit.md`
- [ ] T012 [P] [US1] Audit LoginPage: Read `solune/frontend/src/pages/LoginPage.tsx`, `solune/frontend/src/components/auth/`, `solune/frontend/src/hooks/useAuth*.ts`, related types; run automated scans; score all 65 checklist items; produce findings at `specs/052-ui-audit/checklists/login-page-audit.md`
- [ ] T013 [P] [US1] Audit NotFoundPage: Read `solune/frontend/src/pages/NotFoundPage.tsx`; run automated scans; score all 65 checklist items (many Data Fetching, State, Performance items will be N/A); produce findings at `specs/052-ui-audit/checklists/not-found-page-audit.md`
- [ ] T014 [P] [US1] Audit ProjectsPage: Read `solune/frontend/src/pages/ProjectsPage.tsx`, `solune/frontend/src/components/board/`, `solune/frontend/src/hooks/useProjects*.ts`, related types; run automated scans; score all 65 checklist items; produce findings at `specs/052-ui-audit/checklists/projects-page-audit.md`
- [ ] T015 [P] [US1] Audit SettingsPage: Read `solune/frontend/src/pages/SettingsPage.tsx`, `solune/frontend/src/components/settings/`, `solune/frontend/src/hooks/useSettings*.ts`, related types; run automated scans; score all 65 checklist items; produce findings at `specs/052-ui-audit/checklists/settings-page-audit.md`
- [ ] T016 [P] [US1] Audit ToolsPage: Read `solune/frontend/src/pages/ToolsPage.tsx`, `solune/frontend/src/components/tools/`, `solune/frontend/src/hooks/useTools*.ts`, related types; run automated scans; score all 65 checklist items; produce findings at `specs/052-ui-audit/checklists/tools-page-audit.md`
- [ ] T017 [US1] Compile consolidated audit summary table aggregating all 11 page audits with total Pass/Fail/N/A counts per category and severity counts (Critical/Major/Minor) at `specs/052-ui-audit/checklists/audit-summary.md`

**Checkpoint**: All 11 pages have scored findings. The full remediation backlog is known. Phases 3–9 can now proceed.

---

## Phase 3: Component Architecture Compliance (US2) — Priority: P1

**Goal**: Every page meets modular component architecture standards — pages ≤250 lines, sub-components in feature directories, no deep prop drilling, shared primitives reused, complex state in hooks, no business logic in JSX.

**Independent Test**: Verify each page file is ≤250 lines (`wc -l`), sub-components are in `src/components/[feature]/`, grep finds no prop drilling >2 levels, and no inline computation exists in JSX return blocks.

### Extraction: Oversized Pages

- [ ] T018 [US2] Extract sub-components from `solune/frontend/src/pages/AppsPage.tsx` (709 lines) into `solune/frontend/src/components/apps/` — identify self-contained list sections, filter bars, detail views; create new component files (e.g., `AppsListSection.tsx`, `AppFilterBar.tsx`, `AppCard.tsx`); reduce page file to ≤250 lines; ensure all existing tests still pass
- [ ] T019 [US2] Extract sub-components from `solune/frontend/src/pages/ProjectsPage.tsx` (631 lines) into `solune/frontend/src/components/board/` — identify self-contained board sections, project cards, list/grid views; create new component files; reduce page file to ≤250 lines; ensure all existing tests still pass
- [ ] T020 [US2] Extract sub-components from `solune/frontend/src/pages/AgentsPipelinePage.tsx` (417 lines) into `solune/frontend/src/components/pipeline/` — identify self-contained pipeline stages, configuration panels, status displays; create new component files; reduce page file to ≤250 lines; ensure all existing tests still pass

### Hook Extraction

- [ ] T021 [P] [US2] Audit all 11 pages for complex state logic (>15 lines of useState/useEffect/useCallback) inline in page files; extract into `solune/frontend/src/hooks/use[Feature].ts` where not already extracted; list specific pages and hooks in findings
- [ ] T022 [P] [US2] Audit all 11 pages for business logic in JSX (computation, data transformation, conditional logic beyond simple ternaries); move to hooks or helper functions; verify no inline `.filter()`, `.map()` with transformation, `.sort()`, or `.reduce()` in JSX return blocks

### Architecture Cleanup

- [ ] T023 [P] [US2] Audit all 11 pages for prop drilling exceeding 2 levels; refactor to use composition, context, or hook extraction where found; document changes in page audit files
- [ ] T024 [P] [US2] Audit all 11 pages for reimplemented UI primitives (custom buttons, cards, inputs, tooltips, confirmation dialogs); replace with shared components from `solune/frontend/src/components/ui/` and `solune/frontend/src/components/common/`

**Checkpoint**: All pages ≤250 lines. Component architecture audit items pass for all pages. Run `wc -l solune/frontend/src/pages/*.tsx | sort -rn` to verify.

---

## Phase 4: Loading, Error, and Empty State Coverage (US3) — Priority: P1

**Goal**: Every page that fetches data displays appropriate loading indicators, user-friendly error messages with retry actions, rate-limit-specific messages, and meaningful empty states. No blank screens.

**Independent Test**: Simulate loading delays (React Query devtools or mock slow responses), API errors (network disconnect), rate limit errors (mock 429 response), and empty collections for each page — verify correct state renders.

### Loading States

- [ ] T025 [P] [US3] Add/verify loading state in `solune/frontend/src/pages/AgentsPage.tsx` — show `<CelestialLoader size="md" />` or skeleton while `useAgents` is loading; never show blank content area
- [ ] T026 [P] [US3] Add/verify loading state in `solune/frontend/src/pages/AgentsPipelinePage.tsx` — show `<CelestialLoader>` or skeleton while `usePipelineConfig` is loading
- [ ] T027 [P] [US3] Add/verify loading state in `solune/frontend/src/pages/AppPage.tsx` — show `<CelestialLoader>` or skeleton while app data is loading
- [ ] T028 [P] [US3] Add/verify loading state in `solune/frontend/src/pages/AppsPage.tsx` — show `<CelestialLoader>` or skeleton while `useApps` is loading
- [ ] T029 [P] [US3] Add/verify loading state in `solune/frontend/src/pages/ChoresPage.tsx` — show `<CelestialLoader>` or skeleton while `useChores` is loading
- [ ] T030 [P] [US3] Add/verify loading state in `solune/frontend/src/pages/ProjectsPage.tsx` — show `<CelestialLoader>` or skeleton while `useProjects` is loading
- [ ] T031 [P] [US3] Add/verify loading state in `solune/frontend/src/pages/SettingsPage.tsx` — show `<CelestialLoader>` or skeleton while `useSettings` is loading
- [ ] T032 [P] [US3] Add/verify loading state in `solune/frontend/src/pages/ToolsPage.tsx` — show `<CelestialLoader>` or skeleton while `useTools` is loading
- [ ] T033 [P] [US3] Add/verify loading state in `solune/frontend/src/pages/LoginPage.tsx` — show `<CelestialLoader>` or skeleton during auth check if applicable

### Error States

- [ ] T034 [P] [US3] Add/verify error state in `solune/frontend/src/pages/AgentsPage.tsx` — user-friendly error message with "Retry" button; detect rate limit via `isRateLimitApiError()` from `solune/frontend/src/services/api.ts`; rate-limit-specific message
- [ ] T035 [P] [US3] Add/verify error state in `solune/frontend/src/pages/AgentsPipelinePage.tsx` — user-friendly error with retry and rate limit detection
- [ ] T036 [P] [US3] Add/verify error state in `solune/frontend/src/pages/AppPage.tsx` — user-friendly error with retry and rate limit detection
- [ ] T037 [P] [US3] Add/verify error state in `solune/frontend/src/pages/AppsPage.tsx` — user-friendly error with retry and rate limit detection
- [ ] T038 [P] [US3] Add/verify error state in `solune/frontend/src/pages/ChoresPage.tsx` — user-friendly error with retry and rate limit detection
- [ ] T039 [P] [US3] Add/verify error state in `solune/frontend/src/pages/ProjectsPage.tsx` — user-friendly error with retry and rate limit detection
- [ ] T040 [P] [US3] Add/verify error state in `solune/frontend/src/pages/SettingsPage.tsx` — user-friendly error with retry and rate limit detection
- [ ] T041 [P] [US3] Add/verify error state in `solune/frontend/src/pages/ToolsPage.tsx` — user-friendly error with retry and rate limit detection
- [ ] T042 [P] [US3] Add/verify error state in `solune/frontend/src/pages/LoginPage.tsx` — user-friendly auth error with retry

### Empty States

- [ ] T043 [P] [US3] Add/verify empty state in `solune/frontend/src/pages/AgentsPage.tsx` — meaningful message with call-to-action when no agents exist
- [ ] T044 [P] [US3] Add/verify empty state in `solune/frontend/src/pages/AppsPage.tsx` — meaningful message with call-to-action when no apps exist
- [ ] T045 [P] [US3] Add/verify empty state in `solune/frontend/src/pages/ChoresPage.tsx` — meaningful message when no chores exist
- [ ] T046 [P] [US3] Add/verify empty state in `solune/frontend/src/pages/ProjectsPage.tsx` — meaningful message with call-to-action when no projects exist; use `ProjectSelectionEmptyState` if applicable
- [ ] T047 [P] [US3] Add/verify empty state in `solune/frontend/src/pages/ToolsPage.tsx` — meaningful message when no tools exist
- [ ] T048 [P] [US3] Add/verify empty state in `solune/frontend/src/pages/SettingsPage.tsx` — meaningful fallback if settings data is empty

### Error Boundaries & Partial Loading

- [ ] T049 [US3] Verify all 11 pages are wrapped in `<ErrorBoundary>` (either at route level in `solune/frontend/src/App.tsx` or within each page); add missing error boundaries
- [ ] T050 [US3] Audit pages with multiple independent data sources (`AppsPage`, `ProjectsPage`, `AgentsPipelinePage`) for partial loading — each section should show its own loading/error state independently

**Checkpoint**: Every data-fetching page shows loading indicator, error state with retry, rate limit detection, and empty state. No blank screens. Run through each page with network throttling and disconnected states.

---

## Phase 5: Accessibility Compliance (US4) — Priority: P1

**Goal**: All pages meet WCAG AA accessibility standards — keyboard navigable, proper ARIA attributes, focus management in dialogs, form labels, color contrast, and screen reader compatibility.

**Independent Test**: Navigate every page using only keyboard (Tab/Enter/Space/Escape). Verify ARIA attributes on custom controls with browser DevTools. Check focus trapping in all dialogs. Run `npx eslint --rule 'jsx-a11y/*' src/pages/` for static analysis.

### Keyboard Navigation & Focus

- [ ] T051 [P] [US4] Audit and fix keyboard accessibility in `solune/frontend/src/pages/AgentsPage.tsx` and `solune/frontend/src/components/agents/` — all interactive elements reachable via Tab, activatable via Enter/Space; fix any custom clickable `<div>` elements to use `<button>` or add `role="button"` with keyboard handlers
- [ ] T052 [P] [US4] Audit and fix keyboard accessibility in `solune/frontend/src/pages/AgentsPipelinePage.tsx` and `solune/frontend/src/components/pipeline/` — all interactive elements keyboard-accessible
- [ ] T053 [P] [US4] Audit and fix keyboard accessibility in `solune/frontend/src/pages/AppsPage.tsx` and `solune/frontend/src/components/apps/` — all interactive elements keyboard-accessible
- [ ] T054 [P] [US4] Audit and fix keyboard accessibility in `solune/frontend/src/pages/ProjectsPage.tsx` and `solune/frontend/src/components/board/` — all interactive elements keyboard-accessible
- [ ] T055 [P] [US4] Audit and fix keyboard accessibility in `solune/frontend/src/pages/ChoresPage.tsx` and `solune/frontend/src/components/chores/` — all interactive elements keyboard-accessible
- [ ] T056 [P] [US4] Audit and fix keyboard accessibility in remaining pages (`HelpPage`, `LoginPage`, `SettingsPage`, `ToolsPage`, `NotFoundPage`, `AppPage`) — all interactive elements keyboard-accessible

### ARIA Attributes & Labels

- [ ] T057 [P] [US4] Audit and fix ARIA attributes across all custom controls (dropdowns, toggles, tabs, custom menus) in all 11 pages and their feature components — add `role`, `aria-label`, `aria-expanded`, `aria-selected` as needed per WAI-ARIA patterns
- [ ] T058 [P] [US4] Audit and fix form field labels across all pages — every `<input>`, `<select>`, `<textarea>` has a visible `<label>` or `aria-label`; check `LoginPage`, `SettingsPage`, and any inline forms in other pages
- [ ] T059 [P] [US4] Audit and fix screen reader text across all pages — decorative icons get `aria-hidden="true"`, meaningful icons get `aria-label`; check `ThemedAgentIcon` usage and Lucide icon usage

### Focus Management & Contrast

- [ ] T060 [US4] Verify focus trapping in all dialogs/modals across pages — `ConfirmationDialog` and any custom dialogs trap focus and return focus to trigger on close; fix any dialogs that don't trap focus using the existing manual focus trap pattern from `solune/frontend/src/components/ui/confirmation-dialog.tsx`
- [ ] T061 [P] [US4] Audit focus-visible styles across all pages — all interactive elements use `celestial-focus` class or Tailwind `focus-visible:ring-*` utilities; add missing focus styles
- [ ] T062 [P] [US4] Audit color contrast across all pages — text meets WCAG AA 4.5:1 ratio; status indicators use icon + text, not color alone; check badge components, status labels, and alert components

**Checkpoint**: All pages pass keyboard-only navigation test. ARIA attributes present on custom controls. Focus trapped in dialogs. Run `npx eslint src/pages/ src/components/ --rule 'jsx-a11y/*'` — 0 violations.

---

## Phase 6: Type Safety and Data Fetching Compliance (US5) — Priority: P2

**Goal**: All data fetching uses TanStack React Query (`useQuery`/`useMutation`). No `any` types. No type assertions. API types match backend. Proper query key conventions. Mutation error handling with user-visible feedback.

**Independent Test**: Run `npx tsc --noEmit` (0 errors). Grep for `: any` and ` as ` in page/hook/component files (0 matches). Verify all API calls use `useQuery`/`useMutation` pattern.

### Type Safety Remediation

- [ ] T063 [P] [US5] Eliminate all `any` types in `solune/frontend/src/pages/*.tsx` — replace with proper TypeScript types from `solune/frontend/src/types/index.ts` or `solune/frontend/src/types/apps.ts`
- [ ] T064 [P] [US5] Eliminate all `any` types in `solune/frontend/src/hooks/*.ts` — replace with typed API responses, explicit return types on hooks
- [ ] T065 [P] [US5] Eliminate all `any` types in `solune/frontend/src/components/agents/`, `solune/frontend/src/components/apps/`, `solune/frontend/src/components/pipeline/`, `solune/frontend/src/components/board/` — replace with explicit prop interfaces and typed state
- [ ] T066 [P] [US5] Eliminate all type assertions (`as`) in pages, hooks, and feature components — replace with type guards or discriminated unions where feasible
- [ ] T067 [P] [US5] Audit and fix event handler types across all pages — ensure form events use `React.FormEvent<HTMLFormElement>`, click events use `React.MouseEvent`, change events use `React.ChangeEvent<HTMLInputElement>`, not generic `any`

### Data Fetching Compliance

- [ ] T068 [P] [US5] Scan all hooks in `solune/frontend/src/hooks/` for raw `useEffect` + `fetch` patterns — convert any found to `useQuery`/`useMutation` from TanStack React Query
- [ ] T069 [P] [US5] Audit query key conventions in all hooks — verify keys follow `[feature].all / .list(id) / .detail(id)` pattern consistent with existing `pipelineKeys`, `appKeys` patterns in `solune/frontend/src/services/api.ts`
- [ ] T070 [P] [US5] Audit all `useMutation` calls across hooks — verify each has `onError` callback that surfaces user-visible feedback (toast or inline error); add missing error handlers
- [ ] T071 [P] [US5] Audit for duplicate API calls — check that same data isn't fetched independently in both page and child component; consolidate via prop passing or shared hook
- [ ] T072 [P] [US5] Audit and configure `staleTime` on queries — data that doesn't change frequently should have reasonable staleTime (e.g., 30s for lists, 60s for settings)

**Checkpoint**: `npx tsc --noEmit` — 0 errors. `grep -rn ': any' solune/frontend/src/pages/ solune/frontend/src/hooks/` — 0 matches. All API calls use React Query.

---

## Phase 7: UX Polish and Text Quality (US6) — Priority: P2

**Goal**: All user-visible text is final, professional copy. Consistent terminology. Verb-based action buttons. Destructive actions confirmed. Success feedback on mutations. User-friendly error messages. Consistent timestamps. Truncation with tooltips.

**Independent Test**: Grep for "TODO", "Lorem", "Test" in user-visible strings (0 matches). Verify all delete/remove/stop actions use `<ConfirmationDialog>`. Check button labels are verb phrases.

### Text & Terminology

- [ ] T073 [P] [US6] Scan all 11 pages and feature components for placeholder text ("TODO", "Lorem ipsum", "Test", "placeholder", "xxx", "TBD") — remove or replace with final copy
- [ ] T074 [P] [US6] Audit terminology consistency across all pages — verify consistent use of "pipeline" (not "workflow"), "chore" (not "task"), and other app-specific terms; align all pages to the same vocabulary
- [ ] T075 [P] [US6] Audit action button labels across all pages — ensure verb phrases ("Create Agent", "Save Settings", "Delete Pipeline", "Run Pipeline") not noun phrases ("New Agent", "Settings", "Pipeline")

### Confirmations & Feedback

- [ ] T076 [P] [US6] Audit all destructive actions (delete, remove, stop) across all pages — verify each uses `<ConfirmationDialog>` from `solune/frontend/src/components/ui/confirmation-dialog.tsx`; add missing confirmation dialogs with clear title, consequence description, and cancel/confirm buttons
- [ ] T077 [P] [US6] Audit mutation success feedback across all pages — verify each mutation shows success state (toast, inline message, or status change); add missing success feedback
- [ ] T078 [P] [US6] Audit error messages across all pages — verify format follows "Could not [action]. [Reason, if known]. [Suggested next step]." pattern; replace any raw error codes or stack traces

### Timestamps & Truncation

- [ ] T079 [P] [US6] Audit timestamp formatting across all pages — verify recent timestamps use relative format ("2 hours ago"), older timestamps use absolute format; standardize any inconsistencies
- [ ] T080 [P] [US6] Audit long text handling across all pages — verify names, descriptions, URLs truncated with `text-ellipsis` and full text available via `<Tooltip>` from `solune/frontend/src/components/ui/tooltip.tsx`; add missing truncation/tooltip patterns

**Checkpoint**: `grep -rn 'TODO\|Lorem\|placeholder' solune/frontend/src/pages/` — 0 matches. All destructive actions confirmed. All buttons use verbs.

---

## Phase 8: Styling, Performance, and Code Hygiene (US7) — Priority: P2

**Goal**: All pages use Tailwind utility classes exclusively. Dark mode works. Responsive from 768px to 1920px. No inline styles. No hardcoded colors. Stable list keys. Memoized transforms. No dead code. No console.log. Path alias imports. ESLint clean.

**Independent Test**: Grep for `style=`, hardcoded color hex codes, `key={index}`, `console.log`, relative imports (0 matches each). Run `npx eslint src/pages/` — 0 warnings.

### Styling & Layout

- [ ] T081 [P] [US7] Audit and fix inline `style={}` attributes across all pages and feature components — convert to Tailwind utility classes using `cn()` from `solune/frontend/src/lib/utils.ts`
- [ ] T082 [P] [US7] Audit and fix hardcoded colors across all pages — replace `#fff`, `bg-white`, `text-black`, etc. with theme-aware CSS variables or `dark:` variants
- [ ] T083 [P] [US7] Audit responsive design across all pages — verify layouts work from 768px to 1920px viewport widths; fix grid/flex layouts that break at narrow or wide viewports
- [ ] T084 [P] [US7] Audit and fix arbitrary spacing values across all pages — replace `p-[13px]`, `m-[7px]`, etc. with standard Tailwind spacing scale values (`p-3`, `m-2`, etc.)
- [ ] T085 [P] [US7] Audit content section consistency across all pages — verify sections use `<Card>` from `solune/frontend/src/components/ui/card.tsx` with consistent padding/rounding

### Performance

- [ ] T086 [P] [US7] Audit list rendering keys across all pages — replace any `key={index}` with `key={item.id}` or other stable identifiers
- [ ] T087 [P] [US7] Audit for heavy sync computation in render across all pages — wrap sorting, filtering, grouping transforms in `useMemo`; wrap callbacks passed to memoized children in `useCallback`
- [ ] T088 [P] [US7] Audit large list rendering across all pages — if any page renders >50 items, verify pagination or consider `react-window` virtualization
- [ ] T089 [P] [US7] Audit non-critical images/icons for lazy loading across all pages — add `loading="lazy"` where applicable

### Code Hygiene

- [ ] T090 [P] [US7] Remove dead code across all pages and feature components — unused imports, commented-out blocks, unreachable branches
- [ ] T091 [P] [US7] Remove all `console.log` statements across all pages, hooks, and feature components — replace with structured logging only if operationally needed
- [ ] T092 [P] [US7] Convert all relative imports to `@/` path alias across all pages, hooks, and feature components — replace `../../components/` with `@/components/`, `../../hooks/` with `@/hooks/`, etc.
- [ ] T093 [P] [US7] Audit and fix file naming conventions — components PascalCase `.tsx`, hooks `use*.ts`, types in `types/`, utilities in `lib/`
- [ ] T094 [P] [US7] Extract magic strings (repeated status values, route paths, query keys) into named constants; create or update constant files as needed

**Checkpoint**: `npx eslint solune/frontend/src/pages/ solune/frontend/src/components/ solune/frontend/src/hooks/` — 0 warnings. No inline styles, hardcoded colors, index keys, console.log, or relative imports.

---

## Phase 9: Test Coverage Verification (US8) — Priority: P3

**Goal**: All custom hooks have test files covering happy path, error, loading, and empty states. Key interactive components have interaction tests. Tests use project conventions (`vi.mock`, `renderHook`, `waitFor`, `createWrapper()`). No snapshot tests. All assertion-based.

**Independent Test**: Run `npx vitest run` — all tests pass. Verify test files exist for each hook and key interactive component.

### Hook Tests

- [ ] T095 [P] [US8] Write/verify tests for `useAgents` hook in `solune/frontend/src/hooks/useAgents.test.ts` — cover happy path (agents loaded), error state (API failure), loading state, empty state (no agents), rate limit error; use `vi.mock('@/services/api', ...)`, `renderHook`, `waitFor`, `createWrapper()`
- [ ] T096 [P] [US8] Write/verify tests for `useApps` hook in `solune/frontend/src/hooks/useApps.test.ts` — cover happy path, error, loading, empty, rate limit states
- [ ] T097 [P] [US8] Write/verify tests for `usePipelineConfig` hook in `solune/frontend/src/hooks/usePipelineConfig.test.ts` — cover happy path, error, loading states
- [ ] T098 [P] [US8] Write/verify tests for `useProjects` hook in `solune/frontend/src/hooks/useProjects.test.ts` — cover happy path, error, loading, empty states
- [ ] T099 [P] [US8] Write/verify tests for `useChores` hook in `solune/frontend/src/hooks/useChores.test.ts` — cover happy path, error, loading, empty states
- [ ] T100 [P] [US8] Write/verify tests for `useTools` hook in `solune/frontend/src/hooks/useTools.test.ts` — cover happy path, error, loading, empty states
- [ ] T101 [P] [US8] Write/verify tests for `useSettings` hook in `solune/frontend/src/hooks/useSettings.test.ts` — cover happy path, error, loading states
- [ ] T102 [P] [US8] Write/verify tests for `useAuth` hook in `solune/frontend/src/hooks/useAuth.test.ts` — cover authenticated, unauthenticated, error, loading states

### Component Interaction Tests

- [ ] T103 [P] [US8] Write/verify interaction tests for AgentsPage components in `solune/frontend/src/components/agents/*.test.tsx` — test agent selection, creation dialog, deletion confirmation
- [ ] T104 [P] [US8] Write/verify interaction tests for AppsPage components in `solune/frontend/src/components/apps/*.test.tsx` — test app creation, deletion, app card interactions
- [ ] T105 [P] [US8] Write/verify interaction tests for ProjectsPage/board components in `solune/frontend/src/components/board/*.test.tsx` — test project selection, board interactions
- [ ] T106 [P] [US8] Write/verify interaction tests for ChoresPage components in `solune/frontend/src/components/chores/*.test.tsx` — test chore interactions, status changes
- [ ] T107 [P] [US8] Write/verify interaction tests for PipelinePage components in `solune/frontend/src/components/pipeline/*.test.tsx` — test pipeline configuration, stage interactions
- [ ] T108 [P] [US8] Write/verify interaction tests for SettingsPage components in `solune/frontend/src/components/settings/*.test.tsx` — test settings form submission, validation
- [ ] T109 [P] [US8] Write/verify interaction tests for LoginPage components in `solune/frontend/src/components/auth/*.test.tsx` — test login flow, error handling

### Test Quality Verification

- [ ] T110 [US8] Scan all test files for snapshot tests (`toMatchSnapshot`, `toMatchInlineSnapshot`) — convert any found to assertion-based tests
- [ ] T111 [US8] Run full test suite `npm run test` in `solune/frontend/` — verify all tests pass with 0 failures

**Checkpoint**: `npx vitest run` — all tests pass. Every hook has a test file. Key interactive components have test files. No snapshot tests.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all quality dimensions. Update audit findings with remediation status. Ensure no regressions.

- [ ] T112 Run full ESLint scan: `npx eslint solune/frontend/src/pages/ solune/frontend/src/components/ solune/frontend/src/hooks/` — verify 0 warnings
- [ ] T113 Run full TypeScript check: `npx tsc --noEmit` in `solune/frontend/` — verify 0 errors
- [ ] T114 Run full test suite: `npm run test` in `solune/frontend/` — verify all tests pass
- [ ] T115 Run frontend build: `npm run build` in `solune/frontend/` — verify build succeeds
- [ ] T116 [P] Update all 11 page audit files in `specs/052-ui-audit/checklists/` — re-score all Fail items that were remediated; update status to "Audit Passed" for pages with 0 remaining Fail items
- [ ] T117 [P] Update consolidated audit summary at `specs/052-ui-audit/checklists/audit-summary.md` — final Pass/Fail/N/A counts, all severity counts, overall status
- [ ] T118 Run `specs/052-ui-audit/quickstart.md` verification commands — full lint, type check, test, build, page line count check
- [ ] T119 Manual browser verification: light mode + dark mode, viewport 768px to 1920px, keyboard-only navigation through all 11 pages, screen reader spot check

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Discovery & Assessment (Phase 2 / US1)**: Depends on Setup — BLOCKS all remediation phases
- **Component Architecture (Phase 3 / US2)**: Depends on Phase 2 — should be done FIRST among remediation phases as it restructures files that other phases modify
- **Loading/Error/Empty States (Phase 4 / US3)**: Depends on Phase 2; best after Phase 3 (works with extracted components)
- **Accessibility (Phase 5 / US4)**: Depends on Phase 2; best after Phase 3 (ARIA on final component structure)
- **Type Safety & Data Fetching (Phase 6 / US5)**: Depends on Phase 2; can run in parallel with Phases 4–5
- **UX Polish (Phase 7 / US6)**: Depends on Phase 2; can run in parallel with Phases 4–6
- **Styling, Perf & Hygiene (Phase 8 / US7)**: Depends on Phase 2; best after Phase 3 (works with final file structure)
- **Test Coverage (Phase 9 / US8)**: Depends on Phases 3–8 (tests should verify final state, not pre-remediation state)
- **Polish (Phase 10)**: Depends on all previous phases

### User Story Dependencies

- **US1 (Audit All Categories)**: No dependencies — discovery phase. BLOCKS all other stories.
- **US2 (Component Architecture)**: Depends on US1. Should complete BEFORE US3–US7 to establish final component structure.
- **US3 (Loading/Error/Empty States)**: Depends on US1. Best after US2. No dependency on US4–US7.
- **US4 (Accessibility)**: Depends on US1. Best after US2. No dependency on US3, US5–US7.
- **US5 (Type Safety & Data Fetching)**: Depends on US1. Can run in parallel with US3–US4 and US6–US7.
- **US6 (UX Polish)**: Depends on US1. Can run in parallel with US3–US5.
- **US7 (Styling, Perf & Hygiene)**: Depends on US1. Best after US2. Can run in parallel with US3–US6.
- **US8 (Test Coverage)**: Depends on US1–US7 (tests should verify remediated state).

### Within Each User Story

- Discovery (US1) MUST complete before any remediation
- Within remediation phases: tasks marked [P] can run in parallel (different files)
- Architecture changes (US2) should precede other remediation to avoid rework
- Tests (US8) come last to verify final state

### Parallel Opportunities

- **Phase 1**: T002, T003, T004, T005 can all run in parallel
- **Phase 2**: All 11 page audits (T006–T016) can run in parallel
- **Phase 3**: T021, T022, T023, T024 can run in parallel (different audit dimensions); T018, T019, T020 can run in parallel (different page files)
- **Phase 4**: All loading state tasks (T025–T033) in parallel; all error state tasks (T034–T042) in parallel; all empty state tasks (T043–T048) in parallel
- **Phase 5**: All keyboard tasks (T051–T056) in parallel; T057, T058, T059 in parallel; T061, T062 in parallel
- **Phase 6**: All type safety tasks (T063–T067) in parallel; all data fetching tasks (T068–T072) in parallel
- **Phase 7**: All text tasks (T073–T075) in parallel; all confirmation tasks (T076–T078) in parallel
- **Phase 8**: All styling tasks (T081–T085) in parallel; all performance tasks (T086–T089) in parallel; all hygiene tasks (T090–T094) in parallel
- **Phase 9**: All hook tests (T095–T102) in parallel; all component tests (T103–T109) in parallel

---

## Parallel Example: Phase 2 — Discovery

```bash
# Launch all 11 page audits in parallel (each is independent):
Task T006: "Audit AgentsPage — score 65 items, produce agents-page-audit.md"
Task T007: "Audit AgentsPipelinePage — score 65 items, produce agents-pipeline-page-audit.md"
Task T008: "Audit AppPage — score 65 items, produce app-page-audit.md"
Task T009: "Audit AppsPage — score 65 items, produce apps-page-audit.md"
Task T010: "Audit ChoresPage — score 65 items, produce chores-page-audit.md"
Task T011: "Audit HelpPage — score 65 items, produce help-page-audit.md"
Task T012: "Audit LoginPage — score 65 items, produce login-page-audit.md"
Task T013: "Audit NotFoundPage — score 65 items, produce not-found-page-audit.md"
Task T014: "Audit ProjectsPage — score 65 items, produce projects-page-audit.md"
Task T015: "Audit SettingsPage — score 65 items, produce settings-page-audit.md"
Task T016: "Audit ToolsPage — score 65 items, produce tools-page-audit.md"
```

## Parallel Example: Phase 4 — Loading States

```bash
# Launch all loading state tasks in parallel (each modifies a different page file):
Task T025: "Add/verify loading state in AgentsPage.tsx"
Task T026: "Add/verify loading state in AgentsPipelinePage.tsx"
Task T027: "Add/verify loading state in AppPage.tsx"
Task T028: "Add/verify loading state in AppsPage.tsx"
Task T029: "Add/verify loading state in ChoresPage.tsx"
Task T030: "Add/verify loading state in ProjectsPage.tsx"
Task T031: "Add/verify loading state in SettingsPage.tsx"
Task T032: "Add/verify loading state in ToolsPage.tsx"
Task T033: "Add/verify loading state in LoginPage.tsx"
```

## Parallel Example: Phase 9 — Hook Tests

```bash
# Launch all hook test tasks in parallel (each creates/modifies a different test file):
Task T095: "Write/verify tests for useAgents hook"
Task T096: "Write/verify tests for useApps hook"
Task T097: "Write/verify tests for usePipelineConfig hook"
Task T098: "Write/verify tests for useProjects hook"
Task T099: "Write/verify tests for useChores hook"
Task T100: "Write/verify tests for useTools hook"
Task T101: "Write/verify tests for useSettings hook"
Task T102: "Write/verify tests for useAuth hook"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only — Discovery)

1. Complete Phase 1: Setup (audit infrastructure)
2. Complete Phase 2: Discovery & Assessment (US1) — audit all 11 pages
3. **STOP and VALIDATE**: All pages have scored findings. Full remediation scope is known.
4. Prioritize remediation based on severity (Critical → Major → Minor)

### Incremental Delivery

1. Complete Setup + Discovery → Full audit backlog known
2. Complete US2 (Architecture) → Pages restructured, files manageable
3. Complete US3 (States) → No blank screens, user-friendly errors → Deploy/Demo
4. Complete US4 (Accessibility) → WCAG AA compliant → Deploy/Demo
5. Complete US5 (Type Safety) → Zero `any` types, consistent data fetching → Deploy/Demo
6. Complete US6 (UX Polish) → Professional text, confirmations, feedback → Deploy/Demo
7. Complete US7 (Styling/Perf/Hygiene) → Clean code, responsive, dark mode → Deploy/Demo
8. Complete US8 (Tests) → Regression safety net → Deploy/Demo
9. Complete Polish → Final validation, audit sign-off

### Parallel Team Strategy

With multiple developers after Phase 2 completes:

1. Team completes Setup + Discovery together
2. Developer A: US2 (Architecture) — FIRST, as it changes file structure
3. After US2 completes:
   - Developer A: US3 (States) + US4 (Accessibility)
   - Developer B: US5 (Type Safety) + US6 (UX Polish)
   - Developer C: US7 (Styling/Perf/Hygiene)
4. After US3–US7 complete:
   - Developer A: US8 (Tests)
   - Developer B: Polish & validation

---

## Notes

- [P] tasks = different files, no dependencies — safe to run in parallel
- [Story] label maps each task to a specific user story for traceability
- Each user story phase can be independently verified after completion
- Discovery (US1) is a documentation-only phase — no code changes
- Architecture (US2) changes file structure — should complete before other remediation to avoid merge conflicts
- Tests (US8) come last to verify the remediated state, not the pre-audit state
- Commit after each task or logical group of parallel tasks
- Stop at any checkpoint to validate independently
- Total pages: 11 | Total checklist items per page: 65 | Total evaluations: 715
- Avoid: cross-page tasks that modify the same file, remediation before discovery is complete
