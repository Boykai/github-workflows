# Frontend Component Contracts: Debug & Fix Apps Page — New App Creation UX

**Feature**: `051-fix-app-creation-ux` | **Date**: 2026-03-17

## Modified Components

### AppsPage.tsx — Create App Dialog

**File**: `apps/solune/frontend/src/pages/AppsPage.tsx`

#### New UI Elements

**Pipeline Selector Dropdown**:
- Position: After the "Create Project" checkbox, before Azure credentials section
- Visibility: Always visible in the create dialog (for all repo types)
- Data source: Fetch pipelines from current Solune project via `['pipelines', projectId]` query
- Default: "None" (no pipeline selected)
- Payload: `pipeline_id` sent in `AppCreate` when non-null

```tsx
// Pseudo-component structure
<label>Pipeline (optional)</label>
<select value={pipelineId} onChange={setPipelineId}>
  <option value="">None</option>
  {pipelines.map(p => (
    <option key={p.id} value={p.id}>{p.name}</option>
  ))}
</select>
```

#### Modified: Warning Display

**Before**:
```tsx
if (createdApp.warnings?.length) {
  showError(createdApp.warnings[0]);
}
```

**After**:
```tsx
if (createdApp.warnings?.length) {
  createdApp.warnings.forEach(warning => {
    showWarning(warning);  // or showSuccess with ⚠ prefix if no showWarning exists
  });
}
```

#### New: Structured Success Toast

**After successful creation**:
```
✓ Repository created
✓ Template files committed
✓ Pipeline started           (only if pipeline_id was provided)
⚠ {warning1}                 (for each warning)
⚠ {warning2}
```

Implementation: Single toast with multi-line content, or sequential toasts depending on the existing toast system capabilities.

---

### AppDetailView.tsx — Parent Issue & Pipeline Info

**File**: `apps/solune/frontend/src/components/apps/AppDetailView.tsx`

#### New UI Elements

**Parent Issue Link** (conditionally rendered):
- Position: In the GitHub links section, after existing repo/project links
- Condition: Only shown when `app.parent_issue_url` is non-null
- Behavior: External link, opens in new tab

```tsx
{app.parent_issue_url && (
  <a href={app.parent_issue_url} target="_blank" rel="noopener noreferrer">
    Parent Issue #{app.parent_issue_number}
  </a>
)}
```

**Pipeline Name Display** (conditionally rendered):
- Position: In the info grid, after Repo Type
- Condition: Only shown when `app.associated_pipeline_id` is non-null
- Content: Pipeline name (requires fetching pipeline config by ID) or fallback to pipeline ID

```tsx
{app.associated_pipeline_id && (
  <div>
    <dt>Pipeline</dt>
    <dd>{pipelineName || app.associated_pipeline_id}</dd>
  </div>
)}
```

#### Backward Compatibility

- Apps without `parent_issue_url` (null): Parent Issue section is not rendered
- Apps without `associated_pipeline_id` (null): Pipeline section is not rendered
- No errors thrown for missing data

---

### AppCard.tsx — Pipeline Status Badge

**File**: `apps/solune/frontend/src/components/apps/AppCard.tsx`

#### New UI Element

**Pipeline Badge** (conditionally rendered):
- Position: In the header row, after the status badge
- Condition: Only shown when `app.parent_issue_number` is non-null (indicates active pipeline)
- Style: Small pill badge, purple/indigo color to match pipeline theming

```tsx
{app.parent_issue_number && (
  <span className="inline-flex items-center rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700">
    Pipeline
  </span>
)}
```

#### Backward Compatibility

- Apps without pipeline: No badge shown, layout unchanged
- Badge takes minimal space and doesn't affect card height

---

### apps.ts — Type Extension

**File**: `apps/solune/frontend/src/types/apps.ts`

#### Modified Interface

