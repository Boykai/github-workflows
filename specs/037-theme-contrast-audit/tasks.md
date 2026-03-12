# Tasks: Frontend Theme Audit — Light/Dark Mode Contrast & Style Consistency

**Input**: Design documents from `/specs/037-theme-contrast-audit/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md

**Tests**: No new product test suite is mandated by the specification. Use the existing frontend validation commands and the audit tooling created in this plan to verify token usage, contrast compliance, and theme behavior.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. This is a frontend-only audit across `frontend/src/` plus supporting audit documentation under `specs/037-theme-contrast-audit/`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/` for product code and `frontend/package.json` for validation commands
- **Audit tooling**: `frontend/scripts/`
- **Feature documentation**: `specs/037-theme-contrast-audit/`

---

## Phase 1: Setup (Audit Baseline)

**Purpose**: Establish the audit baseline, current token inventory, and documented exception scope before implementing theme fixes.

- [ ] T001 Run the existing frontend baseline commands defined in `frontend/package.json` (`npm run type-check`, `npm run lint`, `npx vitest run`) and capture any unrelated pre-existing failures before audit changes begin
- [ ] T002 Review the current theme tokens, `@theme` mappings, shadow definitions, `solar-*` utilities, and existing `!important` overrides in `frontend/src/index.css` against `specs/037-theme-contrast-audit/contracts/token-registry.md`
- [ ] T003 [P] Capture the initial approved-exception scope in `specs/037-theme-contrast-audit/contracts/audit-checklist.md` using `frontend/src/components/agents/AgentAvatar.tsx`, `frontend/src/components/board/colorUtils.ts`, and `frontend/src/components/board/IssueCard.tsx`

---

## Phase 2: Foundational (Blocking Audit Infrastructure)

**Purpose**: Build the audit tooling and coverage matrix that MUST exist before story-by-story remediation begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create the hardcoded-color scan script in `frontend/scripts/audit-theme-colors.mjs` to inspect `frontend/src/components/`, `frontend/src/pages/`, and `frontend/src/layout/` for raw hex/rgb/rgba/hsl usage
- [ ] T005 [P] Create the WCAG contrast audit script in `frontend/scripts/check-theme-contrast.mjs` to evaluate the contrast pairs defined in `specs/037-theme-contrast-audit/data-model.md`
- [ ] T006 [P] Add reusable token parsing and HSL/RGB contrast helpers in `frontend/src/lib/themeAudit.ts` for `frontend/scripts/audit-theme-colors.mjs` and `frontend/scripts/check-theme-contrast.mjs`
- [ ] T007 [P] Add audit script entries (`audit:theme-colors`, `audit:theme-contrast`) to `frontend/package.json`
- [ ] T008 Build the component/page/theme-scope coverage matrix in `specs/037-theme-contrast-audit/contracts/audit-checklist.md` using `frontend/src/pages/AppPage.tsx`, `frontend/src/pages/LoginPage.tsx`, `frontend/src/pages/ProjectsPage.tsx`, `frontend/src/pages/AgentsPage.tsx`, `frontend/src/pages/AgentsPipelinePage.tsx`, `frontend/src/pages/ToolsPage.tsx`, `frontend/src/pages/SettingsPage.tsx`, `frontend/src/pages/ChoresPage.tsx`, `frontend/src/pages/NotFoundPage.tsx`, `frontend/src/layout/AuthGate.tsx`, `frontend/src/layout/Sidebar.tsx`, `frontend/src/layout/TopBar.tsx`, `frontend/src/layout/RateLimitBar.tsx`, `frontend/src/layout/NotificationBell.tsx`, `frontend/src/components/board/AddAgentPopover.tsx`, `frontend/src/components/board/CleanUpSummary.tsx`, `frontend/src/components/board/CleanUpAuditHistory.tsx`, `frontend/src/components/board/CleanUpConfirmModal.tsx`, `frontend/src/components/pipeline/ModelSelector.tsx`, `frontend/src/components/pipeline/StageCard.tsx`, `frontend/src/components/agents/AgentIconPickerModal.tsx`, `frontend/src/components/chores/ChoreCard.tsx`, and a named "new component dark-mode token mapping required" rule in `specs/037-theme-contrast-audit/contracts/audit-checklist.md`

