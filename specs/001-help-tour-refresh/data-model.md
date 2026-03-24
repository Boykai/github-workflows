# Data Model: Help Page & Tour Guide Full Refresh + Backend Step-Count Bug Fix

**Feature**: `001-help-tour-refresh` | **Date**: 2026-03-24

## Entities

### 1. OnboardingState (Backend — Pydantic Response Model)

| Field | Type | Default | Constraints | Notes |
|-------|------|---------|-------------|-------|
| `user_id` | `str` | — | required | GitHub user ID |
| `current_step` | `int` | `0` | `0 ≤ x ≤ 13` | 0-indexed tour step (was ≤10) |
| `completed` | `bool` | `False` | — | Tour completion flag |
| `dismissed_at` | `str \| None` | `None` | ISO 8601 | Dismissal timestamp |
| `completed_at` | `str \| None` | `None` | ISO 8601 | Completion timestamp |

### 2. OnboardingStateUpdate (Backend — Pydantic Request Model)

| Field | Type | Default | Constraints | Notes |
|-------|------|---------|-------------|-------|
| `current_step` | `int` | — | `ge=0, le=13` | **CHANGE**: was `le=10` |
| `completed` | `bool` | `False` | — | — |
| `dismissed` | `bool` | `False` | — | — |

### 3. onboarding_tour_state (Database — SQLite Table)

| Column | Type | Default | Constraints | Notes |
|--------|------|---------|-------------|-------|
| `id` | `INTEGER` | auto | PRIMARY KEY AUTOINCREMENT | — |
| `user_id` | `TEXT` | — | NOT NULL UNIQUE | — |
| `current_step` | `INTEGER` | `0` | `CHECK (current_step >= 0 AND current_step <= 13)` | **CHANGE**: was `<= 10` |
| `completed` | `INTEGER` | `0` | `CHECK (completed IN (0, 1))` | Boolean as int |
| `dismissed_at` | `TEXT` | `NULL` | — | ISO 8601 |
| `completed_at` | `TEXT` | `NULL` | — | ISO 8601 |
| `created_at` | `TEXT` | `now()` | NOT NULL | — |
| `updated_at` | `TEXT` | `now()` | NOT NULL | Updated by trigger |

### 4. TourStep (Frontend — TypeScript Interface)

| Field | Type | Notes |
|-------|------|-------|
| `id` | `number` | Display ID (1-indexed, used only for labeling); **new**: ID 14 for Activity. Note: `currentStep` from `useOnboarding` is the 0-indexed array position (0–13). |
| `targetSelector` | `string \| null` | Maps to `data-tour-step` attribute; **new**: `'activity-link'` |
| `title` | `string` | Step display title; **new**: `'Activity'` |
| `description` | `string` | Step explanation text |
| `icon` | `React.FC` | Custom SVG component; **new**: `TimelineStarsIcon` |
| `placement` | `string` | Tooltip position relative to target |

**Array size change**: `TOUR_STEPS` length 13 → 14

### 5. FeatureGuide (Frontend — Inline Object)

| Field | Type | Notes |
|-------|------|-------|
| `title` | `string` | Feature name; **new**: `'Activity'` |
| `description` | `string` | Feature description |
| `icon` | `LucideIcon` | Lucide icon component; **new**: `Clock` |
| `href` | `string` | Route path; **new**: `'/activity'` |

**Array size change**: `FEATURE_GUIDES` length 8 → 9

### 6. FaqEntry (Frontend — TypeScript Interface)

| Field | Type | Notes |
|-------|------|-------|
| `id` | `string` | Unique identifier (category + number pattern) |
| `question` | `string` | FAQ question text |
| `answer` | `string` | FAQ answer text |
| `category` | `FaqCategory` | One of: `getting-started`, `agents-pipelines`, `chat-voice`, `settings-integration` |

**Array size change**: `FAQ_ENTRIES` length 12 → 16 (4 new entries appended to existing categories)

## State Transitions

### OnboardingState.current_step

```
Step 0 (Welcome) → Step 1 → ... → Step 12 → Step 13 (Activity) → Completed
         ↑                                                              │
         └──────── restart() ───────────────────────────────────────────┘
```

- **Valid range**: 0–13 as array index / `currentStep` (was 0–10 for backend `le=`, 0–12 for frontend `TOTAL_STEPS - 1`)
- **Transition**: `next()` increments; at step 13 (last), sets `completed=true`
- **Backward**: `prev()` decrements; clamped at 0
- **Skip**: Sets `completed=true` from any step

## Validation Rules

| Rule | Location | Old Value | New Value |
|------|----------|-----------|-----------|
| Pydantic `le=` | `onboarding.py:32` | `le=10` | `le=13` |
| DB CHECK | `038_onboarding_step_limit.sql` | `<= 10` | `<= 13` |
| Frontend `TOTAL_STEPS` | `useOnboarding.tsx:10` | `13` | `14` |
| Frontend `TOUR_STEPS.length` | `SpotlightTour.tsx` | `13` | `14` |

## Relationships

```
OnboardingStateUpdate (request) → validates → onboarding_tour_state (DB)
                                                     ↑
OnboardingState (response) ← reads ─────────────────┘

TOUR_STEPS[currentStep] → targets → data-tour-step attribute in DOM
                                          ↑
                              Sidebar.tsx mapping provides attribute values

FEATURE_GUIDES → renders → FeatureGuideCard components on HelpPage
FAQ_ENTRIES    → renders → FaqAccordion on HelpPage
```
