# Data Model: Celestial Loading Progress Ring

**Feature**: 002-celestial-progress-ring  
**Date**: 2026-03-27

---

## Entities

### Phase

Represents a single stage in the loading sequence. Phases are ordered; the active phase label shown to the user is the first incomplete phase.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `label` | `string` | Human-readable description of what is loading (e.g., "Connecting to GitHub…") | Non-empty; should include trailing ellipsis per convention |
| `complete` | `boolean` | Whether this phase's data source has resolved | `true` when the corresponding hook's loading state is `false` (or data is truthy) |

```typescript
interface Phase {
  label: string;
  complete: boolean;
}
```

**Validation rules**:
- `phases` array must have at least 1 element (empty array treated as 100% complete or no-render)
- `label` must be non-empty string
- Order matters: labels are displayed based on position in the array

---

### Progress State (Computed)

The visual fill level of the ring, computed from two sources. This is not a persisted entity but a derived value inside the component.

| Field | Type | Description | Range |
|-------|------|-------------|-------|
| `minProgress` | `number` | Time-based floor that starts at 0 and increments to ~0.15 over 3s, capping at ~0.30 | `[0, 0.30]` |
| `realProgress` | `number` | Ratio of completed phases to total phases | `[0, 1.0]` |
| `displayProgress` | `number` | The value actually rendered: `max(minProgress, realProgress)` | `[0, 1.0]` |

**Computation**:
```typescript
const completedCount = phases.filter(p => p.complete).length;
const realProgress = phases.length > 0 ? completedCount / phases.length : 1;
const displayProgress = Math.max(minProgress, realProgress);
```

**State transitions**:
```
mount → minProgress = 0, realProgress = 0 → displayProgress = 0
  ↓ (100ms intervals)
~3s → minProgress ≈ 0.15, realProgress = 0 → displayProgress ≈ 0.15
  ↓ (continues slowly)
~10s → minProgress ≈ 0.30 (capped), realProgress = 0 → displayProgress = 0.30
  ↓ (phase 1 completes)
phase complete → minProgress = 0.30, realProgress = 0.25 → displayProgress = 0.30 (min wins)
  ↓ (phase 2 completes)
phase complete → minProgress = 0.30, realProgress = 0.50 → displayProgress = 0.50 (real wins)
  ↓ (all phases complete)
all done → minProgress = 0.30, realProgress = 1.0 → displayProgress = 1.0
```

---

### Current Phase Label (Computed)

The text displayed below the ring, derived from the phases array.

**Computation**:
```typescript
const currentPhaseLabel = phases.find(p => !p.complete)?.label
  ?? phases[phases.length - 1]?.label
  ?? '';
```

**Rules**:
- Shows the label of the **first incomplete** phase
- When all phases are complete, shows the **last** phase label (briefly, before unmounting)
- Empty array fallback: empty string (component may not render)

---

## Relationships

```
CelestialLoadingProgress (component)
  ├── phases: Phase[]           (input prop)
  ├── minProgress: number       (internal state, useEffect timer)
  ├── realProgress: number      (derived from phases)
  ├── displayProgress: number   (derived: max of above two)
  ├── currentPhaseLabel: string (derived from phases)
  └── embeds: CelestialLoader   (existing component, unmodified)
```

---

## Page-Specific Phase Definitions

### ProjectsPage

| # | Label | Completes when | Source hook |
|---|-------|---------------|-------------|
| 1 | "Connecting to GitHub…" | `!projectsLoading` | `useProjectBoard().projectsLoading` |
| 2 | "Loading project board…" | `!boardLoading` | `useProjectBoard().boardLoading` |
| 3 | "Loading pipelines…" | `!savedPipelinesLoading` | `useQuery(['pipelines', ...]).isLoading` |
| 4 | "Loading agents…" | `!!agents.length` or `!agentsLoading` | `useAvailableAgents().agents` |

### AgentsPipelinePage

| # | Label | Completes when | Source hook |
|---|-------|---------------|-------------|
| 1 | "Connecting to GitHub…" | `!projectsLoading` | `useProjects().isLoading` |
| 2 | "Loading board data…" | `!boardLoading` | `useProjectBoard().boardLoading` |
| 3 | "Loading agents…" | `!agentsLoading` | `useAvailableAgents().isLoading` |

### SettingsPage

| # | Label | Completes when | Source hook |
|---|-------|---------------|-------------|
| 1 | "Loading user settings…" | `!userLoading` | `useUserSettings().isLoading` |
| 2 | "Loading global settings…" | `!globalLoading` | `useGlobalSettings().isLoading` |
