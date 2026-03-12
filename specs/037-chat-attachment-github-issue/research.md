# Research: Attach User Chat Attachments to GitHub Parent Issue

**Feature**: 037-chat-attachment-github-issue | **Date**: 2026-03-12

## R1: Existing File Upload Infrastructure — Current State and Gaps

**Decision**: Extend the existing file upload pipeline rather than building a new one. The current `POST /chat/upload` endpoint, `useFileUpload` hook, `FilePreviewChips` component, and `ChatMessageRequest.file_urls` field already handle file selection, validation, upload, and URL collection. The gap is limited to persisting file URLs through the proposal/recommendation models and embedding them in the GitHub issue body at creation time.

**Rationale**: The current codebase already implements ~90% of the file attachment flow:
- Backend `upload_file()` endpoint validates file size (10 MB max), type (whitelist), and stores files in `/tmp/chat-uploads/`
- Frontend `useFileUpload` hook manages per-file state (pending, uploading, uploaded, error) and returns URLs via `uploadAll()`
- `ChatInterface.tsx` integrates file upload, collects URLs, and passes them via `onSendMessage(content, { fileUrls })`
- `ChatMessageRequest` model already has `file_urls: list[str]` field
- `_handle_feature_request()` already receives `file_urls` and stores them in `action_data`

The missing piece is the final connection: file URLs are stored in `action_data` of chat messages but are not propagated to `AITaskProposal` or `IssueRecommendation` models, and are not embedded in the issue body when `create_issue()` is called.

