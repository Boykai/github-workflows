# Research: Projects Page — Upload GitHub Parent Issue Description & Select Agent Pipeline Config

**Feature**: 032-issue-upload-pipeline-config | **Date**: 2026-03-10

## R1: Input Mechanism — Textarea vs Rich Editor vs Dedicated Upload Page

**Task**: Determine the optimal input mechanism for the GitHub Parent Issue description on the Projects page.

**Decision**: Multi-line `<textarea>` with an adjacent file upload button. The textarea serves as the primary input for paste, while a hidden `<input type="file">` triggered by a button allows `.md` and `.txt` file uploads. File content is read client-side via `File.text()` and placed into the textarea so the user can review and edit before submission.

**Rationale**: A plain textarea is the simplest solution that satisfies FR-001 (paste input) and FR-009 (file upload). GitHub issue descriptions are Markdown text — no WYSIWYG editing is needed since the user is pasting pre-written content, not authoring new content. The textarea preserves formatting and allows quick edits. The file upload is purely a convenience to avoid copy-paste for users who have the description saved locally. Client-side file reading avoids unnecessary server round-trips (the file content is just text). This matches existing patterns in the codebase — `AddAgentModal` uses a textarea for system prompts (up to 30KB), and `AddChoreModal` uses a textarea for chore templates.

**Alternatives Considered**:

- **Rich Markdown editor (e.g., Monaco, CodeMirror)**: Rejected — heavyweight dependency for a paste-and-submit workflow. Users are pasting existing content, not authoring. Adding a Markdown editor would violate Principle V (Simplicity/DRY) and the "no new libraries" constraint.
- **Dedicated upload page/modal**: Rejected — the spec requires the input to be "on the Projects page" as a cohesive form section. A separate page adds navigation overhead. A modal is viable but unnecessary since the form fits naturally into the existing page layout.
- **Drag-and-drop file zone**: Considered as a Phase 2 enhancement but rejected for MVP. The file input button covers FR-009 with minimal UI complexity. Drag-and-drop would require additional event handlers and visual feedback that aren't in the spec's MUST requirements.

---

## R2: Pipeline Config Selector — Native Select vs Custom Dropdown

**Task**: Determine the UI component for selecting an Agent Pipeline Config from available configurations.

**Decision**: Native HTML `<select>` element styled with Tailwind CSS (`moonwell` class for dark theme compatibility). The select is populated from the `pipelinesApi.list()` response, which is already fetched by `ProjectsPage` via TanStack Query with a 60-second staleTime.

**Rationale**: A native `<select>` provides built-in keyboard navigation, screen reader support, and focus management with zero additional code. The pipeline list is typically small (< 20 items), so a simple dropdown is sufficient — no search/filter or virtualization needed. The existing codebase uses native `<select>` elements in similar contexts (e.g., project selector dropdowns, sort-order selectors). This approach avoids adding a custom dropdown component or library, keeping the bundle size stable and following Principle V.

**Alternatives Considered**:

- **Custom `Combobox` component (e.g., Headless UI, Radix)**: Rejected — the project doesn't use Headless UI or Radix. Building a custom combobox from scratch is significant effort for a list of < 20 items. Would violate the "no new libraries" constraint.
- **Radio button group / card selector**: Considered for visual richness (showing pipeline descriptions alongside names) but rejected — takes more vertical space, less standard for selection from a list, and the spec explicitly suggests "dropdown or similar."
- **`PipelineSelector` component from chores**: The existing `PipelineSelector` in `components/chores/` is tightly coupled to the chore creation flow. Extracting it into a shared component is a valid future refactor but not required for this feature (YAGNI). The launch panel's inline `<select>` is simpler and self-contained.

---

## R3: Form Validation Strategy — Client-Side vs Server-Side

**Task**: Determine the validation strategy for the issue description and pipeline config fields.

**Decision**: Client-side validation with real-time feedback, complemented by server-side validation as a safety net. Client-side validation runs on blur and on submit, checking: (1) issue description is non-empty and non-whitespace, (2) issue description length ≤ 65,536 characters, (3) a pipeline config is selected. Error messages appear inline below each field. The server-side `POST /launch` endpoint independently validates the `PipelineIssueLaunchRequest` body (Pydantic `min_length=1` on `issue_description`, `min_length=1` on `pipeline_id`) and the issue body length against `GITHUB_ISSUE_BODY_MAX_LENGTH`.

