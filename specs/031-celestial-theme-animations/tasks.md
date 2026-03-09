# Tasks: Frontend Style Audit & Celestial/Cosmic Theme Animation Enhancement

**Input**: Design documents from `/specs/031-celestial-theme-animations/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/components.md ✅, quickstart.md ✅

**Tests**: No new tests are required by this specification. However, all existing test suites must remain passing after each phase. Accessibility contrast checks are recommended but not mandated.

**Organization**: Tasks are grouped by user story (US1–US6) to enable independent implementation and testing of each story. User stories map to spec.md priorities (P1–P3).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/` (frontend-only feature — zero backend changes)
- **Design tokens**: `frontend/src/index.css` (`@theme` block, `@layer base`, `@media prefers-reduced-motion`)
- **Components**: `frontend/src/components/{agents,board,chat,chores,common,pipeline,settings,tools,ui}/`
- **Layout**: `frontend/src/layout/`
- **Pages**: `frontend/src/pages/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify development environment, confirm build/test baseline is green, and validate the existing design token system before making any changes.

- [ ] T001 Install frontend dependencies and verify build baseline in `frontend/` (`npm install && npm run build`)
- [ ] T002 [P] Verify frontend linting and type-check baseline in `frontend/` (`npm run lint && npm run type-check`)
- [ ] T003 [P] Verify existing test suite passes in `frontend/` (`npm run test`)
- [ ] T004 Document any pre-existing lint warnings, type errors, or test failures as baseline (do not fix — out of scope unless directly related to this feature)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Extend the centralized design token system in `index.css` with new tokens, keyframes, and utility classes needed by all user stories. Create the new `CelestialLoader` component. Update `ThemeProvider` for theme transitions. These must be complete before any component audit work begins.

**⚠️ CRITICAL**: No user story work (component audits) can begin until this phase is complete.

- [ ] T005 Add `--transition-theme-shift: 600ms ease-in-out` and `--animate-celestial-loader: orbit-spin 1.8s linear infinite` tokens to the `@theme` block in `frontend/src/index.css`
- [ ] T006 Add `theme-shift` keyframe (`@keyframes theme-shift { 0% { opacity: 0; } 50% { opacity: 0.3; } 100% { opacity: 0; } }`) to the `@theme` block in `frontend/src/index.css`
- [ ] T007 Add `.theme-transitioning` utility class with `background-color` and `color` transitions, and `::after` pseudo-element with cosmic gradient overlay and `theme-shift` animation in `@layer base` in `frontend/src/index.css`.
- [ ] T008 Update `@media (prefers-reduced-motion: reduce)` block in `frontend/src/index.css` to include `.theme-transitioning` and `.theme-transitioning::after` with `animation: none !important` and `transition: none !important`
- [ ] T009 Create `CelestialLoader` component in `frontend/src/components/common/CelestialLoader.tsx` with `size` (`sm`/`md`/`lg`), `label`, and `className` props; render orbital animation using `celestial-pulse-glow` and `celestial-orbit-spin-fast` CSS classes; include `role="status"` and `aria-label` for accessibility
- [ ] T010 Update `ThemeProvider.tsx` (`frontend/src/components/ThemeProvider.tsx`) to add `theme-transitioning` class to `document.documentElement` before toggling theme, and remove it after 600ms via `setTimeout`; clean up timeout on unmount
- [ ] T011 Verify foundational changes compile and pass lint/type-check in `frontend/` (`npm run build && npm run lint && npm run type-check`)

**Checkpoint**: Foundation ready — design token extensions, CelestialLoader, and ThemeProvider transition are complete. Component audit work can now begin.

---

## Phase 3: User Story 1 — Design Token & Style Consistency Audit (Priority: P1) 🎯 MVP

**Goal**: Audit every frontend component for adherence to the established design token system (colors, typography, spacing, border-radius, shadows) and correct any deviations. Replace hard-coded values with design tokens.

**Independent Test**: Visually inspect every page and component against the design token reference in `index.css`. Verify zero hard-coded color, spacing, typography, radius, or shadow values remain outside the token system. Run `npm run build && npm run lint && npm run type-check` after each directory.

### UI Primitives (components/ui/)

- [ ] T012 [P] [US1] Audit `button.tsx` for design token compliance in `frontend/src/components/ui/button.tsx` — replace hard-coded colors, spacing, radius, shadows with design tokens; add `celestial-focus` class to all variants for themed focus ring; add `solar-action` class to default/primary variants for hover lift
- [ ] T013 [P] [US1] Audit `card.tsx` for design token compliance in `frontend/src/components/ui/card.tsx` — replace hard-coded values with tokens; add `celestial-panel` class for hover glow lift; add `celestial-fade-in` for entry animation
- [ ] T014 [P] [US1] Audit `input.tsx` for design token compliance in `frontend/src/components/ui/input.tsx` — replace hard-coded values with tokens; add `celestial-focus` class for themed focus ring
- [ ] T015 [P] [US1] Audit `tooltip.tsx` for design token compliance in `frontend/src/components/ui/tooltip.tsx` — verify styling uses `--popover`, `--foreground`, `--border` tokens
- [ ] T016 [P] [US1] Audit `confirmation-dialog.tsx` for design token compliance in `frontend/src/components/ui/confirmation-dialog.tsx` — replace hard-coded values; add `celestial-fade-in` on dialog content; align backdrop with celestial theme

### Layout Components (layout/)

- [ ] T017 [P] [US1] Audit `Sidebar.tsx` for design token compliance in `frontend/src/layout/Sidebar.tsx` — verify nav styling uses tokens; add celestial hover glow on nav items
- [ ] T018 [P] [US1] Audit `TopBar.tsx` for design token compliance in `frontend/src/layout/TopBar.tsx` — verify bar styling uses tokens; add `solar-action` on buttons
- [ ] T019 [P] [US1] Audit `Breadcrumb.tsx` for design token compliance in `frontend/src/layout/Breadcrumb.tsx` — verify breadcrumb styling uses tokens
- [ ] T020 [P] [US1] Audit `ProjectSelector.tsx` for design token compliance in `frontend/src/layout/ProjectSelector.tsx` — verify dropdown styling uses tokens; add `celestial-focus`
- [ ] T021 [P] [US1] Audit `NotificationBell.tsx` for design token compliance in `frontend/src/layout/NotificationBell.tsx` — verify bell styling uses tokens; add subtle glow on notification dot
- [ ] T022 [P] [US1] Audit `RateLimitBar.tsx` for design token compliance in `frontend/src/layout/RateLimitBar.tsx` — verify bar styling uses tokens
- [ ] T023 [P] [US1] Audit `AuthGate.tsx` for design token compliance in `frontend/src/layout/AuthGate.tsx` — verify gate styling uses tokens

### Page Components (pages/)

- [ ] T024 [P] [US1] Audit `AppPage.tsx` for design token compliance in `frontend/src/pages/AppPage.tsx` — verify dashboard styling uses tokens; add `celestial-fade-in` on page load
- [ ] T025 [P] [US1] Audit `LoginPage.tsx` for design token compliance in `frontend/src/pages/LoginPage.tsx` — verify login styling uses tokens; add celestial background and `celestial-fade-in`
- [ ] T026 [P] [US1] Audit `ProjectsPage.tsx` for design token compliance in `frontend/src/pages/ProjectsPage.tsx` — verify list styling uses tokens; add `celestial-fade-in`
- [ ] T027 [P] [US1] Audit `AgentsPage.tsx` for design token compliance in `frontend/src/pages/AgentsPage.tsx` — verify page styling uses tokens; add `celestial-fade-in`
- [ ] T028 [P] [US1] Audit `AgentsPipelinePage.tsx` for design token compliance in `frontend/src/pages/AgentsPipelinePage.tsx` — verify page styling uses tokens; add `celestial-fade-in`
- [ ] T029 [P] [US1] Audit `ToolsPage.tsx` for design token compliance in `frontend/src/pages/ToolsPage.tsx` — verify page styling uses tokens; add `celestial-fade-in`
- [ ] T030 [P] [US1] Audit `ChoresPage.tsx` for design token compliance in `frontend/src/pages/ChoresPage.tsx` — verify page styling uses tokens; add `celestial-fade-in`
- [ ] T031 [P] [US1] Audit `SettingsPage.tsx` for design token compliance in `frontend/src/pages/SettingsPage.tsx` — verify page styling uses tokens; add `celestial-fade-in`
- [ ] T032 [P] [US1] Audit `NotFoundPage.tsx` for design token compliance in `frontend/src/pages/NotFoundPage.tsx` — verify error styling uses tokens; add celestial styling

### Agent Components (components/agents/)

- [ ] T033 [P] [US1] Audit `AgentCard.tsx` for design token compliance in `frontend/src/components/agents/AgentCard.tsx` — verify card colors and shadows use tokens; add `celestial-panel` hover
- [ ] T034 [P] [US1] Audit `AgentsPanel.tsx` for design token compliance in `frontend/src/components/agents/AgentsPanel.tsx` — verify panel styling uses tokens; add `celestial-fade-in` on panel
- [ ] T035 [P] [US1] Audit `AddAgentModal.tsx` for design token compliance in `frontend/src/components/agents/AddAgentModal.tsx` — verify modal styling uses tokens; add `celestial-fade-in`
- [ ] T036 [P] [US1] Audit `AgentIconCatalog.tsx` for design token compliance in `frontend/src/components/agents/AgentIconCatalog.tsx` — verify grid styling uses tokens; add hover glow on icon items
- [ ] T037 [P] [US1] Audit `AgentIconPickerModal.tsx` for design token compliance in `frontend/src/components/agents/AgentIconPickerModal.tsx` — verify modal styling uses tokens; add `celestial-fade-in`
- [ ] T038 [P] [US1] Audit `AgentInlineEditor.tsx` for design token compliance in `frontend/src/components/agents/AgentInlineEditor.tsx` — verify input styling uses tokens; add `celestial-focus` on inputs
- [ ] T039 [P] [US1] Audit `AgentChatFlow.tsx` for design token compliance in `frontend/src/components/agents/AgentChatFlow.tsx` — verify chat styling uses tokens
- [ ] T040 [P] [US1] Audit `BulkModelUpdateDialog.tsx` for design token compliance in `frontend/src/components/agents/BulkModelUpdateDialog.tsx` — verify dialog styling uses tokens; add `celestial-fade-in`
- [ ] T041 [P] [US1] Audit `ToolsEditor.tsx` for design token compliance in `frontend/src/components/agents/ToolsEditor.tsx` — verify form styling uses tokens; add `celestial-focus` on inputs
- [ ] T042 [P] [US1] Audit `AgentAvatar.tsx` for design token compliance in `frontend/src/components/agents/AgentAvatar.tsx` — verify image/icon styling uses tokens; add subtle hover glow

### Board Components (components/board/)

- [ ] T043 [P] [US1] Audit `ProjectBoard.tsx` for design token compliance in `frontend/src/components/board/ProjectBoard.tsx` — verify layout styling uses tokens; add `celestial-fade-in`
- [ ] T044 [P] [US1] Audit `BoardColumn.tsx` for design token compliance in `frontend/src/components/board/BoardColumn.tsx` — verify column styling uses tokens
- [ ] T045 [P] [US1] Audit `BoardToolbar.tsx` for design token compliance in `frontend/src/components/board/BoardToolbar.tsx` — verify toolbar styling uses tokens; add `solar-action` on buttons
- [ ] T046 [P] [US1] Audit `IssueCard.tsx` for design token compliance in `frontend/src/components/board/IssueCard.tsx` — verify card styling uses tokens; add `celestial-panel` hover
- [ ] T047 [P] [US1] Audit `IssueDetailModal.tsx` for design token compliance in `frontend/src/components/board/IssueDetailModal.tsx` — verify modal styling uses tokens; add `celestial-fade-in`
- [ ] T048 [P] [US1] Audit `RefreshButton.tsx` for design token compliance in `frontend/src/components/board/RefreshButton.tsx` — verify button styling uses tokens; add `solar-action` hover
- [ ] T049 [P] [US1] Audit `CleanUpButton.tsx` for design token compliance in `frontend/src/components/board/CleanUpButton.tsx` — verify button styling uses tokens; add `solar-action` hover
- [ ] T050 [P] [US1] Audit `AgentTile.tsx` for design token compliance in `frontend/src/components/board/AgentTile.tsx` — verify tile styling uses tokens; add subtle hover glow
- [ ] T051 [P] [US1] Audit `BlockingChainPanel.tsx` for design token compliance in `frontend/src/components/board/BlockingChainPanel.tsx` — verify panel styling uses tokens; add `celestial-fade-in`
- [ ] T052 [P] [US1] Audit remaining board components (`AddAgentPopover.tsx`, `AgentColumnCell.tsx`, `AgentConfigRow.tsx`, `AgentDragOverlay.tsx`, `AgentPresetSelector.tsx`, `AgentSaveBar.tsx`, `CleanUpAuditHistory.tsx`, `CleanUpConfirmModal.tsx`, `CleanUpSummary.tsx`) for design token compliance in `frontend/src/components/board/`

### Chat Components (components/chat/)

- [ ] T053 [P] [US1] Audit `ChatInterface.tsx` for design token compliance in `frontend/src/components/chat/ChatInterface.tsx` — verify layout styling uses tokens
- [ ] T054 [P] [US1] Audit `ChatPopup.tsx` for design token compliance in `frontend/src/components/chat/ChatPopup.tsx` — verify popup styling uses tokens; add `celestial-fade-in` on open
- [ ] T055 [P] [US1] Audit `MessageBubble.tsx` for design token compliance in `frontend/src/components/chat/MessageBubble.tsx` — verify bubble styling uses tokens; add `celestial-fade-in` for messages
- [ ] T056 [P] [US1] Audit `ChatToolbar.tsx` for design token compliance in `frontend/src/components/chat/ChatToolbar.tsx` — verify toolbar styling uses tokens; add `solar-action` on buttons
- [ ] T057 [P] [US1] Audit `MentionInput.tsx` for design token compliance in `frontend/src/components/chat/MentionInput.tsx` — verify input styling uses tokens; add `celestial-focus`
- [ ] T058 [P] [US1] Audit `VoiceInputButton.tsx` for design token compliance in `frontend/src/components/chat/VoiceInputButton.tsx` — verify button styling uses tokens; add `solar-action` hover
- [ ] T059 [P] [US1] Audit remaining chat components (`CommandAutocomplete.tsx`, `FilePreviewChips.tsx`, `IssueRecommendationPreview.tsx`, `MentionAutocomplete.tsx`, `PipelineIndicator.tsx`, `PipelineWarningBanner.tsx`, `StatusChangePreview.tsx`, `SystemMessage.tsx`, `TaskPreview.tsx`) for design token compliance in `frontend/src/components/chat/`

### Chores Components (components/chores/)

- [ ] T060 [P] [US1] Audit `ChoresPanel.tsx` for design token compliance in `frontend/src/components/chores/ChoresPanel.tsx` — verify panel styling uses tokens; add `celestial-fade-in`
- [ ] T061 [P] [US1] Audit `ChoreCard.tsx` for design token compliance in `frontend/src/components/chores/ChoreCard.tsx` — verify card styling uses tokens; add `celestial-panel` hover
- [ ] T062 [P] [US1] Audit `AddChoreModal.tsx` for design token compliance in `frontend/src/components/chores/AddChoreModal.tsx` — verify modal styling uses tokens; add `celestial-fade-in`
- [ ] T063 [P] [US1] Audit `ChoreScheduleConfig.tsx` for design token compliance in `frontend/src/components/chores/ChoreScheduleConfig.tsx` — verify form styling uses tokens; add `celestial-focus` on inputs
- [ ] T064 [P] [US1] Audit `FeaturedRitualsPanel.tsx` for design token compliance in `frontend/src/components/chores/FeaturedRitualsPanel.tsx` — verify panel styling uses tokens; add `celestial-fade-in`
- [ ] T065 [P] [US1] Audit remaining chores components (`ChoreChatFlow.tsx`, `ChoreInlineEditor.tsx`, `ConfirmChoreModal.tsx`, `PipelineSelector.tsx`) for design token compliance in `frontend/src/components/chores/`

### Pipeline Components (components/pipeline/)

- [ ] T066 [P] [US1] Audit `PipelineBoard.tsx` for design token compliance in `frontend/src/components/pipeline/PipelineBoard.tsx` — verify board styling uses tokens; add `celestial-fade-in`
- [ ] T067 [P] [US1] Audit `PipelineFlowGraph.tsx` for design token compliance in `frontend/src/components/pipeline/PipelineFlowGraph.tsx` — verify graph styling uses tokens; add subtle glow on connections
- [ ] T068 [P] [US1] Audit `StageCard.tsx` for design token compliance in `frontend/src/components/pipeline/StageCard.tsx` — verify card styling uses tokens; add `celestial-panel` hover and `celestial-fade-in`
- [ ] T069 [P] [US1] Audit `AgentNode.tsx` for design token compliance in `frontend/src/components/pipeline/AgentNode.tsx` — verify node styling uses tokens; add hover glow
- [ ] T070 [P] [US1] Audit `ModelSelector.tsx` for design token compliance in `frontend/src/components/pipeline/ModelSelector.tsx` — verify dropdown styling uses tokens; add `celestial-focus`
- [ ] T071 [P] [US1] Audit `SavedWorkflowsList.tsx` for design token compliance in `frontend/src/components/pipeline/SavedWorkflowsList.tsx` — verify list styling uses tokens; add `celestial-fade-in`
- [ ] T072 [P] [US1] Audit remaining pipeline components (`PipelineModelDropdown.tsx`, `PipelineToolbar.tsx`, `PresetBadge.tsx`, `UnsavedChangesDialog.tsx`) for design token compliance in `frontend/src/components/pipeline/`

### Settings Components (components/settings/)

- [ ] T073 [P] [US1] Audit `GlobalSettings.tsx` for design token compliance in `frontend/src/components/settings/GlobalSettings.tsx` — verify layout styling uses tokens; add `celestial-fade-in`
- [ ] T074 [P] [US1] Audit `SettingsSection.tsx` for design token compliance in `frontend/src/components/settings/SettingsSection.tsx` — verify section styling uses tokens
- [ ] T075 [P] [US1] Audit `DisplayPreferences.tsx` for design token compliance in `frontend/src/components/settings/DisplayPreferences.tsx` — verify form styling uses tokens; add `celestial-focus` on inputs
- [ ] T076 [P] [US1] Audit `AIPreferences.tsx` for design token compliance in `frontend/src/components/settings/AIPreferences.tsx` — verify form styling uses tokens; add `celestial-focus` on inputs
- [ ] T077 [P] [US1] Audit `NotificationPreferences.tsx` for design token compliance in `frontend/src/components/settings/NotificationPreferences.tsx` — verify form styling uses tokens; add `celestial-focus` on inputs
- [ ] T078 [P] [US1] Audit `AdvancedSettings.tsx` for design token compliance in `frontend/src/components/settings/AdvancedSettings.tsx` — verify form styling uses tokens; add `celestial-focus` on inputs
- [ ] T079 [P] [US1] Audit remaining settings components (`DynamicDropdown.tsx`, `McpSettings.tsx`, `PrimarySettings.tsx`, `ProjectSettings.tsx`, `SignalConnection.tsx`, `WorkflowDefaults.tsx`) for design token compliance in `frontend/src/components/settings/`

### Tools Components (components/tools/)

- [ ] T080 [P] [US1] Audit `ToolsPanel.tsx` for design token compliance in `frontend/src/components/tools/ToolsPanel.tsx` — verify panel styling uses tokens; add `celestial-fade-in`
- [ ] T081 [P] [US1] Audit `ToolCard.tsx` for design token compliance in `frontend/src/components/tools/ToolCard.tsx` — verify card styling uses tokens; add `celestial-panel` hover
- [ ] T082 [P] [US1] Audit `ToolSelectorModal.tsx` for design token compliance in `frontend/src/components/tools/ToolSelectorModal.tsx` — verify modal styling uses tokens; add `celestial-fade-in`
- [ ] T083 [P] [US1] Audit `McpPresetsGallery.tsx` for design token compliance in `frontend/src/components/tools/McpPresetsGallery.tsx` — verify gallery styling uses tokens; add `celestial-fade-in`
- [ ] T084 [P] [US1] Audit remaining tools components (`EditRepoMcpModal.tsx`, `GitHubToolsetSelector.tsx`, `RepoConfigPanel.tsx`, `ToolChips.tsx`, `UploadMcpModal.tsx`) for design token compliance in `frontend/src/components/tools/`

### Common & Auth Components

- [ ] T085 [P] [US1] Audit `CelestialCatalogHero.tsx` for design token compliance in `frontend/src/components/common/CelestialCatalogHero.tsx` — verify hero styling uses tokens (already partially themed)
- [ ] T086 [P] [US1] Audit `ProjectSelectionEmptyState.tsx` for design token compliance in `frontend/src/components/common/ProjectSelectionEmptyState.tsx` — verify empty state styling uses tokens
- [ ] T087 [P] [US1] Audit `ThemedAgentIcon.tsx` for design token compliance in `frontend/src/components/common/ThemedAgentIcon.tsx` — verify icon styling uses tokens
- [ ] T088 [P] [US1] Audit `ErrorBoundary.tsx` for design token compliance in `frontend/src/components/common/ErrorBoundary.tsx` — verify error UI styling uses tokens
- [ ] T089 [P] [US1] Audit `LoginButton.tsx` for design token compliance in `frontend/src/components/auth/LoginButton.tsx` — verify button styling uses tokens

**Checkpoint**: At this point, every component should use design tokens exclusively — zero hard-coded color, spacing, typography, radius, or shadow values remain. Run `npm run build && npm run test && npm run type-check` to confirm no regressions.

---

## Phase 4: User Story 2 — Text Casing Standards Enforcement (Priority: P1)

**Goal**: Enforce proper text casing conventions across all UI text: Title Case for headings and navigation items, sentence case for body copy/descriptions/tooltips/placeholders, ALL CAPS only for short labels and status badges.

**Independent Test**: Audit every visible text element on each page and verify it matches the defined casing convention for its element type. Apply casing directly in JSX source text (not via CSS `text-transform`) for static labels. Use Tailwind `uppercase tracking-wider` class only for badges/labels that require ALL CAPS.

### Layout & Navigation Text Casing

- [ ] T090 [P] [US2] Enforce text casing in `Sidebar.tsx` in `frontend/src/layout/Sidebar.tsx` — Title Case for all navigation items
- [ ] T091 [P] [US2] Enforce text casing in `TopBar.tsx` in `frontend/src/layout/TopBar.tsx` — Title Case for app name and nav labels
- [ ] T092 [P] [US2] Enforce text casing in `Breadcrumb.tsx` in `frontend/src/layout/Breadcrumb.tsx` — Title Case for breadcrumb segments
- [ ] T093 [P] [US2] Enforce text casing in `ProjectSelector.tsx` in `frontend/src/layout/ProjectSelector.tsx` — Title Case for project names in dropdown

### Page Headings Text Casing

- [ ] T094 [P] [US2] Enforce text casing in all page components (`AppPage.tsx`, `LoginPage.tsx`, `ProjectsPage.tsx`, `AgentsPage.tsx`, `AgentsPipelinePage.tsx`, `ToolsPage.tsx`, `ChoresPage.tsx`, `SettingsPage.tsx`, `NotFoundPage.tsx`) in `frontend/src/pages/` — Title Case for all page headings (h1, h2); sentence case for descriptions and body copy

### Agent Components Text Casing

- [ ] T095 [P] [US2] Enforce text casing in `AgentCard.tsx` in `frontend/src/components/agents/AgentCard.tsx` — Title Case for agent name headings
- [ ] T096 [P] [US2] Enforce text casing in `AgentsPanel.tsx` in `frontend/src/components/agents/AgentsPanel.tsx` — Title Case for panel heading
- [ ] T097 [P] [US2] Enforce text casing in `AddAgentModal.tsx` in `frontend/src/components/agents/AddAgentModal.tsx` — Title Case for modal title; sentence case for descriptions and form labels
- [ ] T098 [P] [US2] Enforce text casing in `AgentIconCatalog.tsx` in `frontend/src/components/agents/AgentIconCatalog.tsx` — Title Case for catalog heading
- [ ] T099 [P] [US2] Enforce text casing in remaining agent components (`AgentIconPickerModal.tsx`, `AgentInlineEditor.tsx`, `BulkModelUpdateDialog.tsx`, `ToolsEditor.tsx`) in `frontend/src/components/agents/` — Title Case for headings; sentence case for labels and descriptions

### Board Components Text Casing

- [ ] T100 [P] [US2] Enforce text casing in `ProjectBoard.tsx` and `BoardColumn.tsx` in `frontend/src/components/board/` — Title Case for board title and column headers
- [ ] T101 [P] [US2] Enforce text casing in `BoardToolbar.tsx` in `frontend/src/components/board/BoardToolbar.tsx` — Title Case for toolbar labels and buttons
- [ ] T102 [P] [US2] Enforce text casing in `IssueCard.tsx` and `IssueDetailModal.tsx` in `frontend/src/components/board/` — Title Case for issue titles; sentence case for descriptions; ALL CAPS (`uppercase`) for status badges
- [ ] T103 [P] [US2] Enforce text casing in remaining board components (`CleanUpButton.tsx`, `CleanUpConfirmModal.tsx`, `CleanUpSummary.tsx`, `CleanUpAuditHistory.tsx`, `BlockingChainPanel.tsx`, `AgentTile.tsx`) in `frontend/src/components/board/` — Title Case for headings; sentence case for body text

### Chat Components Text Casing

- [ ] T104 [P] [US2] Enforce text casing in `ChatInterface.tsx` and `ChatPopup.tsx` in `frontend/src/components/chat/` — Title Case for chat header; sentence case for placeholder text
- [ ] T105 [P] [US2] Enforce text casing in `ChatToolbar.tsx` in `frontend/src/components/chat/ChatToolbar.tsx` — sentence case for tooltip text
- [ ] T106 [P] [US2] Enforce text casing in `MentionInput.tsx` in `frontend/src/components/chat/MentionInput.tsx` — sentence case for placeholder
- [ ] T107 [P] [US2] Enforce text casing in remaining chat components (`CommandAutocomplete.tsx`, `PipelineWarningBanner.tsx`, `SystemMessage.tsx`, `StatusChangePreview.tsx`, `TaskPreview.tsx`, `IssueRecommendationPreview.tsx`) in `frontend/src/components/chat/` — sentence case for descriptions; ALL CAPS for status labels

### Chores Components Text Casing

- [ ] T108 [P] [US2] Enforce text casing in `ChoresPanel.tsx` and `ChoreCard.tsx` in `frontend/src/components/chores/` — Title Case for panel heading and chore names
- [ ] T109 [P] [US2] Enforce text casing in `AddChoreModal.tsx` and `FeaturedRitualsPanel.tsx` in `frontend/src/components/chores/` — Title Case for modal title and panel heading; sentence case for descriptions
- [ ] T110 [P] [US2] Enforce text casing in `ChoreScheduleConfig.tsx` and remaining chores components in `frontend/src/components/chores/` — sentence case for form labels and descriptions

### Pipeline Components Text Casing

- [ ] T111 [P] [US2] Enforce text casing in `PipelineBoard.tsx` and `StageCard.tsx` in `frontend/src/components/pipeline/` — Title Case for board title and stage names
- [ ] T112 [P] [US2] Enforce text casing in `AgentNode.tsx` and `ModelSelector.tsx` in `frontend/src/components/pipeline/` — Title Case for agent names; sentence case for options
- [ ] T113 [P] [US2] Enforce text casing in remaining pipeline components (`SavedWorkflowsList.tsx`, `PipelineToolbar.tsx`, `PresetBadge.tsx`, `UnsavedChangesDialog.tsx`, `PipelineModelDropdown.tsx`) in `frontend/src/components/pipeline/` — Title Case for headings; ALL CAPS for preset/status badges

### Settings Components Text Casing

- [ ] T114 [P] [US2] Enforce text casing in `GlobalSettings.tsx` and `SettingsSection.tsx` in `frontend/src/components/settings/` — Title Case for section headings
- [ ] T115 [P] [US2] Enforce text casing in all settings preference components (`DisplayPreferences.tsx`, `AIPreferences.tsx`, `NotificationPreferences.tsx`, `AdvancedSettings.tsx`) in `frontend/src/components/settings/` — sentence case for form labels and descriptions
- [ ] T116 [P] [US2] Enforce text casing in remaining settings components (`McpSettings.tsx`, `PrimarySettings.tsx`, `ProjectSettings.tsx`, `SignalConnection.tsx`, `WorkflowDefaults.tsx`, `DynamicDropdown.tsx`) in `frontend/src/components/settings/` — Title Case for headings; sentence case for labels

### Tools Components Text Casing

- [ ] T117 [P] [US2] Enforce text casing in `ToolsPanel.tsx` and `ToolCard.tsx` in `frontend/src/components/tools/` — Title Case for panel heading and tool names
- [ ] T118 [P] [US2] Enforce text casing in `ToolSelectorModal.tsx` and `McpPresetsGallery.tsx` in `frontend/src/components/tools/` — Title Case for modal title and gallery heading
- [ ] T119 [P] [US2] Enforce text casing in remaining tools components (`EditRepoMcpModal.tsx`, `GitHubToolsetSelector.tsx`, `RepoConfigPanel.tsx`, `ToolChips.tsx`, `UploadMcpModal.tsx`) in `frontend/src/components/tools/` — Title Case for headings; sentence case for labels; ALL CAPS for status badges

### UI Primitives Text Casing

- [ ] T120 [P] [US2] Enforce text casing in `confirmation-dialog.tsx` in `frontend/src/components/ui/confirmation-dialog.tsx` — verify button labels follow convention (Title Case for primary actions, sentence case for secondary)

**Checkpoint**: At this point, all visible text elements follow the defined casing conventions. Run `npm run build && npm run test` to confirm no regressions.

---

## Phase 5: User Story 3 — Celestial/Cosmic Animation Layer (Priority: P2)

**Goal**: Introduce celestial/cosmic-themed animations across the app: star-field backgrounds, glowing hover/focus micro-interactions, themed loading states, and light/dark theme transition effects. All animations use existing CSS utility classes from `index.css`.

**Independent Test**: Interact with each animation-enhanced component and verify that motion is visible, smooth, and thematically appropriate. Toggle themes and observe cosmic gradient transition. Trigger loading states and observe orbital shimmer animation.

### Star-Field & Background Animations

- [ ] T121 [US3] Verify `AppLayout.tsx` starfield background in `frontend/src/layout/AppLayout.tsx` — confirm existing starfield + celestial decorations render correctly and are visible on all pages (already implemented — validation only)
- [ ] T122 [P] [US3] Apply subtle starfield or celestial background enhancement to `LoginPage.tsx` in `frontend/src/pages/LoginPage.tsx` — add celestial ambient styling for login screen

### Theme Transition Effect

- [ ] T123 [US3] Verify theme transition effect works end-to-end — toggle light/dark theme in running app and confirm smooth cosmic gradient overlay fades in/out over 600ms (depends on T007, T010)

### Hover & Focus Micro-Interactions

- [ ] T124 [P] [US3] Apply `celestial-panel` hover glow to all card components — verify `AgentCard.tsx`, `IssueCard.tsx`, `ChoreCard.tsx`, `StageCard.tsx`, `ToolCard.tsx` (in respective `frontend/src/components/` directories) show subtle glow lift on hover (should already be applied from US1 token audit tasks — validate here)
- [ ] T125 [P] [US3] Apply `solar-action` hover effect to all primary action buttons — verify buttons in `BoardToolbar.tsx`, `ChatToolbar.tsx`, `TopBar.tsx`, `RefreshButton.tsx`, `CleanUpButton.tsx` (in respective directories) show hover lift enhancement (should already be applied from US1 — validate here)
- [ ] T126 [P] [US3] Apply `celestial-focus` glow ring to all interactive input elements — verify inputs in `MentionInput.tsx`, `ChoreScheduleConfig.tsx`, `ModelSelector.tsx`, settings preferences components, and all `<input>` elements show themed focus ring (should already be applied from US1 — validate here)

### Celestial Loading States

- [ ] T127 [US3] Replace generic loading indicators with `CelestialLoader` component across all pages in `frontend/src/pages/` — find all `Loading...` text, `Loader2 className="animate-spin"`, and Suspense fallbacks; replace with `<CelestialLoader size="md" label="Loading {context}…" />`
- [ ] T128 [P] [US3] Replace generic loading indicators in component-level loading states in `frontend/src/components/` — find all remaining loading spinners and `Loading...` text in `ChatInterface.tsx`, `ProjectBoard.tsx`, `PipelineBoard.tsx`, `AgentsPanel.tsx`, `ChoresPanel.tsx`, `ToolsPanel.tsx` and replace with `<CelestialLoader />`

### Entry Animations

- [ ] T129 [P] [US3] Verify `celestial-fade-in` entry animation is applied to all major content sections — confirm cards, panels, modals, and page content areas have subtle fade-in on mount (should already be applied from US1 — validate and add any missing instances)

**Checkpoint**: At this point, the celestial animation layer is fully applied — star-field backgrounds, hover/focus effects, themed loading states, and theme transitions are all visible and smooth. Verify `npm run build && npm run test` pass.

---

## Phase 6: User Story 4 — Reduced Motion & Accessibility Compliance (Priority: P2)

**Goal**: Ensure all animations (new and existing) respect `prefers-reduced-motion`, maintain WCAG AA contrast ratios, and preserve focus-visible indicators in all states.

**Independent Test**: Enable `prefers-reduced-motion: reduce` in browser dev tools. Navigate every page and verify all animations are disabled or replaced with non-motion alternatives. Tab through every interactive element and verify focus indicators are visible. Check text contrast ratios in both light and dark themes.

### Reduced Motion Verification

- [ ] T130 [US4] Verify `@media (prefers-reduced-motion: reduce)` block in `frontend/src/index.css` covers ALL animation utility classes — cross-reference the list of celestial utility classes (`celestial-twinkle`, `celestial-twinkle-delayed`, `celestial-twinkle-slow`, `celestial-pulse-glow`, `celestial-orbit-spin`, `celestial-orbit-spin-reverse`, `celestial-orbit-spin-fast`, `celestial-float`, `celestial-float-delayed`, `celestial-star-wink`, `celestial-shimmer`, `celestial-fade-in`, `cosmic-gradient-shift`, `solar-action`, `celestial-panel`, `theme-transitioning`) and confirm each has `animation: none !important` and/or `transition: none !important`
- [ ] T131 [P] [US4] Verify `CelestialLoader` component in `frontend/src/components/common/CelestialLoader.tsx` degrades gracefully with `prefers-reduced-motion` — orbit stops, glow stops, only static arrangement visible
- [ ] T132 [P] [US4] Verify starfield background in `frontend/src/index.css` (`.starfield::after`) renders as static starscape without particle movement when `prefers-reduced-motion: reduce` is active

### Focus Indicator Audit

- [ ] T133 [US4] Verify `celestial-focus` utility class preserves visible focus-visible outline on all interactive elements — tab through every button, input, link, card, and dropdown in the app and confirm glow ring focus indicator is always visible
- [ ] T134 [P] [US4] Verify focus indicators remain visible during and after `celestial-fade-in`, `celestial-panel`, and `solar-action` animations — confirm no animation state hides or obscures the focus ring

### Contrast Ratio Verification

- [ ] T135 [US4] Verify WCAG AA contrast ratios (4.5:1 for normal text, 3:1 for large text) are maintained in both light and dark themes — spot-check text elements on every page during animation states (hover glow, fade-in, theme transition)
- [ ] T136 [P] [US4] Verify contrast ratios for text rendered over star-field backgrounds and cosmic gradient overlays — ensure `--star`, `--star-soft`, `--glow` decorative elements do not reduce text readability

**Checkpoint**: All animations respect reduced motion, all focus indicators are visible, and WCAG AA contrast ratios are maintained. Run `npm run build && npm run test` to confirm.

---

## Phase 7: User Story 5 — Centralized Animation Tokens & Modern CSS Practices (Priority: P2)

**Goal**: Verify all animation durations, easing curves, and keyframes are centralized in the shared design token system. Apply modern CSS best practices where appropriate.

**Independent Test**: Search the codebase for hard-coded animation values (`animation:`, `transition:`, `@keyframes` outside `index.css`, arbitrary timing values like `300ms`, `0.3s`) and confirm all reference shared tokens. Verify `clamp()` is used for fluid typography where appropriate.

### Animation Token Centralization Audit

- [ ] T137 [US5] Search all frontend component files for hard-coded animation values — run `grep -rn 'animation:\|transition:\|@keyframes' frontend/src/components/ frontend/src/layout/ frontend/src/pages/` and verify all animation/transition values reference shared tokens (`--transition-cosmic-fast`, `--transition-cosmic-base`, `--transition-cosmic-slow`, `--transition-cosmic-drift`, `--transition-theme-shift`) or use Tailwind utility classes
- [ ] T138 [P] [US5] Replace any discovered hard-coded animation durations or easing values in component files with references to centralized design tokens from `frontend/src/index.css`

### Modern CSS Practices Audit

- [ ] T139 [P] [US5] Audit for fluid typography opportunities — identify heading and body text elements that could benefit from `clamp()` for responsive sizing and apply where appropriate in `frontend/src/index.css` or component styles
- [ ] T140 [P] [US5] Verify CSS custom properties are used for all themeable values — confirm no inline styles or arbitrary Tailwind values (`bg-[#hex]`, `text-[#hex]`) remain for color, spacing, or typography tokens

**Checkpoint**: All animation values are centralized, no hard-coded timing/easing in components, and modern CSS practices are applied. Run `npm run build && npm run type-check` to confirm.

---

## Phase 8: User Story 6 — Component-Level Style Alignment Report (Priority: P3)

**Goal**: Produce documentation recording what style and theme changes were made to each component during the audit, for future maintainability.

**Independent Test**: Verify that inline code comments exist in each modified component documenting changes applied. Verify a summary report covers every audited component category.

- [ ] T141 [P] [US6] Add inline JSDoc-style comments to each modified component file documenting: (a) token violations found and corrected, (b) text casing changes applied, (c) celestial animation classes added, (d) accessibility observations — apply across all modified files in `frontend/src/components/`, `frontend/src/layout/`, `frontend/src/pages/`
- [ ] T142 [US6] Create style alignment summary in `frontend/STYLE_AUDIT.md` documenting changes per component directory — include table with columns: Component, Directory, Token Violations Fixed, Casing Changes, Animations Added, Accessibility Notes — covering all 12 directories (agents, board, chat, chores, common, pipeline, settings, tools, ui, layout, pages, auth)

**Checkpoint**: Documentation is complete. Every audited component has inline comments and the summary report covers all categories.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final verification pass, performance validation, responsive testing, and cleanup.

- [ ] T143 Run full build and verify zero errors in `frontend/` (`npm run build`)
- [ ] T144 [P] Run full lint and type-check pass in `frontend/` (`npm run lint && npm run type-check`)
- [ ] T145 [P] Run full test suite in `frontend/` (`npm run test`) — verify all existing tests pass with no regressions
- [ ] T146 Verify star-field background adds <100ms to initial page load — check performance in browser dev tools Performance tab
- [ ] T147 [P] Verify all animations maintain 30fps+ on standard hardware — check animation FPS in browser dev tools Performance tab
- [ ] T148 [P] Test all animations and styling on mobile viewports — verify responsive behavior and graceful animation degradation
- [ ] T149 [P] Verify `CelestialLoader` renders correctly at all 3 sizes (`sm`, `md`, `lg`) in isolation
- [ ] T150 Final visual review — navigate every page in both light and dark themes, verify cohesive celestial styling throughout

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 – Token Audit (Phase 3)**: Depends on Foundational (Phase 2) — establishes animation classes on components
- **US2 – Text Casing (Phase 4)**: Depends on Foundational (Phase 2) — can run in parallel with US1 (different concerns: class attributes vs. text content)
- **US3 – Animation Layer (Phase 5)**: Depends on US1 (Phase 3) — validates and extends animation classes applied during token audit
- **US4 – Accessibility (Phase 6)**: Depends on US3 (Phase 5) — verifies all animations respect reduced motion
- **US5 – Token Centralization (Phase 7)**: Depends on US1 (Phase 3) — audits for hard-coded values after token audit is complete
- **US6 – Report (Phase 8)**: Depends on US1, US2, US3 — documents all changes made in previous phases
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)** + **US2 (P1)**: Can run in parallel after Foundational — US1 touches CSS classes, US2 touches text content
- **US3 (P2)**: Depends on US1 for animation classes to already be on components
- **US4 (P2)**: Depends on US3 for all animations to be in place before verification
- **US5 (P2)**: Can run in parallel with US3/US4 after US1
- **US6 (P3)**: Depends on US1 + US2 + US3 for all changes to be documented

