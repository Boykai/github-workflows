# Feature Specification: Onboarding Spotlight Tour & Help/FAQ Page

**Feature Branch**: `042-onboarding-help-faq`  
**Created**: 2026-03-15  
**Status**: Draft  
**Input**: User description: "Add a celestial-themed guided spotlight tour that auto-launches on first login, highlighting key UI elements. Also add a /help route with FAQ accordion, feature guides, and a re-launch button for long-term user guidance."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - First-Time Guided Spotlight Tour (Priority: P1)

A new user logs in for the first time and is greeted by a step-by-step guided spotlight tour. The tour highlights key areas of the application layout — sidebar navigation, project selector, chat, pipelines, agents, and theme toggle — with a glowing cutout around each element and a tooltip explaining its purpose. The user progresses through 9 steps using Next/Back buttons or arrow keys, or skips the tour at any point.

**Why this priority**: First impressions determine whether users engage or abandon the application. Without guided onboarding, new users face a complex interface with no context for what Solune does or how to begin. This is the highest-value feature for reducing time-to-first-action.

**Independent Test**: Can be fully tested by clearing browser storage and logging in — the tour should appear automatically, step through all 9 highlights, and mark completion so it does not reappear on subsequent visits.

**Acceptance Scenarios**:

1. **Given** a user has never visited the application before, **When** they log in and reach the main layout, **Then** the spotlight tour activates automatically with step 1 visible.
2. **Given** the tour is active on step 3, **When** the user clicks "Next", **Then** the spotlight cutout moves to step 4's target element and the tooltip updates with step 4 content.
3. **Given** the tour is active on step 5, **When** the user clicks "Back", **Then** the spotlight returns to step 4.
4. **Given** the tour is active on any step, **When** the user clicks "Skip Tour", **Then** the tour closes, the completion flag is saved, and the tour does not reappear on page refresh.
5. **Given** the tour is active, **When** the user presses the Escape key, **Then** the tour closes (same as "Skip Tour").
6. **Given** the user has completed or skipped the tour previously, **When** they return to the application, **Then** the tour does not auto-launch.

---

### User Story 2 - Help Center Page with FAQ (Priority: P2)

A user navigates to the Help page from the sidebar to find answers to common questions and learn more about each feature. The page presents a hero section, a "Getting Started" section with quick-start cards, an FAQ accordion grouped by category, a feature guide grid with cards linking to each application area, and a reference list of available slash commands.

**Why this priority**: Ongoing self-service guidance is essential beyond the initial tour. Users who encounter confusion days or weeks after onboarding need a reliable Help destination, and FAQ content reduces support burden. This delivers value independently of whether the tour exists.

**Independent Test**: Can be fully tested by navigating to the `/help` route — the page should render with all sections, FAQ items should expand/collapse, and feature guide cards should link to their respective pages.

**Acceptance Scenarios**:

1. **Given** a logged-in user, **When** they click "Help" in the sidebar navigation, **Then** the Help Center page loads with a hero section, Getting Started cards, FAQ accordion, Feature Guide grid, and Slash Commands reference.
2. **Given** the user is on the Help page, **When** they click an FAQ question, **Then** the answer expands with a smooth animation; clicking again collapses it.
3. **Given** the user is on the Help page, **When** they click a Feature Guide card, **Then** they are navigated to the corresponding feature page (Projects, Pipelines, Agents, etc.).
4. **Given** the user is on the Help page, **When** they view the Slash Commands section, **Then** all registered commands are listed with their syntax and descriptions.

---

### User Story 3 - Replay Tour from Help Page (Priority: P3)

A user who completed the onboarding tour previously wants to revisit it. They navigate to the Help page and click "Replay Tour" to restart the guided spotlight from step 1.

**Why this priority**: Users with prior experience may return weeks later or want to refresh their memory. Providing a re-launch mechanism avoids permanent loss of the onboarding resource and adds value to the Help page. This depends on both the tour (P1) and the Help page (P2) existing.

**Independent Test**: Can be fully tested by completing the tour, navigating to the Help page, clicking "Replay Tour", and verifying the tour restarts from step 1 with all steps available.

**Acceptance Scenarios**:

1. **Given** a user who has previously completed the tour, **When** they click "Replay Tour" on the Help page, **Then** the spotlight tour restarts from step 1.
2. **Given** the user replays and completes the tour again, **When** they navigate away and return, **Then** the tour does not auto-launch (replay does not reset the first-visit flag).

---

### User Story 4 - Keyboard & Accessibility Navigation (Priority: P3)

A user navigates the spotlight tour entirely via keyboard. Arrow keys advance and retreat through steps, Tab cycles through interactive elements in the tooltip, and Escape dismisses the tour. Screen readers announce step changes.

**Why this priority**: Accessibility ensures all users can benefit from onboarding regardless of input method or assistive technology. This is a quality requirement on top of the core tour.

**Independent Test**: Can be fully tested by initiating the tour and using only keyboard inputs — ArrowRight to advance, ArrowLeft to go back, Tab to focus buttons, Enter to activate, Escape to dismiss — while verifying screen reader announcements.

**Acceptance Scenarios**:

1. **Given** the tour is active, **When** the user presses ArrowRight, **Then** the tour advances to the next step.
2. **Given** the tour is active, **When** the user presses ArrowLeft, **Then** the tour returns to the previous step.
3. **Given** the tour tooltip is displayed, **When** focus enters the tooltip, **Then** focus is trapped within the tooltip until the step changes or the tour closes.
4. **Given** the tour is active, **When** a step changes, **Then** screen readers announce the new step title and description via a live region.

---

### User Story 5 - Theme-Aware Tour & Help Experience (Priority: P3)

