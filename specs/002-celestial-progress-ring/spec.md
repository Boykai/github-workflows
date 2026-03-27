# Feature Specification: Celestial Loading Progress Ring

**Feature Branch**: `002-celestial-progress-ring`  
**Created**: 2026-03-27  
**Status**: Draft  
**Input**: User description: "Celestial Loading Progress Ring — Replace CelestialLoader with Phased SVG Progress Component on Long-Loading Screens"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Phased Progress Feedback on Project Page (Priority: P1)

As a user navigating to a project page, I want to see a cosmic-themed animated progress ring with labeled status messages so that I always know what is loading and how far along the process is — even before any data has resolved.

When the user selects a project, instead of seeing a static spinner, they see a circular gold progress ring with the existing sun-and-planet animation centered inside it. The ring begins filling immediately upon mount (time-based minimum animation), and a phase label below the ring updates as each data-fetching stage completes: "Connecting to GitHub…" → "Loading project board…" → "Loading pipelines…" → "Loading agents…" → "Almost there…". Small twinkling stars are scattered around the ring for brand continuity.

**Why this priority**: The Project page is the primary long-loading screen users encounter. Replacing the static loader here delivers the highest-impact improvement to perceived performance and user confidence. This is the core component creation story — all other pages reuse it.

**Independent Test**: Can be fully tested by navigating to any project and confirming the gold ring fills through labeled phases with stars twinkling, the ring moves immediately on mount, and jumps forward on each phase completion.

**Acceptance Scenarios**:

1. **Given** a user navigates to a project page and data is loading, **When** the page begins to load, **Then** the progress ring appears immediately with the first phase label ("Connecting to GitHub…") and the ring begins filling from 0% via a time-based animation.
2. **Given** the progress ring is displayed and the first data source resolves, **When** the connection phase completes, **Then** the ring jumps to at least 25% progress and the phase label updates to the next phase ("Loading project board…").
3. **Given** all four phases have completed, **When** the final data source resolves, **Then** the ring reaches 100% and the loading screen is replaced by the fully loaded project page.
4. **Given** all phases resolve very quickly (under 1 second total), **When** the page loads, **Then** the progress ring still displays briefly with smooth transitions and does not flash or stutter.

---

### User Story 2 — Phased Progress Feedback on Agents Pipeline and Settings Pages (Priority: P2)

As a user navigating to the Agents Pipeline page or the Settings page, I want to see the same cosmic-themed progress ring with page-appropriate phase labels so that I receive consistent loading feedback across all long-loading screens.

Each page shows the progress ring with its own set of phases relevant to the data being fetched on that page. The ring behavior (time-based minimum, phase jumps, twinkling stars) is identical to the Project page.

**Why this priority**: Extending the component to these two pages ensures consistent user experience across the application, but depends on the core component being built first (P1).

**Independent Test**: Can be tested by navigating to the Agents Pipeline page and the Settings page and confirming each displays the progress ring with page-specific phase labels.

**Acceptance Scenarios**:

1. **Given** a user navigates to the Agents Pipeline page and data is loading, **When** the page begins to load, **Then** the progress ring appears with phase labels relevant to the agents pipeline data-fetching sequence.
2. **Given** a user navigates to the Settings page and data is loading, **When** the page begins to load, **Then** the progress ring appears with phase labels relevant to the settings data-fetching sequence.
3. **Given** the progress ring is displayed on any of these pages, **When** phases complete, **Then** the ring and labels update identically to the Project page behavior (smooth fill, phase jumps, twinkling stars).

---

### User Story 3 — Accessibility and Dark Mode Support (Priority: P2)

As a user relying on assistive technology or using dark mode, I want the progress ring to be fully accessible and clearly visible so that I am not excluded from the loading feedback experience.

The progress ring exposes proper accessibility attributes so screen readers can announce progress. In dark mode, the gold ring stroke and twinkling star decorations remain clearly visible against the dark space background, maintaining the cosmic theme's visual integrity.

