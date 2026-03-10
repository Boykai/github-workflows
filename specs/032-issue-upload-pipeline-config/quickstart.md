# Quickstart: Projects Page — Upload GitHub Parent Issue Description & Select Agent Pipeline Config

**Feature**: 032-issue-upload-pipeline-config | **Date**: 2026-03-10

## Prerequisites

- Node.js 20+ and npm
- Python 3.13+
- The repository cloned and on the feature branch

```bash
git checkout 032-issue-upload-pipeline-config
```

## Setup

### Backend

```bash
cd backend
pip install -e ".[dev]"
# Database migrations run automatically on startup
uvicorn src.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# App available at http://localhost:5173
```

## New Files to Create

### New Frontend Files

| File | Purpose |
|------|---------|
| `frontend/src/components/board/ProjectIssueLaunchPanel.tsx` | NEW: Form component — textarea, file upload, pipeline selector, submit + validation |

### Files to Modify

| File | Changes |
|------|---------|
| `frontend/src/pages/ProjectsPage.tsx` | Import and render `ProjectIssueLaunchPanel` within the project content area |

### No Backend Changes Required

The backend already provides all necessary endpoints:

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/pipelines/{project_id}` | List available pipeline configs (populates dropdown) |
| `POST /api/v1/pipelines/{project_id}/launch` | Launch pipeline with issue description |
| `POST /api/v1/pipelines/{project_id}/seed-presets` | Seed default pipeline presets (already called on page load) |

## Implementation Order

### Phase 1: ProjectIssueLaunchPanel Component (FR-001–FR-008, FR-014)

1. **Create `ProjectIssueLaunchPanel.tsx`**
   - Define props interface: `projectId`, `pipelines`, `isLoadingPipelines`, `pipelinesError`, `onRetryPipelines`, `onLaunched`
   - Add state: `issueDescription`, `pipelineId`, `uploadedFileName`, `formErrors`, `submissionResult`, `submissionError`
   - Implement `launchMutation` using `useMutation` → `pipelinesApi.launch(projectId, { issue_description, pipeline_id })`
   - Build form layout: textarea, file upload button (hidden input), pipeline `<select>`, submit button
   - Style with existing Tailwind classes: `celestial-panel`, `moonwell`, `solar-action`

2. **Add validation handlers**
   - `handleIssueDescriptionChange`: real-time length validation, clear errors on valid input
   - `handlePipelineChange`: clear pipeline error on selection
   - `handleFileSelection`: validate extension, read file, populate textarea
   - `handleSubmit`: validate both fields, set errors, call `launchMutation.mutateAsync()`

3. **Add success/error display**
   - Success: show `Orbit` icon, issue title preview, issue URL link, "Launch another" reset
   - Error: show inline error message below submit button, preserve form state

**Verify**: Open the Projects page → the form renders with a textarea, file upload, pipeline dropdown, and submit button. Paste text → submit without selecting pipeline → see validation error. Select pipeline + paste text → submit → see loading state → see success confirmation with issue link.

### Phase 2: File Upload Support (FR-009, FR-010)

1. **Implement `isAcceptedIssueFile()` helper**
   - Check file extension against `ACCEPTED_FILE_EXTENSIONS` (`.md`, `.txt`)
   - Case-insensitive comparison

2. **Implement `handleFileSelection()`**
   - Validate file type → show error if unsupported
   - Read file via `File.text()` → validate length → populate textarea
   - Show uploaded filename label
   - Handle read errors gracefully

**Verify**: Upload a `.md` file → textarea populates with file content. Upload a `.jpg` → see inline error "Only Markdown (.md) and plain-text (.txt) files are supported."

### Phase 3: Pipeline Dropdown States (FR-011, FR-012, FR-013)

1. **Handle loading state**: Show "Loading pipeline configs…" in dropdown when `isLoadingPipelines` is true.
2. **Handle empty state**: Show "No pipeline configs available" when `pipelines` is empty.
3. **Handle error state**: Show error message with "Retry" button when `pipelinesError` is set.

**Verify**: Disconnect network → reload page → see error state with retry button. Click retry → pipelines load.

### Phase 4: ProjectsPage Integration

1. **Import `ProjectIssueLaunchPanel`** in `ProjectsPage.tsx`
2. **Pass props** from existing React Query data:
   - `projectId={selectedProjectId}`
   - `pipelines={savedPipelines?.pipelines ?? []}`
   - `isLoadingPipelines={savedPipelinesLoading}`
   - `onLaunched` callback to invalidate board queries
3. **Position** the panel in the project content area

**Verify**: Navigate to Projects page → select a project → see the launch panel. Submit a form → board refreshes with the new issue.

## Testing Strategy

No new test files required unless explicitly requested. Existing tests should continue to pass:

```bash
# Backend
cd backend && uv run --extra dev pytest tests/unit/ -x

# Frontend
cd frontend && npm run test

# Frontend lint + type check
cd frontend && npm run lint && npm run type-check
```

Manual verification covers all acceptance scenarios in the spec.

## Key Architecture Decisions

1. **Reuse existing `POST /launch` endpoint** — zero backend changes needed; the endpoint already handles the full pipeline execution flow
2. **Self-contained component** — `ProjectIssueLaunchPanel` manages all form state internally via `useState`; parent only passes data and callbacks
3. **Native HTML `<select>`** — no custom dropdown library; built-in accessibility and keyboard navigation
4. **Client-side file reading** — `File.text()` reads files into the textarea; no server-side file storage
5. **TanStack Query for data** — pipeline list uses existing `useQuery` in `ProjectsPage`; launch uses `useMutation` in the panel
6. **Real-time validation** — errors clear on field change; form state preserved on failure; submit button disabled during mutation
