# Implementation Plan: Global Page Audit

**Branch**: `044-global-page-audit` | **Date**: 2026-03-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/044-global-page-audit/spec.md`

## Summary

Comprehensive audit of the Global Settings section within the Settings page to ensure modern best practices, modular design, accurate text/copy, and zero bugs. The Global Settings section manages instance-wide defaults for AI preferences, display settings, workflow defaults, notification preferences, and allowed models. The audit covers component decomposition, accessibility, error/loading/empty states, type safety, test coverage, UI/UX polish, responsive layout, and dirty-state tracking.

## Technical Context

**Language/Version**: TypeScript ~5.9 (frontend)
**Primary Dependencies**: React 19.2, Vite 7.3, TanStack React Query 5.90, Tailwind CSS 4.2, react-hook-form, zod, @hookform/resolvers
**Testing**: Vitest 4.0.18 + happy-dom
**Target Platform**: Browser (desktop 768px–1920px)
**Project Type**: Web application frontend (monorepo `solune/frontend/`)
**Build**: `npm run build` | **Test**: `npx vitest run` | **Lint**: `npm run lint` | **Type-check**: `npm run type-check`

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First Development** | ✅ PASS | `spec.md` exists with 6 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, and clear scope |
| **II. Template-Driven Workflow** | ✅ PASS | Follows canonical templates from `.specify/templates/` |
| **III. Agent-Orchestrated Execution** | ✅ PASS | Single-responsibility agent producing well-defined outputs |
| **IV. Test Optionality with Clarity** | ✅ PASS | Tests explicitly requested in US6 (P3) — SC-010 requires dedicated test coverage for useGlobalSettings hook and key sub-components |
| **V. Simplicity and DRY** | ✅ PASS | Audit fixes are minimal, focused changes. No premature abstraction |
| **Branch & Directory Naming** | ✅ PASS | `044-global-page-audit` follows `###-short-name` convention |
| **Phase-Based Execution** | ✅ PASS | Specify → Plan → Tasks → Implement → Analyze |
| **Independent User Stories** | ✅ PASS | Each story is independently testable and delivers standalone value |

**Gate Result**: ✅ ALL GATES PASS

## Project Structure

### Documentation (this feature)

```text
specs/044-global-page-audit/
├── plan.md              # This file
├── spec.md              # Feature specification with 6 user stories
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Task list (/speckit.tasks output)
```

### Source Code (audit scope)

```text
solune/frontend/src/
├── pages/
│   └── SettingsPage.tsx                    # 107 lines — top-level page (two sections: Primary + Advanced)
├── components/settings/
│   ├── GlobalSettings.tsx                  # 88 lines — instance-wide defaults container (react-hook-form + zod)
│   ├── SettingsSection.tsx                 # 100 lines — reusable collapsible section wrapper with save UI
│   ├── AISettingsSection.tsx               # 56 lines — AI settings form fields (provider, model, temperature)
│   ├── DisplaySettings.tsx                 # 55 lines — display settings (theme, default view, sidebar)
│   ├── WorkflowSettings.tsx                # 53 lines — workflow settings (repository, assignee, polling)
│   ├── NotificationSettings.tsx            # 58 lines — notification toggles (4 checkboxes)
│   ├── globalSettingsSchema.ts             # 83 lines — zod schema, flatten/toUpdate utilities, defaults
│   ├── AdvancedSettings.tsx                # 90 lines — advanced settings container
│   ├── PrimarySettings.tsx                 # 147 lines — primary settings (AI + Signal connection)
│   ├── DynamicDropdown.tsx                 # 262 lines — model selector with dynamic loading
│   ├── SettingsSection.test.tsx            # 114 lines — SettingsSection tests
│   └── DynamicDropdown.test.tsx            # 113 lines — DynamicDropdown tests
├── hooks/
│   └── useSettings.ts                      # 302 lines — useGlobalSettings, useUserSettings, useProjectSettings + signal hooks
├── services/
│   └── api.ts                              # settings API group (GET/PUT /settings/global, /settings/user, models)
├── types/
│   └── index.ts                            # GlobalSettings, GlobalSettingsUpdate, AIPreferences, etc.
└── lib/
    └── utils.ts                            # cn() helper for className merging
```

### Shared Components (reference, use as-is)

```text
solune/frontend/src/components/
├── ui/                                     # Button, Card, Input, Tooltip, ConfirmationDialog, HoverCard
└── common/                                 # CelestialLoader, ErrorBoundary, ProjectSelectionEmptyState
```

### Existing Test Coverage

