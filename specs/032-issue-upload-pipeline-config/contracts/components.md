# Component Contracts: Projects Page — Upload GitHub Parent Issue Description & Select Agent Pipeline Config

**Feature**: 032-issue-upload-pipeline-config | **Date**: 2026-03-10

## New Components

### ProjectIssueLaunchPanel

**Location**: `frontend/src/components/board/ProjectIssueLaunchPanel.tsx`
**Purpose**: Self-contained form component for uploading a GitHub Parent Issue description and selecting an Agent Pipeline Config, then launching the pipeline.

```typescript
interface ProjectIssueLaunchPanelProps {
  projectId: string;
  projectName?: string;
  pipelines: PipelineConfigSummary[];
  isLoadingPipelines: boolean;
  pipelinesError?: string | null;
  onRetryPipelines: () => void;
  onLaunched?: (result: WorkflowResult) => void;
}
```

**Behavior**:

- **Issue Description Input** (FR-001, FR-003, FR-015):
  - Multi-line `<textarea>` with `id` from `useId()` for accessibility.
  - Placeholder text guides user to paste a GitHub issue description.
  - Real-time validation: clears error on valid input, shows error on exceeding `MAX_ISSUE_DESCRIPTION_LENGTH` (65,536 chars).
  - Character count not displayed (simple enough to not need one).
  - `rows={10}` default height, resizable.

- **File Upload** (FR-009, FR-010):
  - Hidden `<input type="file" accept=".md,.txt">` triggered by an upload button.
  - `isAcceptedIssueFile()` validates extensions (`.md`, `.txt` only).
  - Reads file content via `File.text()` and populates the textarea.
  - Shows uploaded filename as a label after successful upload.
  - Shows inline error for unsupported file types or read failures.
  - Max file size: implicitly limited by `MAX_ISSUE_DESCRIPTION_LENGTH`.

- **Pipeline Config Selector** (FR-002, FR-011, FR-012, FR-013):
  - Native `<select>` element with `id` from `useId()`.
  - Default option: "— Select a pipeline config —" (disabled, acts as placeholder).
  - Options populated from `pipelines` prop (maps `id` → `name`).
  - Loading state: shows "Loading pipeline configs…" when `isLoadingPipelines` is true.
  - Error state: shows error message with a "Retry" button when `pipelinesError` is set.
  - Empty state: shows "No pipeline configs available" when `pipelines` is empty and not loading.
  - `onChange` clears any pipeline selection error.
  - Styled with `moonwell` Tailwind class for dark theme consistency.

- **Submit Button** (FR-005, FR-008):
  - Button text: "Launch Pipeline" with `FileUp` icon (lucide-react).
  - Disabled when: (a) `launchMutation.isPending`, (b) no pipeline selected (`!pipelineId`).
  - Loading state: shows `LoaderCircle` spinning animation during submission.
  - Styled with `solar-action` class for primary action appearance.

- **Validation** (FR-003, FR-004, FR-007):
  - On submit, validates both fields. Sets `formErrors` for each invalid field.
  - Error messages appear below each field with `text-destructive` styling and `TriangleAlert` icon.
  - Errors clear individually when the user corrects the field (real-time on change).
  - Form state is fully preserved on validation or submission error (FR-007).

- **Success State** (FR-006):
  - On successful launch, replaces form with a confirmation display.
  - Shows `Orbit` icon with animation, issue title preview, issue URL link, and issue number.
  - "Launch another" action resets the form for a new submission.
  - Calls `onLaunched(result)` callback for parent to refresh the board.

- **Error State** (submission failure):
  - Shows inline error message with `TriangleAlert` icon below the submit button.
  - Form fields remain populated for retry (FR-007).

**Accessibility**:

- All form fields have associated `<label>` elements linked via `htmlFor`/`id`.
- Error messages are adjacent to their fields for screen reader proximity.
- Submit button uses semantic `<button>` with clear text.
- File input has an `aria-label` describing the expected file types.

**Styling**:

- Uses `celestial-panel` class for the outer container (backdrop blur, gradient border).
- Form fields use standard Tailwind utility classes consistent with existing forms.
- `<select>` uses `moonwell` class for dark background compatibility.
- Spacing follows the `space-y-4` and `gap-3` patterns used in other form sections.

---

## Modified Components

### ProjectsPage (Modified)

**Location**: `frontend/src/pages/ProjectsPage.tsx`
**Purpose**: Main Projects page container. Extended to render `ProjectIssueLaunchPanel`.

**Changes**:

- Import `ProjectIssueLaunchPanel` from `@/components/board/ProjectIssueLaunchPanel`.
- Pass pipeline data from existing React Query:
  - `pipelines={savedPipelines?.pipelines ?? []}`
  - `isLoadingPipelines={savedPipelinesLoading}`
  - `pipelinesError` from query error state
  - `onRetryPipelines` wired to React Query refetch
- Pass `onLaunched` callback that invalidates board queries to refresh the Kanban view.
- Position: rendered as a dedicated section within the project content area, above or alongside the project board.

**Existing Queries Used** (no new queries needed):

```typescript
// Already exists in ProjectsPage
const { data: savedPipelines, isLoading: savedPipelinesLoading } = useQuery({
  queryKey: ['pipelines', selectedProjectId],
  queryFn: () => pipelinesApi.list(selectedProjectId!),
  enabled: !!selectedProjectId,
  staleTime: 60_000,
});
```

---

## Internal Helper Functions

### deriveIssueTitlePreview

**Location**: `frontend/src/components/board/ProjectIssueLaunchPanel.tsx` (module-level)
**Purpose**: Extracts a short preview title from the issue description for the success state display.

```typescript
function deriveIssueTitlePreview(issueDescription: string): string;
```

**Behavior**:

- Attempts to extract a Markdown heading (`# Title`) from the description.
- Falls back to the first non-empty line.
- Strips Markdown prefix characters (`>`, `-`, `*`, `#`, etc.).
- Truncates to `MAX_PREVIEW_TITLE_LENGTH` (120 chars) with `…` suffix.

### isAcceptedIssueFile

**Location**: `frontend/src/components/board/ProjectIssueLaunchPanel.tsx` (module-level)
**Purpose**: Validates that a file has an accepted extension for upload.

```typescript
function isAcceptedIssueFile(file: File): boolean;
```

**Behavior**:

- Checks file name against `ACCEPTED_FILE_EXTENSIONS` (`.md`, `.txt`).
- Case-insensitive comparison.
- Returns `true` if the file extension matches, `false` otherwise.

---

## Constants

| Constant | Value | Purpose |
|----------|-------|---------|
| `MAX_ISSUE_DESCRIPTION_LENGTH` | `65_536` | Frontend validation limit for textarea content |
| `MAX_PREVIEW_TITLE_LENGTH` | `120` | Maximum length for issue title preview in success state |
| `ACCEPTED_FILE_EXTENSIONS` | `['.md', '.txt']` | Allowed file types for upload |
| `GITHUB_ISSUE_BODY_MAX_LENGTH` | `65_535` | Backend validation limit for GitHub issue body (from `src/constants.py`) |
