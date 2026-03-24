# Quickstart: Help Page & Tour Guide Full Refresh + Backend Step-Count Bug Fix

**Feature**: `001-help-tour-refresh` | **Date**: 2026-03-24

## Overview

This feature fixes a backend validation bug that silently rejects tour steps 11–13, expands the Spotlight Tour to include the Activity page (14 total steps), adds Activity to the Help page feature guides, adds 4 new FAQ entries, and removes dead code from the Sidebar.

## Phase Order & Dependencies

```
Phase 1: Backend Step-Count Fix (no dependencies)
    ├── 1a. Update Pydantic validator (onboarding.py: le=10 → le=13)
    └── 1b. Add DB migration (038_onboarding_step_limit.sql: CHECK <= 13)

Phase 2: Activity Tour Step + Help Additions (depends on Phase 1 for step persistence)
    ├── 2a. Create TimelineStarsIcon (icons.tsx)
    ├── 2b. Add tour step 14 to TOUR_STEPS (SpotlightTour.tsx)
    ├── 2c. Add data-tour-step="activity-link" mapping (Sidebar.tsx)
    ├── 2d. Update TOTAL_STEPS to 14 (useOnboarding.tsx)
    └── 2e. Add Activity to FEATURE_GUIDES (HelpPage.tsx)

Phase 3: FAQ Audit + New Entries (independent of Phases 1–2)
    ├── 3a. Audit 12 existing FAQ entries
    └── 3b. Add 4 new FAQ entries (HelpPage.tsx)

Phase 4: Sidebar Dead-Code Removal (independent)
    └── 4a. Remove /help: "help-link" mapping (Sidebar.tsx)

Phase 5: Test Updates (depends on Phases 1–4)
    ├── 5a. Update test_api_onboarding.py boundaries (0–13)
    ├── 5b. Update useOnboarding.test.tsx assertions (totalSteps=14)
    └── 5c. Run full test suite (pytest + vitest)

Phase 6: Lint & Typecheck (depends on Phase 5)
    ├── 6a. ruff format + ruff check (backend)
    ├── 6b. pyright (backend)
    └── 6c. npx tsc --noEmit (frontend)
```

## Key Files Quick Reference

| File | Change | FR |
|------|--------|----|
| `solune/backend/src/api/onboarding.py` | `le=10` → `le=13` | FR-001 |
| `solune/backend/src/migrations/038_onboarding_step_limit.sql` | New migration: CHECK `<= 13` | FR-002 |
| `solune/frontend/src/components/onboarding/SpotlightTour.tsx` | Add 14th `TOUR_STEPS` entry | FR-003 |
| `solune/frontend/src/layout/Sidebar.tsx` | Add `activity-link` mapping, remove `help-link` | FR-004, FR-010 |
| `solune/frontend/src/hooks/useOnboarding.tsx` | `TOTAL_STEPS = 13` → `14` | FR-005 |
| `solune/frontend/src/assets/onboarding/icons.tsx` | Add `TimelineStarsIcon` | FR-006 |
| `solune/frontend/src/pages/HelpPage.tsx` | Add Activity guide + 4 FAQ entries | FR-007, FR-008, FR-009 |
| `solune/backend/tests/unit/test_api_onboarding.py` | Update step boundary tests | FR-012 |
| `solune/frontend/src/hooks/useOnboarding.test.tsx` | Update `totalSteps` assertion | FR-012 |

## Verification Commands

```bash
# Backend
cd solune/backend
pip install -e ".[dev]"
ruff check src/ tests/
ruff format --check src/ tests/
pyright src/
pytest tests/unit/test_api_onboarding.py -v

# Frontend
cd solune/frontend
npm install
npx vitest run
npx tsc --noEmit
```

## Critical Implementation Notes

1. **Migration numbering**: Use `038_` prefix (next after `037_phase8_recovery_log.sql`).
2. **Step indexing**: Steps are 0-indexed. `TOTAL_STEPS = 14` means valid indices 0–13. Backend `le=13` matches max index.
3. **SQLite constraint update**: Requires table rebuild (CREATE temp → copy → DROP → recreate → copy back → DROP temp) because SQLite does not support ALTER COLUMN.
4. **Icon convention**: All tour icons are 24×24 SVG, `currentColor` stroke, `strokeWidth={1.5}`, exported from `icons.tsx`.
5. **FAQ entry IDs**: Follow `{category}-{number}` pattern (e.g., `getting-started-4`).
6. **Tour step placement**: Activity step should use `placement: 'right'` (consistent with other sidebar-targeted steps).