**Alternatives considered**:
- Building a separate attachment microservice (rejected: over-engineering for the current architecture; the monolith pattern is established)
- Using GitHub's GraphQL mutation for file uploads (rejected: GitHub's REST API for issue comments with file attachments is simpler and already used in the codebase)
- Storing files in a persistent cloud storage (rejected: temporary storage is sufficient since files are immediately attached to GitHub issues; persistence is GitHub's responsibility after attachment)

## R2: GitHub Issue File Attachment Mechanism — Markdown Link Embedding

**Decision**: Embed file URLs as markdown links in the GitHub issue body when creating the issue. For image files, use inline image syntax (`![filename](url)`) so they render as previews. For non-image files, use standard link syntax (`[filename](url)`). Append an "Attachments" section to the issue body.

**Rationale**: GitHub's REST API for issue creation (`POST /repos/{owner}/{repo}/issues`) accepts a `body` field in markdown format. The simplest and most reliable approach is to embed file references directly in the issue body as markdown. This approach:
- Requires zero additional API calls (URLs are embedded before the single `create_issue()` call)
- Works with the existing `create_issue()` method signature (only the `body` parameter changes)
- Renders natively in GitHub's markdown renderer (images display inline, files as clickable links)
- Preserves the chat session reference alongside attachments

**Alternatives considered**:
- Posting file attachments as separate issue comments after creation (rejected: requires additional API calls, creates race conditions, and fragments the attachment context from the issue description)
- Using GitHub's Upload API to create release assets and link them (rejected: release assets serve a different purpose; issue body markdown links are the standard pattern)
- Embedding base64-encoded file content directly in the body (rejected: increases body size dramatically, violates GitHub's 65,536 character body limit for large files)

## R3: Model Persistence — File URLs in Proposals and Recommendations

**Decision**: Add a `file_urls: list[str]` field (default empty list) to both `AITaskProposal` and `IssueRecommendation` Pydantic models. Store file URLs as a JSON-serialized string in the existing `action_data` column for proposals (via `chat_proposals` table) and in a new `file_urls TEXT` column for recommendations (via `chat_recommendations` table). No new database migration is needed for proposals since `action_data` already stores JSON; a migration is needed for recommendations.

**Rationale**: File URLs must survive the gap between message creation (when files are uploaded) and issue confirmation (when the user clicks "Confirm"). Currently, `_handle_feature_request()` stores `file_urls` in the chat message's `action_data`, but this data is not carried forward to the proposal/recommendation models that are used during confirmation. Adding the field to the Pydantic models ensures type safety and makes the data accessible during the `confirm_proposal()` and `confirm_recommendation()` flows.

**Alternatives considered**:
- Looking up `file_urls` from the original chat message at confirmation time (rejected: requires correlating messages to proposals, adds query complexity, and the message might be cleared by then)
- Storing file URLs only in a separate attachment table (rejected: adds unnecessary complexity; the URLs are small strings that belong logically with the proposal/recommendation)
- Using the existing `action_data` JSON column for both models (rejected: recommendations don't have an `action_data` column, and using an untyped JSON blob loses the benefits of Pydantic validation)

## R4: File URL to Markdown Conversion — Formatting Strategy

**Decision**: Create a utility function `format_attachments_markdown(file_urls: list[str]) -> str` that converts file URLs to a formatted markdown section. Image files (detected by extension: `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.svg`) use inline image syntax; all other files use link syntax. The section is appended to the issue body with a horizontal rule separator.

**Rationale**: A dedicated formatting function keeps the conversion logic centralized, testable, and reusable across both the `confirm_proposal()` and `confirm_recommendation()` code paths. Detecting image types by file extension is reliable since the upload endpoint already validates extensions, and the URLs contain the original filename with extension.

**Alternatives considered**:
- Formatting inline within each confirmation handler (rejected: duplicates logic between proposal and recommendation flows)
- Using content-type detection via HTTP HEAD requests (rejected: adds network overhead and failure modes; extensions are sufficient)
- Rendering all files as plain links without image previews (rejected: image previews significantly improve the GitHub issue reading experience)

## R5: Chat Session Reference in GitHub Issue Attachments

**Decision**: Include a brief reference line in the attachments section indicating the files were shared from a chat session. Format: `> 📎 Files shared from chat session`. Do not include the chat session ID or link since chat sessions are internal to the application and not accessible via a public URL.

**Rationale**: FR-008 requires "a reference to the originating chat session" in the GitHub issue. A descriptive label satisfies this requirement without exposing internal identifiers. The reference provides context for anyone reading the GitHub issue (they understand the files came from a chat interaction).

**Alternatives considered**:
- Including the chat session UUID (rejected: meaningless to GitHub readers and potentially a privacy concern)
- Including a deep link to the chat session (rejected: the chat application may not have stable public URLs for specific sessions)
- No reference at all (rejected: violates FR-008)

## R6: File Validation Alignment — Frontend and Backend Consistency

**Decision**: Reuse the existing validation constants from the backend (`MAX_FILE_SIZE_BYTES = 10 MB`, `MAX_FILES_PER_MESSAGE = 5`, `ALLOWED_TYPES`, `BLOCKED_TYPES`) and ensure the frontend `useFileUpload` hook applies matching validation. No changes needed to existing validation logic — it already covers FR-009 (size), FR-010 (type), and FR-011 (empty file).

**Rationale**: The existing validation in `upload_file()` already handles:
- Size validation: Files > 10 MB rejected with `file_too_large` error code
- Type validation: Only whitelisted extensions allowed (images, docs, archives)
- Blocked types: Executable files explicitly blocked
- Empty files: Implicitly rejected (zero-byte files pass type check but produce empty content)

The only gap is explicit zero-byte rejection (FR-011), which should be added as a validation check in the upload endpoint.

**Alternatives considered**:
- Raising the file size limit to match GitHub's 25 MB (rejected: the current 10 MB limit is more conservative and already established; changing it is out of scope)
- Adding MIME type sniffing (rejected: extension-based validation is already implemented and consistent; MIME sniffing adds complexity)

## R7: Error Handling and Retry Strategy

**Decision**: Leverage the existing `useFileUpload` hook's per-file error state for frontend error handling. The hook already tracks per-file status (pending, uploading, uploaded, error) and supports retry by re-calling `uploadAll()` for files in error state. On the backend, file upload failures return structured error responses (`JSONResponse` with `error_code` and `error` message). For GitHub issue creation failures, display the error in the chat UI and allow the user to retry the confirmation.

**Rationale**: The existing error handling infrastructure already satisfies FR-005 (descriptive error messages) and FR-006 (retry mechanism) for the upload phase. The confirmation phase (proposal/recommendation → issue) needs minimal additions: if `create_issue()` fails, the proposal/recommendation remains in PENDING status, allowing the user to retry.

**Alternatives considered**:
- Automatic retry with exponential backoff (rejected: the user should control retry timing; automatic retries can create duplicate issues)
- Queuing failed attachments for background retry (rejected: adds complexity; the current synchronous flow is simpler and more predictable)

## R8: Database Migration Strategy for File URLs Persistence

**Decision**: Add a new SQL migration file to add `file_urls TEXT` column to `chat_proposals` table and `chat_recommendations` table. The column stores a JSON-serialized array of URL strings. Default value is `NULL` (backward compatible with existing rows). The migration follows the existing numbered migration pattern (`NNN_*.sql`).

**Rationale**: The existing migration system applies `.sql` files by numeric prefix. Adding a new migration is the established pattern for schema changes. Using `TEXT` for JSON storage is consistent with the existing `action_data TEXT` column pattern used elsewhere in the chat tables.

**Alternatives considered**:
- Storing in the existing `action_data` column (rejected for proposals: `action_data` is on `chat_messages`, not `chat_proposals`; would require cross-table lookup)
- Using a separate `chat_attachments` table (rejected: over-normalized for simple URL storage; adds JOIN complexity without clear benefit)
- No migration — store only in Pydantic model (rejected: proposals/recommendations may be loaded from the database between creation and confirmation; data must persist)