**Why this priority**: Accessibility is a non-negotiable quality requirement. Dark mode is the primary theme for the cosmic branding, so the ring must render correctly in that context.

**Independent Test**: Can be tested by enabling a screen reader and verifying progress announcements, and by toggling dark mode to confirm visual clarity of the ring and stars.

**Acceptance Scenarios**:

1. **Given** a screen reader is active, **When** the progress ring is displayed, **Then** the screen reader announces the progress ring with its current progress value.
2. **Given** the user has dark mode enabled, **When** the progress ring is displayed, **Then** the gold ring stroke and twinkling stars are clearly visible against the dark background.
3. **Given** the user has dark mode enabled, **When** the ring fills and phase labels transition, **Then** the ring glow effect and phase label text remain legible and visually distinct.

---

### User Story 4 — Time-Based Minimum Progress Animation (Priority: P1)

As a user waiting for data to load, I want the progress ring to begin filling immediately when the page starts loading — before any real data resolves — so that I have continuous visual feedback that the system is working and not frozen.

On mount, the ring automatically starts a time-based animation that increments from 0% to approximately 15% over 3 seconds, capping at approximately 30%. This ensures the ring is always visually moving, even if the first data source is slow. When real phase completions arrive, they jump the ring past the minimum floor.

**Why this priority**: The time-based floor is the key UX innovation that differentiates this from a standard phased loader. Without it, there would be a perceptible stall before the first data source resolves, defeating the purpose of the redesign.

**Independent Test**: Can be tested by introducing artificial delays in all data sources and confirming the ring still advances smoothly from 0% to ~15% within 3 seconds of mount.

**Acceptance Scenarios**:

1. **Given** the progress ring mounts and no phases have completed, **When** 3 seconds elapse, **Then** the ring has smoothly advanced to approximately 15% fill.
2. **Given** the progress ring has been mounted for more than 10 seconds with no phase completions, **When** the time-based animation continues, **Then** the ring caps at approximately 30% and does not advance further until a real phase completes.
3. **Given** the time-based minimum is at 10% and a phase completion moves real progress to 25%, **When** the phase completes, **Then** the ring jumps to 25% (the higher value) smoothly.
4. **Given** the time-based minimum is at 20% and a phase completion moves real progress to 15%, **When** the phase completes, **Then** the ring remains at 20% (the higher value) and does not regress.

---

### Edge Cases