**Checkpoint**: Audit tooling and coverage matrix are ready — user story implementation can now begin in parallel where dependencies allow

---

## Phase 3: User Story 1 — Hardcoded Color Elimination (Priority: P1) 🎯 MVP

**Goal**: Eliminate theme-breaking hardcoded colors across the frontend so all Light/Dark styling derives from shared Celestial tokens or approved documented exceptions.

**Independent Test**: Run `frontend/scripts/audit-theme-colors.mjs` against `frontend/src/components/`, `frontend/src/pages/`, and `frontend/src/layout/`. Every match must either resolve to a shared theme token or remain listed as an approved exception in `specs/037-theme-contrast-audit/contracts/audit-checklist.md`.

### Implementation for User Story 1

- [ ] T009 [P] [US1] Replace hardcoded colors in the base UI layer with token-driven styling in `frontend/src/components/ui/button.tsx`, `frontend/src/components/ui/input.tsx`, `frontend/src/components/ui/card.tsx`, `frontend/src/components/ui/tooltip.tsx`, and `frontend/src/components/ui/confirmation-dialog.tsx`
- [ ] T010 [P] [US1] Replace hardcoded gradients, fills, and surface colors in shared visuals and shell components in `frontend/src/components/AnimatedBackground.tsx`, `frontend/src/components/common/CelestialLoader.tsx`, `frontend/src/components/common/CelestialCatalogHero.tsx`, `frontend/src/layout/Sidebar.tsx`, and `frontend/src/layout/TopBar.tsx`
- [ ] T011 [P] [US1] Remove theme-breaking hardcoded colors from agent and board surfaces while preserving documented GitHub-data exceptions in `frontend/src/components/agents/AgentCard.tsx`, `frontend/src/components/agents/AgentsPanel.tsx`, `frontend/src/components/agents/AgentInlineEditor.tsx`, `frontend/src/components/agents/AddAgentModal.tsx`, `frontend/src/components/board/AgentTile.tsx`, `frontend/src/components/board/BoardToolbar.tsx`, `frontend/src/components/board/ProjectBoard.tsx`, and `frontend/src/components/board/IssueCard.tsx`
- [ ] T012 [P] [US1] Remove theme-breaking hardcoded colors from pipeline, chat, tools, settings, chores, and page-level surfaces in `frontend/src/components/pipeline/PipelineBoard.tsx`, `frontend/src/components/pipeline/PipelineToolbar.tsx`, `frontend/src/components/pipeline/StageCard.tsx`, `frontend/src/components/pipeline/AgentNode.tsx`, `frontend/src/components/chat/ChatToolbar.tsx`, `frontend/src/components/chat/ChatPopup.tsx`, `frontend/src/components/chat/MessageBubble.tsx`, `frontend/src/components/chat/VoiceInputButton.tsx`, `frontend/src/components/tools/ToolsPanel.tsx`, `frontend/src/components/tools/ToolCard.tsx`, `frontend/src/components/tools/RepoConfigPanel.tsx`, `frontend/src/components/settings/DynamicDropdown.tsx`, `frontend/src/components/settings/DisplaySettings.tsx`, `frontend/src/components/settings/AISettingsSection.tsx`, `frontend/src/components/chores/ChoresPanel.tsx`, `frontend/src/components/chores/ChoreCard.tsx`, `frontend/src/components/chores/AddChoreModal.tsx`, `frontend/src/pages/LoginPage.tsx`, `frontend/src/pages/ProjectsPage.tsx`, `frontend/src/pages/AgentsPage.tsx`, `frontend/src/pages/AgentsPipelinePage.tsx`, `frontend/src/pages/ToolsPage.tsx`, `frontend/src/pages/SettingsPage.tsx`, `frontend/src/pages/ChoresPage.tsx`, and `frontend/src/pages/NotFoundPage.tsx`
- [ ] T013 [US1] Re-run `frontend/scripts/audit-theme-colors.mjs` and document any remaining approved exceptions in `specs/037-theme-contrast-audit/contracts/audit-checklist.md` and `specs/037-theme-contrast-audit/contracts/token-registry.md`

**Checkpoint**: User Story 1 complete — the frontend no longer contains unclassified hardcoded theme colors

---

## Phase 4: User Story 2 — WCAG AA Contrast Compliance (Priority: P1)