**Rationale**: Client-side validation provides instant feedback (FR-003, FR-004) and prevents unnecessary API calls. Server-side validation catches any bypasses (e.g., direct API calls, race conditions). The dual approach is standard web practice. Real-time validation on change (clearing errors when the user types) satisfies FR-007 (error messages clear when input corrected). Preserving form state on error satisfies FR-007 (no data loss on failed submission). The `useMutation` hook's error handling naturally preserves form state since the form fields are controlled React state.

**Alternatives Considered**:

- **Server-side only validation**: Rejected — would delay feedback until after a round-trip. The spec says "inline validation feedback" which implies immediate client-side responses.
- **Form library (React Hook Form, Formik)**: Rejected — the form has only 2 fields (textarea + select). A form library adds complexity without proportional value. Simple `useState` for each field plus a `formErrors` object is the established pattern in the codebase (see `ProjectIssueLaunchPanel`, `AddAgentModal`, `AddChoreModal`).
- **Schema validation (Zod, Yup)**: Rejected — overkill for 2 fields with straightforward rules. The validation logic is 10 lines of inline code.

---

## R4: Pipeline Launch Flow — Existing Endpoint Reuse

**Task**: Determine how the form submission should trigger the agent pipeline execution.

**Decision**: Reuse the existing `POST /pipelines/{projectId}/launch` endpoint, which accepts a `PipelineIssueLaunchRequest` body (`{ issue_description: string, pipeline_id: string }`) and returns a `WorkflowResult`. The frontend calls `pipelinesApi.launch(projectId, { issue_description, pipeline_id })` via a TanStack Query `useMutation`. On success, the component displays a confirmation state with the issue URL and number. The parent `ProjectsPage` receives an `onLaunched` callback to refresh the board.

**Rationale**: The `POST /launch` endpoint already implements the complete pipeline execution flow: (1) normalize and validate the issue description, (2) resolve the GitHub repository, (3) fetch the pipeline config, (4) set the pipeline assignment, (5) prepare the workflow configuration (convert pipeline stages to agent mappings), (6) create the GitHub issue, (7) add to the project board, (8) create per-agent sub-issues, (9) enqueue for blocking if needed. There is zero backend work to do — the endpoint handles every functional requirement from FR-005 (association and downstream dispatch) through the full orchestration chain. Creating a new endpoint would duplicate this logic entirely.

**Alternatives Considered**:

- **New dedicated endpoint**: Rejected — the existing `POST /launch` endpoint does exactly what's needed. A new endpoint would violate DRY and require duplicating the entire orchestration flow.
- **Two-step flow (create issue, then assign pipeline)**: Rejected — the spec requires a single-action submission. Splitting into two steps introduces partial-failure states and a worse UX.
- **WebSocket-based launch with real-time progress**: Considered for showing sub-issue creation progress but rejected for MVP. The `WorkflowResult` response provides sufficient feedback. Real-time progress could be a Phase 2 enhancement.

---

## R5: Success State — Confirmation Display vs Navigation Redirect

**Task**: Determine the user experience after a successful pipeline launch.

**Decision**: Display an inline success confirmation state within the form area, showing the created issue number, URL (as a clickable link), and the current status. The form fields are replaced by the confirmation message. The user can dismiss the confirmation to start a new submission. The parent `ProjectsPage` receives the `onLaunched` callback to refresh the project board (via React Query cache invalidation), so the new issue appears on the board in the background.

**Rationale**: An inline confirmation is less disruptive than a page redirect — the user stays on the Projects page and can immediately see the issue on the board. The spec says "display a success confirmation state **or** navigate the user" — the inline confirmation satisfies the first option and is simpler. Navigation to a separate "agent run view" would require building a new page that doesn't exist yet (YAGNI). The board refresh provides the "relevant project view" aspect of FR-006. This matches the existing pattern in `ProjectIssueLaunchPanel` where the success state shows an `Orbit` icon animation, the issue title, issue URL link, and a "Launch another" reset action.

**Alternatives Considered**:

- **Redirect to issue detail page**: Rejected — would require a router navigation and the user would lose context of the board. The inline confirmation + board refresh provides all the feedback needed.
- **Toast notification only**: Rejected — too transient. The user might miss it, especially if the launch takes a few seconds. An inline confirmation is persistent until dismissed.
- **Modal success dialog**: Rejected — modals are heavier than needed for a simple success message. The inline state change within the form area is sufficient and less disruptive.
