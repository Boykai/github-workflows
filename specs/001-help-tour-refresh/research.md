# Research: Help Page & Tour Guide Full Refresh + Backend Step-Count Bug Fix

**Feature**: `001-help-tour-refresh` | **Date**: 2026-03-24

## Research Tasks

### 1. Backend Step Validation — Current State & Fix Strategy

**Context**: The Pydantic validator `le=10` in `OnboardingStateUpdate` and the SQLite CHECK constraint `current_step <= 10` silently reject steps 11–13 even though the frontend `SpotlightTour.tsx` already defines 13 steps (array indices 0–12, with `TOTAL_STEPS = 13`).

**Decision**: Raise both the Pydantic `le=` value and the database CHECK constraint upper bound from 10 to 13.

**Rationale**: The frontend already uses 0-indexed steps with `TOTAL_STEPS = 13`, meaning valid step indices are 0–12. Adding the Activity step (14th step) raises `TOTAL_STEPS` to 14, giving valid indices 0–13. Both backend boundaries must match `le=13` to support the full range.

**Alternatives Considered**:
- **Dynamic validation from DB**: Rejected — over-engineered for a static tour; the step count changes infrequently and is controlled by the codebase, not user input.
- **Remove upper bound entirely**: Rejected — losing input validation would allow arbitrary step values, weakening data integrity.

---

### 2. Database Migration Strategy — SQLite CHECK Constraint

**Context**: SQLite does not support `ALTER TABLE ... ALTER COLUMN` or `ALTER TABLE ... DROP CONSTRAINT`. The original table is defined in `029_pipeline_state_persistence.sql` with `CHECK (current_step >= 0 AND current_step <= 10)`.

**Decision**: Create a new migration `038_onboarding_step_limit.sql` that recreates the `onboarding_tour_state` table with the updated CHECK constraint (`<= 13`) using the standard SQLite table-rebuild pattern: create temp table, copy data, drop original, recreate with new constraint, copy data back, drop temp.

**Rationale**: SQLite's architecture requires table recreation to modify CHECK constraints. This is the standard pattern used across the codebase's existing migrations. The migration sequence is `038` (next after `037_phase8_recovery_log.sql`).

**Alternatives Considered**:
- **Ignore CHECK constraint, only fix Pydantic**: Rejected — the database constraint is a defense-in-depth layer; leaving it at 10 would cause INSERT/UPDATE failures even after fixing the Pydantic validator.
- **Drop CHECK entirely**: Rejected — removes a valuable data integrity safeguard.

---

### 3. Tour Step Architecture — Icon Strategy

**Context**: The `TOUR_STEPS` array in `SpotlightTour.tsx` has 13 steps. Steps 10–13 reuse icons from earlier steps (`CelestialHandIcon`, `OrbitalRingsIcon`, `StarChartIcon`, `ConstellationGridIcon`) because dedicated icons were never created for those steps. The spec requires a new `TimelineStarsIcon` for the Activity step.

**Decision**: Create a single new icon `TimelineStarsIcon` in `icons.tsx` for the Activity tour step. The icon follows the established celestial SVG pattern: 24×24 viewBox, `currentColor` stroke, strokeWidth 1.5. Design: a vertical timeline (line) with small stars/circles at intervals, representing activity/events over time.

**Rationale**: The spec explicitly requests this icon. The existing pattern of celestial-themed SVG icons is well-established with 9 existing icons. Only one new icon is in scope for this feature.

**Alternatives Considered**:
- **Reuse an existing icon**: Rejected — spec explicitly requires a new `TimelineStarsIcon` for thematic consistency.
- **Use a Lucide icon instead of custom SVG**: Rejected — the SpotlightTour exclusively uses custom celestial SVG icons from `icons.tsx`; mixing would break visual consistency.

---

### 4. Sidebar data-tour-step Mapping — Dead Code Analysis

**Context**: `Sidebar.tsx` line 133 maps `/help: 'help-link'`, but `NAV_ROUTES` in `constants.ts` does not include a `/help` route. The help link exists in the TopBar component, not the Sidebar. This mapping is dead code.

**Decision**: Remove the `/help: 'help-link'` entry from the `data-tour-step` mapping object in `Sidebar.tsx` and add `/activity: 'activity-link'` since `/activity` is already in `NAV_ROUTES`.

**Rationale**: `/help` is not in `NAV_ROUTES`, so the mapping is unreachable — it never gets applied to any rendered element. `/activity` IS in `NAV_ROUTES` but lacks a `data-tour-step` mapping, which is needed for the new tour step to target it.

**Alternatives Considered**:
- **Keep `/help` mapping "just in case"**: Rejected — it creates false expectations and potential confusion for developers; the help-link tour step targets the TopBar, not the Sidebar.

---

### 5. FAQ Content Audit

**Context**: 12 existing FAQ entries across 4 categories must be audited against current app behavior, and 4 new entries must be added.

**Decision**: All 12 existing entries are accurate based on current codebase analysis. 4 new entries will be appended to existing categories:
- "What is the Activity page?" → `getting-started` (category already has 3 entries → 4)
- "How do I create a new app?" → `settings-integration` (category already has 3 entries → 4)
- "What are MCP tools?" → `settings-integration` (category → 5)
- "Can Solune monitor multiple projects?" → `agents-pipelines` (category already has 3 entries → 4)

**Rationale**: The existing entries reference features (`Projects board`, `Agent pipelines`, `Chat`, `Settings`) that still exist and function as described. No inaccuracies were found. New entries address gaps identified by the Activity page, Apps page, MCP tools, and multi-project workflows.

**Alternatives Considered**:
- **Create new FAQ categories**: Rejected — spec explicitly states "no new category is needed"; existing categories adequately cover the new entries.
- **Reorganize existing entries**: Rejected — out of scope; current organization is logical and consistent.

---

### 6. Test Strategy

**Context**: FR-012 requires all tests to pass. Backend tests currently validate step range 0–10; frontend tests assert `totalSteps === 13`.

**Decision**:
- **Backend** (`test_api_onboarding.py`): Update `test_invalid_step_rejected` parametrize to `[-1, 14, 100]` (was `[-1, 11, 100]`). Update `test_valid_step_accepted` parametrize to `[0, 5, 13]` (was `[0, 5, 10]`). Add new parametrized test for steps 11, 12, 13 specifically to verify boundary coverage. Update docstrings to reflect new range 0–13.
- **Frontend** (`useOnboarding.test.tsx`): Update `totalSteps` assertion from `13` to `14`. Update completion test loop to iterate 13 times (step 0→12→step 13 triggers completion). Update assertion for `currentStep` at last step from `12` to `13`.

**Rationale**: Tests must reflect the new validation boundaries. The parametrized approach is consistent with existing test patterns in `test_api_onboarding.py`.

**Alternatives Considered**:
- **Skip test updates**: Rejected — FR-012 explicitly requires passing tests, and tests will fail with updated validation boundaries.