**Goal**: Ensure all text, icons, borders, and UI boundaries meet WCAG 2.1 AA contrast ratios in both Light and Dark modes.

**Independent Test**: Run `frontend/scripts/check-theme-contrast.mjs` against the contrast pairs in `specs/037-theme-contrast-audit/data-model.md`. All normal text pairs must pass ≥4.5:1 and all large-text or UI-boundary pairs must pass ≥3:1 in both themes.

### Implementation for User Story 2

- [ ] T014 [P] [US2] Adjust core surface and foreground token pairs to meet AA contrast thresholds in `frontend/src/index.css`
- [ ] T015 [P] [US2] Correct shadow, border, input, and focus-ring contrast behavior for Light/Dark surfaces in `frontend/src/index.css`
- [ ] T016 [P] [US2] Correct semantic/status contrast for `solar-*`, priority, and sync utilities in `frontend/src/index.css`, `frontend/src/components/board/colorUtils.ts`, and `frontend/src/components/board/IssueCard.tsx`
- [ ] T017 [P] [US2] Fix icon, badge, loader, code block, and message contrast issues in `frontend/src/components/common/ThemedAgentIcon.tsx`, `frontend/src/components/common/agentIcons.tsx`, `frontend/src/components/common/CelestialLoader.tsx`, `frontend/src/components/chat/MessageBubble.tsx`, `frontend/src/components/chores/ChoreChatFlow.tsx`, `frontend/src/components/common/ErrorBoundary.tsx`, `frontend/src/components/board/IssueDetailModal.tsx`, `frontend/src/components/tools/GitHubMcpConfigGenerator.tsx`, and `frontend/src/components/agents/AgentInlineEditor.tsx`
- [ ] T018 [US2] Run `frontend/scripts/check-theme-contrast.mjs` and resolve every failing contrast pair referenced in `specs/037-theme-contrast-audit/data-model.md`

**Checkpoint**: User Story 2 complete — all audited token pairs and UI boundaries meet WCAG AA contrast thresholds

---

## Phase 5: User Story 3 — Interactive-State Styling (Priority: P1)

**Goal**: Ensure hover, focus, active, and disabled states remain visually distinct and contrast-compliant across all interactive controls in both themes.

**Independent Test**: Tab through the application routes in both themes and verify every interactive control shows a visible focus indicator, hover/active state change, and a legible disabled state that still meets the required contrast threshold.

### Implementation for User Story 3

- [ ] T019 [P] [US3] Audit and fix button/link interactive states in `frontend/src/components/ui/button.tsx`, `frontend/src/components/auth/LoginButton.tsx`, `frontend/src/layout/Sidebar.tsx`, and `frontend/src/layout/NotificationBell.tsx`
- [ ] T020 [P] [US3] Audit and fix input, dropdown, and selector focus/disabled states in `frontend/src/components/ui/input.tsx`, `frontend/src/components/settings/DynamicDropdown.tsx`, `frontend/src/components/pipeline/ModelSelector.tsx`, and `frontend/src/components/chores/PipelineSelector.tsx`
- [ ] T021 [P] [US3] Audit and fix interactive card/tile states in `frontend/src/components/board/AgentTile.tsx`, `frontend/src/components/board/IssueCard.tsx`, `frontend/src/components/pipeline/StageCard.tsx`, and `frontend/src/components/pipeline/AgentNode.tsx`
- [ ] T022 [P] [US3] Audit and fix chat/editor interactive states in `frontend/src/components/chat/ChatToolbar.tsx`, `frontend/src/components/chat/VoiceInputButton.tsx`, `frontend/src/components/chat/MentionInput.tsx`, and `frontend/src/components/chat/CommandAutocomplete.tsx`
- [ ] T023 [US3] Verify keyboard and pointer interaction states across `frontend/src/pages/AppPage.tsx`, `frontend/src/pages/LoginPage.tsx`, `frontend/src/pages/ProjectsPage.tsx`, `frontend/src/pages/AgentsPage.tsx`, `frontend/src/pages/AgentsPipelinePage.tsx`, `frontend/src/pages/ToolsPage.tsx`, `frontend/src/pages/SettingsPage.tsx`, `frontend/src/pages/ChoresPage.tsx`, `frontend/src/pages/NotFoundPage.tsx`, `frontend/src/layout/AuthGate.tsx`, and `frontend/src/layout/RateLimitBar.tsx`

