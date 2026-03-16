# Feature Specification: Agents Page Audit

**Feature Branch**: `043-agents-page-audit`  
**Created**: 2026-03-16  
**Status**: Draft  
**Input**: User description: "Comprehensive audit of the Agents page to ensure modern best practices, modular design, accurate text/copy, and zero bugs. Covers component decomposition, accessibility, error/loading/empty states, type safety, test coverage, and UI/UX polish."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Modular Component Architecture (Priority: P1)

As a developer maintaining the Agents page, I need each component to follow the single-responsibility principle so that I can understand, test, and modify individual sections without unintended side effects across the page.

**Why this priority**: Large, monolithic components (AgentsPanel at 565 lines, AddAgentModal at 520 lines, AgentCard at 286 lines, AgentInlineEditor at 272 lines) are the root cause of tangled state, difficult testing, and slow onboarding for new contributors. Decomposition unblocks all subsequent audit improvements.

**Independent Test**: Can be verified by checking that no component file exceeds 250 lines, each sub-component lives in `src/components/agents/`, and complex state logic (>15 lines of useState/useEffect/useCallback) is extracted into dedicated hooks.

**Acceptance Scenarios**:

1. **Given** the AgentsPanel component currently has 565 lines, **When** the audit is complete, **Then** the file is ≤250 lines with extracted sub-components in `src/components/agents/` (e.g., AgentSearch, AgentSortControls, SpotlightSection, AgentList).
2. **Given** the AddAgentModal component currently has 520 lines, **When** the audit is complete, **Then** the file is ≤250 lines with create and edit flows separated into distinct sub-components or a shared form component.
3. **Given** AgentCard (286 lines) and AgentInlineEditor (272 lines) exceed the limit, **When** the audit is complete, **Then** each is ≤250 lines with logical sections extracted (e.g., AgentCardActions, AgentCardMetadata, AgentEditForm).
4. **Given** AgentsPanel contains 8+ useState calls with interdependencies, **When** the audit is complete, **Then** complex state logic is extracted into a dedicated hook (e.g., `useAgentsPanel.ts`) or consolidated via a reducer pattern.
5. **Given** useAgentConfig.ts contains two unrelated hooks, **When** the audit is complete, **Then** `useAvailableAgents` is in its own file at `src/hooks/useAvailableAgents.ts`.

---

### User Story 2 - Reliable Loading, Error, and Empty States (Priority: P1)

As a user of the Agents page, I need clear visual feedback when data is loading, when an error occurs, or when no agents exist so that I never encounter a blank screen or confusing state.

**Why this priority**: Users encountering a blank screen or cryptic error lose trust in the product. Proper state handling is a fundamental UX requirement that directly impacts user retention and satisfaction.

**Independent Test**: Can be verified by simulating loading delays, API failures, rate limit errors, and empty agent lists, then confirming appropriate UI states render for each scenario.

**Acceptance Scenarios**:

1. **Given** the page is loading agent data, **When** the API response has not yet returned, **Then** a loading indicator (CelestialLoader or skeleton) is displayed — never a blank screen.
2. **Given** the API returns an error, **When** the error is displayed, **Then** a user-friendly message appears with a retry action button. The message follows the format: "Could not [action]. [Reason, if known]. [Suggested next step]."
3. **Given** the API returns a rate limit error, **When** the error is processed, **Then** the system detects it via `isRateLimitApiError()` and displays a specific rate-limit message with guidance on when to retry.
4. **Given** the user has no agents configured, **When** the agents list loads as empty, **Then** a meaningful empty state is displayed with a clear call-to-action to create the first agent.
5. **Given** the page fetches data from multiple sources (agents, pipelines, board columns), **When** one data source fails, **Then** the other sections still render independently with their own loading/error states — one failure does not block the entire page.
6. **Given** the page encounters an unexpected rendering error, **When** the error boundary catches it, **Then** a recovery UI is displayed with a retry option instead of a white screen.

---

### User Story 3 - Accessible Agent Management (Priority: P2)

As a user who relies on keyboard navigation or assistive technology, I need the Agents page to be fully operable without a mouse so that I can manage agents with the same efficiency as any other user.

