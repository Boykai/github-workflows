# Research: @ Mention in Chat to Select Agent Pipeline Configuration

**Feature**: 030-at-mention-pipeline | **Date**: 2026-03-08

## R1: Input Component Strategy for Inline Mention Tokens

**Task**: Determine how to support visually distinct @mention tokens (chips/tags) inline within the chat input, given that the current input is a plain HTML `<textarea>` that cannot render styled HTML.

**Decision**: Replace the `<textarea>` with a `contentEditable` `<div>` wrapped in a thin `MentionInput` component. Mention tokens are rendered as non-editable `<span>` elements (with `contentEditable="false"`) inside the editable div, carrying `data-pipeline-id` and `data-pipeline-name` attributes. Plain text around tokens remains directly editable.

**Rationale**:

- The spec requires visually distinct inline tokens (FR-004) — a `<textarea>` cannot render HTML.
- A `contentEditable` div is the minimal step above a textarea that supports inline styled elements without adding a third-party rich-text editor.
- The existing `ChatInterface` already manages input state as a string; the migration requires extracting text content (with token placeholders) from the div's DOM on change and on submit.
- The `contentEditable="false"` attribute on token spans makes them behave as atomic units — backspace deletes the entire token (FR-011) and cursor movement treats them as single characters.

**Alternatives Considered**:

- **Keep `<textarea>` with visual overlay**: Rejected — maintaining synchronization between textarea text and an overlay of positioned token chips is fragile, breaks on resize, and does not satisfy "inline" requirement (FR-004).
- **Full rich-text editor (Tiptap, Slate, ProseMirror)**: Rejected — adds significant bundle size and complexity for a feature that only needs plain text + atomic inline nodes. Violates Constitution Principle V (Simplicity/DRY). YAGNI.
- **Hidden input + visual div approach**: Rejected — two sources of truth, complex focus and selection management, poor accessibility.

---

## R2: @mention Trigger Detection and Autocomplete Activation

**Task**: Determine when and how to trigger the autocomplete dropdown when the user types "@" in the chat input, avoiding false positives on email addresses and other "@" usages.

**Decision**: Trigger the autocomplete when "@" is typed and the character immediately before it is a space, newline, or the "@" is at the start of the input (position 0). This matches the spec edge case: "The autocomplete should only trigger when '@' is preceded by a space, newline, or is at the start of the input." After trigger, capture all subsequent characters until a space, newline, or Escape to build the filter query.

**Rationale**:

- The spec explicitly defines the trigger condition in Edge Cases (line 96): preceded by space, newline, or start of input.
- This avoids false triggers on `email@domain.com` patterns (Edge Case line 96).
- The same pattern is used by GitHub's own @mention system and most chat/collaboration tools.
- Implementation: on every input change, inspect the text before the cursor. If the last word starts with "@" and meets the trigger condition, activate the autocomplete with the substring after "@" as the filter query.

**Alternatives Considered**:

- **Trigger on any "@" character**: Rejected — would fire on email addresses, causing confusion (spec edge case).
- **Require a double-tap ("@@") to trigger**: Rejected — non-standard UX, not in spec.
- **Only trigger via a toolbar button**: Rejected — spec requires typing "@" as the trigger (FR-001).

---

## R3: Autocomplete Data Source and Caching Strategy

**Task**: Determine how to fetch and cache the pipeline list for the autocomplete dropdown, ensuring responsive filtering (< 300ms per keystroke per SC-002).

**Decision**: Use the existing `pipelinesApi.list(projectId)` endpoint, cached with TanStack Query (`queryKey: ['pipelines', projectId]`, `staleTime: 30_000`). Filter results client-side using case-insensitive substring matching on `pipeline.name`. Debounce the filter operation at 150ms for rapid keystrokes (FR-017).

**Rationale**:

- The pipeline list endpoint already exists and returns `PipelineConfigSummary[]` with `id`, `name`, `description`, `stage_count`, `agent_count`, `updated_at` — all the data needed for the autocomplete dropdown (FR-014).
- TanStack Query caching ensures the list is fetched once and reused across multiple "@" triggers within the same session. The 30s staleTime matches the existing pipeline list cache configuration.
- Client-side filtering is appropriate for up to 100 pipelines (SC-007) — no server-side search endpoint needed.
- 150ms debounce balances responsiveness with avoiding excessive DOM operations on rapid typing.

**Alternatives Considered**:

- **Dedicated search endpoint**: Rejected — YAGNI for ≤100 pipelines; adds backend complexity without measurable benefit.
- **No caching (fetch on every "@" trigger)**: Rejected — unnecessary network requests; would violate SC-002 responsiveness on slow connections.
- **Prefetch on component mount**: Rejected — wastes bandwidth if user never types "@". TanStack Query's lazy fetch (on first "@") with caching is the right balance.

---

## R4: Pipeline ID Transport in Chat Submission

**Task**: Determine how to send the selected pipeline's identifier alongside the chat message content to the backend.