```typescript
export interface App {
  // ... existing fields unchanged ...
  github_project_id: string | null;
  parent_issue_number: number | null;   // NEW
  parent_issue_url: string | null;      // NEW
  port: number | null;
  // ... rest unchanged ...
}
```

**Insertion point**: After `github_project_id`, before `port` — groups all GitHub-related fields together.

---

## New State / Hooks

### Create Dialog State

```typescript
// New state in AppsPage.tsx
const [pipelineId, setPipelineId] = useState<string>('');

// Reset on dialog close
const closeCreateDialog = () => {
  // ... existing resets ...
  setPipelineId('');
};

// Include in payload
const payload: AppCreate = {
  // ... existing fields ...
  pipeline_id: pipelineId || undefined,
};
```

### Pipeline Data Query

```typescript
// Fetch available pipelines for the dropdown
// Uses existing query key pattern from usePipelineConfig
const { data: pipelines } = useQuery({
  queryKey: ['pipelines', projectId],
  queryFn: () => pipelinesApi.list(projectId),
  enabled: !!projectId,
});
```

---

## Interaction Flows

### Create App with Pipeline

```
User opens Create App dialog
  → User fills in name, description, repo settings
  → User selects a pipeline from dropdown (optional)
  → User clicks "Create"
  → POST /apps with pipeline_id in payload
  → Backend: creates repo → commits files → creates parent issue → creates sub-issues → starts polling
  → Frontend: receives response with warnings[]
  → Frontend: shows structured success toast
  → Frontend: shows all warnings as warning-style toasts
  → Frontend: navigates to app detail view
  → App detail view: shows parent issue link and pipeline info
```

### View App with Pipeline (existing app)

```
User navigates to Apps list
  → AppCard shows pipeline badge for apps with parent_issue_number
  → User clicks on app card
  → AppDetailView shows parent issue link and pipeline name
  → User clicks parent issue link → opens GitHub in new tab
```

### Delete App with Pipeline

```
User clicks Delete on app
  → Confirmation dialog shown
  → User confirms
  → DELETE /apps/{name}
  → Backend: closes parent issue (best-effort) → deletes app record
  → Frontend: refreshes app list
```

---

## Test Contracts

### Backend Tests (`test_app_service_new_repo.py`)

| Test | Validates |
|------|-----------|
| `test_create_app_with_pipeline_creates_parent_issue` | FR-007: Parent issue created when pipeline_id provided |
| `test_create_app_without_pipeline_skips_parent_issue` | FR-010: No parent issue when pipeline_id is None |
| `test_create_app_parent_issue_failure_adds_warning` | FR-010: Best-effort — warning on failure |
| `test_create_app_template_warnings_propagated` | FR-004: Template file warnings in response |
| `test_branch_readiness_exponential_backoff` | FR-003: Retry with exponential backoff |
| `test_delete_app_closes_parent_issue` | FR-020: Parent issue closed on delete |

### Frontend Tests (`AppsPage.test.tsx`)

| Test | Validates |
|------|-----------|
| `test_pipeline_selector_visible_in_create_dialog` | FR-012: Dropdown rendered |
| `test_pipeline_selector_defaults_to_none` | FR-013: Default is "None" |
| `test_pipeline_id_sent_in_payload` | FR-012: pipeline_id in create request |
| `test_all_warnings_displayed` | FR-014: All warnings shown |
| `test_warning_style_not_error_style` | FR-015: Warning toast style |
| `test_success_summary_toast` | FR-016: Structured success feedback |

### Frontend Tests (Component tests)

| Test | Validates |
|------|-----------|
| `test_app_detail_shows_parent_issue_link` | FR-017: Clickable parent issue link |
| `test_app_detail_no_parent_issue_renders_clean` | FR-019: Backward compatibility |
| `test_app_card_shows_pipeline_badge` | FR-018: Pipeline badge on card |
| `test_app_card_no_pipeline_no_badge` | FR-019: No badge for legacy apps |
