# Implementation Plan: Add Profile Page to App

**Branch**: `031-profile-page` | **Date**: 2026-03-09 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/031-profile-page/spec.md`

## Summary

Add a dedicated profile page (`/profile`) for authenticated users to view and manage their personal account information. The page displays GitHub-sourced identity data (avatar, username, email), editable fields (display name, bio) backed by a new `user_profiles` database table, avatar upload with client-side preview and backend storage, and read-only metadata (account creation date, role). The implementation spans frontend (new `ProfilePage` component, React Query mutations, file input with validation) and backend (new `PATCH /api/v1/users/profile` endpoint, new `POST /api/v1/users/profile/avatar` upload endpoint, new `user_profiles` SQLite table). Navigation integrates via a clickable avatar in the existing `TopBar` component. All UI reuses the existing Solune design system components (Card, Input, Button) with responsive layout and Solar theme support.

## Technical Context

**Language/Version**: TypeScript ~5.9 (frontend), Python 3.11+ (backend)
**Primary Dependencies**: React 19.2, react-router-dom 7.13, @tanstack/react-query 5.90, Tailwind CSS v4, FastAPI, aiosqlite, Pydantic
**Storage**: SQLite via aiosqlite — new `user_profiles` table for display name, bio, custom avatar path
**Testing**: Vitest 4 + Testing Library (frontend), pytest (backend)
**Target Platform**: Desktop + mobile browsers (Chrome, Firefox, Safari, Edge); FastAPI backend on Linux
**Project Type**: Web application (frontend + backend changes)
**Performance Goals**: Profile page load <3 seconds (SC-001); profile save round-trip <2 seconds; avatar upload with preview <60 seconds end-to-end (SC-005)
**Constraints**: Avatar file size ≤5 MB; accepted types PNG, JPG, WebP only; display name non-empty; must meet WCAG AA color contrast using existing theme tokens; fully responsive (320px+ mobile, 768px+ tablet, 1024px+ desktop)
**Scale/Scope**: 1 new page, 1 new backend endpoint pair (GET+PATCH profile, POST avatar), 1 new database table, ~4 modified files (App.tsx routing, TopBar.tsx nav, constants.ts routes, api.ts service functions)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 5 prioritized user stories (P1–P2), Given-When-Then acceptance scenarios, 18 functional requirements (FR-001–FR-018), 8 success criteria, edge cases, and assumptions |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan → tasks → implement) |
| **IV. Test Optionality** | ✅ PASS | Tests not explicitly mandated in spec; existing tests must continue to pass |
| **V. Simplicity/DRY** | ✅ PASS | Reuses existing UI components (Card, Input, Button), existing auth system (useAuth, AuthGate), existing settings API patterns, and existing file upload pattern from chat. New backend table is minimal (4 columns). No new frontend libraries needed. |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace back to spec FRs (FR-001–FR-018) |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 |
| **IV. Test Optionality** | ✅ PASS | Existing tests unaffected; no new tests mandated |
| **V. Simplicity/DRY** | ✅ PASS | Single new page reusing all existing primitives. Backend follows established settings_store.py patterns for the new profile store. Avatar upload reuses the validated file upload pattern from chat.py. No new abstractions or libraries introduced. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/031-profile-page/
├── plan.md              # This file
├── research.md          # Phase 0: Research decisions (R1–R5)
├── data-model.md        # Phase 1: Entity definitions, types, database schema
├── quickstart.md        # Phase 1: Developer onboarding guide
├── contracts/
│   └── components.md    # Phase 1: Component and API interface contracts
├── checklists/
│   └── requirements.md  # Specification quality checklist (complete)
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   └── user.py                    # MODIFIED: Add UserProfile, UserProfileUpdate, UserProfileResponse models
│   ├── services/
│   │   └── profile_store.py           # NEW: Profile data persistence (user_profiles table CRUD)
│   └── api/
│       └── profile.py                 # NEW: Profile API endpoints (GET/PATCH profile, POST avatar)
└── tests/
    └── unit/
        └── test_profile.py            # NEW: Unit tests for profile endpoints (if tests added)

frontend/
├── src/
│   ├── components/
│   │   └── profile/
│   │       ├── ProfileHeader.tsx      # NEW: Avatar display + upload control with preview
│   │       ├── ProfileForm.tsx        # NEW: Editable fields (display name, bio) with Save/Cancel
│   │       └── ProfileMetadata.tsx    # NEW: Read-only account metadata display
│   ├── pages/
│   │   └── ProfilePage.tsx            # NEW: Main profile page layout composing sub-components
│   ├── hooks/
│   │   └── useProfile.ts             # NEW: React Query hook for profile data fetch + mutation
│   ├── services/
│   │   └── api.ts                     # MODIFIED: Add profileApi functions (getProfile, updateProfile, uploadAvatar)
│   ├── layout/
│   │   └── TopBar.tsx                 # MODIFIED: Make user avatar clickable → navigates to /profile
│   ├── constants.ts                   # MODIFIED: Add /profile to NAV_ROUTES (optional sidebar entry)
│   └── App.tsx                        # MODIFIED: Add /profile route inside AuthGate-protected layout
└── tests/
```

**Structure Decision**: Web application (frontend + backend). This feature adds a new page to the existing frontend routing structure and a new API endpoint pair to the existing backend. Frontend components are organized in a new `profile/` directory under `components/` following the established pattern (e.g., `agents/`, `chores/`, `pipeline/`). Backend follows the existing `api/ → services/ → models/` layering pattern.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| New `user_profiles` table (not extending `user_sessions`) | User profile data (display name, bio, custom avatar) is independent of session lifecycle. Sessions are ephemeral (8h TTL); profile data is permanent. Extending `user_sessions` would lose profile data on session expiration. | Storing in `user_preferences` (rejected: preferences are for app settings like theme/model, not identity data; mixing concerns) |
| Server-side avatar storage (not client-only) | Avatars must persist across sessions and devices. The existing chat file upload pattern provides a proven approach for file handling with validation. | Client-side only via localStorage/IndexedDB (rejected: not portable across devices; storage limits; lost on cache clear) |
| TopBar avatar click for navigation (not sidebar-only) | The TopBar already displays the user avatar — making it clickable is the most discoverable entry point. Adding to NAV_ROUTES provides a secondary path. | Dropdown menu from avatar (rejected: adds complexity for a single destination; not consistent with the existing TopBar pattern which uses direct links) |