**Decision**: Add an optional `pipeline_id: str | None` field to the backend `ChatMessageRequest` Pydantic model (default `None`). On the frontend, the `useMentionAutocomplete` hook extracts the last valid mention token's `pipelineId` from the input before submission. The `sendMessage` API call includes `pipeline_id` in the request body. The backend `send_message` handler reads `pipeline_id` and, if present, passes it to the issue creation flow instead of the project's default pipeline assignment.

**Rationale**:

- Adding `pipeline_id` to `ChatMessageRequest` is backward-compatible — the field defaults to `None`, so existing clients and tests are unaffected (FR-013).
- The backend already resolves pipeline configuration from `project_settings` / pipeline assignment. Adding an optional override parameter requires minimal changes to the existing flow.
- Sending `pipeline_id` (not `pipeline_name`) guards against pipeline renames between mention and submission (FR-005).
- The "last valid mention wins" strategy (FR-007) is evaluated client-side before submission, so only one `pipeline_id` is ever sent.

**Alternatives Considered**:

- **Parse @mention from message content server-side**: Rejected — fragile text parsing, cannot reliably distinguish @mentions from plain text, and loses the pipeline ID (only has the name).
- **Separate endpoint for pipeline-aware chat**: Rejected — duplicates existing chat logic; a single optional field on the existing request is simpler.
- **Store pipeline selection in session state**: Rejected — couples mention selection to session, doesn't support per-message pipeline overrides.

---

## R5: Mention Token Rendering and Lifecycle

**Task**: Determine the visual design and interaction behavior of @mention tokens inline in the input.

**Decision**: Render each mention token as a `<span>` with `contentEditable="false"`, styled as a rounded chip with a distinct background color (e.g., `bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200`). The token displays the pipeline name prefixed with "@". Tokens have two visual states:

1. **Valid** (resolved): Blue chip styling — the referenced pipeline exists.
2. **Invalid** (unresolved/deleted): Red/amber chip styling with a warning icon — the pipeline no longer exists or was never matched (FR-010).

Backspace into a token removes it entirely as a single unit (FR-011). Clicking a token does nothing (it's non-editable). The token's `data-pipeline-id` attribute carries the pipeline UUID internally (FR-005).

**Rationale**:

- `contentEditable="false"` on the span makes the browser treat the token as an atomic inline element, giving us single-unit deletion (FR-011) and preventing partial editing for free.
- The two visual states (valid/invalid) map directly to FR-004 (visually distinct) and FR-010 (warning state).
- Using `data-*` attributes to store the pipeline ID keeps the rendering pure and allows extraction on submit without maintaining a separate token-to-ID map.
- Blue/red chip styling follows common @mention conventions (Slack, GitHub, Linear) and is accessible with sufficient contrast.

**Alternatives Considered**:

- **Token as a React portal rendered above the input**: Rejected — positioning is fragile and breaks inline flow.
- **Token as a custom element (`<mention-token>`)**: Rejected — adds web component complexity; standard `<span>` with `contentEditable="false"` achieves the same result.
- **Separate token list outside the input**: Rejected — violates FR-004's "inline in the chat input" requirement.

---

## R6: Multiple @mention Handling and Validation Strategy

**Task**: Determine how to handle multiple @mentions in a single chat input and validate mentions at submission time.

**Decision**: Allow multiple @mention tokens in the input but enforce a "last valid mention wins" policy (FR-007). On submit:

1. Extract all mention tokens from the input DOM (by querying `[data-pipeline-id]` spans).
2. Validate each token's `pipeline_id` against the cached pipeline list (or re-fetch if stale).
3. If multiple valid tokens exist, use the last one and display a transient notification: "Multiple pipelines mentioned — using [last pipeline name]."
4. If no valid tokens exist but invalid tokens are present, block submission with an error message (FR-008, FR-010).
5. If no tokens exist at all, proceed with default behavior (FR-013).

The `PipelineIndicator` component near the submit button always reflects the active (last valid) pipeline or shows a warning if the mention is invalid. This provides real-time feedback before submission (FR-009).

**Rationale**:

- The spec explicitly states "the system MUST use the last valid @mention" for multiple mentions (FR-007).
- Client-side validation before submission prevents round-trips for invalid mentions (FR-008).
- Re-validating against the pipeline list at submit time catches pipelines deleted between mention insertion and submission (FR-016).
- The `PipelineIndicator` provides the visual feedback required by FR-009 and User Story 3.

**Alternatives Considered**:

- **Prevent inserting more than one @mention**: Rejected — spec allows multiple mentions and defines handling rules (FR-007, User Story 5). Preventing insertion would be more restrictive than specified.
- **Server-side-only validation**: Rejected — poor UX; users would submit, wait for a response, then see an error. Client-side validation with the `PipelineIndicator` is faster and friendlier.
- **Use first mention instead of last**: Rejected — spec explicitly states "last valid @mention" (FR-007).