**Why this priority**: Accessibility is both a legal/compliance requirement and a moral imperative. Many users depend on keyboard-only or screen-reader navigation, and an inaccessible page excludes them from core functionality.

**Independent Test**: Can be verified by navigating the entire Agents page using only the keyboard (Tab, Enter, Space, Escape) and confirming all interactive elements are reachable and operable; then running an automated accessibility audit (e.g., axe DevTools) for zero critical violations.

**Acceptance Scenarios**:

1. **Given** a user is navigating with the keyboard, **When** they Tab through the page, **Then** all interactive elements (buttons, links, toggles, inputs, agent cards) are reachable in a logical order.
2. **Given** a modal or dialog is open (AddAgentModal, delete confirmation, icon picker), **When** the user presses Tab, **Then** focus is trapped within the dialog and does not escape to background content.
3. **Given** a dialog is closed, **When** it finishes closing, **Then** focus returns to the element that triggered the dialog.
4. **Given** custom interactive elements (search, sort controls, agent cards), **When** inspected by a screen reader, **Then** each has appropriate ARIA attributes (`role`, `aria-label`, `aria-expanded`, `aria-selected`) as applicable.
5. **Given** all form fields on the page (search input, agent name, description, system prompt), **When** inspected, **Then** each has a visible label or `aria-label` providing context.
6. **Given** status indicators (active, pending_pr, pending_deletion), **When** rendered, **Then** they convey meaning through both icon + text, not color alone, meeting WCAG AA contrast requirements (4.5:1 ratio).
7. **Given** all interactive elements, **When** focused via keyboard, **Then** a visible focus ring (`celestial-focus` class or Tailwind `focus-visible:` ring) is displayed.

---

### User Story 4 - Polished Text, Copy, and User Experience (Priority: P2)

As a user interacting with the Agents page, I need all labels, messages, and feedback to be clear, consistent, and professional so that I can accomplish tasks confidently without confusion.

**Why this priority**: Inconsistent terminology, vague error messages, and missing confirmation dialogs erode user confidence and increase support burden. Polished copy directly improves task completion rates.

**Independent Test**: Can be verified by reviewing all user-facing strings for placeholder text, verifying destructive actions require confirmation, and confirming success/error messages follow the established format.

**Acceptance Scenarios**:

1. **Given** any user-visible text on the Agents page, **When** the audit is complete, **Then** no placeholder text remains ("TODO", "Lorem ipsum", "Test") and all strings are final, meaningful copy.
2. **Given** action buttons on the page, **When** their labels are reviewed, **Then** all use verb-based labels (e.g., "Create Agent", "Save Settings", "Delete Agent") rather than noun-only labels.
3. **Given** destructive actions (delete agent, stop agent, clear pending agents), **When** a user initiates any of them, **Then** a ConfirmationDialog appears before the action proceeds — no destructive action happens immediately.
4. **Given** a successful mutation (create, update, delete agent), **When** the operation completes, **Then** the user receives visible success feedback (toast notification, status change, or inline message).
5. **Given** a failed mutation, **When** the error is displayed, **Then** the message follows the format: "Could not [action]. [Reason, if known]. [Suggested next step]." — no raw error codes or stack traces.
6. **Given** long text content (agent names, descriptions, URLs), **When** it exceeds the available space, **Then** it is truncated with `text-ellipsis` and the full text is accessible via a Tooltip on hover.
7. **Given** timestamps on the page (agent creation dates), **When** displayed, **Then** recent timestamps use relative format ("2 hours ago") and older timestamps use absolute format, applied consistently.

---

### User Story 5 - Consistent Styling and Responsive Layout (Priority: P3)

As a user accessing the Agents page on different screen sizes and in dark mode, I need the layout to adapt gracefully and the theme to render correctly so that I have a usable experience regardless of my display setup.

**Why this priority**: Responsive design and dark mode support affect a broad user base. Visual inconsistencies undermine the perceived quality of the application.

**Independent Test**: Can be verified by viewing the Agents page at viewport widths 768px through 1920px in both light and dark modes, confirming no layout breaks, unreadable text, or hardcoded colors.

**Acceptance Scenarios**:

1. **Given** the Agents page, **When** viewed at viewport widths between 768px and 1920px, **Then** the layout adapts with no overflow, overlapping elements, or hidden content.
2. **Given** the Agents page in dark mode, **When** all elements are inspected, **Then** no hardcoded colors (e.g., `#fff`, `bg-white`) exist — all colors use Tailwind `dark:` variants or CSS variables from the theme.
3. **Given** styling throughout the page, **When** class usage is inspected, **Then** all styling uses Tailwind utility classes with `cn()` for conditionals — no inline `style={}` attributes.
4. **Given** spacing throughout the page, **When** inspected, **Then** all spacing uses the Tailwind spacing scale (e.g., `gap-4`, `p-6`) — no arbitrary values like `p-[13px]`.
5. **Given** content sections on the page, **When** inspected, **Then** they use the Card component from `src/components/ui/card.tsx` with consistent padding and border-radius.

---

### User Story 6 - Comprehensive Test Coverage (Priority: P3)

As a developer working on the Agents page, I need comprehensive tests covering hooks, components, and edge cases so that I can refactor and add features with confidence that existing behavior is preserved.

**Why this priority**: Tests are the safety net for all other audit improvements. Without adequate coverage, refactoring risks regressions. This story supports long-term maintainability.

**Independent Test**: Can be verified by running the test suite for agent-related files and confirming hooks are tested via `renderHook()`, components have `.test.tsx` files covering interactions, and edge cases (empty state, error state, loading, rate limit, null data) are covered.

**Acceptance Scenarios**:

1. **Given** custom hooks used by the Agents page (`useAgents`, `useAgentConfig`, `useAgentTools`), **When** tests are reviewed, **Then** each hook has test coverage via `renderHook()` with mocked API calls covering happy path, error, and loading states.
2. **Given** key interactive components (AgentsPanel, AddAgentModal, AgentCard), **When** tests are reviewed, **Then** each has `.test.tsx` files testing user interactions (click, keyboard, form submission).
3. **Given** test implementation, **When** patterns are reviewed, **Then** tests follow codebase conventions: `vi.mock('@/services/api', ...)`, `renderHook`, `waitFor`, `createWrapper()`.
4. **Given** the test suite, **When** edge cases are reviewed, **Then** the following scenarios are covered: empty state, error state, loading state, rate limit error, long strings, null/missing data.
5. **Given** the test suite, **When** test types are reviewed, **Then** no snapshot tests exist — all assertions are explicit and behavioral.

---

### User Story 7 - Performance and Code Hygiene (Priority: P3)

As a developer and end user, I need the Agents page to perform efficiently with clean, maintainable code so that the page loads quickly for users and is easy to understand and modify for developers.

**Why this priority**: Performance and code hygiene affect the long-term health of the codebase. While not user-facing in isolation, they enable faster iteration and prevent degradation over time.

**Independent Test**: Can be verified by running ESLint with zero warnings, confirming no `any` types or type assertions exist, verifying no dead code or `console.log` statements remain, and checking that expensive computations are memoized.

**Acceptance Scenarios**:

1. **Given** all agent-related files, **When** ESLint is run, **Then** zero warnings are produced.
2. **Given** all agent-related files, **When** type safety is reviewed, **Then** no `any` types or type assertions (`as`) exist — all props, state, and API responses are fully typed.
3. **Given** all agent-related files, **When** code is reviewed for dead code, **Then** no unused imports, commented-out blocks, or unreachable branches remain.
4. **Given** all agent-related files, **When** reviewed for debugging artifacts, **Then** no `console.log` statements exist.
5. **Given** all project imports in agent-related files, **When** reviewed, **Then** all use the `@/` alias — no relative paths like `../../`.
6. **Given** list renders on the page, **When** reviewed, **Then** all use `key={item.id}` — never `key={index}`.
7. **Given** expensive computations (sorting, filtering, usage counting), **When** reviewed, **Then** they are wrapped in `useMemo` or `useCallback` where appropriate to prevent unnecessary recalculation.

---

### Edge Cases