**Checkpoint**: User Story 3 complete — interactive states are visible, consistent, and accessible in both themes

---

## Phase 6: User Story 4 — Component Variant Consistency (Priority: P2)

**Goal**: Align every component variant with the Project Solune visual language so shared UI patterns look cohesive in both Light and Dark mode.

**Independent Test**: Render each major component variant in Light and Dark mode and compare the result against the Celestial token reference in `specs/037-theme-contrast-audit/contracts/token-registry.md`. Buttons, cards, inputs, badges, navigation, overlays, and panels should match the approved style language with no mismatched surfaces or shadows.

### Implementation for User Story 4

- [ ] T024 [P] [US4] Normalize base UI component variants to Celestial tokens in `frontend/src/components/ui/button.tsx`, `frontend/src/components/ui/card.tsx`, `frontend/src/components/ui/input.tsx`, `frontend/src/components/ui/tooltip.tsx`, and `frontend/src/components/ui/confirmation-dialog.tsx`
- [ ] T025 [P] [US4] Normalize app-shell and navigation variants in `frontend/src/layout/AppLayout.tsx`, `frontend/src/layout/AuthGate.tsx`, `frontend/src/layout/Sidebar.tsx`, `frontend/src/layout/TopBar.tsx`, `frontend/src/layout/Breadcrumb.tsx`, `frontend/src/layout/ProjectSelector.tsx`, and `frontend/src/layout/RateLimitBar.tsx`
- [ ] T026 [P] [US4] Normalize board and pipeline surface variants in `frontend/src/components/board/ProjectBoard.tsx`, `frontend/src/components/board/BoardToolbar.tsx`, `frontend/src/components/board/ProjectIssueLaunchPanel.tsx`, `frontend/src/components/pipeline/PipelineBoard.tsx`, `frontend/src/components/pipeline/PipelineToolbar.tsx`, and `frontend/src/components/pipeline/SavedWorkflowsList.tsx`
- [ ] T027 [P] [US4] Normalize feature-specific cards, badges, panels, and modal variants in `frontend/src/components/agents/AgentCard.tsx`, `frontend/src/components/agents/AgentsPanel.tsx`, `frontend/src/components/agents/AddAgentModal.tsx`, `frontend/src/components/tools/ToolsPanel.tsx`, `frontend/src/components/tools/ToolCard.tsx`, `frontend/src/components/tools/RepoConfigPanel.tsx`, `frontend/src/components/settings/DisplaySettings.tsx`, `frontend/src/components/settings/NotificationSettings.tsx`, `frontend/src/components/settings/WorkflowSettings.tsx`, `frontend/src/components/chores/ChoresPanel.tsx`, `frontend/src/components/chores/ChoreCard.tsx`, and `frontend/src/components/chores/AddChoreModal.tsx`
- [ ] T028 [US4] Perform a cross-page consistency pass against `specs/037-theme-contrast-audit/contracts/token-registry.md` using `frontend/src/pages/AppPage.tsx`, `frontend/src/pages/LoginPage.tsx`, `frontend/src/pages/ProjectsPage.tsx`, `frontend/src/pages/AgentsPage.tsx`, `frontend/src/pages/AgentsPipelinePage.tsx`, `frontend/src/pages/ToolsPage.tsx`, `frontend/src/pages/SettingsPage.tsx`, `frontend/src/pages/ChoresPage.tsx`, and `frontend/src/pages/NotFoundPage.tsx`

**Checkpoint**: User Story 4 complete — component variants render consistently with the app’s established style guide in both themes

---

## Phase 7: User Story 5 — Theme-Switch Stability (Priority: P2)

**Goal**: Make theme toggling seamless, with no FOUC, broken layouts, or lingering theme artifacts on any page or overlay.

**Independent Test**: Follow the toggle scenarios in `specs/037-theme-contrast-audit/quickstart.md` on every major page, switching between Light and Dark three or more times. The final state must always render correctly with no flash, layout shift, or stale colors.

### Implementation for User Story 5

