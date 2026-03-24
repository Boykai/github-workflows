# Feature Specification: Help Page & Tour Guide Full Refresh + Backend Step-Count Bug Fix

**Feature Branch**: `001-help-tour-refresh`  
**Created**: 2026-03-24  
**Status**: Draft  
**Input**: User description: "Help Page & Tour Guide Full Refresh + Backend Step-Count Bug Fix"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tour Steps Persist Correctly Beyond Step 10 (Priority: P1)

As a new user progressing through the Spotlight Tour, I want my progress to be reliably saved at every step (including steps 11–13) so that I can resume the tour from where I left off without silently losing my place.

**Why this priority**: This is a critical data-integrity bug. The backend currently caps `current_step` at 10 via a Pydantic validator and database CHECK constraint, causing steps 11–13 to silently fail to persist. Users experience a broken onboarding flow where progress is lost, leading to confusion and repeated tour steps.

**Independent Test**: Can be tested by advancing the tour to step 11, refreshing the page, and confirming the tour resumes at step 11 rather than resetting. Backend API tests can verify steps 0–13 are all accepted.

**Acceptance Scenarios**:

1. **Given** a user is on tour step 11, **When** the frontend sends `current_step=11` to the API, **Then** the backend persists the value and returns it on subsequent queries.
2. **Given** a user is on tour step 13 (the last step), **When** the frontend sends `current_step=13` to the API, **Then** the backend persists the value without error.
3. **Given** a user sends `current_step=14` (out of range), **When** the API processes the request, **Then** the backend rejects the value with a validation error.
4. **Given** the database has the updated CHECK constraint, **When** a value of 13 is inserted into `current_step`, **Then** the database accepts it without constraint violation.

---

### User Story 2 - Activity Page Appears in the Spotlight Tour (Priority: P2)

As a new user taking the Spotlight Tour, I want to see the Activity page highlighted as a tour step so that I know where to find it and understand its purpose.

**Why this priority**: The Activity page already exists in the sidebar navigation and has its own route, but it is completely absent from the onboarding tour. This gap means new users may never discover this feature during their guided introduction to the application.

**Independent Test**: Can be tested by starting or resuming the Spotlight Tour and verifying a step highlights the Activity page sidebar link with an appropriate icon and description.

**Acceptance Scenarios**:

1. **Given** the Spotlight Tour is active, **When** the user reaches the Activity page tour step, **Then** the sidebar's Activity link is highlighted with a tooltip explaining its purpose.
2. **Given** the Sidebar renders with tour data attributes, **When** the Activity link is present, **Then** it has the `data-tour-step="activity-link"` attribute for the tour to target.
3. **Given** the tour step for Activity is displayed, **When** the user views its icon, **Then** a new celestial-themed icon (consistent with existing tour step icons) is shown.
4. **Given** the tour has been updated, **When** the `totalSteps` constant is checked, **Then** it reflects the new total of 14 steps.

---

### User Story 3 - Activity Page Listed in Help Page Feature Guides (Priority: P2)

As a user browsing the Help page, I want to see an Activity feature guide entry so that I can quickly navigate to the Activity page and understand what it offers.

**Why this priority**: The Help page serves as a reference for all application features. Without an Activity entry, users looking for help cannot discover or navigate to the Activity page from the Help center.

**Independent Test**: Can be tested by navigating to the Help page and verifying the Activity feature guide is displayed with the correct icon and links to `/activity`.

**Acceptance Scenarios**:

1. **Given** the user opens the Help page, **When** the feature guides section loads, **Then** an "Activity" entry is displayed with a Clock icon.
2. **Given** the Activity feature guide is present, **When** the user clicks on it, **Then** they are navigated to the `/activity` route.
3. **Given** all feature guides are rendered, **When** the total count is verified, **Then** exactly 9 feature guides are displayed.

---

### User Story 4 - FAQ Content Is Accurate and Comprehensive (Priority: P3)

As a user browsing the FAQ section, I want all existing FAQ answers to be accurate and I want to find answers about the Activity page, app creation, MCP tools, and multi-project monitoring so that I have comprehensive self-service support.

**Why this priority**: FAQ content is the first line of self-service support. Inaccurate or missing entries cause users to file unnecessary support requests and create confusion about application capabilities.

**Independent Test**: Can be tested by navigating to the FAQ section and verifying all 16 entries render correctly, with the 4 new entries appearing under their respective categories.

**Acceptance Scenarios**:

1. **Given** the user opens the FAQ section, **When** all entries load, **Then** exactly 16 FAQ entries are displayed.
2. **Given** the "Getting Started" category, **When** the user looks for Activity page information, **Then** a "What is the Activity page?" FAQ entry is present with an accurate description.
3. **Given** the "Settings & Integration" category, **When** the user looks for app creation help, **Then** a "How do I create a new app?" FAQ entry is present.
4. **Given** the "Settings & Integration" category, **When** the user looks for MCP tools information, **Then** a "What are MCP tools?" FAQ entry is present.
5. **Given** the "Agents & Pipelines" category, **When** the user looks for multi-project monitoring, **Then** a "Can Solune monitor multiple projects?" FAQ entry is present.
6. **Given** the existing 12 FAQ entries, **When** the audit is complete, **Then** all entries accurately reflect current application behavior.

---

### User Story 5 - Dead Help Link Mapping Removed from Sidebar (Priority: P3)

As a developer maintaining the codebase, I want the dead `/help: "help-link"` mapping removed from the Sidebar's `data-tour-step` map so that the code accurately reflects the navigation structure and does not reference a non-existent route.

**Why this priority**: Dead code creates confusion for developers and can cause subtle bugs if the mapping is ever relied upon. The help link resides in the TopBar, not in `NAV_ROUTES`, making this sidebar mapping orphaned.

