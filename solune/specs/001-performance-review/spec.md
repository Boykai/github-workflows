# Feature Specification: Performance Review

**Feature Branch**: `001-performance-review`  
**Created**: 2026-03-11  
**Status**: Draft  
**Input**: User description: "Perform a balanced first pass focused on measurable, low-risk performance gains across backend and frontend. Start with baselines and guardrails, then reduce backend refresh churn and improve frontend board responsiveness without broader architectural rewrites unless metrics prove they are needed."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Team Establishes a Trusted Performance Baseline (Priority: P1)

An engineering lead needs proof that any performance change is real and not just anecdotal. Before behavior changes, the team captures a before-state for idle board activity, board refresh cost, refresh-source behavior, and frontend render hot spots. The same checklist is reused after optimization so the team can demonstrate which changes improved performance and which behaviors remained stable.

**Why this priority**: Every later optimization depends on trustworthy before/after measurements. Without a baseline, the team cannot prove success or detect regressions introduced by the performance pass.

**Independent Test**: Capture baseline measurements for one representative board, record the same measurements after the first-pass optimizations, and verify the comparison can be reproduced using the documented checklist and existing automated tests.

**Acceptance Scenarios**:

1. **Given** the performance review is starting, **When** the team begins the work, **Then** it documents baseline measurements for idle board activity, board refresh cost, refresh-source behavior, and frontend render hot spots before any optimization is merged.
2. **Given** existing automated checks already cover cache, polling, WebSocket fallback, and board refresh behavior, **When** the baseline checklist is defined, **Then** those checks are reused as regression guardrails in the before/after comparison.
3. **Given** optimization work is proposed before baseline capture is complete, **When** the work is reviewed, **Then** the optimization is considered blocked until the baseline checklist and measurements exist.

---

### User Story 2 — Idle Board Viewing Stops Wasting Upstream Request Budget (Priority: P1)

A maintainer leaves a board open while monitoring work. Today, unchanged board state can still consume unnecessary upstream requests through refresh loops, polling behavior, or redundant repository resolution. After the first pass, an idle board stays quiet when nothing has changed, while manual refresh still gives the maintainer a deliberate full refresh when they ask for one.

**Why this priority**: Reducing unnecessary upstream activity protects rate limits, lowers backend cost, and removes the highest-value backend inefficiencies already identified in the codebase.

**Independent Test**: Observe an open board over a fixed interval before and after the change, verify reduced unchanged-state refresh activity, and confirm automated checks still pass for cache behavior, WebSocket change detection, polling fallback, and manual refresh semantics.

**Acceptance Scenarios**:

1. **Given** a board is open and the underlying data has not changed, **When** the observation interval completes, **Then** the system does not emit repeated full refreshes for the unchanged board state.
2. **Given** the board data and sub-issue data are already warm, **When** the same board is refreshed again, **Then** the refresh consumes fewer upstream requests than the captured baseline for the same scenario.
3. **Given** live updates are unavailable and safety polling is active, **When** no relevant board changes occur, **Then** the fallback behavior avoids triggering an expensive full board refresh.
4. **Given** a user explicitly requests a manual refresh, **When** the refresh runs, **Then** the system performs a full fresh board load even if automatic refresh paths would stay lightweight.

---

### User Story 3 — Live Updates Stay Responsive Without Recreating the Polling Storm (Priority: P1)

A board user expects task status updates to appear quickly, but does not want every small update to trigger an expensive board reload. After the first pass, lightweight real-time and fallback updates refresh only the data needed for task freshness, while full board reloads are reserved for manual refresh or confirmed board-level changes.

**Why this priority**: Frontend refresh behavior is directly tied to both responsiveness and backend request volume. A coherent refresh contract prevents the previous pattern of broad invalidation and unnecessary board reloads from coming back.

**Independent Test**: Simulate live updates, WebSocket unavailability, fallback polling, auto-refresh, and manual refresh paths; verify that task freshness stays timely while unchanged board data is not broadly reloaded.

**Acceptance Scenarios**:

1. **Given** a task update arrives through the live-update path, **When** only task-level data changed, **Then** the user sees the updated task state without a full board data reload.
2. **Given** the system is temporarily using fallback refresh behavior, **When** lightweight task updates continue to arrive, **Then** the fallback path follows the same refresh policy as the live-update path for unchanged board structure.
3. **Given** auto-refresh, fallback polling, WebSocket events, and manual refresh can all request updates, **When** the refresh contract is applied, **Then** only one coherent policy determines whether the result is a lightweight update or a full board reload.
4. **Given** board-level data really has changed, **When** the change is detected, **Then** the board performs a full reload and the user sees the updated board state promptly.