- [ ] T029 [P] [US5] Verify root theme class handling, persisted preference, and transition timing in `frontend/src/components/ThemeProvider.tsx`, `frontend/src/hooks/useAppTheme.ts`, and `frontend/src/layout/Sidebar.tsx`
- [ ] T030 [P] [US5] Remove or adjust theme-toggle flicker sources in portaled overlays and dialogs in `frontend/src/components/board/IssueDetailModal.tsx`, `frontend/src/components/board/CleanUpSummary.tsx`, `frontend/src/components/board/CleanUpAuditHistory.tsx`, `frontend/src/components/board/CleanUpConfirmModal.tsx`, `frontend/src/components/agents/AddAgentModal.tsx`, `frontend/src/components/agents/AgentIconPickerModal.tsx`, and `frontend/src/components/agents/BulkModelUpdateDialog.tsx`
- [ ] T031 [P] [US5] Verify loaders, gradients, and skeleton states transition cleanly during rapid theme toggles in `frontend/src/components/AnimatedBackground.tsx`, `frontend/src/components/common/CelestialLoader.tsx`, `frontend/src/components/chores/FeaturedRitualsPanel.tsx`, and `frontend/src/components/chat/ChatPopup.tsx`
- [ ] T032 [P] [US5] Verify `prefers-color-scheme` resolution, persisted theme restoration, and system-theme conflicts in `frontend/src/components/ThemeProvider.tsx`, `frontend/src/hooks/useAppTheme.ts`, and `frontend/src/pages/AppPage.tsx`
- [ ] T033 [P] [US5] Audit and remediate scrollbar, transparent-media, background-layer, and theme-blocking `!important` behavior during theme toggles in `frontend/src/index.css`, `frontend/src/components/AnimatedBackground.tsx`, `frontend/src/pages/LoginPage.tsx`, and `frontend/src/layout/AppLayout.tsx`
- [ ] T034 [US5] Execute the theme-toggle scenarios from `specs/037-theme-contrast-audit/quickstart.md` across `frontend/src/pages/AppPage.tsx`, `frontend/src/pages/LoginPage.tsx`, `frontend/src/pages/ProjectsPage.tsx`, `frontend/src/pages/AgentsPage.tsx`, `frontend/src/pages/AgentsPipelinePage.tsx`, `frontend/src/pages/ToolsPage.tsx`, `frontend/src/pages/SettingsPage.tsx`, `frontend/src/pages/ChoresPage.tsx`, and `frontend/src/pages/NotFoundPage.tsx`

**Checkpoint**: User Story 5 complete — theme switching is smooth, stable, and visually correct across pages and overlays

---

## Phase 8: User Story 6 — Third-Party Component Theme Inheritance (Priority: P3)

**Goal**: Ensure all Radix and portal-based third-party surfaces inherit the active theme context instead of rendering with default or mismatched styling.

**Independent Test**: Render every third-party or portal-based surface in both Light and Dark mode and verify that the active theme from `<html>` propagates correctly into the rendered content, including overlays, tooltips, and selectors.

### Implementation for User Story 6

- [ ] T035 [P] [US6] Audit Radix primitives and className forwarding for theme inheritance in `frontend/src/components/ui/tooltip.tsx`, `frontend/src/components/ui/button.tsx`, and `frontend/src/components/common/ThemedAgentIcon.tsx`
- [ ] T036 [P] [US6] Audit portal-rendered selectors and popovers for inherited `.light`/`.dark` styling in `frontend/src/layout/NotificationBell.tsx`, `frontend/src/components/chores/ChoreCard.tsx`, `frontend/src/components/board/AddAgentPopover.tsx`, `frontend/src/components/pipeline/ModelSelector.tsx`, and `frontend/src/components/pipeline/StageCard.tsx`
- [ ] T037 [US6] Add any required theme-context forwarding or wrapper fixes for third-party surfaces in `frontend/src/components/ui/tooltip.tsx`, `frontend/src/layout/NotificationBell.tsx`, `frontend/src/components/board/AddAgentPopover.tsx`, `frontend/src/components/pipeline/ModelSelector.tsx`, and `frontend/src/components/pipeline/StageCard.tsx`
- [ ] T038 [US6] Validate Light→Dark and Dark→Light inheritance behavior for third-party surfaces in `frontend/src/components/ui/tooltip.tsx`, `frontend/src/layout/NotificationBell.tsx`, `frontend/src/components/board/AddAgentPopover.tsx`, `frontend/src/components/pipeline/ModelSelector.tsx`, and `frontend/src/components/pipeline/StageCard.tsx`