**Independent Test**: Can be tested by verifying the Sidebar component's `data-tour-step` mapping no longer contains a `/help` entry and that no functionality is broken.

**Acceptance Scenarios**:

1. **Given** the Sidebar component, **When** the `data-tour-step` dynamic mapping is inspected, **Then** there is no entry for `/help: "help-link"`.
2. **Given** the help link in the TopBar, **When** the user clicks it, **Then** it continues to function correctly (no regression).

---

### Edge Cases

- What happens when a user's `current_step` is already persisted as a value above 10 before the migration runs? The migration should expand the constraint, so existing values (if any were saved via a workaround) remain valid.
- How does the system handle a `current_step` of exactly 0 (tour not started)? Step 0 should continue to be valid and persist correctly.
- What happens if the tour is completed (step 13) and the user tries to restart? The frontend should handle tour completion state independently of step persistence.
- What if the FAQ entries already contain partial or similar content? The audit must deduplicate and ensure no conflicting information exists.
- How does the system handle the Sidebar rendering when the Activity route is disabled or unavailable? The `data-tour-step` attribute should only appear when the Activity link is present in `NAV_ROUTES`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST update the `OnboardingStateUpdate.current_step` Pydantic validator from `le=10` to `le=13` in `onboarding.py` to support 14 tour steps (0-indexed, range 0–13).
- **FR-002**: System MUST add a new database migration changing the CHECK constraint on `current_step` from `CHECK (current_step <= 10)` to `CHECK (current_step <= 13)` to align the database boundary with the expanded tour.
- **FR-003**: System MUST add a new tour step entry in `SpotlightTour.tsx` for the Activity page using the `activity-link` target selector, positioned as the 14th step in the `TOUR_STEPS` array.
- **FR-004**: System MUST add `data-tour-step="activity-link"` to the Sidebar component's dynamic mapping in `Sidebar.tsx` for the Activity page link.
- **FR-005**: System MUST update the `totalSteps` constant in `useOnboarding.tsx` from 13 to 14 to reflect the addition of the Activity tour step.
- **FR-006**: System MUST create a new celestial-themed icon (`TimelineStarsIcon` or equivalent) in `icons.tsx` for the Activity tour step, consistent with the existing tour step icon style.
- **FR-007**: System MUST add an "Activity" entry to the `FEATURE_GUIDES` array in `HelpPage.tsx` with a Clock icon and `/activity` route, bringing the total feature guide count to 9.
- **FR-008**: System MUST audit all 12 existing FAQ entries against current application behavior and correct any inaccuracies found.
- **FR-009**: System MUST add 4 new FAQ entries to existing categories:
  - "What is the Activity page?" under Getting Started
  - "How do I create a new app?" under Settings & Integration
  - "What are MCP tools?" under Settings & Integration
  - "Can Solune monitor multiple projects?" under Agents & Pipelines
- **FR-010**: System MUST remove the dead `/help: "help-link"` entry from the Sidebar's dynamic `data-tour-step` mapping in `Sidebar.tsx`.
- **FR-011**: System MUST ensure the total FAQ entry count is exactly 16 after all additions (12 existing + 4 new).
- **FR-012**: System MUST pass all verification checks before merge: `pytest tests/unit/test_api_onboarding.py`, `npx vitest run`, `npx tsc --noEmit`, `ruff format`, `ruff check`, and `pyright` — all with zero errors.

### Key Entities

- **OnboardingState**: Represents a user's onboarding progress. Key attributes: `current_step` (integer, 0–13), `is_completed` (boolean). Validated via Pydantic model and database CHECK constraint.
- **TourStep**: Represents a single step in the Spotlight Tour. Key attributes: target selector (CSS selector string), title, description, icon component. Stored as a frontend constant array.
- **FeatureGuide**: Represents a help entry for an application feature. Key attributes: name, icon, route path. Displayed on the Help page.
- **FAQEntry**: Represents a frequently asked question. Key attributes: question text, answer text, category. Grouped by category in the FAQ accordion.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can progress through all 14 Spotlight Tour steps (0–13) without any step failing to persist, verified by completing the full tour and refreshing at each step boundary.
- **SC-002**: The Help page displays exactly 9 feature guides, including the new Activity entry, all linking to their correct routes.
- **SC-003**: The FAQ section displays exactly 16 entries across existing categories, with all answers accurately reflecting current application behavior.
- **SC-004**: Tour step persistence for steps 11, 12, and 13 succeeds on first attempt with no silent failures, measured by backend API tests covering the full 0–13 range.
- **SC-005**: New users completing the Spotlight Tour encounter the Activity page step with a correctly rendered celestial icon and descriptive tooltip.
- **SC-006**: The Sidebar component contains no dead `data-tour-step` mappings for routes not present in `NAV_ROUTES`.
- **SC-007**: All automated verification checks pass with zero errors: unit tests (pytest, vitest), type checking (tsc, pyright), and linting (ruff format, ruff check).

## Assumptions

- The existing 13 tour steps (steps 0–12, with `totalSteps=13`) are correctly implemented and working; this feature adds a 14th step (step index 13) and fixes persistence for steps 11–13 that were already defined in the frontend but blocked by backend validation.
- The Activity page route (`/activity`) and its corresponding sidebar navigation link already exist in the application.
- The Spotlight Tour uses a 0-indexed step system where `totalSteps` represents the count (not the max index).
- FAQ categories ("Getting Started", "Settings & Integration", "Agents & Pipelines") already exist; no new categories need to be created.
- The celestial icon style (stars, cosmic themes) is an established pattern in the existing tour step icons.
- The database migration framework is already set up and migration files follow an existing naming convention.
- The Pydantic `le=` validator on `current_step` is the only backend validation that needs updating (no additional middleware or service-layer checks).