- What happens when the agents API returns an empty list but pipelines returns data? The page should display the empty agent state with a call-to-action, and the pipeline section should still render column data (with zero agents assigned).
- How does the system handle a rate-limited API response during an agent creation mutation? The error message should detect the rate limit via `isRateLimitApiError()` and advise the user to wait before retrying.
- What happens when an agent name is extremely long (>200 characters)? The name should be truncated with ellipsis in card and list views, with the full name accessible via Tooltip.
- How does the page behave when the user has no project selected? The ProjectSelectionEmptyState component renders, preventing any agent data fetching.
- What happens when a user rapidly clicks the delete button on multiple agents? Each click should open a ConfirmationDialog; only one dialog should be visible at a time; previous mutation should complete or be queued.
- How does the page handle agents with null or missing optional fields (icon_name, status_column, github_issue_number)? The UI should gracefully fall back to defaults (auto-generated avatar, "Unassigned" label, hidden issue link).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: All component files in the Agents feature MUST be ≤250 lines. Components exceeding this limit MUST be decomposed into sub-components within `src/components/agents/`.
- **FR-002**: Complex state logic (>15 lines of useState/useEffect/useCallback) MUST be extracted into dedicated hooks in `src/hooks/`.
- **FR-003**: The page MUST display a loading indicator (CelestialLoader or skeleton) while any data source is fetching — a blank screen MUST NOT appear.
- **FR-004**: API errors MUST display a user-friendly message with a retry action. Rate limit errors MUST be detected via `isRateLimitApiError()` and display specific guidance.
- **FR-005**: An empty agents list MUST display a meaningful empty state with a call-to-action to create the first agent.
- **FR-006**: Multiple independent data sources (agents, pipelines, board columns) MUST render their own loading and error states independently — one failure MUST NOT block other sections.
- **FR-007**: The page MUST be wrapped in an ErrorBoundary (at route or page level) to catch unexpected rendering errors.
- **FR-008**: All interactive elements MUST be keyboard-accessible (Tab navigation, Enter/Space activation).
- **FR-009**: All dialogs and modals MUST trap focus and return focus to the trigger element on close.
- **FR-010**: All form fields MUST have a visible label or `aria-label`. Custom controls MUST have appropriate ARIA attributes.
- **FR-011**: Status indicators MUST convey meaning through icon + text, not color alone, meeting WCAG AA contrast (4.5:1 ratio).
- **FR-012**: All destructive actions (delete, clear pending) MUST require confirmation via ConfirmationDialog before executing.
- **FR-013**: All mutations (create, update, delete) MUST provide visible success feedback (toast, status change, or inline message).
- **FR-014**: Error messages MUST follow the format: "Could not [action]. [Reason, if known]. [Suggested next step]." — no raw error codes or stack traces.
- **FR-015**: Long text (names, descriptions, URLs) MUST be truncated with `text-ellipsis` and full content accessible via Tooltip.
- **FR-016**: The page layout MUST be responsive from 768px to 1920px viewport width without overflow or hidden content.
- **FR-017**: All styling MUST use Tailwind utility classes (no inline `style={}`). Dark mode MUST use `dark:` variants or CSS variables — no hardcoded colors.
- **FR-018**: All agent-related code MUST have zero `any` types and zero type assertions (`as`). All props, state, and API responses MUST be fully typed.
- **FR-019**: Custom hooks for the Agents page MUST have test coverage via `renderHook()` with mocked API calls.
- **FR-020**: Key interactive components MUST have `.test.tsx` files testing user interactions, following codebase conventions.
- **FR-021**: All agent-related files MUST produce zero ESLint warnings when linted.
- **FR-022**: No dead code (unused imports, commented-out blocks), no `console.log` statements, and all imports MUST use the `@/` alias.
- **FR-023**: All React Query hooks MUST use the established query key factory pattern and configure appropriate `staleTime`.
- **FR-024**: Mutations MUST use `invalidateQueries` on success for cache consistency. All `useMutation` calls MUST have `onError` handling that surfaces user-visible feedback.

### Key Entities