**Checkpoint**: User Story 6 complete — third-party and portal-rendered components inherit the active theme correctly

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final documentation, validation, and cross-story cleanup once all desired story work is complete.

- [ ] T039 [P] Update the final token inventory, changed values, and rationale in `specs/037-theme-contrast-audit/contracts/token-registry.md`
- [ ] T040 [P] Update the final audit evidence, approved exceptions, and component/page coverage results in `specs/037-theme-contrast-audit/contracts/audit-checklist.md`
- [ ] T041 Run the final frontend validation commands from `frontend/package.json` (`npm run type-check`, `npm run lint`, `npm run test:a11y`, `npx vitest run`) and resolve regressions in files identified by `frontend/scripts/audit-theme-colors.mjs` and `frontend/scripts/check-theme-contrast.mjs`
- [ ] T042 Run the final acceptance scenarios from `specs/037-theme-contrast-audit/quickstart.md` and confirm the implemented audit still matches `frontend/src/index.css`, `frontend/src/components/ThemeProvider.tsx`, `frontend/src/layout/Sidebar.tsx`, `frontend/src/pages/ProjectsPage.tsx`, and `frontend/src/pages/AgentsPage.tsx`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can begin immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories because the audit tooling and coverage matrix are shared prerequisites
- **User Story 1 (Phase 3)**: Depends on Foundational — establishes token-only color usage and is the MVP
- **User Story 2 (Phase 4)**: Depends on User Story 1 — contrast fixes are most reliable after raw hardcoded colors are removed
- **User Story 3 (Phase 5)**: Depends on User Stories 1 and 2 — interactive states should be evaluated on top of tokenized, contrast-compliant colors
- **User Story 4 (Phase 6)**: Depends on User Stories 1 and 2 — component consistency work assumes stable token and contrast baselines
- **User Story 5 (Phase 7)**: Depends on User Stories 1 and 4 — toggle stability should be verified after themed surfaces and variants are aligned
- **User Story 6 (Phase 8)**: Depends on Foundational and User Story 5 — inheritance validation should run after transition behavior is stable
- **Polish (Phase 9)**: Depends on all selected user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start immediately after Foundational — this is the MVP because hardcoded colors are the root cause for theme drift
- **US2 (P1)**: Starts after US1 — token-based contrast fixes depend on the color-elimination pass
- **US3 (P1)**: Starts after US1 and US2 — interactive states need compliant base tokens and boundaries
- **US4 (P2)**: Starts after US1 and US2 — consistency work assumes corrected tokens and contrast
- **US5 (P2)**: Starts after US1 and US4 — transition stability should be checked once visuals are aligned
- **US6 (P3)**: Starts after Foundational and US5 — third-party inheritance validation should run on stable theme transitions and finalized overlays

### Within Each User Story

- Shared audit tooling before remediation
- Token and theme-source fixes before contrast and state tuning
- Base component fixes before page-level validation
- Story-level validation before advancing to the next dependency-heavy phase

### Parallel Opportunities

- **Phase 1**: T002 and T003 can run in parallel after T001 starts the baseline record
- **Phase 2**: T005, T006, and T007 can run in parallel after T004 defines the tooling direction
- **US1**: T009–T012 can run in parallel by component area
- **US2**: T014–T017 can run in parallel by token/category
- **US3**: T019–T022 can run in parallel by control family
- **US4**: T024–T027 can run in parallel by layout/component domain
- **US5**: T029–T033 can run in parallel by transition surface type, then T034 validates the full route set
- **US6**: T035 and T036 can run in parallel before T037 integrates any fixes and T038 validates them
- **Polish**: T039 and T040 can run in parallel before the final validation tasks

---

## Parallel Example: User Story 1

```bash
# Execute hardcoded-color cleanup in parallel by UI domain:
Task T009: "Tokenize base UI components in frontend/src/components/ui/"
Task T010: "Tokenize shared visuals and shell components in frontend/src/components/ and frontend/src/layout/"
Task T011: "Tokenize agent/board/pipeline components in frontend/src/components/agents/, board/, and pipeline/"
Task T012: "Tokenize chat/tools/settings/chores/pages in frontend/src/components/ and frontend/src/pages/"
```

## Parallel Example: User Story 2