The spotlight overlay, tooltips, and Help page all adapt to the user's current theme (light/dark/system). If a user toggles the theme mid-tour, all tour elements update immediately to match the new theme.

**Why this priority**: Visual consistency with the celestial design system is a quality polish requirement. The application already has a robust theming system; the new components must participate in it.

**Independent Test**: Can be fully tested by starting the tour in dark mode, toggling to light mode mid-tour, and verifying overlay darkness, tooltip backgrounds, icon colors, and progress indicator colors all update.

**Acceptance Scenarios**:

1. **Given** the tour is active in dark mode, **When** the user toggles to light mode, **Then** the spotlight overlay, tooltip, and progress dots immediately reflect light theme colors.
2. **Given** the Help page is open in light mode, **When** the user switches to dark mode, **Then** all FAQ panels, feature guide cards, and hero decorations adapt to the dark theme.

---

### Edge Cases

- What happens when the sidebar is collapsed during the tour? The tour should auto-expand the sidebar for sidebar-related steps (2, 3, 5, 6, 7, 9) and restore the collapsed state after those steps or when the tour ends.
- What happens when the tour target element is off-screen? The system should scroll the element into view before positioning the spotlight cutout.
- What happens when the browser window is resized during the tour? The spotlight cutout and tooltip should reposition dynamically using viewport-relative calculations.
- What happens on mobile viewports (<768px)? The tooltip should render as a bottom sheet instead of a positioned popover to avoid clipping.
- What happens if the user refreshes the page mid-tour? The tour should not resume mid-step; it should either restart from step 1 (if not yet completed) or not appear (if previously completed/skipped).
- What happens when the user starts the tour but has not yet selected a project? The project selector step should still highlight the selector and explain its purpose, with the description noting that linking a repository is the first action to take.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST detect first-time visitors by checking for the absence of a completion flag in browser storage.
- **FR-002**: System MUST auto-launch the spotlight tour when a first-time visitor reaches the authenticated layout.
- **FR-003**: System MUST display a translucent overlay with a cutout window around the currently highlighted element during the tour.
- **FR-004**: System MUST display a tooltip near the highlighted element containing: step icon, title, description, step counter, and navigation controls (Back, Next, Skip Tour).
- **FR-005**: System MUST support 9 sequential tour steps: Welcome, Sidebar Navigation, Project Selector, Chat, Projects Board, Agent Pipelines, Agents, Theme Toggle, Help Link.
- **FR-006**: System MUST persist the tour completion flag in browser storage so the tour does not auto-launch on subsequent visits.
- **FR-007**: System MUST allow the user to skip the tour at any step, which sets the completion flag.
- **FR-008**: System MUST provide a `/help` route accessible from the sidebar navigation.
- **FR-009**: The Help page MUST include a "Replay Tour" action that restarts the spotlight tour from step 1.
- **FR-010**: The Help page MUST include an FAQ section with collapsible question-and-answer entries grouped by category.
- **FR-011**: The Help page MUST include a feature guide section with cards for each major application area linking to their respective pages.
- **FR-012**: The Help page MUST include a reference of available slash commands sourced from the existing command registry.
- **FR-013**: System MUST support keyboard navigation during the tour: ArrowRight (next), ArrowLeft (back), Escape (skip), Tab (cycle within tooltip).
- **FR-014**: System MUST trap focus within the tour tooltip while the tour is active.
- **FR-015**: System MUST announce step changes to screen readers via a live region.
- **FR-016**: All new components MUST adapt to the current theme (light/dark/system) and respond to mid-session theme changes.
- **FR-017**: All tour and Help page animations MUST respect the user's reduced motion preference.
- **FR-018**: On mobile viewports, the tour tooltip MUST render as a bottom sheet to avoid viewport overflow.

### Key Entities

- **Tour Step**: A single highlight in the onboarding flow. Attributes: step number, target element identifier, title, description, icon, preferred tooltip placement.
- **Tour State**: The user's progress through the tour. Attributes: active/inactive, current step index, completion status.
- **FAQ Entry**: A question-and-answer pair. Attributes: question text, answer text, category grouping, expanded/collapsed state.
- **Feature Guide**: A summary card for an application area. Attributes: icon, title, short description, link to feature page.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 90% of first-time users who begin the tour complete all 9 steps without skipping.
- **SC-002**: Users can navigate from login to completing the full tour in under 90 seconds.
- **SC-003**: The Help page loads and renders all sections (hero, Getting Started, FAQ, Feature Guides, Slash Commands) in under 2 seconds.
- **SC-004**: 100% of FAQ accordion items expand and collapse correctly across all supported viewports (375px, 768px, 1280px+).
- **SC-005**: "Replay Tour" successfully restarts the tour from step 1 within 1 second of clicking.
- **SC-006**: All tour and Help page components pass accessibility audit with no critical violations (keyboard navigation, focus management, screen reader announcements, color contrast).
- **SC-007**: All animations gracefully degrade to instant transitions when the user has reduced motion enabled.

## Assumptions

- The application already has a working authentication flow and the spotlight tour activates only within the authenticated layout (post-login).
- The existing celestial CSS animation system (`.celestial-fade-in`, `.celestial-panel`, `.golden-ring`, `.starfield`, `.celestial-pulse-glow`, `.celestial-twinkle`) is fully functional and will be reused without modification.
- The existing `ThemeProvider` and `useAppTheme()` hook correctly handle light/dark/system modes and the new components inherit theme context automatically.
- No backend changes are required; all tour state is client-side only.
- The FAQ content will be hardcoded initially; extraction to markdown files is a future consideration.
- SVG icons follow line-art style (geometric, thin strokes, gold/orange accent) inspired by the Cleric hand logo, using `currentColor` for theme adaptability.