```text
solune/frontend/src/
├── components/settings/SettingsSection.test.tsx   # 114 lines — save lifecycle, collapse, dirty state
├── components/settings/DynamicDropdown.test.tsx    # 113 lines — loading/error/success states
├── hooks/useSettingsForm.test.tsx                  # 103 lines — form state initialization, dirty tracking
└── lib/commands/handlers/settings.test.ts          # 221 lines — command handler tests
```

## Complexity Tracking

| File | Current Lines | Target | Action |
|------|--------------|--------|--------|
| SettingsPage.tsx | 107 | ≤250 | ✅ Already under limit |
| GlobalSettings.tsx | 88 | ≤250 | ✅ Already under limit — consider extracting AllowedModels |
| SettingsSection.tsx | 100 | ≤250 | ✅ Already under limit |
| useSettings.ts | 302 | ≤250 | ⚠️ 302 lines — may benefit from splitting Global vs Signal hooks |
| DynamicDropdown.tsx | 262 | ≤250 | ⚠️ 262 lines — slightly over, assess during audit |
| PrimarySettings.tsx | 147 | ≤250 | ✅ Already under limit |

## Key Architecture Patterns

### Form Management
1. **Schema** (`globalSettingsSchema.ts`): Zod validation with `flatten()` and `toUpdate()` transforms
2. **Hook** (`useSettings.ts`): TanStack Query for server state (`useGlobalSettings`)
3. **Container** (`GlobalSettings.tsx`): react-hook-form with zodResolver
4. **Sub-sections**: AISettingsSection, DisplaySettings, WorkflowSettings, NotificationSettings
5. **Wrapper** (`SettingsSection.tsx`): Reusable collapsible section with save/error/success UI

### Data Flow
```
API → useGlobalSettings() → GlobalSettings → flatten() → form fields
form fields → handleSubmit → toUpdate() → settingsApi.updateGlobalSettings()
save success → invalidate user settings cache
```

### Query Key Pattern
```typescript
settingsKeys = {
  all: ['settings'],
  global: () => [...settingsKeys.all, 'global'],
  user: () => [...settingsKeys.all, 'user'],
  project: (id) => [...settingsKeys.all, 'project', id],
  models: (provider) => [...settingsKeys.all, 'models', provider],
}
```

## Key Audit Findings (Pre-Assessment)

### Architecture (✅ Mostly Good)
- GlobalSettings.tsx at 88 lines — well under 250 limit
- Good component decomposition (5 sub-sections + schema + wrapper)
- "Allowed Models" input is inline in GlobalSettings.tsx (lines 69-84) — candidate for extraction
- useSettings.ts at 302 lines — includes signal hooks not related to Global Settings

### Data Fetching (✅ Good)
- All API calls use TanStack Query (no raw fetch)
- Query keys follow pattern conventions
- Cache invalidation on save (global → user settings)
- staleTime configured with constants (STALE_TIME_LONG, STALE_TIME_SHORT)

### States (⚠️ Needs Assessment)
- Loading: CelestialLoader used in SettingsPage — verify Global section specifically
- Error: SettingsSection has error display — verify rate limit detection
- Empty: Settings always have defaults — N/A for empty state
- Validation: react-hook-form + zod — verify inline error display

### Accessibility (⚠️ Needs Assessment)
- Form labels present — verify association and screen reader compatibility
- Temperature slider — verify aria-valuetext and keyboard control
- Collapsible section — verify aria-expanded attribute
- Dropdown selects — verify keyboard navigation

### Type Safety (✅ Good)
- No obvious `any` types in settings code
- Types defined in `src/types/index.ts`
- Zod schema provides runtime validation

### Test Coverage (⚠️ Gaps)
- SettingsSection: tested (114 lines)
- DynamicDropdown: tested (113 lines)
- useSettingsForm: tested (103 lines)
- **Missing**: useGlobalSettings hook tests, GlobalSettings component tests, sub-section component tests

## User Story Mapping

| Story | Priority | Primary Files | Key Changes |
|-------|----------|---------------|-------------|
| US1: Page States | P1 | SettingsPage.tsx, GlobalSettings.tsx, SettingsSection.tsx | Loading/error/validation states |
| US2: Accessibility | P1 | All settings components | ARIA, keyboard, focus management |
| US3: UX Polish | P2 | All settings components | Copy, design tokens, feedback |
| US4: Dirty State | P2 | GlobalSettings.tsx, SettingsSection.tsx, useSettings.ts | Dirty tracking, save guard |
| US5: Responsive | P2 | GlobalSettings.tsx, sub-sections | Breakpoint layout |
| US6: Code Quality | P3 | All files | Structure, types, lint, tests |
