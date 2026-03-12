# Quickstart: Attach User Chat Attachments to GitHub Parent Issue

**Feature**: 037-chat-attachment-github-issue | **Date**: 2026-03-12

## Overview

This feature connects the existing file upload pipeline to the GitHub issue creation flow. When a user uploads files in the chat interface and then confirms a proposal or recommendation, the uploaded files are automatically embedded in the GitHub issue body as markdown-formatted attachment links. Image files render as inline previews; other files appear as clickable download links.

## What Already Exists (~90% Complete)

The file upload infrastructure is already implemented end-to-end:

| Component | Location | What It Does |
|-----------|----------|--------------|
| Upload endpoint | `backend/src/api/chat.py` → `upload_file()` | Validates files (size, type), stores in `/tmp/chat-uploads/`, returns URL |
| Upload hook | `frontend/src/hooks/useFileUpload.ts` | Manages per-file state (pending→uploading→uploaded/error), returns URLs |
| File preview | `frontend/src/components/chat/FilePreviewChips.tsx` | Shows filename, icon, size, status for each file |
| Message request | `backend/src/models/chat.py` → `ChatMessageRequest` | Already has `file_urls: list[str]` field |
| Chat interface | `frontend/src/components/chat/ChatInterface.tsx` | Integrates upload hook, passes `fileUrls` to `onSendMessage()` |
| Feature handler | `backend/src/api/chat.py` → `_handle_feature_request()` | Already receives `file_urls` and stores in `action_data` |

## What Needs to Change

### 1. New Utility: `format_attachments_markdown()`

**File**: `backend/src/utils/attachment_formatter.py` (NEW)

Converts a list of file URLs into a formatted markdown section for the GitHub issue body.

```python
from pathlib import PurePosixPath

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}


def format_attachments_markdown(file_urls: list[str]) -> str:
    """Convert file URLs to a markdown attachments section.

    Image files use inline image syntax (![name](url));
    other files use standard link syntax ([name](url)).
    Returns empty string if no URLs provided.
    """
    if not file_urls:
        return ""

    lines = [
        "",
        "---",
        "",
        "## Attachments",
        "",
        "> 📎 Files shared from chat session",
        "",
    ]

    for url in file_urls:
        filename = PurePosixPath(url).name
        # Strip upload ID prefix (e.g., "abc123-screenshot.png" → "screenshot.png")
        if "-" in filename:
            filename = filename.split("-", 1)[1]
        ext = PurePosixPath(filename).suffix.lower()
        if ext in IMAGE_EXTENSIONS:
            lines.append(f"![{filename}]({url})")
        else:
            lines.append(f"[{filename}]({url})")

    return "\n".join(lines)
```

### 2. Model Changes: Add `file_urls` Field

**File**: `backend/src/models/recommendation.py` (MODIFIED)

Add to both `AITaskProposal` and `IssueRecommendation`:

```python
file_urls: list[str] = Field(default_factory=list, description="URLs of files to attach to GitHub issue")
```

### 3. Database Migration

**File**: `backend/src/migrations/022_chat_file_urls.sql` (NEW)

```sql
ALTER TABLE chat_proposals ADD COLUMN file_urls TEXT DEFAULT NULL;
ALTER TABLE chat_recommendations ADD COLUMN file_urls TEXT DEFAULT NULL;
```

### 4. Embed File URLs in Issue Body — Proposal Flow

**File**: `backend/src/api/chat.py` → `confirm_proposal()` (MODIFIED)

Before the `create_issue()` call (~line 696), append the attachment section:

```python
from src.utils.attachment_formatter import format_attachments_markdown

body = proposal.final_description or ""
# Embed file attachments in issue body
body += format_attachments_markdown(proposal.file_urls)
# Validate total length
if len(body) > GITHUB_ISSUE_BODY_MAX_LENGTH:
    ...
```

### 5. Embed File URLs in Issue Body — Recommendation Flow

**File**: `backend/src/api/workflow.py` → `confirm_recommendation()` (MODIFIED)

Pass `file_urls` from the recommendation through the workflow context so the orchestrator can embed them in the issue body. The exact integration point depends on how the orchestrator constructs the issue body.

### 6. Propagate file_urls from Chat Message to Models

**File**: `backend/src/api/chat.py` → `_handle_feature_request()` (MODIFIED)

When creating an `AITaskProposal` or `IssueRecommendation`, pass `file_urls` from the handler parameter to the model constructor:

```python
proposal = AITaskProposal(
    session_id=session.session_id,
    original_input=content,
    proposed_title=title,
    proposed_description=description,
    file_urls=file_urls or [],  # NEW
    ...
)
```

### 7. Zero-Byte File Validation

**File**: `backend/src/api/chat.py` → `upload_file()` (MODIFIED)

Add a check after reading file content:

```python
content = await file.read()
if len(content) == 0:
    return JSONResponse(
        status_code=400,
        content={
            "filename": file.filename,
            "error": "Empty file — cannot attach a file with no content",
            "error_code": "empty_file",
        },
    )
```

## Architecture

```text
┌─────────────────────────────────────────────────────────────────────┐
│                        USER CHAT INTERFACE                         │
│                                                                     │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐  │
│  │ File Picker  │───▶│  useFileUpload   │───▶│ FilePreviewChips │  │
│  │ (drag/drop)  │    │  (upload + state) │    │ (status display) │  │
│  └──────────────┘    └────────┬─────────┘    └──────────────────┘  │
│                               │                                     │
│                    file_urls: string[]                              │
│                               │                                     │
│  ┌────────────────────────────▼─────────────────────────────────┐  │
│  │              ChatInterface.onSendMessage()                    │  │
│  │              { content, fileUrls, aiEnhance, pipelineId }    │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                     POST /chat/messages
                     { content, file_urls }
                                  │
┌─────────────────────────────────▼───────────────────────────────────┐
│                           BACKEND                                    │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  _handle_feature_request(file_urls)                          │   │
│  │  ├── Creates AITaskProposal(file_urls=file_urls)  ──────┐   │   │
│  │  └── Creates IssueRecommendation(file_urls=file_urls) ──┤   │   │
│  └──────────────────────────────────────────────────────────┘   │   │
│                                                                  │   │
│                   User clicks "Confirm"                          │   │
│                         │                                        │   │
│  ┌──────────────────────▼───────────────────────────────────┐   │   │
│  │  confirm_proposal() / confirm_recommendation()            │   │   │
│  │  ├── body = proposal.final_description                    │   │   │
│  │  ├── body += format_attachments_markdown(proposal.file_urls)│  │   │
│  │  └── create_issue(title=..., body=body_with_attachments)  │   │   │
│  └──────────────────────────────────────────────────────────┘   │   │
│                         │                                        │   │
└─────────────────────────┼────────────────────────────────────────┘   │
                          │                                            │
               GitHub REST API                                         │
               POST /repos/{owner}/{repo}/issues                       │
               { title, body: "...\\n---\\n## Attachments\\n..." }     │
                          │                                            │
┌─────────────────────────▼────────────────────────────────────────────┘
│                     GITHUB ISSUE                                      │
│                                                                       │
│  Issue #123: Feature request title                                   │
│  ─────────────────────────────────                                   │
│  Feature description body...                                         │
│                                                                       │
│  ---                                                                  │
│  ## Attachments                                                       │
│  > 📎 Files shared from chat session                                 │
│                                                                       │
│  ![screenshot.png](/chat/uploads/abc-screenshot.png)                 │
│  [report.pdf](/chat/uploads/def-report.pdf)                          │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

## Test Strategy

### Backend Unit Tests (NEW)

**File**: `backend/tests/unit/test_attachment_formatter.py`

| Test | Description |
|------|-------------|
| `test_empty_list_returns_empty_string` | `format_attachments_markdown([])` → `""` |
| `test_single_image_file` | PNG URL → inline image markdown |
| `test_single_document_file` | PDF URL → standard link markdown |
| `test_mixed_file_types` | Image + document + archive → correct markdown per type |
| `test_filename_prefix_stripping` | `abc123-screenshot.png` → `screenshot.png` in display |
| `test_all_image_extensions` | Verify all 6 image extensions use `![]()` syntax |
| `test_chat_session_reference` | Output contains `📎 Files shared from chat session` |
| `test_separator_present` | Output starts with `---` separator |

### Backend Model Tests (MODIFIED)

**File**: `backend/tests/unit/test_recommendation.py`

| Test | Description |
|------|-------------|
| `test_proposal_file_urls_default` | New AITaskProposal has empty `file_urls` list |
| `test_proposal_file_urls_serialization` | `file_urls` round-trips through JSON serialization |
| `test_recommendation_file_urls_default` | New IssueRecommendation has empty `file_urls` list |

### Existing Tests (NO CHANGES)

Frontend tests for `useFileUpload`, `FilePreviewChips`, and `ChatInterface` already cover the upload flow, status display, and error handling. No new frontend tests are needed.