- **Agent (AgentConfig)**: A configured AI agent with properties including name, slug, description, system prompt, model assignment, tools, status (active/pending_pr/pending_deletion), source (local/repo/both), and optional icon. The primary entity managed on the Agents page.
- **Agent Assignment**: An instance of an agent assigned to a board column, with a unique instance ID, agent slug, display name, and optional model configuration override.
- **Available Agent**: A registered agent template from the workflow API, with slug, display name, default model, and source classification (builtin/repository).
- **Agent Tool**: A tool capability that can be assigned to an agent, identified by a tool ID and display chip metadata.
- **Board Column**: A project board column (status) to which agents are assigned. Column names may vary in casing and are handled case-insensitively.
- **Pipeline Configuration**: Pipeline stage definitions that reference agents, used to display pipeline configuration counts alongside agent usage counts.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All component files in the Agents feature are ≤250 lines, verified by automated line count check.
- **SC-002**: The Agents page renders a visible loading state within 100ms of navigation — users never see a blank screen during data loading.
- **SC-003**: 100% of destructive actions on the page require user confirmation before executing.
- **SC-004**: A keyboard-only user can complete all core tasks (browse agents, create agent, edit agent, delete agent, assign agent to column) without using a mouse.
- **SC-005**: The page produces zero ESLint warnings and zero TypeScript errors (`tsc --noEmit`).
- **SC-006**: Automated accessibility audit reports zero critical or serious violations on the Agents page.
- **SC-007**: All agent-related custom hooks have test coverage with passing tests for happy path, error, and loading states.
- **SC-008**: The page renders correctly at viewport widths 768px, 1024px, 1440px, and 1920px in both light and dark modes with no layout breaks.
- **SC-009**: Users receive clear, actionable feedback for every mutation outcome (success or failure) within 2 seconds of the action completing.
- **SC-010**: No `any` types, type assertions, dead code, or `console.log` statements exist in agent-related files.

## Assumptions

- The existing agent-related API endpoints and their response shapes will not change during this audit. The audit focuses on frontend presentation and architecture only.
- The existing shared component library (`src/components/ui/`, `src/components/common/`) is stable and does not need modification — the audit will consume these primitives as-is.
- The project uses TanStack React Query as its established data-fetching library, and all new or refactored data fetching will use this library.
- Dark mode theming relies on Tailwind's `dark:` variant system and CSS custom properties already configured in the project.
- The audit will not add new third-party dependencies unless strictly necessary (e.g., virtualization for large lists). Existing dependencies are preferred.
- The 250-line component limit is a guideline that may be exceeded by up to 10% (275 lines) if splitting would create artificial boundaries that harm readability.
- Test conventions follow the existing patterns in the codebase: vitest, `vi.mock`, `renderHook`, `waitFor`, and `createWrapper()`.
- Performance optimizations (memoization, virtualization) are applied only where measurable benefit exists — premature optimization is avoided.

## Scope Boundaries

### In Scope

- All files directly related to the Agents page: `AgentsPage.tsx`, all components in `src/components/agents/` and `src/components/board/`, hooks (`useAgents.ts`, `useAgentConfig.ts`, `useAgentTools.ts`, `useProjectBoard.ts`), and related type definitions.
- Component decomposition and code organization improvements.
- Loading, error, and empty state implementation or fixes.
- Accessibility improvements (keyboard navigation, ARIA attributes, focus management, contrast).
- Text/copy review and UX polish (labels, messages, confirmations, tooltips).
- Styling audit (Tailwind usage, responsive design, dark mode).
- Type safety improvements (eliminating `any`, adding proper types).
- Test coverage additions for hooks and components.
- Code hygiene (dead code removal, import cleanup, ESLint compliance).

### Out of Scope

- Backend API changes or new endpoint development.
- Changes to shared components (`src/components/ui/`, `src/components/common/`) unless a bug is discovered during the audit.
- Changes to other pages (Pipelines, Settings, Dashboard) — this audit is scoped exclusively to the Agents page.
- New feature development (new agent capabilities, new UI features not currently present).
- Database schema changes or migration updates.
- CI/CD pipeline changes.
- Third-party dependency upgrades unless required for a specific audit finding.

## Dependencies

- **Shared UI Components**: Button, Card, Input, Tooltip, ConfirmationDialog, HoverCard from `src/components/ui/`.
- **Common Components**: CelestialLoader, ErrorBoundary, ProjectSelectionEmptyState, ThemedAgentIcon from `src/components/common/`.
- **Utility Library**: `cn()` helper from `src/lib/utils.ts` for conditional class composition.
- **Data Fetching**: TanStack React Query (useQuery, useMutation, queryClient).
- **Styling**: Tailwind CSS with project theme configuration.
- **Testing**: vitest, @testing-library/react, @testing-library/user-event.