### Within Each User Story

- Tasks marked [P] within a phase can run in parallel (different files, no dependencies)
- Non-[P] tasks should be executed sequentially
- Complete each story fully before moving to dependent stories

### Parallel Opportunities

- **Phase 1**: T002 and T003 can run in parallel (lint vs. test)
- **Phase 2**: T005–T008 (index.css changes) are sequential; T009 (CelestialLoader) and T010 (ThemeProvider) can parallel after T008
- **Phase 3**: All component audit tasks (T012–T089) can run in parallel within their directory groups
- **Phase 4**: All text casing tasks (T090–T120) can run in parallel within their groups
- **Phase 5**: All animation layer tasks (T121–T129) can run in parallel
- **Phase 6**: Verification tasks (T130–T136) can mostly run in parallel
- **Phase 7**: T137 must run before T138; T139 and T140 can parallel
- **Phase 8**: T141 and T142 can parallel
- **Phase 9**: T144, T145, T147, T148, T149 can run in parallel

---

## Parallel Example: User Story 1 (Design Token Audit)

```bash
# Launch UI primitive audits together (different files):
Task T012: "Audit button.tsx for design token compliance"
Task T013: "Audit card.tsx for design token compliance"
Task T014: "Audit input.tsx for design token compliance"
Task T015: "Audit tooltip.tsx for design token compliance"
Task T016: "Audit confirmation-dialog.tsx for design token compliance"

# Launch layout audits together (different files):
Task T017: "Audit Sidebar.tsx for design token compliance"
Task T018: "Audit TopBar.tsx for design token compliance"
Task T019: "Audit Breadcrumb.tsx for design token compliance"

# Launch page audits together (different files):
Task T024–T032: All 9 page components in parallel
```