- What happens when all phases complete almost instantly (under 500ms)? The ring should still display briefly with a smooth transition to 100% — no flash or stutter.
- What happens when a single phase takes an unusually long time (over 30 seconds)? The time-based minimum caps at ~30%, and the phase label remains on the current phase until it completes. The ring does not stall visually — the time-based fill keeps it moving until the cap.
- What happens when the user navigates away before all phases complete? The component unmounts cleanly with no errors or memory leaks from timers or animation state.
- What happens when the phases prop is an empty array? The component should handle this gracefully — either showing 100% (no phases to complete) or not rendering the progress ring at all.
- How does the ring behave when phases complete out of expected order? The ring reflects the total ratio of completed-to-total phases regardless of completion order; the phase label shows the first incomplete phase.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a new reusable loading progress component that accepts an ordered list of phases (each with a label and completion status) and renders a circular progress ring reflecting the proportion of completed phases.
- **FR-002**: System MUST implement a time-based minimum progress animation that begins on mount, advancing from 0% to approximately 15% over 3 seconds and capping at approximately 30%, ensuring the ring visually moves immediately even when no data has resolved.
- **FR-003**: System MUST compute visual progress as the greater of the time-based minimum floor and the ratio of completed phases to total phases, ensuring the ring never visually regresses.
- **FR-004**: System MUST render the progress ring as a circular shape (not a linear bar) using a gold/primary gradient stroke, reinforcing the orbital motif of the existing cosmic theme.
- **FR-005**: System MUST embed the existing celestial loader animation (sun and planet) centered inside the progress ring without modifying the existing loader component, preserving brand continuity.
- **FR-006**: System MUST display the current phase label below the ring, transitioning each label in with a fade-in animation as phases progress.
- **FR-007**: System MUST include small twinkling star decorations scattered around the progress ring, using existing animation styles.
- **FR-008**: System MUST apply a subtle gold glow effect on the ring using a drop-shadow filter, leveraging existing design tokens.
- **FR-009**: System MUST advance the ring fill smoothly via a transition on the ring's stroke offset — no frame-by-frame animation loop is required for the ring itself.
- **FR-010**: System MUST expose accessibility attributes on the progress ring, including a progressbar role and a dynamically updated current-value attribute reflecting computed progress.
- **FR-011**: System MUST replace the existing static loader on the Project page with the new progress component, wiring four phases: (1) "Connecting to GitHub…" — completes when project data is no longer loading, (2) "Loading project board…" — completes when board data is no longer loading, (3) "Loading pipelines…" — completes when saved pipelines are no longer loading, (4) "Loading agents…" — completes when agents data is available.
- **FR-012**: System MUST replace the existing static loader on the Agents Pipeline page with the new progress component using phases relevant to that page's data-fetching sequence.
- **FR-013**: System MUST replace the existing static loader on the Settings page with the new progress component using phases relevant to that page's data-fetching sequence.
- **FR-014**: System MUST NOT apply the phased progress component to the app-level suspense fallback or the authentication gate, as those transitions are too brief for phased messaging.
- **FR-015**: System MUST ensure the gold ring and twinkling stars remain clearly visible in dark mode against the dark space background.
- **FR-016**: System MUST include dedicated tests for the progress component covering: (a) rendering initial phase label with zero completions, (b) updating ring progress as phases complete, (c) exposing the progressbar role with correct progress value.
- **FR-017**: System MUST update existing Project page tests to account for the replaced loader component, with the full test suite passing without regressions.

### Key Entities

- **Phase**: Represents a single stage in the loading sequence. Each phase has a human-readable label (e.g., "Connecting to GitHub…") and a boolean completion status. Phases are ordered; the active phase label shown to the user is the first incomplete phase in the sequence.
- **Progress State**: The computed visual fill level of the ring, derived from two sources: (1) the time-based minimum floor and (2) the ratio of completed phases to total phases. The final displayed value is the greater of the two, expressed as a percentage from 0% to 100%.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users see the progress ring begin moving within 200ms of navigating to a long-loading page — eliminating the previous static-spinner stall.
- **SC-002**: 100% of loading phases display a descriptive label, giving users clear context on what is loading at each stage.
- **SC-003**: The progress ring reaches 100% and transitions to the loaded page content with zero visible stutter, flash, or regression in ring fill.
- **SC-004**: Users on all three target pages (Project, Agents Pipeline, Settings) see consistent progress ring behavior with page-appropriate phase labels.
- **SC-005**: Screen reader users can identify the progress ring and hear the current progress value announced.
- **SC-006**: In dark mode, the gold ring and twinkling star decorations are clearly visible with adequate contrast against the dark background.
- **SC-007**: All existing automated tests continue to pass with no regressions after the loader replacement.
- **SC-008**: The new progress component has dedicated automated tests achieving coverage of its core behaviors: initial render, phase progression, and accessibility attributes.

## Assumptions

- Progress is derived entirely from the resolution states of existing data-fetching hooks on each page. The backend does not stream progress percentages.
- The existing celestial loader (sun and planet animation) component is used as-is and is not modified. It is embedded inside the ring for visual continuity.
- The time-based minimum floor of ~30% is sufficient to prevent perceived stalls. If real completions are exceptionally slow, users see the ring pause at ~30% with the current phase label still displayed — which is preferable to a static spinner with no context.
- Each page's phases are derived from its existing loading state hooks. No new data-fetching hooks or backend endpoints are needed.
- The circular ring shape was an explicit design choice to echo the orbital motif; a linear progress bar was considered and rejected.
- Standard web/mobile performance expectations apply — the progress component itself should add negligible overhead to page load time.