```bash
# Execute contrast remediation in parallel by contrast category:
Task T014: "Adjust core surface/text tokens in frontend/src/index.css"
Task T015: "Adjust border, input, ring, and shadow contrast in frontend/src/index.css"
Task T016: "Fix semantic/status contrast in frontend/src/index.css and frontend/src/components/board/"
Task T017: "Fix icon, loader, and message contrast in frontend/src/components/common/ and frontend/src/components/chat/"
```

## Parallel Example: User Story 3

```bash
# Audit interactive states in parallel by control family:
Task T019: "Buttons and links"
Task T020: "Inputs, dropdowns, and selectors"
Task T021: "Cards and tiles"
Task T022: "Chat/editor controls"
```

## Parallel Example: User Story 4

```bash
# Align variants in parallel by product area:
Task T024: "Base UI variants"
Task T025: "App shell and navigation variants"
Task T026: "Board and pipeline variants"
Task T027: "Agents/tools/settings/chores variants"
```

## Parallel Example: User Story 5

```bash
# Verify theme-switch stability in parallel by transition surface:
Task T029: "ThemeProvider, persistence, and sidebar toggle"
Task T030: "Portaled overlays and dialogs"
Task T031: "Loaders, gradients, and skeleton surfaces"
Task T032: "prefers-color-scheme and restored-theme resolution"
Task T033: "Scrollbar and transparent-media behavior"
```

## Parallel Example: User Story 6

```bash
# Audit third-party inheritance in parallel before applying fixes:
Task T035: "Radix primitives and className forwarding"
Task T036: "Portal-rendered selectors and popovers"
Task T037: "Integrate any required theme-context fixes"
Task T038: "Validate live theme inheritance after fixes"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup baseline and exception review
2. Complete Phase 2: Audit tooling and coverage matrix
3. Complete Phase 3: User Story 1 hardcoded-color elimination
4. **STOP and VALIDATE**: Run `frontend/scripts/audit-theme-colors.mjs` and verify zero unclassified violations
5. Demo the tokenized theme baseline before continuing with deeper contrast and interaction work

### Incremental Delivery

1. Finish Setup + Foundational → audit tooling is ready
2. Deliver US1 → eliminate hardcoded theme drift
3. Deliver US2 → achieve measurable AA contrast compliance
4. Deliver US3 → finalize accessible interactive states
5. Deliver US4 → align component variants with the Solune style language
6. Deliver US5 → stabilize theme switching across the app
7. Deliver US6 → close third-party inheritance gaps
8. Finish Polish → documentation and full validation

### Parallel Team Strategy

1. One developer owns audit tooling (Phase 2) while another prepares the baseline review artifacts
2. After Phase 2:
   - Developer A: US1 hardcoded-color elimination
   - Developer B: Prepare third-party inheritance inventory for US6
   - Developer C: Prep contrast analysis inputs for US2
3. After US1 lands:
   - Developer A: US2 contrast fixes
   - Developer B: US3 interactive states
   - Developer C: US4 component consistency
4. After US4 lands:
   - Developer A: US5 transition stability
   - Developer B: Prepare US6 validation inputs while US5 is in progress
5. After US5 completes:
   - Developer B: US6 third-party inheritance
6. Finish with the Polish phase as a coordinated release hardening pass

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 42 |
| **Setup tasks** | 3 |
| **Foundational tasks** | 5 |
| **US1 tasks** | 5 |
| **US2 tasks** | 5 |
| **US3 tasks** | 5 |
| **US4 tasks** | 5 |
| **US5 tasks** | 6 |
| **US6 tasks** | 4 |
| **Polish tasks** | 4 |
| **MVP scope** | Phases 1–3 (Tasks T001–T013) |
| **Primary output files** | `frontend/src/index.css`, `frontend/src/components/`, `frontend/src/pages/`, `frontend/src/layout/`, `frontend/scripts/`, `specs/037-theme-contrast-audit/contracts/` |

## Notes

- [P] tasks are safe to parallelize because they target different files or audit domains
- All user story tasks include exact repository paths so they can be executed without extra discovery work
- Audit scripts created in Phase 2 are intentionally reusable for future theme regressions
- Approved hardcoded-color exceptions must remain documented in `specs/037-theme-contrast-audit/contracts/audit-checklist.md`
