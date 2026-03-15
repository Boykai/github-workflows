# Data Model: Onboarding Spotlight Tour & Help/FAQ Page

**Feature**: `042-onboarding-help-faq` | **Date**: 2026-03-15

## Entities

### TourStep

A single step in the onboarding spotlight tour. Immutable configuration — defined at build time, not user-editable.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `number` | Sequential step number (1–9) |
| `targetSelector` | `string \| null` | Value of `data-tour-step` attribute on target element. `null` for centered welcome step (no element highlight). |
| `title` | `string` | Short heading displayed in tooltip (e.g., "Welcome to Solune") |
| `description` | `string` | Explanatory body text (1–2 sentences) |
| `icon` | `React.ComponentType` | SVG icon component rendered in tooltip |
| `placement` | `'top' \| 'bottom' \| 'left' \| 'right'` | Preferred tooltip position relative to target element |

**Constraints**:
- `id` is unique and sequential within the step array
- `targetSelector` must match a `data-tour-step` attribute in the rendered DOM (or be `null` for step 1)
- Step definitions are static — no CRUD operations

---

### TourState

The user's runtime progress through the tour. Ephemeral React state with one persisted flag.

| Field | Type | Persisted | Description |
|-------|------|-----------|-------------|
| `isActive` | `boolean` | No | Whether the tour overlay is currently displayed |
| `currentStep` | `number` | No | Index into the steps array (0-based) |
| `hasCompleted` | `boolean` | Yes (localStorage) | Whether the user has finished or skipped the tour |

**Persistence**:
- `hasCompleted` stored as `localStorage.getItem('solune-onboarding-completed') === 'true'`
- `isActive` and `currentStep` are ephemeral — reset on page refresh

**State Transitions**:
```
[First Visit] → isActive: true, currentStep: 0
  → "Next" → currentStep + 1
  → "Back" → currentStep - 1
  → "Skip" / "Escape" → isActive: false, hasCompleted: true
  → Last step "Done" → isActive: false, hasCompleted: true
[Return Visit] → isActive: false (hasCompleted: true)
[Replay from Help] → isActive: true, currentStep: 0 (hasCompleted remains true)
```

---

### FaqEntry

A question-and-answer pair for the Help page FAQ section.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique identifier (e.g., `"getting-started-1"`) |
| `question` | `string` | The question text displayed as the accordion header |
| `answer` | `string` | The answer text displayed when expanded (supports inline markup) |
| `category` | `FaqCategory` | Grouping for visual sections |

**FaqCategory values**: `'getting-started'` | `'agents-pipelines'` | `'chat-voice'` | `'settings-integration'`

**Constraints**:
- `id` is unique across all entries
- Content is hardcoded in `FaqAccordion.tsx` (not fetched from API)
- 12 entries total: 3 per category

---

### FeatureGuide

A summary card for the Help page feature guide grid.

| Field | Type | Description |
|-------|------|-------------|
| `title` | `string` | Feature name (e.g., "Projects") |
| `description` | `string` | One-sentence summary |
| `icon` | `React.ComponentType` | Lucide icon component |
| `href` | `string` | Route path to navigate to (e.g., `"/projects"`) |

**Constraints**:
- One guide per major application area (8 total: App, Projects, Pipelines, Agents, Tools, Chores, Apps, Settings)
- Content is hardcoded in `HelpPage.tsx`

---

### CommandReference

Read from the existing command registry. No new data model — consumed via `getAllCommands()` from `@/lib/commands/registry`.

| Field | Type | Source |
|-------|------|--------|
| `name` | `string` | `CommandDefinition.name` |
| `description` | `string` | `CommandDefinition.description` |
| `syntax` | `string` | `CommandDefinition.syntax` |

---

## Relationships

```
SpotlightTour
  ├── contains → TourStep[] (9 static steps)
  ├── manages → TourState (via useOnboarding hook)
  └── renders → SpotlightOverlay + SpotlightTooltip + TourProgress

HelpPage
  ├── contains → FaqEntry[] (12 static entries grouped by FaqCategory)
  ├── contains → FeatureGuide[] (8 static guides)
  ├── reads → CommandReference[] (via getAllCommands())
  └── triggers → TourState.restart() (Replay Tour button)
```

## Storage Schema

No database tables. No API endpoints. All data is either:
1. **Static configuration** — hardcoded TypeScript arrays (tour steps, FAQ entries, feature guides)
2. **Client-side state** — single localStorage key (`solune-onboarding-completed`) + ephemeral React state