---

### User Story 4 — Large Board Interactions Feel Smoother During the First Pass (Priority: P2)

A user works on a representative board with many cards, opens chat, drags tasks, and interacts with popovers. Today, unnecessary derived-data recalculation, broad rerenders, and hot event listeners can make the UI feel sluggish. After the first pass, these common interactions feel smoother because the system avoids unnecessary rerender work and bounds hot listener activity.

**Why this priority**: The first pass is explicitly meant to deliver low-risk responsiveness improvements on the most visible board and chat interactions without jumping straight to virtualization or major rewrites.

**Independent Test**: Profile a representative board before and after the changes, repeat common interactions such as card updates, drag operations, chat dragging, and popover display, and compare render and interaction cost against the baseline.

**Acceptance Scenarios**:

1. **Given** a representative board size is loaded, **When** unaffected columns and cards receive no data changes, **Then** they are not rerendered solely because another part of the board updated.
2. **Given** derived board data is needed for rendering, **When** the user performs repeated lightweight interactions, **Then** the system avoids recomputing unchanged derived data on every interaction.
3. **Given** drag and popover listeners fire continuously during movement, **When** the user drags or repositions UI elements, **Then** listener-driven updates occur at a bounded rate that keeps the interaction responsive.
4. **Given** the first-pass optimizations still leave large boards materially laggy, **When** the work is evaluated against success criteria, **Then** a follow-on recommendation is created for structural improvements rather than extending the first pass indefinitely.

---

### Edge Cases

- What happens if the baseline shows the frontend is slow but the backend already meets unchanged-refresh expectations? The first pass still proceeds, but only the remaining high-value gaps are optimized and already-correct backend behavior is preserved.
- What happens if live updates disconnect for an extended period? The fallback path must remain safe, avoid expensive unchanged-state board reloads, and keep task freshness available until live updates recover.
- What happens if a user triggers a manual refresh while an automatic lightweight update is already in progress? The explicit manual refresh takes precedence and results in one full fresh board load rather than two competing refreshes.
- What happens if a representative large board still fails the first-pass responsiveness targets after low-risk render fixes? The work stops short of architectural rewrites and records a follow-on plan for structural improvements.
- What happens if baseline instrumentation or profiling reveals a hotspot outside the initially listed files? The hotspot can be included only if it directly affects the same board refresh and responsiveness goals for this first pass.

## Requirements *(mandatory)*

### Functional Requirements

#### Phase 1 — Baseline and Guardrails

- **FR-001**: The performance review MUST capture pre-change baseline measurements for idle board activity, board refresh cost, refresh-source behavior, and frontend render hot spots on a representative board before optimization work is considered complete.
- **FR-002**: The baseline package MUST define a repeatable before/after checklist that reuses the existing automated coverage for cache behavior, fallback refresh behavior, polling behavior, and board refresh behavior as regression guardrails.
- **FR-003**: The first pass MUST verify which previously intended protections for unchanged refresh behavior, cache time-to-live alignment, and sub-issue cache invalidation are already working so completed behavior is preserved rather than reimplemented.

#### Phase 2 — Backend Request Reduction

- **FR-004**: When a board remains unchanged during idle viewing, the system MUST suppress repeated automatic full refreshes for that unchanged state.
- **FR-005**: Repeating the same board refresh against warm board data and warm sub-issue data MUST consume fewer upstream requests than the captured baseline for the same scenario.
- **FR-006**: Fallback polling MUST NOT trigger a full board refresh unless a board-level change is detected or the user explicitly requests a manual refresh.
- **FR-007**: Any repository-resolution or polling logic touched by this first pass MUST reuse the existing canonical shared logic instead of introducing new duplicate request paths.
- **FR-008**: Manual refresh MUST continue to provide a full fresh board load and preserve the current expectation that it bypasses stale cached board state.

#### Phase 2 — Frontend Refresh Contract

- **FR-009**: The real-time update path, fallback polling path, auto-refresh path, and manual refresh path MUST follow one documented refresh contract that distinguishes lightweight task updates from full board reloads.
- **FR-010**: Lightweight task updates MUST remain decoupled from the expensive full-board load path unless a board-level change or manual refresh requires a full board reload.
- **FR-011**: Automatic refresh behavior MUST avoid recreating the previous broad invalidation pattern that refreshes the whole board for unchanged task-level updates.

#### Phase 3 — Frontend Render Optimization

