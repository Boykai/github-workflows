# Data Model: Attach User Chat Attachments to GitHub Parent Issue

**Feature**: 037-chat-attachment-github-issue | **Date**: 2026-03-12

## Entities

### ChatAttachment (Conceptual — not a separate database entity)

Represents a file uploaded by a user within a chat session. Stored as a URL string within the parent model's `file_urls` list.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `file_url` | `str` | URL path to the uploaded file (e.g., `/chat/uploads/abc123-screenshot.png`) | Must be a valid URL returned by `POST /chat/upload` |
| `filename` | `str` | Original filename including extension | Derived from file_url path segment |
| `content_type` | `str` | MIME type of the file | Validated on upload against ALLOWED_TYPES |
| `file_size` | `int` | Size in bytes | Max 10 MB (10,485,760 bytes) |
| `status` | `enum` | Upload status: `pending`, `uploading`, `uploaded`, `error` | Frontend-only state in `useFileUpload` hook |

**Note**: ChatAttachment is not stored as a separate database entity. The file is stored temporarily in `/tmp/chat-uploads/` and its URL is stored as a string in the `file_urls` list of `AITaskProposal` or `IssueRecommendation`. After the issue is created on GitHub, the file's lifecycle is managed by GitHub.

### AITaskProposal (Modified)

Existing entity representing an AI-generated task awaiting user confirmation. **Modified to add `file_urls` field**.

| Field | Type | Description | Validation | Status |
|-------|------|-------------|------------|--------|
| `proposal_id` | `UUID` | Unique proposal identifier | Auto-generated | Existing |
| `session_id` | `UUID` | Parent session ID | Required | Existing |
| `original_input` | `str` | User's natural language input | Required | Existing |
| `proposed_title` | `str` | AI-generated task title | Max 256 chars | Existing |
| `proposed_description` | `str` | AI-generated task description | Max 65,536 chars | Existing |
| `status` | `ProposalStatus` | PENDING, CONFIRMED, EXPIRED, CANCELLED | Default: PENDING | Existing |
| `edited_title` | `str \| None` | User-modified title | Optional | Existing |
| `edited_description` | `str \| None` | User-modified description | Optional | Existing |
| `created_at` | `datetime` | Proposal creation time | Auto-generated | Existing |
| `expires_at` | `datetime` | Auto-expiration time | Default: +10 minutes | Existing |
| `pipeline_name` | `str \| None` | Applied Agent Pipeline name | Optional | Existing |
| `pipeline_source` | `str \| None` | Pipeline resolution source | Optional | Existing |
| `selected_pipeline_id` | `str \| None` | Saved pipeline ID | Optional | Existing |
| **`file_urls`** | **`list[str]`** | **URLs of files to attach to GitHub issue** | **Default: empty list** | **NEW** |

**State transitions** (unchanged):
- `PENDING` → `CONFIRMED`: User clicks "Confirm" → files embedded in issue body → issue created
- `PENDING` → `EXPIRED`: 10-minute timeout
- `PENDING` → `CANCELLED`: User cancels

### IssueRecommendation (Modified)

Existing entity representing an AI-generated issue recommendation. **Modified to add `file_urls` field**.

| Field | Type | Description | Validation | Status |
|-------|------|-------------|------------|--------|
| `recommendation_id` | `UUID` | Unique recommendation ID | Auto-generated | Existing |
| `session_id` | `UUID` | Parent session ID | Required | Existing |
| `original_input` | `str` | User's feature request text | Required | Existing |
| `original_context` | `str` | Complete user input preserved verbatim | Default: empty | Existing |
| `title` | `str` | AI-generated issue title | Max 256 chars | Existing |
| `user_story` | `str` | User story (As a/I want/So that) | Required | Existing |
| `ui_ux_description` | `str` | UI/UX guidance | Required | Existing |
| `functional_requirements` | `list[str]` | Testable requirements | Required | Existing |
| `technical_notes` | `str` | Implementation hints | Default: empty | Existing |
| `selected_pipeline_id` | `str \| None` | Saved pipeline ID | Optional | Existing |
| `metadata` | `IssueMetadata` | Priority, size, dates, labels | Default factory | Existing |
| `status` | `RecommendationStatus` | PENDING, CONFIRMED, EXPIRED, CANCELLED | Default: PENDING | Existing |
| `created_at` | `datetime` | Creation timestamp | Auto-generated | Existing |
| `confirmed_at` | `datetime \| None` | Confirmation timestamp | Optional | Existing |
| **`file_urls`** | **`list[str]`** | **URLs of files to attach to GitHub issue** | **Default: empty list** | **NEW** |

**State transitions** (unchanged):
- `PENDING` → `CONFIRMED`: User clicks "Confirm" → files embedded in issue body → issue created
- `PENDING` → `EXPIRED`: Timeout
- `PENDING` → `CANCELLED`: User cancels

### AttachmentComment (Output — GitHub side)

Represents the formatted attachment section within a GitHub issue body. This is not a database entity but describes the markdown output produced by `format_attachments_markdown()`.

| Field | Type | Description |
|-------|------|-------------|
| `separator` | `str` | Horizontal rule (`---`) separating attachments from issue body |
| `header` | `str` | Section header: `## Attachments` |
| `chat_reference` | `str` | Blockquote: `> 📎 Files shared from chat session` |
| `file_entries` | `list[str]` | Markdown-formatted file links (image or standard) |

**Markdown format**:
```markdown
---

## Attachments

> 📎 Files shared from chat session

![screenshot.png](/chat/uploads/abc-screenshot.png)
[report.pdf](/chat/uploads/def-report.pdf)
[data.csv](/chat/uploads/ghi-data.csv)
```

## Relationships

```text
ChatSession ──creates──▶ ChatMessage (with file_urls in action_data)
ChatMessage ──spawns──▶ AITaskProposal (file_urls propagated)
ChatMessage ──spawns──▶ IssueRecommendation (file_urls propagated)
AITaskProposal ──on confirm──▶ GitHubIssue (file_urls embedded in body)
IssueRecommendation ──on confirm──▶ GitHubIssue (file_urls embedded in body)
format_attachments_markdown() ──formats──▶ AttachmentComment (markdown section)
```

## Database Changes

### Migration: `022_chat_file_urls.sql`

```sql
-- Add file_urls column to chat_proposals for persisting attachment URLs
ALTER TABLE chat_proposals ADD COLUMN file_urls TEXT DEFAULT NULL;

-- Add file_urls column to chat_recommendations for persisting attachment URLs
ALTER TABLE chat_recommendations ADD COLUMN file_urls TEXT DEFAULT NULL;
```

**Notes**:
- `TEXT` type stores JSON-serialized `list[str]` (e.g., `'["/chat/uploads/abc.png", "/chat/uploads/def.pdf"]'`)
- `DEFAULT NULL` ensures backward compatibility with existing rows
- No index needed — file_urls is not queried directly, only read when loading the model
- Follows existing pattern: `action_data TEXT` in `chat_messages` table uses the same approach

## File Type Classification

Used by `format_attachments_markdown()` to determine markdown syntax:

| Category | Extensions | Markdown Syntax |
|----------|-----------|-----------------|
| Image | `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.svg` | `![filename](url)` (inline image) |
| Document | `.pdf`, `.txt`, `.md`, `.csv`, `.json`, `.yaml`, `.yml` | `[filename](url)` (link) |
| Archive | `.zip` | `[filename](url)` (link) |

This classification mirrors the existing `ALLOWED_IMAGE_TYPES`, `ALLOWED_DOC_TYPES`, and `ALLOWED_ARCHIVE_TYPES` constants in `backend/src/api/chat.py`.