## Parallel Example: User Story 2 (Text Casing)

```bash
# Launch text casing audits by directory (different files):
Task T090–T093: Layout components in parallel
Task T094: All page components
Task T095–T099: Agent components in parallel
Task T100–T103: Board components in parallel
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (index.css tokens, CelestialLoader, ThemeProvider)
3. Complete Phase 3: User Story 1 — Design Token Audit (all ~126 components)
4. Complete Phase 4: User Story 2 — Text Casing Enforcement
5. **STOP and VALIDATE**: Build, test, and visually inspect — the app should now look consistent and professional
6. Deploy/demo if ready — this is the MVP

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 (Token Audit) + US2 (Text Casing) → Consistent visual baseline (MVP! ✅)
3. US3 (Animation Layer) → Celestial animations active everywhere
4. US4 (Accessibility) → Verified reduced motion and contrast compliance
5. US5 (Token Centralization) → Clean, maintainable animation system
6. US6 (Report) → Full documentation of all changes
7. Polish → Final verification and performance validation

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 — Design Token Audit (components/ui/ → layout/ → pages/ → agents/ → board/ → ...)
   - Developer B: US2 — Text Casing Enforcement (layout/ → pages/ → agents/ → board/ → ...)
3. After US1 completes:
   - Developer A: US3 — Animation Layer validation + loading state replacement
   - Developer B: US5 — Token Centralization audit
4. After US3 completes:
   - Developer A: US4 — Accessibility verification
   - Developer B: US6 — Style Alignment Report
5. Both: Phase 9 — Polish & Final Review

---

## Notes

- [P] tasks = different files, no dependencies — safe to parallelize
- [Story] label (US1–US6) maps task to specific user story from spec.md
- Each user story is independently completable and testable at its checkpoint
- All animations use CSS-only approach — no JavaScript animation libraries (Framer Motion not in dep tree)
- All new tokens, keyframes, and utility classes go in `frontend/src/index.css` (centralized)
- `CelestialLoader` is the only new component — all other changes are modifications to existing files
- ~126 component files across 12 directories need to be visited for US1 and US2
- Commit after each logical group of tasks (e.g., after completing a directory)
- Existing `prefers-reduced-motion` block already covers most animation classes — only new additions need to be added
- Total estimated effort: 32 hours (per spec metadata)