- **FR-012**: The first pass MUST reduce repeated derived-data work in board and chat rendering paths for unchanged inputs during steady-state interactions.
- **FR-013**: The first pass MUST reduce unnecessary rerenders for unaffected board lists, cards, and adjacent UI surfaces during localized updates.
- **FR-014**: Hot event listeners used for drag, positioning, or similar continuous UI interactions MUST update at a bounded rate that improves responsiveness without changing visible behavior.
- **FR-015**: The first pass MUST stay within low-risk optimization techniques; it MUST NOT introduce board virtualization, major service decomposition, new dependencies, or broad architectural rewrites unless the measured results prove the first-pass targets were not met.

#### Phase 3 — Verification and Regression Coverage

- **FR-016**: Automated regression coverage MUST verify backend cache behavior, unchanged refresh suppression, live-update change detection, fallback polling behavior, and frontend board refresh policy after the first-pass changes.
- **FR-017**: The work MUST include at least one manual network/profile verification pass comparing post-change behavior against the documented baseline.
- **FR-018**: The documented verification results MUST show whether the first-pass success criteria were met for both request reduction and interactive responsiveness.

#### Phase 4 — Optional Follow-on Planning

- **FR-019**: If the first pass does not meet the documented success criteria, the outcome MUST include a follow-on recommendation that identifies which structural improvements should be considered next and why.
- **FR-020**: If the first pass meets the documented success criteria, broader structural changes MUST remain explicitly deferred and out of scope for this implementation.

### Key Entities

- **Performance Baseline**: The recorded before-state for idle board activity, board refresh cost, refresh-source behavior, and render hot spots on a representative board. Used as the reference point for all later verification.
- **Refresh Contract**: The agreed policy that determines when an incoming update should remain a lightweight task refresh and when it should trigger a full board reload.
- **Board Refresh Event**: Any automatic or user-initiated action that attempts to refresh board-related data. Includes live updates, fallback polling, auto-refresh, and manual refresh.
- **Warm Board State**: A board state in which the board data and related sub-issue data have already been loaded recently enough to support a lower-cost repeated refresh.
- **Render Hot Spot**: A UI surface or interaction that contributes a disproportionate share of repeated render or listener work during board and chat usage.
- **Follow-on Performance Plan**: A documented recommendation for second-wave structural work that is produced only if the first pass fails to meet its measured targets.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: During a fixed 10-minute idle-board observation, unchanged board viewing triggers 0 repeated automatic full board refreshes after the first-pass changes.
- **SC-002**: For the same representative board scenario used in the baseline, repeated refreshes against warm board state consume at least 30% fewer upstream requests than the pre-change baseline.
- **SC-003**: In fallback mode with no board-level changes, a fixed 10-minute observation triggers 0 unnecessary full board reloads while task freshness checks continue to run.
- **SC-004**: Lightweight live or fallback task updates appear to the user within 5 seconds without forcing a full board reload when board structure is unchanged.
- **SC-005**: On the representative board profile used for the baseline, 95% of common interactions in scope for this feature (card update, drag movement, chat drag, popover display) complete within 200 milliseconds after the first-pass changes.
- **SC-006**: The regression suite covering backend cache/polling/refresh behavior and frontend refresh behavior passes with 0 newly failing checks after the performance work is complete.
- **SC-007**: Manual refresh continues to return a fully refreshed board state in 100% of manual verification attempts performed during the final validation pass.
- **SC-008**: If any of SC-001 through SC-007 are not met, a follow-on performance plan is documented before the work is considered complete.

## Assumptions

- The existing automated tests around cache behavior, polling, WebSocket fallback, and board refresh behavior are reliable enough to serve as regression guardrails for this first pass.
- The parent issue's prior rate-limit protection expectations remain the acceptance reference for unchanged refresh suppression, cache alignment, and manual refresh semantics.
- A representative board can be chosen that is large enough to expose current render hot spots without requiring synthetic stress tooling.
- This work does not change user-facing product scope beyond improving refresh efficiency and responsiveness for existing board and chat behaviors.
- Manual network and profiling verification can be performed with the repository's existing local development and test setup.

## Scope Boundaries

### In Scope

- Capturing before/after performance baselines and documenting the guardrail checklist
- Reducing unnecessary backend request activity during idle viewing, polling, and repeated board refreshes
- Defining and enforcing a single refresh contract across live updates, fallback polling, auto-refresh, and manual refresh
- Applying low-risk render and listener optimizations to board and chat interactions
- Extending regression coverage and producing a follow-on recommendation if the first pass misses its targets

### Out of Scope

- Board virtualization during the first implementation pass
- Large service decomposition or broader architectural rewrites unrelated to the measured first-pass bottlenecks
- New dependencies added solely for optimization work
- Unrelated feature changes to board behavior, chat behavior, or project-management workflows
